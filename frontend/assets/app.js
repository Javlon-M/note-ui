const API = {
  channels: '/api/channels/',
  channelsStatus: '/api/channels/status',
  publish: '/api/publish',
  testPublish: '/api/publish/test',
  validate: '/api/publish/validate',
};

const state = {
  channels: [],
  channelsStatus: null,
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
  
  // Add bot status indicator
  if (state.channelsStatus) {
    const botStatusEl = document.createElement('div');
    botStatusEl.className = 'bot-status';
    const botConfigured = state.channelsStatus.bot_configured;
    const botUsername = state.channelsStatus.bot_username || 'Unknown';
    botStatusEl.innerHTML = `
      <div class="status-indicator ${botConfigured ? 'connected' : 'disconnected'}"></div>
      <span class="bot-info">Bot: ${botUsername}</span>
    `;
    container.appendChild(botStatusEl);
  }
  
  state.channels.forEach(ch => {
    const el = document.createElement('div');
    el.className = 'folder' + (state.currentChannelId === ch.id ? ' active' : '');
    
    // Find channel status
    const channelStatus = state.channelsStatus?.channels?.find(cs => cs.id === ch.id);
    const isAccessible = channelStatus?.accessible || false;
    const statusIcon = isAccessible ? '✓' : '✗';
    const statusClass = isAccessible ? 'accessible' : 'inaccessible';
    
    el.innerHTML = `
      <span class="name">${ch.name}</span>
      <span class="status ${statusClass}" title="${channelStatus?.error || 'Channel accessible'}">${statusIcon}</span>
    `;
    el.onclick = () => { 
      state.currentChannelId = ch.id; 
      loadNotes(); 
    };
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
    li.innerHTML = `
      <div class="note-content-wrapper">
        <div class="title" id="note-title">${n.title || 'New Note'}</div>
        <div class="snippet">${snippetFromHtml(n.content_html || 'No additional text')}</div>
      </div>
    `;
    // <button class="note-trash-btn" title="Delete Note" onclick="event.stopPropagation(); deleteNote(${n.id})">🗑️</button>
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
  // updateCharCounter();
}

function scheduleSave(){
  if(state.saveTimer) clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(saveCurrentNote, 500);
  // updateCharCounter();
}

function updateCharCounter(){
  const title = document.getElementById('note-title').value;
  const content = document.getElementById('note-content').innerHTML;
  
  // Simple text length calculation (approximate)
  const titleText = title || '';
  const contentText = content.replace(/<[^>]*>/g, ''); // Remove HTML tags
  const totalLength = titleText.length + contentText.length + 2; // +2 for newlines
  
  const counter = document.getElementById('char-counter');
  const hasImages = content.includes('<img');
  
  if (hasImages) {
    counter.textContent = `${totalLength} / 1024`;
    if (totalLength > 1024) {
      counter.className = 'char-counter error';
    } else if (totalLength > 900) {
      counter.className = 'char-counter warning';
    } else {
      counter.className = 'char-counter';
    }
  } else {
    counter.textContent = `${totalLength} / 4096`;
    if (totalLength > 4096) {
      counter.className = 'char-counter error';
    } else if (totalLength > 3500) {
      counter.className = 'char-counter warning';
    } else {
      counter.className = 'char-counter';
    }
  }
}

function persistNotes(){
  if(!state.currentChannelId) return;
  const key = `drafts:${state.currentChannelId}`;
  localStorage.setItem(key, JSON.stringify(state.notes));
}

async function saveCurrentNote(){
  let id = state.currentNoteId;
  const content = document.getElementById('note-content').innerHTML;
  const title = getTitle(content)
  if(!id) {
    if(!state.currentChannelId){ alert('Select a channel first'); return; }
    const note = { id: Date.now(), title: 'New Note', content_html: content === "" ? '' : content, is_pinned: false, updated_at: Date.now() };
    
    state.notes.unshift(note);
    state.currentNoteId = note.id
    persistNotes();
    renderNotes();
    id = state.currentNoteId
  };
  
  const idx = state.notes.findIndex(n => n.id === id);
  if(idx >= 0){
    state.notes[idx].title = title;
    state.notes[idx].content_html = content;
    state.notes[idx].updated_at = Date.now();
    persistNotes();
    renderNotes();
  }
}

function getTitle(content){
  const divs = document.querySelectorAll("#note-content div")

  if(divs.length != 0) {
    return (Array.from(divs).map(div => {
      return div.innerHTML === '<br>' ? '' : div.textContent;
    }))[0].slice(0, 100);
  }

  return content.replace(/<[^>]*>/g, '').slice(0, 100);
}

async function loadChannels(){
  try {
    const channel = localStorage.getItem("TELEGRAM_CHANNELS")
    const token = localStorage.getItem("TELEGRAM_BOT_TOKEN")

    if (!channel || !token) {
      const container = document.getElementById('folders');
      container.innerHTML = `<div class="info">Please configure the bot and channel</div>`;
      return
    }

    state.channels = [{name: channel.split("=")[0], id: channel.split("=")[1]}]
    state.channelsStatus = await http('POST', API.channelsStatus, {
      channels: state.channels,
      token: token
    });
    
    if(state.channels.length && state.currentChannelId == null){
      state.currentChannelId = state.channels[0].id;
      // document.getElementById('current-folder-name').textContent = state.channels[0].name;
    }
    renderFolders();
  } catch (error) {
    console.error('Failed to load channels:', error);
    // Show error in UI
    const container = document.getElementById('folders');
    container.innerHTML = `<div class="error">Failed to load channels: ${error.message}</div>`;
  }
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
  if (localStorage.getItem('TELEGRAM_CHANNELS') && localStorage.getItem('TELEGRAM_BOT_TOKEN')) {
    showNotification('You already have all the details', 'success');
    return;
  }

  const channelName = prompt('Enter the channel name');
  const channelId = prompt('Enter the channel id. Starts with -100');
  const botToken = prompt('Enter the bot token');

  if (!channelName || !channelId || !botToken) {
    showNotification('Please enter all the details of channel and bot', 'error');
    return;
  }

  const TELEGRAM_CHANNELS = `${channelName}=${channelId}`

  localStorage.setItem('TELEGRAM_CHANNELS', TELEGRAM_CHANNELS)
  localStorage.setItem('TELEGRAM_BOT_TOKEN', botToken)

  window.location.reload();
}

async function createNote(){
  if(!state.currentChannelId){ alert('Select a channel first'); return; }
  const note = { id: Date.now(), title: 'New Note', content_html: '', is_pinned: false, updated_at: Date.now() };
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

async function validateContent(title, content, telegram_channel, telegram_bot_token) {
  try {
    const result = await http('POST', API.validate, {
      channel_id: state.currentChannelId,
      title,
      content_html: content,
      telegram_channel: telegram_channel,
      telegram_bot_token: telegram_bot_token,
    });
    return result;
  } catch (error) {
    console.error('Validation error:', error);
    return { success: false, error: error.message };
  }
}

async function publishCurrent(){
  const telegram_channel = localStorage.getItem('TELEGRAM_CHANNELS')
  const telegram_bot_token = localStorage.getItem('TELEGRAM_BOT_TOKEN')

  const id = state.currentNoteId;
  if(!id){ 
    showNotification('Select a note first', 'error');
    return; 
  }
  if(!state.currentChannelId){ 
    showNotification('Select a channel', 'error');
    return; 
  }
  
  const title = document.getElementById('note-title').value;
  const content = document.getElementById('note-content').innerHTML;
  
  if(!title.trim() && !content.trim()){
    showNotification('Note is empty', 'error');
    return;
  }
  
  // Check if current channel is accessible
  const channelStatus = state.channelsStatus?.channels?.find(cs => cs.id === state.currentChannelId);
  if (channelStatus && !channelStatus.accessible) {
    showNotification(`Cannot publish to ${channelStatus.name}: ${channelStatus.error}`, 'error');
    return;
  }
  
  // Validate content length first
  showNotification('Validating content...', 'info');
  const validation = await validateContent(title, content, telegram_channel, telegram_bot_token);
  
  if (!validation.success) {
    showNotification('Validation failed: ' + validation.error, 'error');
    return;
  }
  
  if (!validation.validation.is_valid) {
    showNotification(validation.recommendation, 'error');
    return;
  }
  
  try {
    showNotification('Publishing...', 'info');

    const result = await http('POST', API.publish, { 
      telegram_channel: telegram_channel,
      telegram_bot_token: telegram_bot_token,
      channel_id: state.currentChannelId, 
      title, 
      content_html: content,
      verify_channel: true
    });
    
    if (result.success) {
      showNotification('Published to Telegram successfully!', 'success');
    } else {
      showNotification('Publish failed: ' + (result.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Publish error:', error);
    showNotification('Publish failed: ' + error.message, 'error');
  }
}

function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Add to page
  document.body.appendChild(notification);
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 5000);
}

function deleteNote() {
  if (!confirm('Are you sure you want to delete this note?')) {
    return;
  }

  if (!state.currentNoteId) return

  noteId = state.currentNoteId

  // Remove note from state
  state.notes = state.notes.filter(n => n.id !== noteId);
  
  // If deleted note was current, clear editor
  if (state.currentNoteId === noteId) {
    state.currentNoteId = null;
    document.getElementById('note-title').value = '';
    document.getElementById('note-content').innerHTML = '';
  }
  
  // Persist changes
  persistNotes();
  
  // Re-render
  renderNotes();
  
  showNotification('Note deleted', 'success');
}

function deleteAllNotes() {
  if (!state.notes.length) {
    showNotification('No notes to delete', 'info');
    return;
  }
  
  if (!confirm(`Are you sure you want to delete all ${state.notes.length} notes? This action cannot be undone.`)) {
    return;
  }
  
  // Clear all notes
  state.notes = [];
  state.currentNoteId = null;
  
  // Clear editor
  document.getElementById('note-title').value = '';
  document.getElementById('note-content').innerHTML = '';
  
  // Persist changes
  persistNotes();
  
  // Re-render
  renderNotes();
  
  showNotification('All notes deleted', 'success');
}

function bindEvents(){
  document.getElementById('new-folder').onclick = createFolder;
  document.getElementById('new-note').onclick = createNote;
  // document.getElementById('note-item').onclick = selectNote;
  document.getElementById('note-trash-btn').onclick = deleteNote;
  // document.getElementById('trash-all').onclick = deleteAllNotes;
  // document.getElementById('note-title').addEventListener('input', scheduleSave);
  document.getElementById('note-content').addEventListener('input', () => {
    const editor = document.getElementById('note-content');
    
    editor.querySelectorAll('span').forEach(span => {
      // Move all child nodes (text, elements) before the span
      while (span.firstChild) {
        span.parentNode.insertBefore(span.firstChild, span);
      }
      // Remove the empty span
      span.remove();
    });

    scheduleSave()
  });
  document.querySelectorAll('[data-cmd]').forEach(btn => btn.onclick = () => exec(btn.dataset.cmd));
  document.querySelectorAll('[data-block]').forEach(btn => btn.onclick = () => setBlock(btn.dataset.block));
  // document.getElementById('insert-bullets').onclick = () => exec('insertUnorderedList');
  // document.getElementById('insert-numbers').onclick = () => exec('insertOrderedList');
  // document.getElementById('image-input').addEventListener('change', (e) => {
  //   const f = e.target.files?.[0]; if(f) handleImageUpload(f); e.target.value = '';
  // });
  // document.querySelector('.upload').onclick = () => document.getElementById('image-input').click();
  // document.getElementById('publish').onclick = publishCurrent;
  document.getElementById('global-search').addEventListener('input', async (e) => {
    state.searchQuery = e.target.value; await loadNotes();
  });
  // document.getElementById('pin-note').onclick = async () => {
  //   const id = state.currentNoteId; if(!id) return;
  //   const n = state.notes.find(n => n.id === id); if(!n) return;
  //   n.is_pinned = !n.is_pinned; n.updated_at = Date.now();
  //   persistNotes();
  //   await loadNotes();
  // };
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
