async function fetchJson(url, options) {
  options = options || {};
  options.cache = 'no-store';
  options.credentials = 'include';
  try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  } catch (err) {
    console.error('Fetch failed for ' + url + ':', err);
    throw err;
  }
}

async function fetchText(url) {
  try {
    const res = await fetch(url, { cache: 'no-store', credentials: 'include' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.text();
  } catch (err) {
    console.error('Fetch failed for ' + url + ':', err);
    throw err;
  }
}

let fleetData = { team: [], projects: [] };
let fleetSettings = { org_name: "Fleet Hub", github_org_url: "", main_repo_url: "", is_demo: true };
let dailyStandupsIndex = [];
let activeDailyDate = '';
let MAIN_SECTION_BUTTONS = [];
let MAIN_SECTIONS = [];
let currentUser = null;
let memorySearchQuery = '';

const memoryTree = [
  { folder: 'Global Rules', files: [
    { title: 'Team Rules', desc: 'Standardized protocols for commits, Kanban, and shared memory.', path: 'AGENTS/RULES.md' },
    { title: 'KeyVault Strategy', desc: 'Infisical secrets management guide.', path: 'AGENTS/KEYVAULT.md' }
  ]},
  { folder: 'Project Context', files: [
    { title: 'CRM Prototype', desc: 'Relational management logic for sales leads.', path: 'AGENTS/CONTEXT/crm_poc_context.md' }
  ]}
];

function replacePlaceholders(str) {
  if (!str) return str;
  let s = str;
  if (fleetSettings.github_org_url) s = s.replace(/{{GITHUB_ORG}}/g, fleetSettings.github_org_url);
  if (fleetSettings.main_repo_url) s = s.replace(/{{MAIN_REPO}}/g, fleetSettings.main_repo_url);
  if (fleetSettings.crm_url) s = s.replace(/{{CRM_URL}}/g, fleetSettings.crm_url);
  if (fleetSettings.kanban_url) s = s.replace(/{{KANBAN_URL}}/g, fleetSettings.kanban_url);
  return s;
}

async function loadFleetMeta() {
  const path = window.location.pathname;
  const isDemo = path.indexOf('/demo') !== -1;
  const isGrowth = path.indexOf('/growth') !== -1;
  let endpoint = '/fleet/api/config';
  if (isDemo) endpoint = '/fleet/api/config/demo';
  if (isGrowth) endpoint = '/fleet/api/config/growth';
  try {
    try { fleetSettings = await fetchJson('/fleet/api/settings'); } catch (e) {}
    const data = await fetchJson(endpoint);
    fleetData = data;
    loadTeamWithStatus();
    populateProjects();
    loadLessons();
    if (fleetSettings.is_demo === true) setupReducedMode(isGrowth);
    else setupStandaloneMode();
  } catch (err) { console.error('Core metadata load failed:', err); }
}

function setupStandaloneMode() {
  const els = document.querySelectorAll('.standalone-only');
  for (let i = 0; i < els.length; i++) els[i].style.display = 'inline-flex';
}
function setupReducedMode(isGrowth) {
  const h1 = document.querySelector('h1');
  if (h1) h1.textContent = isGrowth ? 'Growth Fleet Hub' : 'Demo Fleet Hub';
  if (isGrowth) { const els = document.querySelectorAll('.growth-only'); for (let i = 0; i < els.length; i++) els[i].style.display = 'flex'; }
}

async function verifyAuth() {
  try { const data = await fetchJson('/auth/verify'); if (data && data.ok) currentUser = data.user; } catch (err) {}
}

let agentHeartbeats = {};
let agentTaskCounts = {};

async function loadTeamWithStatus() {
  try {
    const [hbData, taskData] = await Promise.all([fetchJson('/fleet/api/heartbeats').catch(() => []), fetchJson('/fleet/api/tasks').catch(() => [])]);
    agentHeartbeats = {};
    for (let i = 0; i < hbData.length; i++) {
      const h = hbData[i], key = (h.agent || '').toLowerCase().split(' ')[0];
      if (!agentHeartbeats[key] || h.updated > agentHeartbeats[key].updated) agentHeartbeats[key] = h;
    }
    agentTaskCounts = {};
    for (let i = 0; i < taskData.length; i++) {
      const t = taskData[i];
      if ((t.status === 'todo' || t.status === 'in_progress' || t.status === 'peer_review') && t.assigned_agent) {
        const key = t.assigned_agent.toLowerCase().split(' ')[0];
        agentTaskCounts[key] = (agentTaskCounts[key] || 0) + 1;
      }
    }
  } catch (e) {}
  populateTeam();
}

function populateTeam() {
  const container = document.getElementById('team-grid');
  if (!container || !fleetData.team) return;
  const isStandalone = fleetSettings.is_demo === false;
  let html = '';
  for (let i = 0; i < fleetData.team.length; i++) {
    const m = fleetData.team[i];
    const key = m.name.toLowerCase().split(' ')[0];
    const hbKey = (m.heartbeatKey || key).toLowerCase();
    const hb = agentHeartbeats[hbKey];
    let hbClass = 'hb-offline', hbStatus = 'Offline', hbLastSeen = '';
    if (hb) {
      const ageSec = (Date.now() - new Date(hb.updated)) / 1000;
      if (ageSec < 3600) {
        hbClass = hb.status === 'working' ? 'hb-working' : 'hb-idle';
        hbStatus = hb.status.charAt(0).toUpperCase() + hb.status.slice(1);
        hbLastSeen = ageSec < 60 ? Math.round(ageSec) + 's ago' : Math.round(ageSec / 60) + 'm ago';
      }
    } else if (fleetSettings.is_demo) {
      var mockPool = ['working', 'idle', 'working', 'idle', 'idle'];
      var mockSt = mockPool[i % mockPool.length];
      hbClass = mockSt === 'working' ? 'hb-working' : 'hb-idle';
      hbStatus = mockSt.charAt(0).toUpperCase() + mockSt.slice(1);
      hbLastSeen = (3 + i * 4) + 'm ago';
    }
    const hbTooltip = m.name + '<br>' + hbStatus + (hbLastSeen ? '<br>' + hbLastSeen : '');
    const count = agentTaskCounts[key] || 0;
    const countBadge = count > 0 ? '<span class="task-count">' + count + '</span>' : '';
    let skillsHtml = '';
    if (m.skills) for (let j = 0; j < m.skills.length; j++) skillsHtml += '<span class="tag">' + m.skills[j] + '</span>';
    const memLink = replacePlaceholders(m.memoryLink) || '#';
    const removeBtn = isStandalone ? '<button class="btn-remove" onclick="removeAgent(\'' + m.name + '\')">Remove</button>' : '';
    html +=
      '<article class="agent-card" id="agent-card-' + i + '">' +
        '<div class="card-summary" onclick="toggleAgentCard(' + i + ')">' +
          '<div class="hb-dot-wrap"><div class="hb-dot ' + hbClass + '"></div><div class="hb-tooltip">' + hbTooltip + '</div></div>' +
          '<div class="agent-avatar">' + m.avatar + '</div>' +
          '<div class="card-summary-info"><h3>' + m.name + '</h3><div class="role-title">' + m.roleTitle + '</div></div>' +
          '<div class="card-meta">' + countBadge + '<span style="font-size:10px;color:var(--text-muted)">&#9660;</span></div>' +
        '</div>' +
        '<div class="card-details">' +
          '<div class="runtime-badge">RUNTIME: ' + (m.runtime || '') + '</div>' +
          '<p class="role-desc">' + (m.roleDesc || '') + '</p>' +
          '<div class="tag-list">' + skillsHtml + '</div>' +
          '<div style="margin-top:12px;display:flex;gap:8px"><a href="' + memLink + '" target="_blank" class="btn-link">MANDATE</a>' + removeBtn + '</div>' +
        '</div>' +
      '</article>';
  }
  container.innerHTML = html;
}

window.toggleAgentCard = function(i) { const c = document.getElementById('agent-card-' + i); if (c) c.classList.toggle('expanded'); };

function populateProjects() {
  const container = document.getElementById('projects-grid');
  if (!container || !fleetData.projects) return;
  let html = '';
  for (let i = 0; i < fleetData.projects.length; i++) {
    const p = fleetData.projects[i];
    html += '<div class="agent-card"><div class="card-summary"><div style="flex:1"><h3 style="font-size:14px">' + p.title + '</h3><p style="font-size:12px;color:var(--text-secondary)">' + p.summary + '</p></div><a href="' + (p.kanban || (p.docs && p.docs[0]) || '#') + '" target="_blank" class="btn-link">OPEN</a></div></div>';
  }
  container.innerHTML = html;
}

async function loadLessons() {
  const container = document.getElementById('lessons-grid');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/lessons');
    const items = (data.items || data).slice(0, 5);
    let html = '';
    for (let i = 0; i < items.length; i++) {
      const l = items[i];
      html += '<article class="agent-card" id="lesson-card-' + i + '">' +
        '<div class="card-summary" onclick="toggleLessonCard(' + i + ')">' +
          '<div style="flex:1"><h3 style="font-size:13px">' + (l.title || 'Lesson') + '</h3><span class="tag" style="font-size:10px">' + (l.category || 'Insight') + '</span></div>' +
          '<span style="font-size:11px;color:var(--text-muted);margin-right:8px">' + (l.agent || '') + '</span>' +
          '<span style="font-size:10px;color:var(--text-muted)">&#9660;</span>' +
        '</div>' +
        '<div class="card-details"><p style="font-size:13px;color:var(--text-secondary);white-space:pre-wrap">' + (l.body || l.lesson || '') + '</p></div>' +
      '</article>';
    }
    container.innerHTML = html || '<p style="padding:16px;font-size:13px;color:var(--text-muted)">No lessons yet.</p>';
  } catch (err) { console.error(err); }
}
window.toggleLessonCard = function(i) { const c = document.getElementById('lesson-card-' + i); if (c) c.classList.toggle('expanded'); };

function renderMemoryTree(query) {
  const container = document.getElementById('docs-grid');
  if (!container) return;
  const q = (query || '').toLowerCase().trim();
  let html = '', idx = 0;
  for (let i = 0; i < memoryTree.length; i++) {
    const group = memoryTree[i];
    const folderMatch = !q || group.folder.toLowerCase().includes(q);
    for (let j = 0; j < group.files.length; j++) {
      const f = group.files[j];
      if (!folderMatch && !f.title.toLowerCase().includes(q) && !f.desc.toLowerCase().includes(q)) continue;
      const id = idx++;
      html += '<article class="agent-card" id="doc-card-' + id + '">' +
        '<div class="card-summary" onclick="toggleDocCard(' + id + ')">' +
          '<div style="flex:1"><h3 style="font-size:13px">' + f.title + '</h3><span style="font-size:11px;color:var(--text-muted)">' + group.folder + '</span></div>' +
          '<span style="font-size:10px;color:var(--text-muted)">&#9660;</span>' +
        '</div>' +
        '<div class="card-details"><p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">' + f.desc + '</p>' +
          '<a href="https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/' + f.path + '" target="_blank" class="btn-link">VIEW ON GITHUB</a>' +
        '</div>' +
      '</article>';
    }
  }
  container.innerHTML = html || '<p style="padding:16px;font-size:13px;color:var(--text-muted)">No results.</p>';
}
window.toggleDocCard = function(i) { const c = document.getElementById('doc-card-' + i); if (c) c.classList.toggle('expanded'); };
window.handleMemorySearch = function(value) { memorySearchQuery = value; renderMemoryTree(value); };

async function loadInbox() {
  const container = document.getElementById('inbox-feed');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/messages');
    const messages = data.messages || data;
    let html = '';
    for (let i = 0; i < messages.length; i++) {
      const m = messages[i];
      const isUnread = m.status === 'unread';
      const ts = m.timestamp ? new Date(m.timestamp).toLocaleString() : '';
      html += '<article class="agent-card' + (isUnread ? ' inbox-unread' : '') + '" id="inbox-card-' + i + '">' +
        '<div class="card-summary" onclick="toggleInboxCard(' + i + ')">' +
          '<div style="flex:1"><strong style="font-size:13px">' + (m.subject || '(no subject)') + '</strong>' +
          '<div style="font-size:11px;color:var(--text-muted);margin-top:2px">From: ' + (m.from || '?') + ' &rarr; ' + (m.to || 'All') + '</div></div>' +
          (isUnread ? '<span class="tag" style="font-size:10px;background:var(--accent-muted);color:var(--accent);margin-right:6px">NEW</span>' : '') +
          '<span style="font-size:10px;color:var(--text-muted)">&#9660;</span>' +
        '</div>' +
        '<div class="card-details"><p style="font-size:13px;color:var(--text-secondary);white-space:pre-wrap;margin-bottom:8px">' + (m.body || '') + '</p>' +
          '<div style="font-size:11px;color:var(--text-muted)">' + ts + '</div></div>' +
      '</article>';
    }
    container.innerHTML = html || '<p style="font-size:13px;color:var(--text-muted);padding:8px">No messages.</p>';
  } catch (err) { console.error(err); }
}
window.toggleInboxCard = function(i) { const c = document.getElementById('inbox-card-' + i); if (c) c.classList.toggle('expanded'); };

function statusLabel(s) {
  return { 'in_work': 'IN WORK', 'planned': 'PLANNED', 'todo': 'TODO', 'waiting_human': 'WAITING', 'peer_review': 'REVIEW', 'done': 'DONE', 'completed': 'DONE' }[s] || (s || '').toUpperCase();
}

async function loadKanban() {
  const cP = document.getElementById('kanban-planned'), cW = document.getElementById('kanban-working'), cD = document.getElementById('kanban-done');
  if (!cP) return;
  try {
    const data = await fetchJson('/fleet/api/kanban');
    const empty = '<p style="font-size:12px;color:var(--text-muted);padding:8px">Empty</p>';
    const renderCard = function(t) {
      return '<div class="activity-item"><strong>#' + t.id + ': ' + t.title + '</strong>' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">' +
          '<span style="font-size:11px;font-weight:600;color:var(--accent)">' + (t.owner || '') + '</span>' +
          '<span style="font-size:10px;color:var(--text-muted)">' + statusLabel(t.status) + '</span>' +
        '</div></div>';
    };
    cP.innerHTML = (data.planned || []).length ? (data.planned || []).map(renderCard).join('') : empty;
    cW.innerHTML = (data.working || []).length ? (data.working || []).map(renderCard).join('') : empty;
    cD.innerHTML = (data.done || []).length ? (data.done || []).map(renderCard).join('') : empty;
  } catch (err) { console.error(err); }
}
window.refreshKanban = function() { loadKanban(); };

async function loadRules() {
  const el = document.getElementById('rules-view');
  if (!el) return;
  try { el.innerHTML = renderSimpleMarkdown(await fetchText('/fleet/AGENTS/RULES.md')); }
  catch (err) { el.innerHTML = '<p>Error loading rules.</p>'; }
}

function renderSimpleMarkdown(raw) {
  return raw
    .replace(/^# (.*$)/gm, '<h1>$1</h1>').replace(/^## (.*$)/gm, '<h2>$1</h2>').replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^\* (.*$)/gm, '<li>$1</li>').replace(/^- (.*$)/gm, '<li>$1</li>').replace(/\n/g, '<br>');
}

function activateSection(targetId) {
  for (let i = 0; i < MAIN_SECTION_BUTTONS.length; i++) MAIN_SECTION_BUTTONS[i].classList.toggle('is-active', MAIN_SECTION_BUTTONS[i].getAttribute('data-section-button') === targetId);
  for (let i = 0; i < MAIN_SECTIONS.length; i++) MAIN_SECTIONS[i].classList.toggle('is-active', MAIN_SECTIONS[i].id === targetId);
  if (targetId === 'section-rules') loadRules();
  if (targetId === 'section-users') loadUsers();
  if (targetId === 'section-inbox') loadInbox();
  if (targetId === 'section-kanban') loadKanban();
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('is-open');
}

function wireNavControls() {
  MAIN_SECTION_BUTTONS = Array.prototype.slice.call(document.querySelectorAll('[data-section-button]'));
  MAIN_SECTIONS = Array.prototype.slice.call(document.querySelectorAll('.section'));
  for (let i = 0; i < MAIN_SECTION_BUTTONS.length; i++) {
    const btn = MAIN_SECTION_BUTTONS[i];
    btn.onclick = function() { activateSection(this.getAttribute('data-section-button')); };
  }
  const toggle = document.getElementById('mobile-toggle'), sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) toggle.onclick = function() { sidebar.classList.toggle('is-open'); };
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) themeBtn.onclick = toggleTheme;
  const mandateSelect = document.querySelector('select[name="mandateFile"]');
  if (mandateSelect) mandateSelect.onchange = function() {
    const row = document.getElementById('mandate-url-row');
    if (row) row.style.display = this.value === 'other' ? 'flex' : 'none';
  };
}

function initTheme() { const saved = localStorage.getItem('theme'); if (saved) document.documentElement.setAttribute('data-theme', saved); }
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : current === 'light' ? 'dark' : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'light' : 'dark');
  document.documentElement.setAttribute('data-theme', target);
  localStorage.setItem('theme', target);
}

async function loadDailyStandups() {
  const view = document.getElementById('daily-view');
  if (!view) return;
  try {
    const data = await fetchJson('/fleet/api/standups');
    const seen = {};
    dailyStandupsIndex = data.filter(function(d) { if (seen[d.date]) return false; seen[d.date] = true; return true; })
      .sort(function(a, b) { return b.date.localeCompare(a.date); });
    renderDailyButtons();
    if (dailyStandupsIndex.length > 0) selectDaily(dailyStandupsIndex[0]);
  } catch (err) { console.error(err); }
}

function renderDailyButtons() {
  const container = document.getElementById('daily-buttons');
  if (!container) return;
  container.innerHTML = dailyStandupsIndex.map(function(day) {
    return '<button class="daily-button ' + (day.date === activeDailyDate ? 'is-active' : '') + '" onclick="selectDailyByDate(\'' + day.date + '\')">' + day.date + '</button>';
  }).join('');
}

window.selectDailyByDate = function(date) { const day = dailyStandupsIndex.find(function(d) { return d.date === date; }); if (day) selectDaily(day); };

async function selectDaily(day) {
  activeDailyDate = day.date;
  renderDailyButtons();
  const view = document.getElementById('daily-view');
  if (!view) return;
  try { view.innerHTML = renderSimpleMarkdown(await fetchText('/fleet/api/standups/' + day.date)); }
  catch (err) { console.error(err); }
}

function setupForms() {
  document.getElementById('standup-form').onsubmit = async function(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    try { await fetchJson('/fleet/api/standup', { method: 'POST', body: JSON.stringify({ done: fd.get('done'), today: fd.get('today'), blockers: fd.get('blockers'), agent: (currentUser && currentUser.email) || 'Admin' }) }); e.target.reset(); loadDailyStandups(); } catch (err) { alert('Failed to save.'); }
  };
  document.getElementById('message-form').onsubmit = async function(e) {
    e.preventDefault();
    try { await fetchJson('/fleet/api/messages', { method: 'POST', body: JSON.stringify({ to: document.getElementById('m-to').value, subject: document.getElementById('m-subject').value, body: document.getElementById('m-body').value, from: (currentUser && currentUser.email) || 'Admin', timestamp: new Date().toISOString(), status: 'unread' }) }); e.target.reset(); loadInbox(); } catch (err) { alert('Failed to send.'); }
  };
  document.getElementById('user-form').onsubmit = async function(e) {
    e.preventDefault();
    const email = new FormData(e.target).get('email').trim().toLowerCase();
    if (!email) return;
    try { const data = await fetchJson('/fleet/api/users'); const users = data.users || []; if (!users.includes(email)) users.push(email); await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users }) }); e.target.reset(); loadUsers(); } catch (err) { alert('Failed.'); }
  };
  document.getElementById('agent-form').onsubmit = async function(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const mandateFile = fd.get('mandateFile'), mandateUrl = fd.get('mandateUrl') || '';
    const memoryLink = mandateFile === 'other' ? mandateUrl : 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/' + mandateFile;
    const skills = (fd.get('skills') || '').split(',').map(function(s) { return s.trim(); }).filter(Boolean);
    const newAgent = { name: fd.get('name'), avatar: fd.get('avatar'), roleTitle: fd.get('roleTitle'), roleDesc: fd.get('roleDesc'), runtime: fd.get('runtime') || 'Hybrid', skills: skills, heartbeatKey: fd.get('heartbeatKey') || fd.get('name').toLowerCase(), memoryLink: memoryLink };
    try { const current = await fetchJson('/fleet/api/config'); current.team = current.team || []; current.team.push(newAgent); await fetchJson('/fleet/api/config', { method: 'POST', body: JSON.stringify(current) }); closeAgentModal(); loadTeamWithStatus(); } catch (err) { alert('Failed to save agent.'); }
  };
}

async function loadUsers() {
  const container = document.getElementById('users-list');
  if (!container) return;
  try { const data = await fetchJson('/fleet/api/users'); container.innerHTML = (data.users || []).map(function(u) { return '<div class="agent-card" style="margin-bottom:4px"><div class="card-summary"><span style="flex:1;font-size:13px">' + u + '</span><button class="btn-link" onclick="removeUser(\'' + u + '\')">Remove</button></div></div>'; }).join(''); } catch (err) {}
}

window.removeUser = async function(email) { if (!confirm('Remove ' + email + '?')) return; try { const data = await fetchJson('/fleet/api/users'); const users = (data.users || []).filter(function(u) { return u !== email; }); await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users }) }); loadUsers(); } catch (err) {} };
window.removeAgent = async function(name) { if (!confirm('Remove agent ' + name + '?')) return; try { const current = await fetchJson('/fleet/api/config'); current.team = (current.team || []).filter(function(a) { return a.name !== name; }); await fetchJson('/fleet/api/config', { method: 'POST', body: JSON.stringify(current) }); loadTeamWithStatus(); } catch (err) {} };

window.openProjectModal = function() { document.getElementById('project-modal').style.display = 'flex'; };
window.closeProjectModal = function() { document.getElementById('project-modal').style.display = 'none'; };
window.openAgentModal = function() { document.getElementById('agent-modal').style.display = 'flex'; };
window.closeAgentModal = function() { document.getElementById('agent-modal').style.display = 'none'; };


document.addEventListener('DOMContentLoaded', function() { initTheme(); verifyAuth(); wireNavControls(); loadFleetMeta(); renderMemoryTree(''); loadDailyStandups(); setupForms(); });
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeProjectModal(); closeAgentModal(); } });
document.addEventListener('click', function(e) { if (e.target && e.target.classList && e.target.classList.contains('modal-overlay')) { closeProjectModal(); closeAgentModal(); } });
