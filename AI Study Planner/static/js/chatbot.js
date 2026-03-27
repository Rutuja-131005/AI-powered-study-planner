/* ═══════════════════════════════════════════════════
   chatbot.js — AI Chatbot UI & Messaging
   ═══════════════════════════════════════════════════ */

let chatOpen = false;

// ── Toggle ──
function toggleChat() {
  chatOpen = !chatOpen;
  const win = document.getElementById('chatWindow');
  const fab = document.getElementById('chatFab');
  win.classList.toggle('open', chatOpen);
  fab.classList.toggle('hidden', chatOpen);
  if (chatOpen) {
    setTimeout(() => document.getElementById('chatInput').focus(), 300);
  }
}

// ── Send message on Enter ──
function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendChatMessage();
  }
}

// ── Quick prompt buttons ──
function quickPrompt(text) {
  document.getElementById('chatInput').value = text;
  sendChatMessage();
}

// ── Main send function ──
async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const msg   = input.value.trim();
  if (!msg) return;

  // Clear input
  input.value = '';

  // Append user message
  appendMessage(msg, 'user');

  // Show typing indicator
  showTyping(true);

  try {
    const res = await fetch('/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });

    const data = await res.json();
    showTyping(false);
    appendMessage(data.reply, 'bot');
  } catch (err) {
    showTyping(false);
    appendMessage('Sorry, I couldn\'t connect to the server. Please make sure the Flask app is running.', 'bot');
  }
}

// ── Append a chat bubble ──
function appendMessage(text, role) {
  const container = document.getElementById('chatMessages');

  const wrapper = document.createElement('div');
  wrapper.className = `chat-msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.innerHTML = role === 'bot' ? '<i data-lucide="bot"></i>' : '<i data-lucide="user"></i>';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = formatChatText(text);

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  container.appendChild(wrapper);

  lucide.createIcons({ root: wrapper });

  // Scroll to bottom smoothly
  container.scrollTop = container.scrollHeight;
}

// ── Typing indicator ──
function showTyping(show) {
  document.getElementById('chatTyping').style.display = show ? 'flex' : 'none';
  if (show) {
    const container = document.getElementById('chatMessages');
    container.scrollTop = container.scrollHeight;
  }
}

// ── Format chatbot text (markdown-lite) ──
function formatChatText(text) {
  if (!text) return '';

  // Escape HTML first
  let safe = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold: **text**
  safe = safe.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italic: *text*
  safe = safe.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Bullet list: lines starting with •
  const lines = safe.split('\n');
  let inList = false;
  const result = [];

  for (let line of lines) {
    if (line.startsWith('• ') || line.startsWith('- ')) {
      if (!inList) { result.push('<ul>'); inList = true; }
      result.push(`<li>${line.slice(2)}</li>`);
    } else {
      if (inList) { result.push('</ul>'); inList = false; }
      if (line.trim() === '') {
        result.push('');
      } else {
        result.push(`<p>${line}</p>`);
      }
    }
  }
  if (inList) result.push('</ul>');

  return result.join('');
}
