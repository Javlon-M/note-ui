const API = {
  folders: '/api/folders/',
  notes: '/api/notes/',
  upload: '/api/upload/',
  publish: (id) => `/api/publish/note/${id}`,
};

const state = {
  folders: [],
  currentFolderId: null,
  notes: [],
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
  state.folders.forEach(f => {
    const el = document.createElement('div');
    el.className = 'folder' + (state.currentFolderId === f.id ? ' active' : '');
    el.innerHTML = `<span class="name">${f.name}</span>`;
    el.onclick = () => { state.currentFolderId = f.id; loadNotes(); document.getElementById('current-folder-name').textContent = f.name; };
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

async function saveCurrentNote(){
  const id = state.currentNoteId;
  if(!id) return;
  const title = document.getElementById('note-title').value;
  const content = document.getElementById('note-content').innerHTML;
  try{
    await http('PATCH', API.notes + id, { title, content_html: content });
  }catch(err){ console.error('Save failed', err); }
}

async function loadFolders(){
  state.folders = await http('GET', API.folders);
  if(state.folders.length && state.currentFolderId == null){
    state.currentFolderId = state.folders[0].id;
  }
  renderFolders();
}

async function loadNotes(){
  const params = new URLSearchParams();
  if(state.currentFolderId) params.set('folder_id', state.currentFolderId);
  if(state.searchQuery) params.set('q', state.searchQuery);
  const data = await http('GET', API.notes + '?' + params.toString());
  state.notes = data.items;
  renderNotes();
}

async function createFolder(){
  const name = prompt('Folder name');
  if(!name) return;
  await http('POST', API.folders, { name });
  await loadFolders();
}

async function createNote(){
  const title = 'Untitled';
  const folder_id = state.currentFolderId;
  const note = await http('POST', API.notes, { title, folder_id, content_html: '' });
  await loadNotes();
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
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(API.upload, { method: 'POST', body: form });
  if(!res.ok) throw new Error(await res.text());
  const data = await res.json();
  const editor = document.getElementById('note-content');
  const img = document.createElement('img');
  img.src = data.url;
  editor.appendChild(img);
  scheduleSave();
}

async function publishCurrent(){
  const id = state.currentNoteId;
  if(!id){ alert('Select a note first'); return; }
  try{
    await http('POST', API.publish(id), {});
    alert('Published to Telegram');
  }catch(err){
    alert('Publish failed: ' + err);
  }
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
    await http('POST', API.notes + id + '/pin');
    await loadNotes();
  };
}

async function ensureDefaultFolder(){
  if(!state.folders.length){
    await http('POST', API.folders, { name: 'Notes' });
    await loadFolders();
  }
}

async function bootstrap(){
  bindEvents();
  await loadFolders();
  await ensureDefaultFolder();
  await loadNotes();
}

window.addEventListener('DOMContentLoaded', bootstrap);
