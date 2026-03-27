/* ═══════════════════════════════════════════════════
   app.js — Core Logic: CRUD, Dashboard, Reminders
   ═══════════════════════════════════════════════════ */

const API = '';  // Same origin

// ── Global State ──
let allTasks = [];
let selectedCalDate = null;

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  loadUserInfo();
  setGreeting();
  setNavTime();
  setInterval(setNavTime, 1000);
  setInterval(checkReminders, 30000);
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('logDate').value = today;
  document.getElementById('taskDate').value = today;
  loadDashboard();
  loadAllTasks();
  requestNotificationPermission();
});

// ── Navigation ──
function showSection(id, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if (btn) btn.classList.add('active');

  // Lazy-load section data
  if (id === 'dashboard') { loadDashboard(); loadTodayTasks(); }
  if (id === 'calendar')  { renderCalendar(); }
  if (id === 'tasks')     { loadAllTasks(); }
  if (id === 'schedule')  { loadSchedule(); }
}

// ── Time & Greeting ──
function setNavTime() {
  const now = new Date();
  document.getElementById('navTime').textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function setGreeting() {
  const h = new Date().getHours();
  let greet = h < 12 ? '🌅 Good morning' : h < 17 ? '☀️ Good afternoon' : '🌙 Good evening';
  const el = document.getElementById('dashGreeting');
  if (el) el.textContent = `${greet}! Here's your study overview.`;
}

// ── Dashboard ──
async function loadDashboard() {
  try {
    const res = await fetch(`${API}/dashboard`);
    const d = await res.json();
    document.getElementById('statTotal').textContent     = d.total;
    document.getElementById('statCompleted').textContent = d.completed;
    document.getElementById('statPending').textContent   = d.pending;
    document.getElementById('statHours').textContent     = d.study_hours + 'h';
    document.getElementById('statTodayTasks').textContent= d.today_tasks;
    document.getElementById('statTodayDone').textContent = d.today_done;

    const pct = d.total > 0 ? Math.round((d.completed / d.total) * 100) : 0;
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('progressPct').textContent = pct + '%';

    loadTodayTasks();
  } catch (e) { console.error('Dashboard error:', e); }
}

async function loadTodayTasks() {
  const today = new Date().toISOString().split('T')[0];
  try {
    const res = await fetch(`${API}/tasks?date=${today}`);
    const tasks = await res.json();
    const el = document.getElementById('todayTasksList');
    if (!tasks.length) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon"><i data-lucide="clipboard-list"></i></div><p>No tasks for today</p></div>`;
      lucide.createIcons({ root: el });
      return;
    }
    el.innerHTML = tasks.map(t => `
      <div class="today-task-item ${t.status === 'completed' ? 'done' : ''}">
        <div class="priority-dot ${t.priority}"></div>
        <span style="flex:1">${t.title}</span>
        ${t.time ? `<span class="task-time-badge"><i data-lucide="clock"></i> ${formatTime(t.time)}</span>` : ''}
        <span class="${t.status === 'completed' ? 'badge-completed' : 'badge-pending'} task-badge">
          <i data-lucide="${t.status === 'completed' ? 'check-circle-2' : 'clock'}"></i>
        </span>
      </div>
    `).join('');
    lucide.createIcons({ root: el });
  } catch (e) { console.error(e); }
}

// ── Log Study Hours ──
async function logStudyHours() {
  const hours = parseFloat(document.getElementById('logHours').value);
  const date  = document.getElementById('logDate').value;
  const note  = document.getElementById('logNote').value;
  if (!hours || hours <= 0) { showToast('Please enter valid hours', 'error'); return; }
  if (!date) { showToast('Please select a date', 'error'); return; }
  try {
    const res = await fetch(`${API}/study-logs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hours, date, note })
    });
    if (res.ok) {
      showToast(`Logged ${hours}h of study!`, 'success');
      document.getElementById('logHours').value = '';
      document.getElementById('logNote').value  = '';
      loadDashboard();
    }
  } catch (e) { showToast('Failed to log hours', 'error'); }
}

// ── Tasks CRUD ──
async function loadAllTasks(filters = {}) {
  try {
    let url = `${API}/tasks?`;
    if (filters.status)   url += `status=${filters.status}&`;
    if (filters.date)     url += `date=${filters.date}&`;
    const res = await fetch(url);
    allTasks = await res.json();
    // Client-side priority filter
    let tasks = allTasks;
    if (filters.priority) tasks = tasks.filter(t => t.priority === filters.priority);
    renderTaskList(tasks, 'taskList');
  } catch (e) { console.error(e); }
}

function renderTaskList(tasks, containerId) {
  const el = document.getElementById(containerId);
  if (!tasks.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon"><i data-lucide="inbox"></i></div><p>No tasks found</p></div>`;
    lucide.createIcons({ root: el });
    return;
  }
  el.innerHTML = tasks.map(t => buildTaskCard(t)).join('');
  lucide.createIcons({ root: el });
}

function buildTaskCard(t) {
  return `
    <div class="task-card ${t.status === 'completed' ? 'completed-task' : ''}" id="task-card-${t.id}">
      <div class="task-check ${t.status === 'completed' ? 'checked' : ''}"
           onclick="toggleTaskStatus(${t.id}, '${t.status}')" title="Toggle complete">
        <i data-lucide="check"></i>
      </div>
      <div class="priority-dot ${t.priority}"></div>
      <div class="task-info">
        <div class="task-title">${escHtml(t.title)}</div>
        <div class="task-meta">
          <span><i data-lucide="calendar"></i> ${t.date}</span>
          ${t.time ? `<span><i data-lucide="clock"></i> ${formatTime(t.time)}</span>` : ''}
          <span class="task-badge badge-${t.priority}">${capitalize(t.priority)}</span>
          <span class="task-badge badge-${t.status}">${t.status === 'completed' ? '<i data-lucide="check-circle-2"></i> Done' : '<i data-lucide="clock"></i> Pending'}</span>
        </div>
        ${t.description ? `<div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">${escHtml(t.description)}</div>` : ''}
      </div>
      <div class="task-actions">
        <button class="btn btn-ghost btn-icon" onclick="openEditTaskModal(${t.id})" title="Edit"><i data-lucide="edit-2"></i></button>
        <button class="btn btn-danger btn-icon" onclick="deleteTask(${t.id})" title="Delete"><i data-lucide="trash-2"></i></button>
      </div>
    </div>
  `;
}

async function toggleTaskStatus(id, currentStatus) {
  const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
  try {
    const res = await fetch(`${API}/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast(newStatus === 'completed' ? 'Task completed!' : 'Task marked pending', newStatus === 'completed' ? 'success' : 'info');
      loadAllTasks(getCurrentFilters());
      loadDashboard();
      if (window._calendarLoaded) renderCalendar();
    }
  } catch (e) { showToast('Update failed', 'error'); }
}

async function deleteTask(id) {
  if (!confirm('Delete this task?')) return;
  try {
    const res = await fetch(`${API}/tasks/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Task deleted', 'info');
      loadAllTasks(getCurrentFilters());
      loadDashboard();
      if (window._calendarLoaded) renderCalendar();
    }
  } catch (e) { showToast('Delete failed', 'error'); }
}

// ── Modal ──
function openAddTaskModal() {
  document.getElementById('editTaskId').value = '';
  document.getElementById('taskTitle').value   = '';
  document.getElementById('taskDesc').value    = '';
  document.getElementById('taskDate').value    = new Date().toISOString().split('T')[0];
  document.getElementById('taskTime').value    = '';
  document.getElementById('taskPriority').value = 'medium';
  document.getElementById('taskStatus').value   = 'pending';
  document.getElementById('modalTitle').textContent = 'Add New Task';
  document.getElementById('taskModal').classList.add('open');
}

function openAddTaskModalForDate() {
  openAddTaskModal();
  if (selectedCalDate) document.getElementById('taskDate').value = selectedCalDate;
}

function openEditTaskModal(id) {
  const task = allTasks.find(t => t.id === id);
  if (!task) return;
  document.getElementById('editTaskId').value   = task.id;
  document.getElementById('taskTitle').value    = task.title;
  document.getElementById('taskDesc').value     = task.description || '';
  document.getElementById('taskDate').value     = task.date;
  document.getElementById('taskTime').value     = task.time || '';
  document.getElementById('taskPriority').value = task.priority;
  document.getElementById('taskStatus').value   = task.status;
  document.getElementById('modalTitle').textContent = 'Edit Task';
  document.getElementById('taskModal').classList.add('open');
}

function closeTaskModal() {
  document.getElementById('taskModal').classList.remove('open');
}

function closeModalOnOverlay(e) {
  if (e.target === document.getElementById('taskModal')) closeTaskModal();
}

async function saveTask() {
  const id    = document.getElementById('editTaskId').value;
  const title = document.getElementById('taskTitle').value.trim();
  const date  = document.getElementById('taskDate').value;
  if (!title) { showToast('Title is required', 'error'); return; }
  if (!date)  { showToast('Date is required',  'error'); return; }

  const payload = {
    title,
    description: document.getElementById('taskDesc').value.trim(),
    date,
    time:     document.getElementById('taskTime').value,
    priority: document.getElementById('taskPriority').value,
    status:   document.getElementById('taskStatus').value,
  };

  try {
    const url    = id ? `${API}/tasks/${id}` : `${API}/tasks`;
    const method = id ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast(id ? 'Task updated!' : 'Task added!', 'success');
      closeTaskModal();
      loadAllTasks(getCurrentFilters());
      loadDashboard();
      if (window._calendarLoaded) renderCalendar();
    } else {
      const err = await res.json();
      showToast(err.error || 'Failed to save task', 'error');
    }
  } catch (e) { showToast('Network error', 'error'); }
}

// ── Filters ──
function applyFilters() { loadAllTasks(getCurrentFilters()); }
function clearFilters() {
  document.getElementById('filterStatus').value   = '';
  document.getElementById('filterPriority').value = '';
  document.getElementById('filterDate').value     = '';
  loadAllTasks();
}
function getCurrentFilters() {
  return {
    status:   document.getElementById('filterStatus').value,
    priority: document.getElementById('filterPriority').value,
    date:     document.getElementById('filterDate').value,
  };
}

// ── Smart Schedule ──
async function loadSchedule() {
  try {
    const res = await fetch(`${API}/schedule`);
    const data = await res.json();
    const el = document.getElementById('scheduleContent');
    if (!data.schedule.length) {
      el.innerHTML = `<div class="glass-card"><div class="empty-state"><div class="empty-icon"><i data-lucide="party-popper"></i></div><p>No upcoming pending tasks! You're all caught up.</p></div></div>`;
      lucide.createIcons({ root: el });
      return;
    }
    el.innerHTML = data.schedule.map(day => {
      const tasks = day.tasks.map(t => {
        return `
          <div class="schedule-task-item">
            <span class="schedule-task-name">${escHtml(t.title)}</span>
            ${t.time ? `<span class="task-time-badge"><i data-lucide="clock"></i> ${formatTime(t.time)}</span>` : ''}
            <span class="task-badge badge-${t.priority}">${capitalize(t.priority)}</span>
          </div>`;
      }).join('');
      const label = isToday(day.date) ? '— Today' : isTomorrow(day.date) ? '— Tomorrow' : '';
      return `
        <div class="schedule-day-card">
          <div class="schedule-day-header">
            <span class="schedule-day-title"><i data-lucide="calendar"></i> ${formatDate(day.date)} <span style="font-size:0.8rem;color:var(--text-secondary);margin-left:0.3rem">${label}</span></span>
            <span class="schedule-day-count">${day.tasks.length} task${day.tasks.length !== 1 ? 's' : ''}</span>
          </div>
          <div class="schedule-tasks">${tasks}</div>
        </div>`;
    }).join('');
    lucide.createIcons({ root: el });
  } catch (e) { console.error(e); }
}

// ── Browser Notifications ──
function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

function checkReminders() {
  const now = new Date();
  const todayStr = now.toISOString().split('T')[0];
  const curTime  = now.toTimeString().slice(0, 5);  // HH:MM

  allTasks.forEach(t => {
    if (t.status === 'completed') return;
    if (t.date !== todayStr) return;
    if (!t.time) return;
    if (t.time === curTime) {
      fireReminder(t);
    }
  });
}

function fireReminder(task) {
  // Browser notification
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(`⏰ Study Reminder: ${task.title}`, {
      body: `It's time to study! Priority: ${task.priority}`,
      icon: '/static/favicon.ico',
      tag: `task-${task.id}`
    });
  }
  // Fallback alert
  showToast(`⏰ Reminder: ${task.title}`, 'info');
}

// ── Auth: Load user info & Logout ──
async function loadUserInfo() {
  try {
    const res = await fetch('/auth/me', { credentials: 'include' });
    if (!res.ok) { window.location.href = '/auth'; return; }
    const data = await res.json();
    const name = data.user.name;
    // Header user pill
    const nameEl = document.getElementById('userNameDisplay');
    if (nameEl) nameEl.textContent = name;
    // Avatar initial
    const avatarEl = document.getElementById('userAvatarInitial');
    if (avatarEl) avatarEl.textContent = name ? name.charAt(0).toUpperCase() : '?';
    // Footer username
    const footerEl = document.getElementById('footerUserName');
    if (footerEl) footerEl.textContent = name;
  } catch { window.location.href = '/auth'; }
}

async function handleLogout() {
  try {
    await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
  } catch {}
  window.location.href = '/auth';
}

// ── Utility ──
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 3500);
}

function escHtml(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function capitalize(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
function formatTime(t) {
  if (!t) return '';
  const [h, m] = t.split(':');
  const num = parseInt(h, 10);
  return `${num % 12 || 12}:${m} ${num >= 12 ? 'PM' : 'AM'}`;
}
function formatDate(d) {
  if (!d) return '';
  return new Date(d + 'T00:00:00').toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' });
}
function isToday(dateStr) { return dateStr === new Date().toISOString().split('T')[0]; }
function isTomorrow(dateStr) {
  const t = new Date(); t.setDate(t.getDate() + 1);
  return dateStr === t.toISOString().split('T')[0];
}
