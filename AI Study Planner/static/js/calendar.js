/* ═══════════════════════════════════════════════════
   calendar.js — Monthly Calendar Rendering
   ═══════════════════════════════════════════════════ */

let calYear  = new Date().getFullYear();
let calMonth = new Date().getMonth();   // 0-indexed
let calTasks = {};  // { 'YYYY-MM-DD': [task, …] }

window._calendarLoaded = false;

// ── Public entry point ──
async function renderCalendar() {
  window._calendarLoaded = true;
  await fetchCalendarTasks();
  drawCalendar();
}

// ── Fetch all tasks and index by date ──
async function fetchCalendarTasks() {
  try {
    const res = await fetch(`/tasks`);
    const tasks = await res.json();
    calTasks = {};
    tasks.forEach(t => {
      if (!calTasks[t.date]) calTasks[t.date] = [];
      calTasks[t.date].push(t);
    });
  } catch (e) { console.error('Calendar fetch error:', e); }
}

// ── Draw the calendar grid ──
function drawCalendar() {
  const MONTHS = ['January','February','March','April','May','June',
                  'July','August','September','October','November','December'];
  document.getElementById('calMonthTitle').textContent = `${MONTHS[calMonth]} ${calYear}`;

  const firstDay  = new Date(calYear, calMonth, 1).getDay();   // 0=Sun
  const daysInMonth = new Date(calYear, calMonth + 1, 0).getDate();
  const daysInPrev  = new Date(calYear, calMonth, 0).getDate();

  const today = new Date().toISOString().split('T')[0];
  const grid  = document.getElementById('calGrid');
  grid.innerHTML = '';

  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;

  for (let i = 0; i < totalCells; i++) {
    const cell = document.createElement('div');
    cell.className = 'cal-day';

    let dayNum, dateStr, isOther = false;

    if (i < firstDay) {
      dayNum = daysInPrev - firstDay + i + 1;
      const m = calMonth === 0 ? 12 : calMonth;
      const y = calMonth === 0 ? calYear - 1 : calYear;
      dateStr = `${y}-${String(m).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
      isOther = true;
    } else if (i >= firstDay + daysInMonth) {
      dayNum = i - firstDay - daysInMonth + 1;
      const m = calMonth === 11 ? 1 : calMonth + 2;
      const y = calMonth === 11 ? calYear + 1 : calYear;
      dateStr = `${y}-${String(m).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
      isOther = true;
    } else {
      dayNum  = i - firstDay + 1;
      dateStr = `${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
    }

    if (isOther)        cell.classList.add('other-month');
    if (dateStr === today) cell.classList.add('today');
    if (dateStr === selectedCalDate) cell.classList.add('selected');

    // Day number
    const num = document.createElement('div');
    num.className = 'cal-day-num';
    num.textContent = dayNum;
    cell.appendChild(num);

    // Task dots
    const dayTasks = calTasks[dateStr] || [];
    if (dayTasks.length) {
      const dots = document.createElement('div');
      dots.className = 'cal-dots';
      // Show up to 4 dots
      dayTasks.slice(0, 4).forEach(t => {
        const dot = document.createElement('div');
        dot.className = `cal-dot ${t.status === 'completed' ? 'done' : t.priority}`;
        dots.appendChild(dot);
      });
      cell.appendChild(dots);
    }

    cell.addEventListener('click', () => selectCalDay(dateStr, dayTasks));
    grid.appendChild(cell);
  }
}

// ── Month navigation ──
function changeMonth(delta) {
  calMonth += delta;
  if (calMonth > 11) { calMonth = 0;  calYear++; }
  if (calMonth < 0)  { calMonth = 11; calYear--; }
  renderCalendar();
}

// ── Day selection ──
function selectCalDay(dateStr, tasks) {
  selectedCalDate = dateStr;
  // Re-draw to show selection
  drawCalendar();
  showDayDetail(dateStr, tasks);
}

function showDayDetail(dateStr, tasks) {
  const panel = document.getElementById('dayDetail');
  const title = document.getElementById('dayDetailTitle');
  const list  = document.getElementById('dayDetailList');

  title.innerHTML = `<i data-lucide="calendar-days"></i> <span>${formatDate(dateStr)}</span>`;
  panel.style.display = 'block';

  if (!tasks.length) {
    list.innerHTML = `<div class="empty-state" style="padding:1.5rem"><div class="empty-icon"><i data-lucide="clipboard-list"></i></div><p>No tasks this day. Add one!</p></div>`;
    lucide.createIcons({ root: panel });
    return;
  }

  list.innerHTML = tasks.map(t => `
    <div class="today-task-item ${t.status === 'completed' ? 'done' : ''}">
      <div class="priority-dot ${t.priority}"></div>
      <span style="flex:1">${escHtml(t.title)}</span>
      ${t.time ? `<span class="task-time-badge"><i data-lucide="clock"></i> ${formatTime(t.time)}</span>` : ''}
      <span class="task-badge badge-${t.priority}">${t.priority.charAt(0).toUpperCase() + t.priority.slice(1)}</span>
      <span class="task-badge badge-${t.status}"><i data-lucide="${t.status === 'completed' ? 'check-circle-2' : 'clock'}"></i></span>
      <button class="btn btn-ghost btn-icon" onclick="openEditTaskModal(${t.id})" style="font-size:0.75rem"><i data-lucide="edit-2"></i></button>
    </div>
  `).join('');
  lucide.createIcons({ root: panel });
}
