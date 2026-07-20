document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

const chatBox = document.getElementById('chat-box');
if (chatBox) {
  const appendMessage = (message) => {
    const row = document.createElement('div');
    row.className = 'chat-message';
    row.dataset.id = String(message.id);
    const author = document.createElement('strong');
    author.textContent = message.sender;
    const body = document.createElement('span');
    body.textContent = `: ${message.body}`;
    row.append(author, body);
    chatBox.append(row);
  };
  const poll = async () => {
    const rows = chatBox.querySelectorAll('[data-id]');
    const after = rows.length ? rows[rows.length - 1].dataset.id : '0';
    const params = new URLSearchParams({ after });
    if (chatBox.dataset.peer) params.set('with', chatBox.dataset.peer);
    try {
      const response = await fetch(`${chatBox.dataset.endpoint}?${params}`, { credentials: 'same-origin' });
      if (response.ok) {
        const messages = await response.json();
        messages.forEach(appendMessage);
        if (messages.length) chatBox.scrollTop = chatBox.scrollHeight;
      }
    } catch (_) { /* 다음 polling 주기에 재시도 */ }
  };
  chatBox.scrollTop = chatBox.scrollHeight;
  window.setInterval(poll, 3000);
}

