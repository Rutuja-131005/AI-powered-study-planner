from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import random
from datetime import datetime, date
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'study-planner-secret-key-2026'
CORS(app, supports_credentials=True)

# ─────────────────────────────────────────────
# Flask-Mail Configuration (Gmail SMTP)
# ─────────────────────────────────────────────
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')   # set env var
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')   # set env var
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'noreply@studyplanner.com')

mail = Mail(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'study_planner.db')

# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            email        TEXT    NOT NULL UNIQUE,
            password     TEXT    NOT NULL,
            created_at   TEXT    DEFAULT (datetime('now'))
        )
    ''')

    # Tasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            date        TEXT    NOT NULL,
            time        TEXT    DEFAULT '',
            priority    TEXT    DEFAULT 'medium',
            status      TEXT    DEFAULT 'pending',
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Study Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_logs (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            date    TEXT    NOT NULL,
            hours   REAL    NOT NULL DEFAULT 0,
            note    TEXT    DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row) if row else None

# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated

def current_user_id():
    return session.get('user_id')

# ─────────────────────────────────────────────
# Welcome Email
# ─────────────────────────────────────────────
def send_welcome_email(user_name: str, user_email: str):
    """Send a rich HTML welcome email after successful registration."""
    try:
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f0f4f8; margin:0; padding:0; }}
  .wrapper {{ max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px;
              overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.10); }}
  .header {{ background:linear-gradient(135deg,#1a56db,#0ea5e9);
             padding:40px 32px; text-align:center; color:#fff; }}
  .header h1 {{ margin:0 0 8px; font-size:26px; font-weight:700; }}
  .header p  {{ margin:0; font-size:15px; opacity:0.9; }}
  .body {{ padding:36px 32px; color:#374151; }}
  .body h2 {{ color:#1a56db; font-size:20px; margin-top:0; }}
  .body p  {{ font-size:15px; line-height:1.7; color:#4b5563; }}
  .features {{ background:#f8fafc; border-radius:12px; padding:24px; margin:24px 0; }}
  .features h3 {{ margin:0 0 16px; color:#1e293b; font-size:16px; }}
  .feat-item {{ display:flex; align-items:flex-start; margin-bottom:14px; }}
  .feat-icon {{ font-size:22px; margin-right:12px; flex-shrink:0; }}
  .feat-text h4 {{ margin:0 0 2px; font-size:14px; color:#1e293b; font-weight:600; }}
  .feat-text p  {{ margin:0; font-size:13px; color:#6b7280; }}
  .cta {{ text-align:center; margin:28px 0 0; }}
  .cta a {{ display:inline-block; background:linear-gradient(135deg,#1a56db,#0ea5e9);
             color:#fff; text-decoration:none; padding:14px 36px; border-radius:10px;
             font-size:15px; font-weight:600; letter-spacing:0.02em; }}
  .footer {{ background:#f8fafc; padding:20px 32px; text-align:center;
              font-size:12px; color:#9ca3af; border-top:1px solid #e5e7eb; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Welcome to AI Smart Study Planner</h1>
    <p>Your personal study companion is ready!</p>
  </div>
  <div class="body">
    <h2>Hi {user_name}! 🎉</h2>
    <p>Thank you for registering on <strong>AI Smart Study Planner</strong>! We are thrilled to have you on board. Your account has been created successfully and you can now start organizing your studies like a pro.</p>

    <div class="features">
      <h3>✨ What you can do with AI Smart Study Planner:</h3>

      <div class="feat-item">
        <div class="feat-icon">📅</div>
        <div class="feat-text">
          <h4>Monthly Calendar View</h4>
          <p>Visualize all your study tasks on an interactive monthly calendar with color-coded priority indicators.</p>
        </div>
      </div>

      <div class="feat-item">
        <div class="feat-icon">✅</div>
        <div class="feat-text">
          <h4>Smart Task Management</h4>
          <p>Add, edit, delete and complete study tasks with title, description, date, time, and priority. Stay organized effortlessly.</p>
        </div>
      </div>

      <div class="feat-item">
        <div class="feat-icon">🗓️</div>
        <div class="feat-text">
          <h4>AI Smart Scheduler</h4>
          <p>Automatically organizes your pending tasks by deadline and priority, generating the optimal study plan for you.</p>
        </div>
      </div>

      <div class="feat-item">
        <div class="feat-icon">🤖</div>
        <div class="feat-text">
          <h4>AI Chatbot Assistant</h4>
          <p>Ask your chatbot anything — today's plan, pending tasks, study tips, hours logged, and more. Available 24/7.</p>
        </div>
      </div>

      <div class="feat-item">
        <div class="feat-icon">⏰</div>
        <div class="feat-text">
          <h4>Time-Based Reminders</h4>
          <p>Never miss a study session. Get browser notifications exactly when your scheduled tasks are due.</p>
        </div>
      </div>

      <div class="feat-item">
        <div class="feat-icon">📊</div>
        <div class="feat-text">
          <h4>Productivity Dashboard</h4>
          <p>Track your total tasks, completion rate, study hours logged, and today's progress — all at a glance.</p>
        </div>
      </div>
    </div>

    <p>Ready to ace your studies? Click the button below to get started:</p>
    <div class="cta">
      <a href="http://localhost:5000">Open AI Smart Study Planner →</a>
    </div>
  </div>
  <div class="footer">
    <p>You received this email because you registered at AI Smart Study Planner.</p>
    <p>© 2026 AI Smart Study Planner. All rights reserved.</p>
  </div>
</div>
</body>
</html>
"""
        msg = Message(
            subject="🎉 Welcome to AI Smart Study Planner!",
            recipients=[user_email],
            html=html_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"[Email Error] Could not send welcome email: {e}")
        return False

# ─────────────────────────────────────────────
# Serve pages
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/auth')
def auth_page():
    return send_from_directory('static', 'auth.html')

# ─────────────────────────────────────────────
# Auth API
# ─────────────────────────────────────────────
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    name     = (data.get('name') or '').strip()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not name or not email or not password:
        return jsonify({'error': 'Name, email and password are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'An account with this email already exists.'}), 409

    hashed = generate_password_hash(password)
    c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed))
    conn.commit()
    user_id = c.lastrowid
    conn.close()

    # Set session
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    # Send welcome email (non-blocking — won't fail registration if email fails)
    send_welcome_email(name, email)

    return jsonify({
        'message': f'Welcome, {name}! Registration successful.',
        'user': {'id': user_id, 'name': name, 'email': email},
        'email_sent': True
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email    = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = row_to_dict(c.fetchone())
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session['user_id']    = user['id']
    session['user_name']  = user['name']
    session['user_email'] = user['email']

    return jsonify({
        'message': f'Welcome back, {user["name"]}!',
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
    })

@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully.'})

@app.route('/auth/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 401
    return jsonify({
        'authenticated': True,
        'user': {
            'id':    session['user_id'],
            'name':  session['user_name'],
            'email': session['user_email']
        }
    })

# ─────────────────────────────────────────────
# Tasks API (protected)
# ─────────────────────────────────────────────
@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    uid = current_user_id()
    date_filter   = request.args.get('date')
    status_filter = request.args.get('status')
    conn = get_db()
    c = conn.cursor()
    query  = 'SELECT * FROM tasks WHERE user_id = ?'
    params = [uid]
    if date_filter:
        query += ' AND date = ?';   params.append(date_filter)
    if status_filter:
        query += ' AND status = ?'; params.append(status_filter)
    query += ' ORDER BY date ASC, time ASC'
    c.execute(query, params)
    tasks = [row_to_dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
@login_required
def create_task():
    uid  = current_user_id()
    data = request.get_json()
    if not data.get('title') or not data.get('date'):
        return jsonify({'error': 'title and date are required'}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (user_id, title, description, date, time, priority, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (uid, data['title'], data.get('description',''), data['date'],
          data.get('time',''), data.get('priority','medium'), data.get('status','pending')))
    conn.commit()
    task_id = c.lastrowid
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = row_to_dict(c.fetchone())
    conn.close()
    return jsonify(task), 201

@app.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    uid = current_user_id()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, uid))
    task = row_to_dict(c.fetchone())
    conn.close()
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    uid  = current_user_id()
    data = request.get_json()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM tasks WHERE id = ? AND user_id = ?', (task_id, uid))
    task = row_to_dict(c.fetchone())
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    up = {
        'title':       data.get('title',       task['title']),
        'description': data.get('description', task['description']),
        'date':        data.get('date',         task['date']),
        'time':        data.get('time',         task['time']),
        'priority':    data.get('priority',     task['priority']),
        'status':      data.get('status',       task['status']),
    }
    c.execute('''
        UPDATE tasks SET title=?, description=?, date=?, time=?, priority=?, status=? WHERE id=?
    ''', (up['title'], up['description'], up['date'], up['time'], up['priority'], up['status'], task_id))
    conn.commit()
    c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    task = row_to_dict(c.fetchone())
    conn.close()
    return jsonify(task)

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    uid = current_user_id()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM tasks WHERE id = ? AND user_id = ?', (task_id, uid))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Task not found'}), 404
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task deleted successfully'})

# ─────────────────────────────────────────────
# Dashboard API (protected)
# ─────────────────────────────────────────────
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    uid = current_user_id()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM tasks WHERE user_id=?', (uid,))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='completed'", (uid,))
    completed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND status='pending'", (uid,))
    pending = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(hours),0) FROM study_logs WHERE user_id=?', (uid,))
    hours = c.fetchone()[0]
    today_str = date.today().isoformat()
    c.execute('SELECT COUNT(*) FROM tasks WHERE user_id=? AND date=?', (uid, today_str))
    today_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND date=? AND status='completed'", (uid, today_str))
    today_done = c.fetchone()[0]
    conn.close()
    return jsonify({
        'total': total, 'completed': completed, 'pending': pending,
        'study_hours': round(hours, 1), 'today_tasks': today_tasks, 'today_done': today_done
    })

# ─────────────────────────────────────────────
# Smart Scheduler API (protected)
# ─────────────────────────────────────────────
PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}

@app.route('/schedule', methods=['GET'])
@login_required
def smart_schedule():
    uid = current_user_id()
    conn = get_db()
    c = conn.cursor()
    today_str = date.today().isoformat()
    c.execute("SELECT * FROM tasks WHERE user_id=? AND status='pending' AND date>=?", (uid, today_str))
    tasks = [row_to_dict(r) for r in c.fetchall()]
    conn.close()
    tasks.sort(key=lambda t: (t['date'], PRIORITY_ORDER.get(t['priority'],1), t['time'] or '99:99'))
    grouped = {}
    for task in tasks:
        d = task['date']
        if d not in grouped: grouped[d] = []
        grouped[d].append(task)
    schedule = [{'date': d, 'tasks': dt} for d, dt in grouped.items()]
    return jsonify({'schedule': schedule, 'total_pending': len(tasks)})

# ─────────────────────────────────────────────
# Study Logs API (protected)
# ─────────────────────────────────────────────
@app.route('/study-logs', methods=['GET'])
@login_required
def get_study_logs():
    uid = current_user_id()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM study_logs WHERE user_id=? ORDER BY date DESC', (uid,))
    logs = [row_to_dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/study-logs', methods=['POST'])
@login_required
def add_study_log():
    uid  = current_user_id()
    data = request.get_json()
    if not data.get('hours'):
        return jsonify({'error': 'hours is required'}), 400
    conn = get_db()
    c = conn.cursor()
    log_date = data.get('date', date.today().isoformat())
    c.execute('INSERT INTO study_logs (user_id, date, hours, note) VALUES (?, ?, ?, ?)',
              (uid, log_date, float(data['hours']), data.get('note','')))
    conn.commit()
    log_id = c.lastrowid
    c.execute('SELECT * FROM study_logs WHERE id=?', (log_id,))
    log = row_to_dict(c.fetchone())
    conn.close()
    return jsonify(log), 201

# ─────────────────────────────────────────────
# AI Chatbot API (protected)
# ─────────────────────────────────────────────
def detect_intent(message: str):
    msg = message.lower().strip()
    if any(k in msg for k in ['today', 'what should i study', 'study today', 'plan today']):
        return 'today_tasks'
    if any(k in msg for k in ['pending', 'incomplete', 'not done', 'remaining']):
        return 'pending_tasks'
    if any(k in msg for k in ['completed', 'done', 'finished', 'complete']):
        return 'completed_tasks'
    if any(k in msg for k in ['schedule', 'plan', 'organize', 'arrange']):
        return 'schedule'
    if any(k in msg for k in ['high priority', 'urgent', 'important', 'priority']):
        return 'priority_tasks'
    if any(k in msg for k in ['reschedule', 'postpone', 'delay', 'move']):
        return 'reschedule'
    if any(k in msg for k in ['hours', 'time studied', 'study time', 'log', 'progress']):
        return 'study_hours'
    if any(k in msg for k in ['help', 'commands', 'what can you do', 'how']):
        return 'help'
    if any(k in msg for k in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
        return 'greeting'
    if any(k in msg for k in ['tip', 'advice', 'suggestion', 'improve', 'better']):
        return 'tips'
    return 'unknown'

def build_task_list_text(tasks):
    if not tasks: return None
    return '\n'.join(
        f"• **{t['title']}** ({t['priority']} priority) — {t['date']}" +
        (f" at {t['time']}" if t.get('time') else '')
        for t in tasks
    )

STUDY_TIPS = [
    "Use the **Pomodoro Technique**: study for 25 minutes, then take a 5-minute break.",
    "Active recall beats passive reading. Quiz yourself after each topic!",
    "Sleep is crucial for memory consolidation — aim for 7-8 hours.",
    "Summarize what you learned in your own words — it cements understanding.",
    "Set specific daily goals rather than vague intentions like 'study math'.",
    "Spaced repetition: review topics at increasing intervals for better retention.",
    "Minimize distractions — put your phone on Do Not Disturb during study sessions.",
    "Regular exercise improves focus and cognitive performance.",
    "Break large tasks into smaller subtasks to avoid feeling overwhelmed.",
    "Stay hydrated — even mild dehydration reduces concentration."
]

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    uid  = current_user_id()
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'reply': 'Please type a message!', 'type': 'error'})

    intent    = detect_intent(user_message)
    today_str = date.today().isoformat()
    conn = get_db()
    c = conn.cursor()

    if intent == 'greeting':
        c.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND date=? AND status='pending'", (uid, today_str))
        cnt = c.fetchone()[0]
        conn.close()
        name = session.get('user_name', 'there')
        msg = f"Hello {name}! You have **{cnt} pending task(s)** for today."
        msg += " Let's get started!" if cnt > 0 else " You're all caught up for today!"
        return jsonify({'reply': msg, 'type': 'greeting'})

    elif intent == 'today_tasks':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY time ASC", (uid, today_str))
        tasks = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not tasks:
            return jsonify({'reply': "You have **no tasks scheduled for today**. Use the Tasks section to add some!", 'type': 'info'})
        pending = [t for t in tasks if t['status']=='pending']
        done    = [t for t in tasks if t['status']=='completed']
        text = f"**Today's Study Plan** ({today_str}):\n\n"
        if pending: text += f"**Pending ({len(pending)}):**\n" + build_task_list_text(pending)
        if done:    text += f"\n\n**Completed ({len(done)}):**\n" + build_task_list_text(done)
        return jsonify({'reply': text, 'type': 'task_list', 'tasks': tasks})

    elif intent == 'pending_tasks':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND status='pending' ORDER BY date ASC, time ASC", (uid,))
        tasks = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not tasks:
            return jsonify({'reply': "You have **no pending tasks**. You're all caught up!", 'type': 'success'})
        return jsonify({'reply': f"**Pending Tasks ({len(tasks)}):**\n\n" + build_task_list_text(tasks), 'type': 'task_list', 'tasks': tasks})

    elif intent == 'completed_tasks':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND status='completed' ORDER BY date DESC", (uid,))
        tasks = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not tasks:
            return jsonify({'reply': "No completed tasks yet. Start studying and mark tasks as complete!", 'type': 'info'})
        return jsonify({'reply': f"**Completed Tasks ({len(tasks)}):**\n\n" + build_task_list_text(tasks), 'type': 'task_list', 'tasks': tasks})

    elif intent == 'schedule':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND status='pending' AND date>=? ORDER BY date ASC, time ASC", (uid, today_str))
        tasks = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not tasks:
            return jsonify({'reply': "No upcoming pending tasks. Add tasks to generate a smart schedule!", 'type': 'info'})
        tasks.sort(key=lambda t: (t['date'], PRIORITY_ORDER.get(t['priority'],1), t['time'] or '99:99'))
        text = f"**Your Smart Study Schedule** ({len(tasks)} tasks):\n\n"
        current_date = None
        for t in tasks:
            if t['date'] != current_date:
                current_date = t['date']
                text += f"\n**{current_date}:**\n"
            flag = '[H]' if t['priority']=='high' else '[M]' if t['priority']=='medium' else '[L]'
            text += f"  {flag} {t['title']}" + (f" at {t['time']}" if t.get('time') else '') + "\n"
        return jsonify({'reply': text, 'type': 'schedule', 'tasks': tasks})

    elif intent == 'priority_tasks':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND priority='high' AND status='pending' ORDER BY date ASC", (uid,))
        tasks = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not tasks:
            return jsonify({'reply': "No high-priority pending tasks! You're on top of the urgent stuff.", 'type': 'success'})
        text = f"**High Priority Pending Tasks ({len(tasks)}):**\n\n" + build_task_list_text(tasks)
        text += "\n\n*Tackle these first for maximum impact!*"
        return jsonify({'reply': text, 'type': 'task_list', 'tasks': tasks})

    elif intent == 'reschedule':
        c.execute("SELECT * FROM tasks WHERE user_id=? AND status='pending' AND date<? ORDER BY date ASC", (uid, today_str))
        overdue = [row_to_dict(r) for r in c.fetchall()]
        conn.close()
        if not overdue:
            return jsonify({'reply': "No overdue tasks to reschedule! All your pending tasks are on schedule.", 'type': 'success'})
        text = f"**Overdue Tasks Needing Reschedule ({len(overdue)}):**\n\n" + build_task_list_text(overdue)
        text += "\n\n*Tip: Edit each task's date to reschedule it to a future date.*"
        return jsonify({'reply': text, 'type': 'task_list', 'tasks': overdue})

    elif intent == 'study_hours':
        c.execute('SELECT COALESCE(SUM(hours),0) FROM study_logs WHERE user_id=?', (uid,))
        total_hours = c.fetchone()[0]
        c.execute('SELECT COALESCE(SUM(hours),0) FROM study_logs WHERE user_id=? AND date=?', (uid, today_str))
        today_hours = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM study_logs WHERE user_id=?', (uid,))
        sessions = c.fetchone()[0]
        conn.close()
        text = f"**Your Study Progress:**\n\nTotal study hours: **{round(total_hours,1)}h**\nToday's hours: **{round(today_hours,1)}h**\nSessions logged: **{sessions}**\n\n"
        if total_hours < 10: text += "*Keep going! Consistency is key. Aim for at least 2 hours daily.*"
        elif total_hours < 50: text += "*Great progress! You're building solid study habits.*"
        else: text += "*Impressive dedication! Keep up the excellent work!*"
        return jsonify({'reply': text, 'type': 'stats'})

    elif intent == 'tips':
        conn.close()
        return jsonify({'reply': f"**Study Tip:**\n\n{random.choice(STUDY_TIPS)}", 'type': 'tip'})

    elif intent == 'help':
        conn.close()
        text = ("**Study Assistant — Available Commands:**\n\n"
                "Today's plan — 'What should I study today?'\n"
                "Pending tasks — 'Show my pending tasks'\n"
                "Completed tasks — 'Show completed tasks'\n"
                "Smart schedule — 'Show my schedule'\n"
                "Priority tasks — 'What are my urgent tasks?'\n"
                "Reschedule — 'What tasks need rescheduling?'\n"
                "Study hours — 'How many hours have I studied?'\n"
                "Study tips — 'Give me a study tip'\n"
                "Greeting — 'Hello!'")
        return jsonify({'reply': text, 'type': 'help'})

    else:
        conn.close()
        responses = [
            "I didn't quite understand that. Try asking:\n• 'What should I study today?'\n• 'Show pending tasks'\n• 'Give me a study tip'\n• Type **'help'** for all commands!",
            "Could you rephrase that? I understand queries like:\n• 'Show my schedule'\n• 'What are urgent tasks?'\n• 'How many hours have I studied?'",
            "I'm not sure what you mean. Type **'help'** to see everything I can do!"
        ]
        return jsonify({'reply': random.choice(responses), 'type': 'unknown'})


if __name__ == '__main__':
    init_db()
    print("Study Planner running at http://localhost:5000")
    app.run(debug=True, port=5000)
