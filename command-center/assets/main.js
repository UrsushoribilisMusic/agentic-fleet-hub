
async function fetchJson(url, options = {}) {
  const res = await fetch(url, { cache: 'no-store', credentials: 'include', ...options });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchText(url) {
  const res = await fetch(url, { cache: 'no-store', credentials: 'include' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
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
      { title: 'Team Rules', desc: 'Standardized protocols for commits, Kanban, and shared memory.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/RULES.md' },
      { title: 'KeyVault Strategy', desc: 'Infisical secrets management guide.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/KEYVAULT.md' }
    ]
  },
  {
    folder: 'Project Context',
    files: [
      { title: 'Salesman API', desc: 'Commerce and Marketplace logic.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/robot_ross_salesman.md' },
      { title: 'Artist Architecture', desc: 'Robot control and Huenit integration.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/robot_ross_artist.md' },
      { title: 'Music Video Automation', desc: 'Video generation heuristics.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/music_video_tool.md' },
      { title: 'Story Video Tool', desc: 'Narrative video pipeline.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/story_video_tool.md' },
      { title: 'The Lost Coins Story', desc: 'Story chapter breakdown.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/the_lost_coins_story.md' },
      { title: 'CRM Prototype', desc: 'Relational management logic.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/crm_poc_context.md' },
      { title: 'Agentegra Briefing', desc: 'Global project context and business model.', url: 'https://github.com/UrsushoribilisMusic/salesman-cloud-infra/blob/main/AGENTS/CONTEXT/agentegra.md' }
    ]
  }
];

async function loadFleetMeta() {
  const isDemo = window.location.pathname.startsWith('/demo');
  const endpoint = isDemo ? '/fleet/api/config/demo' : '/fleet/api/config';
  try {
    fleetData = await fetchJson(endpoint);
    populateTeam();
    populateProjects();
    if (isDemo) setupDemoMode();
  } catch (err) { console.error(err); }
}

function setupDemoMode() {
  // Update header
  const h1 = document.querySelector('h1');
  const lede = document.querySelector('.lede');
  if (h1) h1.textContent = 'Demo Fleet Hub';
  if (lede) lede.textContent = 'This is a reduced version of the Fleet Hub management plane.';
  
  // Replace Users tab label
  const usersBtn = document.querySelector('[data-section-button="section-users"]');
  if (usersBtn) {
    usersBtn.innerHTML = '<span>👥</span> User Management';
  }
  
  const usersSection = document.getElementById('section-users');
  if (usersSection) {
    usersSection.innerHTML = `
      <header class="page-header">
        <p class="eyebrow">Production Feature</p>
        <h1>User Access Control</h1>
        <p class="lede">In the full Fleet Hub, you can manage team access dynamically.</p>
      </header>
      <div class="standup-form" style="padding: 3rem; text-align: center; border-style: dashed;">
        <p style="color: var(--teal-bright); font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">
          "A user would be added after entering the mail."
        </p>
        <p class="muted">
          Access is gated via Google OAuth. You simply whitelist an email address, and that agent or team member is instantly granted access to the shared consciousness.
        </p>
      </div>
    `;
  }
}

async function verifyAuth() {
  try {
    const data = await fetchJson('/auth/verify');
    if (data.ok) {
      currentUser = data.user;
      document.getElementById('user-info').innerHTML = `Logged in as:<br><strong>${currentUser.email}</strong>`;
    }
  } catch (err) { console.error(err); }
}

function populateTeam() {
  const container = document.getElementById('team-grid');
  if (!container) return;
  container.innerHTML = (fleetData.team || [])
    .map((m) => `
        <article class="agent-card">
          <div class="agent-avatar">${m.avatar}</div>
          <div class="agent-info">
            <div class="runtime-badge">EXECUTION: ${m.runtime}</div>
            <h3>${m.name}</h3>
            <div class="role-title">${m.roleTitle}</div>
            <p class="role-desc">${m.roleDesc}</p>
            <div class="tag-list">
              ${m.skills.map(s => `<span class="tag">${s}</span>`).join('')}
            </div>
            <div class="project-links">
              <a href="${m.memoryLink}" target="_blank" class="btn-link">ROLE CARD</a>
            </div>
          </div>
        </article>
      `)
    .join('');
}

function populateProjects() {
  const container = document.getElementById('projects-grid');
  if (!container) return;
  container.innerHTML = (fleetData.projects || [])
    .map((p) => {
      const extra = p.statsLink ? `<a href="${p.statsLink}" target="_blank" class="btn-link">📊 VIEW STATS</a>` : '';
      const crm = p.crmLink ? `<a href="${p.crmLink}" target="_blank" class="btn-link">🤝 VIEW CRM</a>` : '';
      return `
        <article class="project-card">
          <h3>${p.title}</h3>
          <p class="project-summary">${p.summary}</p>
          <div class="project-links">
            <a href="${p.docs[0]}" target="_blank" class="btn-link">DOCUMENTATION</a>
            <a href="${p.kanban}" target="_blank" class="btn-link">KANBAN BOARD</a>
            ${extra}
            ${crm}
          </div>
        </article>
      `;
    })
    .join('');
}

function renderMemoryTree() {
  const container = document.getElementById('docs-grid');
  if (!container) return;
  container.innerHTML = memoryTree
    .map((group) => `
      <div class="tree-group">
        <h4>${group.folder}</h4>
        <div class="tree-list">
          ${group.files.map((file) => `
            <div class="tree-item">
              <div class="tree-item-info">
                <strong>${file.title}</strong>
                <span>${file.desc}</span>
              </div>
              <a href="${file.url}" target="_blank">OPEN ON GITHUB →</a>
            </div>
          `).join('')}
        </div>
      </div>
    `)
    .join('');
}

async function loadRules() {
  const el = document.getElementById('rules-view');
  if (!el) return;
  try {
    const isDemo = window.location.pathname.startsWith('/demo');
    const base = isDemo ? '/demo' : '/fleet';
    const raw = await fetchText(`${base}/AGENTS/RULES.md`);
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
  MAIN_SECTION_BUTTONS.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.sectionButton === targetId);
  });
  MAIN_SECTIONS.forEach((section) => {
    section.classList.toggle('is-active', section.id === targetId);
  });
  if (targetId === 'section-rules') loadRules();
  if (targetId === 'section-users') loadUsers();
}

function wireNavControls() {
  MAIN_SECTION_BUTTONS = Array.from(document.querySelectorAll('[data-section-button]'));
  MAIN_SECTIONS = Array.from(document.querySelectorAll('.section'));
  MAIN_SECTION_BUTTONS.forEach((button) => {
    button.addEventListener('click', () => activateSection(button.dataset.sectionButton));
  });
}

async function loadDailyStandups() {
  const view = document.getElementById('daily-view');
  try {
    const isDemo = window.location.pathname.startsWith('/demo');
    const base = isDemo ? '/demo' : '/fleet';
    const data = await fetchJson(`${base}/standups/index.json`);
    dailyStandupsIndex = data.slice().sort((a, b) => b.date.localeCompare(a.date));
    renderDailyButtons();
    if (dailyStandupsIndex.length) selectDaily(dailyStandupsIndex[0]);
  } catch (err) { if (view) view.innerHTML = '<p class="muted">Unable to load standups index.</p>'; }
}

function renderDailyButtons() {
  const container = document.getElementById('daily-buttons');
  if (!container) return;
  container.innerHTML = dailyStandupsIndex.map(day => `
    <button class="daily-button ${day.date === activeDailyDate ? 'is-active' : ''}" onclick="selectDailyByDate('${day.date}')">
      ${day.date}
    </button>
  `).join('');
}

window.selectDailyByDate = (date) => {
  const day = dailyStandupsIndex.find(d => d.date === date);
  if (day) selectDaily(day);
};

async function selectDaily(day) {
  activeDailyDate = day.date;
  renderDailyButtons();
  const view = document.getElementById('daily-view');
  try {
    const isDemo = window.location.pathname.startsWith('/demo');
    const base = isDemo ? '/demo' : '/fleet';
    const raw = await fetchText(`${base}/standups/${day.file}`);
    view.innerHTML = renderSimpleMarkdown(raw);
  } catch (err) { view.innerHTML = '<p class="muted">Error loading file.</p>'; }
}

function setupStandupForm() {
  const form = document.getElementById('standup-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const body = {
      done: formData.get('done'),
      today: formData.get('today'),
      blockers: formData.get('blockers'),
      agent: currentUser?.email || 'Admin'
    };
    try {
      await fetchJson('/fleet/api/standup', { method: 'POST', body: JSON.stringify(body) });
      form.reset();
      loadDailyStandups();
      alert('Standup entry saved!');
    } catch (err) { alert('Failed to save standup.'); }
  });
}

// User Management
async function loadUsers() {
  const container = document.getElementById('users-list');
  try {
    const data = await fetchJson('/fleet/api/users');
    container.innerHTML = data.users.map(email => `
      <div class="user-item">
        <span>${email}</span>
        <button class="btn-remove" onclick="removeUser('${email}')">REMOVE</button>
      </div>
    `).join('');
  } catch (err) { container.innerHTML = '<p class="muted">Failed to load users.</p>'; }
}

window.removeUser = async (email) => {
  if (!confirm(`Remove ${email}?`)) return;
  try {
    const data = await fetchJson('/fleet/api/users');
    const newUsers = data.users.filter(u => u !== email);
    await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users: newUsers }) });
    loadUsers();
  } catch (err) { alert('Failed to remove user.'); }
};

document.getElementById('user-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = e.target.email.value.trim().toLowerCase();
  try {
    const data = await fetchJson('/fleet/api/users');
    if (data.users.includes(email)) return alert('User already exists.');
    data.users.push(email);
    await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users: data.users }) });
    e.target.reset();
    loadUsers();
  } catch (err) { alert('Failed to add user.'); }
});

// Project Modal
window.openProjectModal = () => document.getElementById('project-modal').style.display = 'flex';
window.closeProjectModal = () => document.getElementById('project-modal').style.display = 'none';

document.getElementById('project-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
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
});

document.addEventListener('DOMContentLoaded', () => {
  verifyAuth();
  wireNavControls();
  loadFleetMeta();
  renderMemoryTree();
  loadDailyStandups();
  setupStandupForm();
});
