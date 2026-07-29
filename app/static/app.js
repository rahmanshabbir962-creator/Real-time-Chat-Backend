const $ = (selector) => document.querySelector(selector);
const state = { token: localStorage.getItem('chat_access_token'), user: null, room: null, socket: null, typingTimer: null };
const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`/api${path}`, { ...options, headers });
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(body?.message || body?.error || 'Request failed');
  return body;
};
const initials = (name = '?') => name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
const toast = (message) => { const el = $('#toast'); el.textContent = message; el.classList.add('show'); clearTimeout(el.timer); el.timer = setTimeout(() => el.classList.remove('show'), 2800); };
const errorText = (error) => error?.message || 'Something went wrong';

function showChat() { $('#auth-view').classList.add('hide'); $('#chat-view').classList.remove('hide'); $('#profile-name').textContent = state.user.display_name; $('#profile-avatar').textContent = initials(state.user.display_name); }
function showAuth() { $('#chat-view').classList.add('hide'); $('#auth-view').classList.remove('hide'); }

async function authenticate(form, signup = false) {
  const output = $('#auth-error'); output.textContent = '';
  try {
    const values = Object.fromEntries(new FormData(form));
    const data = await api(signup ? '/auth/signup' : '/auth/login', { method: 'POST', body: JSON.stringify(values) });
    state.token = data.access_token; state.user = data.user; localStorage.setItem('chat_access_token', state.token);
    showChat(); connectSocket(); await loadRooms();
  } catch (error) { output.textContent = errorText(error); }
}

function connectSocket() {
  if (state.socket) state.socket.disconnect();
  state.socket = io({ auth: { token: state.token } });
  state.socket.on('connect_error', () => toast('Realtime connection failed. Refresh and sign in again.'));
  state.socket.on('new_message', ({ message }) => { if (state.room?.id === message.room_id) appendMessage(message); });
  state.socket.on('message_updated', ({ message }) => { const el = document.querySelector(`[data-message-id="${message.id}"]`); if (el) el.replaceWith(messageElement(message)); });
  state.socket.on('message_deleted', ({ message_id }) => { const el = document.querySelector(`[data-message-id="${message_id}"] .message-text`); if (el) { el.textContent = 'This message was deleted'; el.classList.add('deleted'); } });
  state.socket.on('typing', ({ room_id, user_id, is_typing }) => { if (state.room?.id === room_id && user_id !== state.user.id) $('#typing').textContent = is_typing ? 'Someone is typing…' : ''; });
  state.socket.on('member_joined', () => state.room && toast('A member joined the room'));
}

async function restoreSession() {
  if (!state.token) return;
  try { state.user = (await api('/users/me')).user; showChat(); connectSocket(); await loadRooms(); }
  catch (_) { localStorage.removeItem('chat_access_token'); state.token = null; showAuth(); }
}

async function loadRooms() {
  const { rooms } = await api('/rooms?scope=joined');
  const container = $('#rooms'); container.innerHTML = '';
  if (!rooms.length) container.innerHTML = '<p class="empty">No rooms yet.</p>';
  rooms.forEach(room => { const button = document.createElement('button'); button.className = `room ${state.room?.id === room.id ? 'active' : ''}`; button.innerHTML = `<span>#</span>${escapeHtml(room.name)}<small>${escapeHtml(room.description || 'No description')}</small>`; button.onclick = () => selectRoom(room); container.append(button); });
}

async function selectRoom(room) {
  state.room = room; $('#chat-header').innerHTML = `<div><p>${room.is_private ? 'PRIVATE ROOM' : 'ROOM'}</p><h2># ${escapeHtml(room.name)}</h2></div>`; $('#message-form').classList.remove('hide'); $('#typing').textContent = ''; await loadRooms();
  const { messages } = await api(`/messages/rooms/${room.id}?per_page=100`); $('#messages').innerHTML = ''; messages.forEach(appendMessage); $('#messages').scrollTop = $('#messages').scrollHeight;
  state.socket?.emit('join_room', { room_id: room.id });
}

function escapeHtml(value) { const node = document.createElement('div'); node.textContent = value ?? ''; return node.innerHTML; }
function messageElement(message) {
  const mine = message.author_id === state.user.id; const element = document.createElement('article'); element.className = 'message'; element.dataset.messageId = message.id;
  const text = message.deleted_at ? 'This message was deleted' : message.content;
  const actions = mine && !message.deleted_at ? `<span class="message-actions"><button data-edit="${message.id}">Edit</button><button data-delete="${message.id}">Delete</button></span>` : '';
  element.innerHTML = `<div class="message-avatar">${initials(message.author.display_name)}</div><div><div class="message-meta"><b>${escapeHtml(message.author.display_name)}</b><time>${new Date(message.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</time>${actions}</div><div class="message-text ${message.deleted_at ? 'deleted' : ''}">${escapeHtml(text)}</div></div>`;
  element.querySelector('[data-edit]')?.addEventListener('click', () => editMessage(message));
  element.querySelector('[data-delete]')?.addEventListener('click', () => deleteMessage(message.id));
  return element;
}
function appendMessage(message) { const list = $('#messages'); list.append(messageElement(message)); list.scrollTop = list.scrollHeight; }
async function editMessage(message) { const content = prompt('Edit message', message.content); if (content === null || !content.trim()) return; try { await api(`/messages/${message.id}`, { method:'PATCH', body:JSON.stringify({ content:content.trim() }) }); } catch (error) { toast(errorText(error)); } }
async function deleteMessage(id) { if (!confirm('Delete this message?')) return; try { await api(`/messages/${id}`, { method:'DELETE' }); } catch (error) { toast(errorText(error)); } }

$('#login-form').addEventListener('submit', event => { event.preventDefault(); authenticate(event.currentTarget); });
$('#signup-form').addEventListener('submit', event => { event.preventDefault(); authenticate(event.currentTarget, true); });
$('#show-signup').addEventListener('click', () => { $('#login-form').classList.add('hide'); $('#show-signup').classList.add('hide'); $('#signup-form').classList.remove('hide'); });
$('#logout').addEventListener('click', async () => { try { await api('/auth/logout', {method:'POST'}); } catch (_) {} state.socket?.disconnect(); state.token = null; localStorage.removeItem('chat_access_token'); showAuth(); });
$('#refresh').addEventListener('click', () => loadRooms().catch(error => toast(errorText(error))));
$('#new-room').addEventListener('click', () => $('#create-dialog').showModal());
$('#room-form').addEventListener('submit', async event => { event.preventDefault(); const output = $('#room-error'); output.textContent = ''; const values = Object.fromEntries(new FormData(event.currentTarget)); values.is_private = event.currentTarget.is_private.checked; try { const { room } = await api('/rooms', {method:'POST',body:JSON.stringify(values)}); $('#create-dialog').close(); event.currentTarget.reset(); await loadRooms(); selectRoom(room); } catch (error) { output.textContent = errorText(error); } });
$('#browse').addEventListener('click', async () => { try { const { rooms } = await api('/rooms?scope=public&per_page=100'); const box = $('#public-rooms'); box.innerHTML = rooms.map(room => `<div class="public-room"><div><b># ${escapeHtml(room.name)}</b><p>${escapeHtml(room.description || 'No description')}</p></div><button data-room="${room.id}">Join</button></div>`).join('') || '<p>No public rooms yet.</p>'; box.querySelectorAll('[data-room]').forEach(button => button.onclick = async () => { try { await api(`/rooms/${button.dataset.room}/join`, {method:'POST'}); $('#public-dialog').close(); await loadRooms(); toast('Room joined'); } catch (error) { toast(errorText(error)); } }); $('#public-dialog').showModal(); } catch (error) { toast(errorText(error)); } });
$('#close-public').addEventListener('click', () => $('#public-dialog').close());
$('#message-form').addEventListener('submit', event => { event.preventDefault(); const input = $('#message'); const content = input.value.trim(); if (!content || !state.room) return; state.socket.emit('send_message', {room_id:state.room.id,content}); input.value = ''; state.socket.emit('typing', {room_id:state.room.id,is_typing:false}); });
$('#message').addEventListener('input', () => { if (!state.room) return; state.socket.emit('typing', {room_id:state.room.id,is_typing:true}); clearTimeout(state.typingTimer); state.typingTimer = setTimeout(() => state.socket.emit('typing',{room_id:state.room.id,is_typing:false}), 900); });
restoreSession();
