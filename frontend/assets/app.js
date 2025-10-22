const API = {
  channels: '/api/channels/',
  publish: '/api/publish',
};

const state = {
  channels: [],
  currentChannelId: null,
  notes: [], // local drafts for current channel
  currentNoteId: null,
  saveTimer: null,
  searchQuery: '',
};

async function http(method, url, body){
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if(body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if(!res.ok){ throw new Error(await res.text()); }
  return res.headers.get('content-type')?.includes('application/json') ? res.json() : res.text();
}

function renderFolders(){
  const container = document.getElementById('folders');
  container.innerHTML = '';
  state.channels.forEach(ch => {
    const el = document.createElement('div');
    el.className = 'folder' + (state.currentChannelId === ch.id ? ' active' : '');
    el.innerHTML = `<span class="name">${ch.name}</span>`;
    el.onclick = () => { state.currentChannelId = ch.id; loadNotes(); document.getElementById('current-folder-name').textContent = ch.name; };
    container.appendChild(el);
  });
}

function snippetFromHtml(html){
  const tmp = document.createElement('div');
  tmp.innerHTML = html || '';
  return (tmp.textContent || '').trim().slice(0, 120);
}

function renderNotes(){
  const list = document.getElementById('notes');
  list.innerHTML = '';
  state.notes.forEach(n => {
    const li = document.createElement('li');
    li.className = 'note-item' + (state.currentNoteId === n.id ? ' active' : '');
    li.innerHTML = `<div class="title">${n.title || 'Untitled'}</div><div class="snippet">${snippetFromHtml(n.content_html)}</div>`;
    li.onclick = () => selectNote(n.id);
    list.appendChild(li);
  });
}

function selectNote(id){
  state.currentNoteId = id;
  const note = state.notes.find(n => n.id === id);
  document.getElementById('note-title').value = note?.title || '';
  document.getElementById('note-content').innerHTML = note?.content_html || '';
  renderNotes();
}

function scheduleSave(){
  if(state.saveTimer) clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(saveCurrentNote, 500);
}

function persistNotes(){
  if(!state.currentChannelId) return;
  const key = `drafts:${state.currentChannelId}`;
  localStorage.setItem(key, JSON.stringify(state.notes));
}

async function saveCurrentNote(){
  const id = state.currentNoteId;
  if(!id) return;
  const title = document.getElementById('note-title').value;
  const content = document.getElementById('note-content').innerHTML;
  const idx = state.notes.findIndex(n => n.id === id);
  if(idx >= 0){
    state.notes[idx].title = title;
    state.notes[idx].content_html = content;
    state.notes[idx].updated_at = Date.now();
    persistNotes();
    renderNotes();
  }
}

async function loadChannels(){
  state.channels = await http('GET', API.channels);
  if(state.channels.length && state.currentChannelId == null){
    state.currentChannelId = state.channels[0].id;
    document.getElementById('current-folder-name').textContent = state.channels[0].name;
  }
  renderFolders();
}

async function loadNotes(){
  if(!state.currentChannelId){ state.notes = []; renderNotes(); return; }
  const key = `drafts:${state.currentChannelId}`;
  const saved = localStorage.getItem(key);
  const items = saved ? JSON.parse(saved) : [];
  const q = state.searchQuery?.toLowerCase?.() || '';
  state.notes = q ? items.filter(n => (n.title||'').toLowerCase().includes(q) || snippetFromHtml(n.content_html).toLowerCase().includes(q)) : items;
  // Sort: pinned first then updated_at desc
  state.notes.sort((a,b) => (b.is_pinned?1:0)-(a.is_pinned?1:0) || (b.updated_at||0)-(a.updated_at||0));
  renderNotes();
}

async function createFolder(){
  alert('Channels are managed by server config (TELEGRAM_CHANNELS).');
}

async function createNote(){
  if(!state.currentChannelId){ alert('Select a channel first'); return; }
  const note = { id: Date.now(), title: 'Untitled', content_html: '', is_pinned: false, updated_at: Date.now() };
  state.notes.unshift(note);
  persistNotes();
  renderNotes();
  selectNote(note.id);
}

function exec(cmd){
  document.execCommand(cmd, false, null);
  scheduleSave();
}

function setBlock(tag){
  document.execCommand('formatBlock', false, tag);
  scheduleSave();
}

async function handleImageUpload(file){
  const reader = new FileReader();
  reader.onload = () => {
    const editor = document.getElementById('note-content');
    const img = document.createElement('img');
    img.src = reader.result;
    editor.appendChild(img);
    scheduleSave();
  };
  reader.readAsDataURL(file);
}

async function publishCurrent(){
  const id = state.currentNoteId;
  if(!id){ alert('Select a note first'); return; }
  if(!state.currentChannelId){ alert('Select a channel'); return; }
  const title = document.getElementById('note-title').value;
  const content = document.getElementById('note-content').innerHTML;
  await http('POST', API.publish, { channel_id: state.currentChannelId, title, content_html: content });
  alert('Published to Telegram');
}

function bindEvents(){
  document.getElementById('new-folder').onclick = createFolder;
  document.getElementById('new-note').onclick = createNote;
  document.getElementById('note-title').addEventListener('input', scheduleSave);
  document.getElementById('note-content').addEventListener('input', scheduleSave);
  document.querySelectorAll('[data-cmd]').forEach(btn => btn.onclick = () => exec(btn.dataset.cmd));
  document.querySelectorAll('[data-block]').forEach(btn => btn.onclick = () => setBlock(btn.dataset.block));
  document.getElementById('insert-bullets').onclick = () => exec('insertUnorderedList');
  document.getElementById('insert-numbers').onclick = () => exec('insertOrderedList');
  document.getElementById('image-input').addEventListener('change', (e) => {
    const f = e.target.files?.[0]; if(f) handleImageUpload(f); e.target.value = '';
  });
  document.querySelector('.upload').onclick = () => document.getElementById('image-input').click();
  document.getElementById('publish').onclick = publishCurrent;
  document.getElementById('global-search').addEventListener('input', async (e) => {
    state.searchQuery = e.target.value; await loadNotes();
  });
  document.getElementById('pin-note').onclick = async () => {
    const id = state.currentNoteId; if(!id) return;
    const n = state.notes.find(n => n.id === id); if(!n) return;
    n.is_pinned = !n.is_pinned; n.updated_at = Date.now();
    persistNotes();
    await loadNotes();
  };
}

async function ensureDefaultFolder(){
  // Channels are server-configured; nothing to create here.
}

async function bootstrap(){
  bindEvents();
  await loadChannels();
  await ensureDefaultFolder();
  await loadNotes();
}

window.addEventListener('DOMContentLoaded', bootstrap);
