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

const memoryTree = [
  {
    folder: 'Global Rules',
    files: [
      { title: 'Team Rules', desc: 'Standardized protocols for commits, Kanban, and shared memory.', path: 'AGENTS/RULES.md' },
      { title: 'KeyVault Strategy', desc: 'Infisical secrets management guide.', path: 'AGENTS/KEYVAULT.md' }
    ]
  },
  {
    folder: 'Project Context',
    files: [
      { title: 'CRM Prototype', desc: 'Relational management logic for sales leads.', path: 'AGENTS/CONTEXT/crm_poc_context.md' }
    ]
  }
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
    try {
      fleetSettings = await fetchJson('/fleet/api/settings');
    } catch (e) { console.warn('Settings load failed, using defaults'); }

    const data = await fetchJson(endpoint);
    fleetData = data;

    loadTeamWithStatus();
    populateProjects();
    loadLessons(); 
    
    if (fleetSettings.is_demo === true) {
      setupReducedMode(isGrowth);
    } else {
      setupStandaloneMode();
    }
  } catch (err) { 
    console.error('Core metadata load failed:', err);
  }
}

function setupStandaloneMode() {
  const standaloneBtns = document.querySelectorAll('.standalone-only');
  for (let i = 0; i < standaloneBtns.length; i++) standaloneBtns[i].style.display = 'inline-flex';
}

function setupReducedMode(isGrowth) {
  const h1 = document.querySelector('h1');
  const lede = document.querySelector('.lede');
  if (h1) h1.textContent = isGrowth ? 'Growth Fleet Hub' : 'Demo Fleet Hub';
  if (lede) lede.textContent = isGrowth
    ? 'Specialized agentic fleet for Sales, Marketing, and Lead Discovery.'
    : 'This is a reduced version of the Fleet Hub management plane.';

  if (isGrowth) {
    document.querySelectorAll('.growth-only').forEach(el => el.style.display = 'flex');
  }

  const usersBtn = document.querySelector('[data-section-button="section-users"]');
  if (usersBtn) {
    usersBtn.innerHTML = '<span>👤</span> User Management';
  }

  const usersSection = document.getElementById('section-users');
  if (usersSection) {
    usersSection.innerHTML = `
      <header class="page-header">
        <p class="eyebrow">${isGrowth ? 'Growth Strategy' : 'Production Feature'}</p>
        <h1>${isGrowth ? 'Request Industry Setup' : 'User Access Control'}</h1>
        <p class="lede">In the full Fleet Hub, you can manage team access dynamically.</p>
      </header>
      <div class="standup-form" style="padding: 3rem; text-align: center; border-style: dashed;">
        <p style="color: var(--teal-bright); font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;">
          Your sales team — human and AI — in one place.
        </p>
        <p class="muted" style="margin-bottom: 1.5rem;">
          In the full Growth Fleet Hub, you whitelist a team member's email and they instantly join the shared pipeline. Scout pushes leads, Closer logs follow-ups, and your reps take the final action — no context lost in translation.
        </p>
        <a href="https://bigbearengineering.com" target="_blank" style="display:inline-block; padding: 0.6rem 1.5rem; background: linear-gradient(135deg, var(--teal-bright), var(--teal)); color: #fff; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 0.9rem;">
          Request Your Industry Setup &rarr;
        </a>
      </div>
    `;
  }
}

async function verifyAuth() {
  try {
    const data = await fetchJson('/auth/verify');
    if (data && data.ok) {
      currentUser = data.user;
      const userInfo = document.getElementById('user-info');
      if (userInfo) userInfo.innerHTML = `Logged in as:<br><strong>${currentUser.email}</strong>`;
    }
  } catch (err) { console.error(err); }
}

let agentHeartbeats = {};
let agentTaskCounts = {};
let agentApprovedCounts = {};
let agentStats = {};

async function loadTeamWithStatus() {
  try {
    const [hbData, taskData, statsData] = await Promise.all([
      fetchJson('/fleet/api/heartbeats').catch(() => []),
      fetchJson('/fleet/api/tasks').catch(() => []),
      fetchJson('/fleet/api/agent-stats').catch(() => ({}))
    ]);

    agentHeartbeats = {};
    for (let i = 0; i < hbData.length; i++) {
      const h = hbData[i];
      const key = (h.agent || '').toLowerCase().split(' ')[0];
      if (!agentHeartbeats[key] || h.updated > agentHeartbeats[key].updated) {
        agentHeartbeats[key] = h;
      }
    }

    agentTaskCounts = {};
    agentApprovedCounts = {};
    const tasks = taskData.items || taskData;
    for (let i = 0; i < tasks.length; i++) {
      const t = tasks[i];
      if (t.assigned_agent) {
        const key = t.assigned_agent.toLowerCase().split(' ')[0];
        const active = t.status === 'todo' || t.status === 'in_progress' || t.status === 'peer_review';
        if (active) agentTaskCounts[key] = (agentTaskCounts[key] || 0) + 1;
        if (t.status === 'approved') agentApprovedCounts[key] = (agentApprovedCounts[key] || 0) + 1;
      }
    }

    agentStats = statsData || {};
  } catch (e) { console.warn('Status fetch failed:', e); }

  populateTeam();
  populateAgentsTable(); 
  loadAggregateStats();
  if (typeof loadSchichtplan === 'function') loadSchichtplan(schichtplanWindow);
}

function populateAgentsTable() { 
  const container = document.getElementById("agents-stats-table"); 
  if (!container || !fleetData.team) return; 
  let html = `<table class="agents-table"><thead><tr><th>Agent</th><th>Status</th><th>Last Seen</th><th>Idle Until</th><th>Tasks</th><th>Tokens (est.)</th><th>Type</th><th>Success Rate</th><th>Avg Session</th></tr></thead><tbody>`; 
  for (let i = 0; i < fleetData.team.length; i++) { 
    const m = fleetData.team[i]; 
    const key = (m.heartbeatKey || m.name.toLowerCase().split(" ")[0]).toLowerCase(); 
    const hb = agentHeartbeats[key]; 
    const stats = agentStats[key] || { approved: 0, rejected: 0, sessions: 0, avg_session_ms: 0 }; 
    let hbClass = "hb-offline", hbText = "Offline", lastSeen = "—", isDark = false; 
    if (hb) { 
      const ageSec = (Date.now() - new Date(hb.updated)) / 1000; 
      if (ageSec < 1800) { hbClass = hb.status === "working" ? "hb-working" : "hb-idle"; hbText = hb.status.charAt(0).toUpperCase() + hb.status.slice(1); } 
      else { hbClass = "hb-offline"; hbText = "Offline"; if (ageSec > 3600 * 2) isDark = true; } 
      lastSeen = formatAge(ageSec); 
    } 
    // Success rate needs task_events reassignment data (#94) to be meaningful — show placeholder until then
    const srValue = null;
    let srClass = ""; 
    if (srValue !== null) { 
      if (srValue >= 90) srClass = "stat-good"; 
      else if (srValue >= 70) srClass = "stat-warn"; 
      else srClass = "stat-bad"; 
    } 
    const successRateStr = srValue !== null ? srValue + "%" : "—"; 
    const tokenProxy = { "clau": 8000, "gem": 12000, "codi": 8000, "misty": 1500, "openclaw": 500 }; 
    const avgTokens = tokenProxy[key] || 1500; 
    const tokensEst = formatTokens(stats.sessions * avgTokens); 
    const idleUntil = (isDark && m.idleUntil) ? m.idleUntil : "—"; 
    const runtimeType = (m.runtime || "").includes("Local") ? "Local" : "Cloud"; 
    const runtimeClass = runtimeType === "Local" ? "type-local" : "type-cloud"; 
    html += `<tr><td><div style="display:flex;align-items:center;gap:8px;"><span>${m.avatar}</span> <strong>${m.name}</strong></div></td><td><div style="display:flex;align-items:center;gap:6px;"><div class="hb-dot ${hbClass}"></div> ${hbText}</div></td><td>${lastSeen}</td><td>${idleUntil}</td><td>${agentApprovedCounts[key] || 0}</td><td>${tokensEst}</td><td class="${runtimeClass}">${runtimeType}</td><td class="${srClass}">${successRateStr}</td><td>${formatDuration(stats.avg_session_ms)}</td></tr>`; 
  } 
  html += "</tbody></table>"; 
  container.innerHTML = html; 
} 

function formatAge(sec) { 
  if (sec < 60) return Math.round(sec) + "s ago"; 
  if (sec < 3600) return Math.round(sec / 60) + "m ago"; 
  if (sec < 3600 * 24) return Math.round(sec / 3600) + "h ago"; 
  return Math.round(sec / (3600 * 24)) + "d ago"; 
} 

function formatTokens(n) { 
  if (n < 1000) return n; 
  if (n < 1000000) return (n / 1000).toFixed(1) + "k"; 
  return (n / 1000000).toFixed(1) + "M"; 
} 

function formatDuration(ms) { 
  if (!ms) return "—"; 
  const m = Math.floor(ms / 60000); 
  const s = Math.floor((ms % 60000) / 1000); 
  return m > 0 ? m + "m " + s + "s" : s + "s"; 
} 

async function loadAggregateStats() { 
  const tasks24hEl = document.getElementById("stat-tasks-24h"); 
  if (!tasks24hEl) return; 
  try { 
    const taskData = await fetchJson("/fleet/api/tasks"); 
    const items = taskData.items || taskData; 
    const now = Date.now(); 
    const dayMs = 24 * 3600 * 1000; 
    let completed = 0, inReview = 0, blocked = 0; 
    for (const t of items) { 
      const created = new Date(t.created).getTime(); 
      if (now - created < dayMs) { 
        if (t.status === "approved") completed++; 
        else if (t.status === "peer_review") inReview++; 
        else if (t.status === "blocked") blocked++; 
      } 
    } 
    tasks24hEl.textContent = `${completed} / ${inReview} / ${blocked}`; 
  } catch (e) { tasks24hEl.textContent = "Err"; } 
  
  const fields = ["stat-reassigns", "stat-circuit", "stat-mtbf", "stat-mttr", "stat-wake"];
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = "—";
  });
} 

function populateTeam() {
  const container = document.getElementById('team-grid');
  if (!container || !fleetData.team) return;
  let html = '';
  const isStandalone = fleetSettings.is_demo === false;

  for (let i = 0; i < fleetData.team.length; i++) {
    const m = fleetData.team[i];
    const key = m.name.toLowerCase().split(' ')[0];
    const hbKey = (m.heartbeatKey || key).toLowerCase();
    const hb = agentHeartbeats[hbKey];
    let hbClass = 'hb-offline';
    let hbTitle = 'Offline';
    if (hb) {
      const ageSec = (Date.now() - new Date(hb.updated)) / 1000;
      if (ageSec < 1800) { 
        hbClass = hb.status === 'working' ? 'hb-working' : 'hb-idle';
        hbTitle = hb.status.charAt(0).toUpperCase() + hb.status.slice(1);
      } else if (ageSec < 3600 * 24) { 
        hbClass = 'hb-suspected-offline';
        const mins = Math.floor(ageSec / 60);
        hbTitle = 'Suspected Offline (Last seen ' + mins + 'm ago)';
      }
    }

    const count = agentTaskCounts[key] || 0;
    const countBadge = count > 0 ? '<span class="task-count">' + count + '</span>' : '';

    let skillsHtml = '';
    if (m.skills) {
      for (let j = 0; j < m.skills.length; j++) {
        const s = m.skills[j];
        skillsHtml += '<span class="tag skill-chip" onclick="removeSkill(\'' + hbKey + '\', \'' + s + '\')">' + s + ' <span class="remove-x">&times;</span></span>';
      }
    }
    skillsHtml += '<button class="btn-add-tag" onclick="addSkill(\'' + hbKey + '\')">+</button>';

    const memLink = replacePlaceholders(m.memoryLink);
    const removeBtn = isStandalone
      ? '<button class="btn-remove" onclick="removeAgent(\'' + m.name + '\')">Remove</button>'
      : '';

    html +=
      '<article class="agent-card" id="agent-card-' + i + '">' +
        '<div class="card-summary" onclick="toggleAgentCard(' + i + ')">' +
          '<div class="hb-dot ' + hbClass + '" title="' + hbTitle + '"></div>' +
          '<div class="agent-avatar">' + m.avatar + '</div>' +
          '<div class="card-summary-info">' +
            '<h3>' + m.name + '</h3>' +
            '<div class="role-title">' + m.roleTitle + '</div>' +
          '</div>' +
          '<div class="card-meta">' +
            countBadge +
            '<span style="font-size: 10px; color: var(--text-muted);">▼</span>' +
          '</div>' +
        '</div>' +
        '<div class="card-details">' +
          '<div class="runtime-badge">RUNTIME: ' + m.runtime + '</div>' +
          '<p class="role-desc">' + m.roleDesc + '</p>' +
          '<div class="tag-list">' + skillsHtml + '</div>' +
          '<div style="margin-top: 12px; display: flex; gap: 8px;">' +
            '<a href="' + memLink + '" target="_blank" class="btn-link">MANDATE</a>' +
            removeBtn +
          '</div>' +
        '</div>' +
      '</article>';
  }
  container.innerHTML = html;
}

window.addSkill = async function(agentKey) {
  const skill = prompt('Enter new skill for ' + agentKey + ':');
  if (!skill) return;
  const agent = fleetData.team.find(a => (a.heartbeatKey || a.name.toLowerCase().split(' ')[0]) === agentKey);
  if (agent) {
    if (!agent.skills) agent.skills = [];
    if (!agent.skills.includes(skill)) {
      agent.skills.push(skill);
      await saveFleetMeta();
    }
  }
};

window.removeSkill = async function(agentKey, skill) {
  if (!confirm('Remove skill "' + skill + '" from ' + agentKey + '?')) return;
  const agent = fleetData.team.find(a => (a.heartbeatKey || a.name.toLowerCase().split(' ')[0]) === agentKey);
  if (agent && agent.skills) {
    agent.skills = agent.skills.filter(s => s !== skill);
    await saveFleetMeta();
  }
};

window.toggleAgentCard = function(i) {
  const card = document.getElementById('agent-card-' + i);
  if (card) card.classList.toggle('expanded');
};

async function loadLessons() {
  const container = document.getElementById('lessons-grid');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/lessons');
    let html = '';
    const items = (data.items || data).slice(0, 5);
    for (let i = 0; i < items.length; i++) {
      const l = items[i];
      html +=
        '<div class="agent-card">' +
          '<div class="card-summary">' +
            '<div style="flex: 1;">' +
              '<h3 style="font-size: 13px;">' + l.title + '</h3>' +
              '<span class="tag" style="font-size: 10px;">' + (l.category || 'Insight') + '</span>' +
            '</div>' +
            '<span style="font-size: 11px; color: var(--text-muted);">' + l.agent + '</span>' +
          '</div>' +
        '</div>';
    }
    container.innerHTML = html || '<p style="padding: 16px; font-size: 13px; color: var(--text-muted);">No lessons yet.</p>';
  } catch (err) { console.error(err); }
}

window.updateLessonStatus = async (id, status) => {
  try {
    await fetchJson(`/fleet/api/lessons/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
    loadLessons();
  } catch (err) { alert('Failed to update lesson status.'); }
};

function populateProjects() {
  const container = document.getElementById('projects-grid');
  if (!container) return;
  container.innerHTML = (fleetData.projects || [])
    .map((p) => {
      const isActive = p.is_active === true;
      const extra = p.statsLink ? `<a href="${p.statsLink}" target="_blank" class="btn-link">📊 VIEW STATS</a>` : '';
      const crm = p.crmLink ? `<a href="${p.crmLink}" target="_blank" class="btn-link">🤝 VIEW CRM</a>` : '';
      const activeBadge = isActive
        ? `<span style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--teal-bright);background:rgba(21,153,136,0.12);border:1px solid rgba(21,153,136,0.3);border-radius:6px;padding:0.25rem 0.75rem;">ACTIVE</span>`
        : `<button class="btn-link" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.15);color:var(--text-muted);" onclick="activateProject('${p.title.replace(/'/g, "\\'")}', this)">SET ACTIVE</button>`;
      return `
        <article class="project-card" style="${isActive ? 'border-color:rgba(21,153,136,0.5);box-shadow:0 0 0 1px rgba(21,153,136,0.15);' : ''}">
          <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
            <h3 style="margin-bottom:0;">${p.title}</h3>
            ${activeBadge}
          </div>
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

window.activateProject = async (title, btn) => {
  btn.disabled = true;
  btn.textContent = 'ACTIVATING...';
  try {
    const result = await fetchJson('/fleet/api/activate-project', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
    if (result.ok) {
      if (!result.synced_to_git) {
        alert(`Dashboard updated to "${title}".\n\nAgents: the change was not pushed to GitHub automatically (no deploy key on server). Commit AGENTS/CONFIG/fleet_meta.json from your local machine to sync agents.`);
      }
      await loadFleetMeta();
    } else {
      alert('Failed: ' + (result.error || 'unknown error'));
      btn.disabled = false;
      btn.textContent = 'SET ACTIVE';
    }
  } catch (e) {
    alert('Error: ' + e.message);
    btn.disabled = false;
    btn.textContent = 'SET ACTIVE';
  }
};

function renderMemoryTree(query) {
  const container = document.getElementById('docs-grid');
  if (!container) return;
  let html = '';
  for (let i = 0; i < memoryTree.length; i++) {
    const group = memoryTree[i];
    for (let j = 0; j < group.files.length; j++) {
      const f = group.files[j];
      if (query && !f.title.toLowerCase().includes(query.toLowerCase()) && !f.desc.toLowerCase().includes(query.toLowerCase())) continue;
      html +=
        '<div class="agent-card">' +
          '<div class="card-summary">' +
            '<div style="flex: 1;">' +
              '<h3 style="font-size: 13px;">' + f.title + '</h3>' +
              '<p style="font-size: 11px; color: var(--text-muted);">' + f.desc + '</p>' +
            '</div>' +
            '<a href="https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/' + f.path + '" target="_blank" class="btn-link">VIEW</a>' +
          '</div>' +
        '</div>';
    }
  }
  container.innerHTML = html;
}

async function loadInbox() {
  const container = document.getElementById('inbox-feed');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/messages');
    let html = '';
    const messages = data.messages || data;
    for (let i = 0; i < messages.length; i++) {
      const m = messages[i];
      const isUnread = m.status === 'unread';
      html +=
        '<div class="inbox-card ' + (isUnread ? 'inbox-unread' : '') + '">' +
          '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">' +
            '<strong style="font-size: 13px;">' + m.subject + '</strong>' +
            '<span style="font-size: 11px; color: var(--text-muted);">' + m.from + '</span>' +
          '</div>' +
          '<p style="font-size: 13px; color: var(--text-secondary); margin-bottom: 8px;">' + m.body + '</p>' +
          '<div style="font-size: 11px; color: var(--text-muted);">' + new Date(m.timestamp).toLocaleString() + '</div>' +
        '</div>';
    }
    container.innerHTML = html;
  } catch (err) { console.error(err); }
}

async function loadKanban() {
  const containers = {
    planned: document.getElementById('kanban-planned'),
    working: document.getElementById('kanban-working'),
    done: document.getElementById('kanban-done'),
    blocked: document.getElementById('kanban-blocked')
  };
  if (!containers.planned) return;

  try {
    const data = await fetchJson('/fleet/api/kanban');
    const renderCard = (t) => {
      let skillsHtml = '';
      if (t.required_skills && Array.isArray(t.required_skills)) {
        skillsHtml = t.required_skills.map(s => `<span class="tag" style="font-size: 9px; padding: 0 4px; margin-right: 4px;">${s}</span>`).join('');
      }
      return `
      <div class="activity-item">
        <strong>#${t.id}: ${t.title}</strong>
        <div style="margin-top: 4px;">${skillsHtml}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
          <span style="font-size: 11px; font-weight: 600; color: var(--accent);">${t.owner || t.assigned_agent || 'Unassigned'}</span>
          <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">${t.status || ''}</span>
        </div>
      </div>
    `;
    };

    containers.planned.innerHTML = (data.planned || []).map(renderCard).join('') || '<p style="font-size: 12px; color: var(--text-muted); padding: 8px;">Empty</p>';
    containers.working.innerHTML = (data.working || []).map(renderCard).join('') || '<p style="font-size: 12px; color: var(--text-muted); padding: 8px;">Empty</p>';
    containers.done.innerHTML = (data.done || []).map(renderCard).join('') || '<p style="font-size: 12px; color: var(--text-muted); padding: 8px;">Empty</p>';
    if (containers.blocked) containers.blocked.innerHTML = (data.blocked || []).map(renderCard).join('') || '<p style="font-size: 12px; color: var(--text-muted); padding: 8px;">Empty</p>';
  } catch (err) { console.error(err); }
}

window.refreshKanban = function() { loadKanban(); };

async function loadPBTasks() {
  const container = document.getElementById('pb-tasks-container');
  if (!container) return;
  
  const statusFilterEl = document.getElementById('pb-status-filter');
  const statusFilter = statusFilterEl ? statusFilterEl.value : 'all';
  const filterParam = statusFilter === 'all' ? '' : `status = "${statusFilter}"`;
  
  try {
    const params = filterParam ? { filter: filterParam } : {};
    const url = `/fleet/api/tasks?${new URLSearchParams(params).toString()}`;
    const data = await fetchJson(url);
    
    if (!data || !data.items || data.items.length === 0) {
      container.innerHTML = '<p style="font-size: 12px; color: var(--text-muted); padding: 8px;">No tasks found</p>';
      return;
    }
    
    const renderTask = (task) => {
      const ghIssue = task.gh_issue_id ? ` <a href="https://github.com/UrsushoribilisMusic/agentic-fleet-hub/issues/${task.gh_issue_id}" target="_blank" title="GitHub Issue #${task.gh_issue_id}">#${task.gh_issue_id}</a>` : '';
      const sourceBadge = task.source === 'telegram' ? ' <span class="tag" style="background: var(--accent); color: white; font-size: 9px;">TELEGRAM</span>' : '';
      const syncBadge = task.is_github_sync === false ? ' <span class="tag" style="background: var(--text-muted); color: white; font-size: 9px;">NO GITHUB SYNC</span>' : '';
      
      return `
      <div class="activity-item" style="border-left: 3px solid ${getStatusColor(task.status)}">
        <div style="display: flex; justify-content: space-between; align-items: start;">
          <div style="flex: 1;">
            <strong>#${task.id}: ${task.title}</strong>${ghIssue}${sourceBadge}${syncBadge}
            <div style="margin-top: 4px; font-size: 12px;">
              <span style="color: var(--text-secondary);">Status: ${task.status}</span>
              ${task.assigned_agent ? ` | Agent: ${task.assigned_agent}` : ''}
            </div>
            ${task.description ? `<div style="margin-top: 6px; font-size: 11px; color: var(--text-muted);">${task.description.substring(0, 200)}${task.description.length > 200 ? '...' : ''}</div>` : ''}
          </div>
        </div>
      </div>`;
    };
    
    container.innerHTML = data.items.map(renderTask).join('');
  } catch (err) {
    console.error('PB Viewer error:', err);
    container.innerHTML = '<p style="color: var(--error); font-size: 12px; padding: 8px;">Error loading tasks.</p>';
  }
}

function getStatusColor(status) {
  const colors = {
    'todo': '#5865F2',
    'in_progress': '#F5A623',
    'peer_review': '#7ED321',
    'waiting_human': '#BD10E0',
    'blocked': '#E74C3C',
    'approved': '#2ECC71',
    'backlog': '#95A5A6'
  };
  return colors[status] || '#7F8C8D';
}

let schichtplanWindow = '24h';

window.loadSchichtplan = async function(windowParam) {
  windowParam = windowParam || schichtplanWindow;
  schichtplanWindow = windowParam;

  const chart = document.getElementById('schichtplan-chart');
  if (!chart) return;
  chart.innerHTML = '<p style="font-size: 12px; color: var(--text-muted); padding: 16px;">Loading timeline...</p>';

  const btns = document.querySelectorAll('.schicht-btn');
  for (let i = 0; i < btns.length; i++) {
    btns[i].classList.toggle('is-active', btns[i].getAttribute('data-window') === windowParam);
  }

  const windowMs = windowParam === '30d' ? 30*24*3600*1000 :
                   windowParam === '7d'  ?  7*24*3600*1000 :
                                               24*3600*1000;
  const windowEnd = Date.now();
  const windowStart = windowEnd - windowMs;

  let heartbeats = [];
  try {
    const data = await fetchJson('/fleet/api/heartbeats/timeline?window=' + windowParam);
    heartbeats = data.items || [];
  } catch (e) {
    chart.innerHTML = '<p style="font-size: 12px; color: var(--danger); padding: 16px;">Failed to load timeline.</p>';
    return;
  }

  const agents = (fleetData.team || []).map(function(m) {
    return { name: m.name, key: (m.heartbeatKey || m.name.toLowerCase().split(' ')[0]).toLowerCase() };
  });

  if (agents.length === 0) {
    chart.innerHTML = '<p style="font-size: 12px; color: var(--text-muted); padding: 16px;">No agents found.</p>';
    return;
  }

  const byAgent = {};
  for (let i = 0; i < heartbeats.length; i++) {
    const h = heartbeats[i];
    const key = (h.agent || '').toLowerCase().split(' ')[0];
    if (!byAgent[key]) byAgent[key] = [];
    byAgent[key].push(h);
  }

  const tickInterval = windowParam === '30d' ? 5*24*3600*1000 :
                       windowParam === '7d'  ?   24*3600*1000 :
                                                  4*3600*1000;
  const ticks = [];
  for (let t = windowStart; t <= windowEnd + tickInterval; t += tickInterval) {
    if (t <= windowEnd) ticks.push(t);
  }
  ticks.push(windowEnd);

  let html = '<div class="schichtplan-wrap">';
  html += '<div class="schichtplan-row schichtplan-axis-row">';
  html += '<div class="schichtplan-label-col"></div>';
  html += '<div class="schichtplan-timeline-col">';
  for (let i = 0; i < ticks.length; i++) {
    const pct = ((ticks[i] - windowStart) / windowMs * 100).toFixed(2);
    html += '<span class="schichtplan-tick-label" style="left:' + pct + '%">' + schichtFormatTick(ticks[i], windowParam) + '</span>';
  }
  html += '</div></div>';

  for (let i = 0; i < agents.length; i++) {
    const agent = agents[i];
    const hbs = (byAgent[agent.key] || []).slice().sort(function(a, b) {
      return new Date(a.created) - new Date(b.created);
    });
    const segs = schichtBuildSegments(hbs, windowStart, windowEnd);

    html += '<div class="schichtplan-row">';
    html += '<div class="schichtplan-label-col"><span class="schichtplan-agent-name">' + agent.name + '</span></div>';
    html += '<div class="schichtplan-timeline-col schichtplan-lane">';

    for (let j = 0; j < ticks.length; j++) {
      const pct = ((ticks[j] - windowStart) / windowMs * 100).toFixed(2);
      html += '<div class="schichtplan-grid-line" style="left:' + pct + '%"></div>';
    }

    for (let j = 0; j < segs.length; j++) {
      const seg = segs[j];
      const left = ((seg.start - windowStart) / windowMs * 100).toFixed(3);
      const width = ((seg.end - seg.start) / windowMs * 100).toFixed(3);
      if (parseFloat(width) < 0.05) continue;
      const title = seg.status + ' (' + schichtFormatDur(seg.end - seg.start) + ')';
      html += '<div class="schichtplan-seg seg-' + seg.status + '" style="left:' + left + '%;width:' + width + '%" title="' + title + '"></div>';
    }
    html += '</div></div>';
  }

  html += '<div class="schichtplan-legend">';
  html += '<span class="schichtplan-leg"><span class="schichtplan-leg-swatch seg-working"></span>Working</span>';
  html += '<span class="schichtplan-leg"><span class="schichtplan-leg-swatch seg-idle"></span>Idle</span>';
  html += '<span class="schichtplan-leg"><span class="schichtplan-leg-swatch seg-dark"></span>Dark / Quota</span>';
  html += '<span class="schichtplan-leg"><span class="schichtplan-leg-swatch seg-offline"></span>Offline</span>';
  html += '</div></div>';
  chart.innerHTML = html;
};

function schichtBuildSegments(heartbeats, windowStart, windowEnd) {
  const DARK_THRESHOLD = 2 * 3600 * 1000;
  const CARRY_MS       =    10 * 60 * 1000;
  const segments = [];

  if (heartbeats.length === 0) return segments;

  const firstTs = new Date(heartbeats[0].created).getTime();
  if (firstTs > windowStart + DARK_THRESHOLD) {
    segments.push({ start: windowStart, end: Math.min(firstTs, windowEnd), status: 'offline' });
  }

  for (let i = 0; i < heartbeats.length; i++) {
    const hb = heartbeats[i];
    const start = Math.max(new Date(hb.created).getTime(), windowStart);
    const nextTs = i + 1 < heartbeats.length ? new Date(heartbeats[i + 1].created).getTime() : windowEnd;
    const end = Math.min(nextTs, windowEnd);
    if (end <= start) continue;

    const gap = end - start;
    if (gap > DARK_THRESHOLD) {
      const carry = Math.min(start + CARRY_MS, end);
      if (carry > start) segments.push({ start: start, end: carry, status: hb.status });
      segments.push({ start: carry, end: end, status: 'dark' });
    } else {
      segments.push({ start: start, end: end, status: hb.status });
    }
  }
  return segments;
}

function schichtFormatTick(ts, windowParam) {
  const d = new Date(ts);
  if (windowParam === '24h') return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (windowParam === '7d')  return d.toLocaleDateString([], { weekday: 'short', month: 'numeric', day: 'numeric' });
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function schichtFormatDur(ms) {
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return h > 0 ? h + 'h ' + m + 'm' : m + 'm';
}

async function loadRules() {
  const el = document.getElementById('rules-view');
  if (!el) return;
  try {
    const raw = await fetchText('/fleet/AGENTS/RULES.md');
    el.innerHTML = renderSimpleMarkdown(raw);
  } catch (err) { el.innerHTML = '<p>Error loading rules.</p>'; }
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
  if (targetId === 'section-kanban') loadKanban();
  if (targetId === 'section-pbviewer') loadPBTasks();
  
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('is-open');
}

function wireNavControls() {
  MAIN_SECTION_BUTTONS = Array.prototype.slice.call(document.querySelectorAll('[data-section-button]'));
  MAIN_SECTIONS = Array.prototype.slice.call(document.querySelectorAll('.section'));
  for (let i = 0; i < MAIN_SECTION_BUTTONS.length; i++) {
    const button = MAIN_SECTION_BUTTONS[i];
    button.onclick = function() { activateSection(this.getAttribute('data-section-button')); };
  }

  const toggle = document.getElementById('mobile-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.onclick = function() {
      sidebar.classList.toggle('is-open');
    };
  }

  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.onclick = toggleTheme;
  }
}

function initTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  let target = 'dark';
  
  if (current === 'dark') {
    target = 'light';
  } else if (current === 'light') {
    target = 'dark';
  } else {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    target = isDark ? 'light' : 'dark';
  }
  
  document.documentElement.setAttribute('data-theme', target);
  localStorage.setItem('theme', target);
}

async function loadDailyStandups() {
  const view = document.getElementById('daily-view');
  if (!view) return;
  try {
    const data = await fetchJson('/fleet/api/standups');
    dailyStandupsIndex = data.sort((a, b) => b.date.localeCompare(a.date));
    renderDailyButtons();
    if (dailyStandupsIndex.length > 0) selectDaily(dailyStandupsIndex[0]);
  } catch (err) { console.error(err); }
}

function renderDailyButtons() {
  const container = document.getElementById('daily-buttons');
  if (!container) return;
  container.innerHTML = dailyStandupsIndex.map(day => `
    <button class="daily-button ${day.date === activeDailyDate ? 'is-active' : ''}" onclick="selectDailyByDate('${day.date}')">${day.date}</button>
  `).join('');
}

window.selectDailyByDate = function(date) {
  const day = dailyStandupsIndex.find(d => d.date === date);
  if (day) selectDaily(day);
};

async function selectDaily(day) {
  activeDailyDate = day.date;
  renderDailyButtons();
  const view = document.getElementById('daily-view');
  if (!view) return;
  try {
    const raw = await fetchText('/fleet/api/standups/' + day.date);
    view.innerHTML = renderSimpleMarkdown(raw);
  } catch (err) { console.error(err); }
}

async function saveFleetMeta() {
  try {
    await fetchJson('/fleet/api/config', {
      method: 'POST',
      body: JSON.stringify(fleetData)
    });
    loadFleetMeta();
  } catch (err) { alert('Failed to save metadata.'); }
}

window.openTaskModal = () => { const el = document.getElementById('task-modal'); if (el) el.style.display = 'flex'; };
window.closeTaskModal = () => { const el = document.getElementById('task-modal'); if (el) el.style.display = 'none'; };

function setupForms() {
  const standupForm = document.getElementById('standup-form');
  if (standupForm) {
    standupForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = { done: fd.get('done'), today: fd.get('today'), blockers: fd.get('blockers'), agent: (currentUser && currentUser.email) || 'Admin' };
      try {
        await fetchJson('/fleet/api/standup', { method: 'POST', body: JSON.stringify(body) });
        e.target.reset();
        loadDailyStandups();
      } catch (err) { alert('Failed to save.'); }
    };
  }

  const taskForm = document.getElementById('task-form');
  if (taskForm) {
    taskForm.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const skillsRaw = fd.get('required_skills') || '';
      const skills = skillsRaw.split(',').map(s => s.trim()).filter(Boolean);
      
      const body = {
        title: fd.get('title'),
        description: fd.get('description'),
        assigned_agent: fd.get('assigned_agent'),
        status: 'todo',
        required_skills: skills
      };
      
      try {
        await fetchJson('/fleet/api/tasks', { method: 'POST', body: JSON.stringify(body) });
        window.closeTaskModal();
        e.target.reset();
        loadKanban();
      } catch (err) { alert('Failed to create task.'); }
    };
  }

  const agentForm = document.getElementById('agent-form');
  if (agentForm) {
    document.getElementById('agent-form').onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = {
        name: fd.get('name'),
        avatar: fd.get('avatar'),
        heartbeatKey: fd.get('heartbeatKey'),
        fallbackChain: (fd.get('fallbackChain') || '').split(',').map(s => s.trim()).filter(Boolean),
        skills: (fd.get('skills') || '').split(',').map(s => s.trim()).filter(Boolean)
      };
      
      try {
        const meta = await fetchJson('/fleet/api/config');
        meta.team.push(body);
        await fetchJson('/fleet/api/config', { method: 'POST', body: JSON.stringify(meta) });
        window.closeAgentModal();
        e.target.reset();
        loadFleetMeta();
      } catch (err) { alert('Failed to add agent.'); }
    };
  }

  const projectForm = document.getElementById('project-form');
  if (projectForm) {
    document.getElementById('project-form').onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = {
        id: fd.get('id'),
        name: fd.get('name'),
        path: fd.get('path'),
        repo: fd.get('repo'),
        kanban: fd.get('kanban'),
        docs: fd.get('docs'),
        active: false
      };
      
      try {
        const meta = await fetchJson('/fleet/api/config');
        meta.projects.push(body);
        await fetchJson('/fleet/api/config', { method: 'POST', body: JSON.stringify(meta) });
        window.closeProjectModal();
        e.target.reset();
        loadFleetMeta();
      } catch (err) { alert('Failed to add project.'); }
    };
  }
}

async function loadUsers() {
  const container = document.getElementById('users-list');
  if (!container) return;
  try {
    const data = await fetchJson('/fleet/api/users');
    container.innerHTML = (data.users || []).map(u => `
      <div class="agent-card" style="margin-bottom: 4px;">
        <div class="card-summary">
          <span style="flex: 1; font-size: 13px;">${u}</span>
          <button class="btn-link" onclick="removeUser('${u}')">Remove</button>
        </div>
      </div>
    `).join('');
  } catch (err) { console.error(err); }
}

window.removeUser = async function(email) {
  if (!confirm('Remove ' + email + '?')) return;
  try {
    const data = await fetchJson('/fleet/api/users');
    const users = data.users.filter(u => u !== email);
    await fetchJson('/fleet/api/users', { method: 'POST', body: JSON.stringify({ users }) });
    loadUsers();
  } catch (err) { alert('Removed.'); }
};

window.openProjectModal = () => { const el = document.getElementById('project-modal'); if (el) el.style.display = 'flex'; };
window.closeProjectModal = () => { const el = document.getElementById('project-modal'); if (el) el.style.display = 'none'; };
window.openAgentModal = () => { const el = document.getElementById('agent-modal'); if (el) el.style.display = 'flex'; };
window.closeAgentModal = () => { const el = document.getElementById('agent-modal'); if (el) el.style.display = 'none'; };

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  const themeToggle = document.getElementById('theme-toggle-btn');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('flotilla-theme', next);
    });
  }
  verifyAuth();
  wireNavControls();
  loadFleetMeta();
  renderMemoryTree();
  loadDailyStandups();
  setupForms();
});
