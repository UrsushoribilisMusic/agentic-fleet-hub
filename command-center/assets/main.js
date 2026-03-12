
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
let dailyStandupsIndex = [];
let activeDailyDate = '';
let MAIN_SECTION_BUTTONS = [];
let MAIN_SECTIONS = [];
let currentUser = null;

const memoryTree = [
  {
    folder: 'Global Rules',
    files: [
      { title: 'Team Rules', desc: 'Standardized protocols for commits, Kanban, and shared memory.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/RULES.md' },
      { title: 'KeyVault Strategy', desc: 'Infisical secrets management guide.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/KEYVAULT.md' }
    ]
  },
  {
    folder: 'Project Context',
    files: [
      { title: 'Salesman API', desc: 'Commerce and Marketplace logic.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/robot_ross_salesman.md' },
      { title: 'Artist Architecture', desc: 'Robot control and Huenit integration.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/robot_ross_artist.md' },
      { title: 'Music Video Automation', desc: 'Video generation heuristics.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/music_video_tool.md' },
      { title: 'Story Video Tool', desc: 'Narrative video pipeline.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/story_video_tool.md' },
      { title: 'The Lost Coins Story', desc: 'Story chapter breakdown.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/the_lost_coins_story.md' },
      { title: 'CRM Prototype', desc: 'Relational management logic.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/crm_poc_context.md' },
      { title: 'Agentegra Briefing', desc: 'Global project context and business model.', url: 'https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/AGENTS/CONTEXT/agentegra.md' }
    ]
  }
];

async function loadFleetMeta() {
  const path = window.location.pathname;
  const isDemo = path.indexOf('/demo') !== -1;
  const isGrowth = path.indexOf('/growth') !== -1;
  
  let endpoint = '/fleet/api/config';
  if (isDemo) endpoint = '/fleet/api/config/demo';
  if (isGrowth) endpoint = '/fleet/api/config/growth';

  try {
    const data = await fetchJson(endpoint);
    fleetData = data;
    populateTeam();
    populateProjects();
    loadLessons(); 
    if (isDemo || isGrowth) setupReducedMode(isGrowth);
  } catch (err) { 
    console.error('Core metadata load failed:', err);
  }
}

function setupReducedMode(isGrowth) {
  const h1 = document.querySelector('h1');
  const lede = document.querySelector('.lede');
  if (h1) h1.textContent = isGrowth ? 'Growth Fleet Hub' : 'Demo Fleet Hub';
  if (lede) lede.textContent = isGrowth 
    ? 'Specialized agentic fleet for Sales, Marketing, and Lead Discovery.' 
    : 'This is a reduced version of the Fleet Hub management plane.';
  
  if (isGrowth) {
    const growEls = document.querySelectorAll('.growth-only');
    for (let i = 0; i < growEls.length; i++) growEls[i].style.display = 'flex';
  }

  const usersBtn = document.querySelector('[data-section-button="section-users"]');
  if (usersBtn) {
    usersBtn.innerHTML = '<span>👤</span> User Management';
  }
  
  const usersSection = document.getElementById('section-users');
  if (usersSection) {
    usersSection.innerHTML = '<header class="page-header"><p class="eyebrow">' + (isGrowth ? 'Growth Strategy' : 'Production Feature') + '</p><h1>' + (isGrowth ? 'Request Industry Setup' : 'User Access Control') + '</h1><p class="lede">In the full Fleet Hub, you can manage team access dynamically.</p></header><div class="standup-form" style="padding: 3rem; text-align: center; border-style: dashed;"><p style="color: var(--teal-bright); font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">"A user would be added after entering the mail."</p><p class="muted">Access is gated via Google OAuth. You simply whitelist an email address, and that agent or team member is instantly granted access to the shared consciousness.</p></div>';
  }
}

async function verifyAuth() {
  try {
    const data = await fetchJson('/auth/verify');
    if (data && data.ok) {
      currentUser = data.user;
      const el = document.getElementById('user-info');
      if (el && currentUser) el.innerHTML = 'Logged in as:<br><strong>' + currentUser.email + '</strong>';
    }
  } catch (err) { console.error(err); }
}

function populateTeam() {
  const container = document.getElementById('team-grid');
  if (!container || !fleetData.team) return;
  let html = '';
  for (let i = 0; i < fleetData.team.length; i++) {
    const m = fleetData.team[i];
    let skillsHtml = '';
    if (m.skills) {
      for (let j = 0; j < m.skills.length; j++) {
        skillsHtml += '<span class="tag">' + m.skills[j] + '</span>';
      }
    }
    html += '<article class="agent-card"><div class="agent-avatar">' + m.avatar + '</div><div class="agent-info"><div class="runtime-badge">EXECUTION: ' + m.runtime + '</div><h3>' + m.name + '</h3><div class="role-title">' + m.roleTitle + '</div><p class="role-desc">' + m.roleDesc + '</p><div class="tag-list">' + skillsHtml + '</div><div class="project-links"><a href="' + m.memoryLink + '" target="_blank" class="btn-link">ROLE CARD</a></div></div></article>';
  }
  container.innerHTML = html;
}

function populateProjects() {
  const container = document.getElementById('projects-grid');
  if (!container || !fleetData.projects) return;
  let html = '';
  for (let i = 0; i < fleetData.projects.length; i++) {
    const p = fleetData.projects[i];
    const extra = p.statsLink ? '<a href="' + p.statsLink + '" target="_blank" class="btn-link">📊 VIEW STATS</a>' : '';
    const crm = p.crmLink ? '<a href="' + p.crmLink + '" target="_blank" class="btn-link">🤝 VIEW CRM</a>' : '';
    const docUrl = (p.docs && p.docs.length > 0) ? p.docs[0] : '#';
    html += '<article class="project-card"><h3>' + p.title + '</h3><p class="project-summary">' + p.summary + '</p><div class="project-links"><a href="' + docUrl + '" target="_blank" class="btn-link">DOCUMENTATION</a><a href="' + (p.kanban || '#') + '" target="_blank" class="btn-link">KANBAN BOARD</a>' + extra + ' ' + crm + '</div></article>';
  }
  container.innerHTML = html;
}

function renderMemoryTree() {
  const container = document.getElementById('docs-grid');
  if (!container) return;
  
  const path = window.location.pathname;
  const isGrowth = path.indexOf('/growth') !== -1;
  const isDemo = path.indexOf('/demo') !== -1;
  const base = isGrowth ? '/growth' : (isDemo ? '/demo' : '/fleet');

  let displayTree = memoryTree;
  if (isGrowth) {
    displayTree = [
      {
        folder: 'Growth Blueprint',
        files: [
          { title: 'CRM Prototype', desc: 'Relational management logic for sales leads.', path: 'AGENTS/CONTEXT/crm_poc_context.md' },
          { title: 'Growth Strategy', desc: 'Sample project for autonomous lead discovery.', path: 'AGENTS/CONTEXT/agentegra.md' }
        ]
      }
    ];
  } else {
    displayTree = [];
    for (let i = 0; i < memoryTree.length; i++) {
      const group = memoryTree[i];
      const newFiles = [];
      for (let j = 0; j < group.files.length; j++) {
        const f = group.files[j];
        const localPath = f.url.indexOf('AGENTS/') !== -1 ? f.url.split('master/')[1] : null;
        newFiles.push({ title: f.title, desc: f.desc, path: localPath });
      }
      displayTree.push({ folder: group.folder, files: newFiles });
    }
  }

  let html = '';
  for (let i = 0; i < displayTree.length; i++) {
    const group = displayTree[i];
    let filesHtml = '';
    for (let j = 0; j < group.files.length; j++) {
      const file = group.files[j];
      const fullUrl = file.path ? base + '/' + file.path : '#';
      filesHtml += '<div class="tree-item"><div class="tree-item-info"><strong>' + file.title + '</strong><span>' + file.desc + '</span></div><a href="' + fullUrl + '" target="_blank">VIEW LOCAL MD →</a></div>';
    }
    html += '<div class="tree-group"><h4>' + group.folder + '</h4><div class="tree-list">' + filesHtml + '</div></div>';
  }
  container.innerHTML = html;
}

async function loadLessons() {
  const container = document.getElementById('lessons-grid');
  if (!container) return;
  try {
    const path = window.location.pathname;
    const isDemo = path.indexOf('/demo') !== -1;
    const isGrowth = path.indexOf('/growth') !== -1;
    const lessons = await fetchJson('/fleet/api/lessons');
    const filtered = [];
    for (let i = 0; i < lessons.length; i++) {
      if ((isDemo || isGrowth)) {
        if (lessons[i].status === 'active') filtered.push(lessons[i]);
      } else {
        filtered.push(lessons[i]);
      }
    }
    
    if (filtered.length === 0) {
      container.innerHTML = '<p class="muted">No lessons logged yet.</p>';
      return;
    }

    let html = '';
    for (let i = 0; i < filtered.length; i++) {
      const l = filtered[i];
      const color = l.status === 'active' ? 'var(--teal-bright)' : '#f59e0b';
      let actions = '';
      if (!(isDemo || isGrowth) && l.status === 'pending_review') {
        actions = '<div style="margin-top:1rem; display:flex; gap:0.5rem;"><button class="btn-link" style="padding:0.25rem 0.75rem;" onclick="updateLessonStatus(\'' + l.id + '\', \'active\')">APPROVE</button><button class="btn-link" style="padding:0.25rem 0.75rem; border-color:#FF5252; color:#FF5252;" onclick="updateLessonStatus(\'' + l.id + '\', \'rejected\')">REJECT</button></div>';
      }
      html += '<div class="tree-item lesson-card ' + l.status + '" style="border-left: 4px solid ' + color + '"><div class="tree-item-info"><div style="display:flex; gap:0.5rem; margin-bottom:0.25rem;"><span class="tag" style="background:rgba(255,255,255,0.05); color:var(--text-muted)">' + l.category + '</span><span class="tag" style="background:rgba(255,255,255,0.05); color:var(--text-muted)">' + l.project + '</span></div><strong>' + l.title + '</strong><span style="display:block; margin: 0.5rem 0; font-style:italic;">"' + l.lesson + '"</span><div class="muted" style="font-size:0.75rem;">Found by <strong>' + l.agent + '</strong> on ' + new Date(l.date).toLocaleDateString() + '</div>' + actions + '</div></div>';
    }
    container.innerHTML = html;
  } catch (err) { console.error(err); }
}

window.updateLessonStatus = async function(id, status) {
  try {
    await fetchJson('/fleet/api/lessons/' + id, { method: 'PATCH', body: JSON.stringify({ status: status }) });
    loadLessons();
  } catch (err) { alert('Failed to update lesson status.'); }
};

async function loadInbox() {
  const container = document.getElementById('inbox-feed');
  if (!container) return;
  try {
    const messages = await fetchJson('/fleet/api/messages');
    let html = '';
    if (messages.length === 0) {
      html = '<p class="muted">No messages in your inbox.</p>';
    } else {
      for (let i = 0; i < messages.length; i++) {
        const m = messages[i];
        const isUrgent = m.priority === 'urgent';
        const statusIcon = m.status === 'unread' ? '🔵' : '⚪';
        html += '<div class="activity-item" style="border-left: 3px solid ' + (isUrgent ? '#FF5252' : 'var(--teal)') + '">';
        html += '<div style="display:flex; justify-content:space-between; align-items:center;">';
        html += '<span class="badge" style="background:rgba(255,255,255,0.05); color:var(--teal-bright)">' + m.from + ' → ' + m.to + '</span>';
        html += '<span style="font-size:0.7rem; color:var(--text-muted)">' + new Date(m.timestamp).toLocaleString() + '</span>';
        html += '</div>';
        html += '<h4 style="margin:0.5rem 0; font-size:0.95rem;">' + statusIcon + ' ' + m.subject + '</h4>';
        html += '<p style="font-size:0.85rem; color:var(--text-muted); white-space: pre-wrap;">' + m.body + '</p>';
        if (m.status === 'unread') {
          html += '<button class="btn" style="margin-top:0.75rem; font-size:0.65rem; padding:0.25rem 0.5rem;" onclick="markAsRead(\'' + m.id + '\')">MARK AS READ</button>';
        }
        html += '</div>';
      }
    }
    container.innerHTML = html;
  } catch (err) { console.error(err); }
}

window.markAsRead = async function(id) {
  try {
    await fetchJson('/fleet/api/messages/' + id, { method: 'PATCH', body: JSON.stringify({ status: 'read' }) });
    loadInbox();
  } catch (err) { alert('Failed to update message.'); }
};

async function loadRules() {
  const el = document.getElementById('rules-view');
  if (!el) return;
  try {
    const path = window.location.pathname;
    const isDemo = path.indexOf('/demo') !== -1;
    const isGrowth = path.indexOf('/growth') !== -1;
    const base = (isDemo || isGrowth) ? (isDemo ? '/demo' : '/growth') : '/fleet';
    const raw = await fetchText(base + '/AGENTS/RULES.md');
    el.innerHTML = renderSimpleMarkdown(raw);
  } catch (err) { el.innerHTML = '<p class="muted">Unable to load rules.</p>'; }
}

function renderSimpleMarkdown(raw) {
  return raw
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^\* (.*$)/gm, '<li>$1</li>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>');
}

function activateSection(targetId) {
  if (!MAIN_SECTION_BUTTONS.length || !MAIN_SECTIONS.length) return;
  for (let i = 0; i < MAIN_SECTION_BUTTONS.length; i++) {
    const btn = MAIN_SECTION_BUTTONS[i];
    btn.classList.toggle('is-active', btn.getAttribute('data-section-button') === targetId);
  }
  for (let i = 0; i < MAIN_SECTIONS.length; i++) {
    const sec = MAIN_SECTIONS[i];
    sec.classList.toggle('is-active', sec.id === targetId);
  }
  if (targetId === 'section-rules') loadRules();
  if (targetId === 'section-users') loadUsers();
  if (targetId === 'section-inbox') loadInbox();

  // Close sidebar on mobile after selection
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('mobile-toggle');
  if (sidebar) {
    sidebar.classList.remove('is-open');
    if (toggle) toggle.textContent = '☰';
  }
}

function wireNavControls() {
  MAIN_SECTION_BUTTONS = Array.prototype.slice.call(document.querySelectorAll('[data-section-button]'));
  MAIN_SECTIONS = Array.prototype.slice.call(document.querySelectorAll('.section'));
  for (let i = 0; i < MAIN_SECTION_BUTTONS.length; i++) {
    const button = MAIN_SECTION_BUTTONS[i];
    button.onclick = function() { activateSection(this.getAttribute('data-section-button')); };
  }

  // Mobile Toggle
  const toggle = document.getElementById('mobile-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.onclick = function() {
      const isOpen = sidebar.classList.toggle('is-open');
      toggle.textContent = isOpen ? '✕' : '☰';
    };
  }
}

async function loadDailyStandups() {
  const view = document.getElementById('daily-view');
  if (!view) return;
  try {
    const path = window.location.pathname;
    const isDemo = path.indexOf('/demo') !== -1;
    const isGrowth = path.indexOf('/growth') !== -1;
    const base = (isDemo || isGrowth) ? (isDemo ? '/demo' : '/growth') : '/fleet';
    const data = await fetchJson(base + '/standups/index.json');
    dailyStandupsIndex = data.sort(function(a, b) { return b.date.localeCompare(a.date); });
    renderDailyButtons();
    if (dailyStandupsIndex.length > 0) selectDaily(dailyStandupsIndex[0]);
  } catch (err) { view.innerHTML = '<p class="muted">Unable to load standups index.</p>'; }
}

function renderDailyButtons() {
  const container = document.getElementById('daily-buttons');
  if (!container) return;
  let html = '';
  for (let i = 0; i < dailyStandupsIndex.length; i++) {
    const day = dailyStandupsIndex[i];
    const activeClass = day.date === activeDailyDate ? 'is-active' : '';
    html += '<button class="daily-button ' + activeClass + '" onclick="selectDailyByDate(\'' + day.date + '\')">' + day.date + '</button>';
  }
  container.innerHTML = html;
}

window.selectDailyByDate = function(date) {
  let day = null;
  for (let i = 0; i < dailyStandupsIndex.length; i++) {
    if (dailyStandupsIndex[i].date === date) {
      day = dailyStandupsIndex[i];
      break;
    }
  }
  if (day) selectDaily(day);
};

async function selectDaily(day) {
  activeDailyDate = day.date;
  renderDailyButtons();
  const view = document.getElementById('daily-view');
  if (!view) return;
  try {
    const path = window.location.pathname;
    const isDemo = path.indexOf('/demo') !== -1;
    const isGrowth = path.indexOf('/growth') !== -1;
    const base = (isDemo || isGrowth) ? (isDemo ? '/demo' : '/growth') : '/fleet';
    const raw = await fetchText(base + '/standups/' + day.file);
    view.innerHTML = renderSimpleMarkdown(raw);
  } catch (err) { view.innerHTML = '<p class="muted">Error loading file.</p>'; }
}

function setupForms() {
  const standupForm = document.getElementById('standup-form');
  if (standupForm) {
    standupForm.onsubmit = async function(e) {
      e.preventDefault();
      const formData = new FormData(standupForm);
      const body = {
        done: formData.get('done'),
        today: formData.get('today'),
        blockers: formData.get('blockers'),
        agent: (currentUser && currentUser.email) || 'Admin'
      };
      try {
        await fetchJson('/fleet/api/standup', { method: 'POST', body: JSON.stringify(body) });
        standupForm.reset();
        loadDailyStandups();
        alert('Standup entry saved!');
      } catch (err) { alert('Failed to save standup.'); }
    };
  }

  const userForm = document.getElementById('user-form');
  if (userForm) {
    userForm.onsubmit = async function(e) {
      e.preventDefault();
      const email = e.target.email.value.trim().toLowerCase();
      try {
        const data = await fetchJson('/fleet/api/users');
        if (data.users.indexOf(email) !== -1) return alert('User already exists.');
        data.users.push(email);
        await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users: data.users }) });
        e.target.reset();
        loadUsers();
      } catch (err) { alert('Failed to add user.'); }
    };
  }

  const projectForm = document.getElementById('project-form');
  if (projectForm) {
    projectForm.onsubmit = async function(e) {
      e.preventDefault();
      const f = new FormData(projectForm);
      const newProject = {
        title: f.get('title'),
        summary: f.get('summary'),
        docs: [f.get('docs') || f.get('github')],
        kanban: f.get('kanban') || f.get('github'),
        statsLink: f.get('extra_url') || null
      };
      fleetData.projects.push(newProject);
      try {
        await fetchJson('/fleet/api/config', { method: 'POST', body: JSON.stringify(fleetData) });
        closeProjectModal();
        loadFleetMeta();
      } catch (err) { alert('Failed to save project.'); }
    };
  }

  const msgForm = document.getElementById('message-form');
  if (msgForm) {
    msgForm.onsubmit = async function(e) {
      e.preventDefault();
      const body = {
        from: (currentUser && currentUser.email) || 'Admin',
        to: document.getElementById('m-to').value,
        subject: document.getElementById('m-subject').value,
        priority: document.getElementById('m-priority').value,
        body: document.getElementById('m-body').value
      };
      try {
        await fetchJson('/fleet/api/messages', { method: 'POST', body: JSON.stringify(body) });
        msgForm.reset();
        loadInbox();
        alert('Message sent to the fleet!');
      } catch (err) { alert('Failed to send message.'); }
    };
  }
}

async function loadUsers() {
  const container = document.getElementById('users-list');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/users');
    let html = '';
    const users = data.users || [];
    for (let i = 0; i < users.length; i++) {
      html += '<div class="user-item"><span>' + users[i] + '</span><button class="btn-remove" onclick="removeUser(\'' + users[i] + '\')">REMOVE</button></div>';
    }
    container.innerHTML = html;
  } catch (err) { container.innerHTML = '<p class="muted">Failed to load users.</p>'; }
}

window.removeUser = async function(email) {
  if (!confirm('Remove ' + email + '?')) return;
  try {
    const data = await fetchJson('/fleet/api/users');
    const newUsers = [];
    for (let i = 0; i < data.users.length; i++) {
      if (data.users[i] !== email) newUsers.push(data.users[i]);
    }
    await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users: newUsers }) });
    loadUsers();
  } catch (err) { alert('Failed to remove user.'); }
};

window.openProjectModal = function() {
  const modal = document.getElementById('project-modal');
  if (modal) modal.style.display = 'flex';
};
window.closeProjectModal = function() {
  const modal = document.getElementById('project-modal');
  if (modal) modal.style.display = 'none';
};

document.addEventListener('DOMContentLoaded', function() {
  verifyAuth();
  wireNavControls();
  loadFleetMeta();
  renderMemoryTree();
  loadDailyStandups();
  setupForms();
});
