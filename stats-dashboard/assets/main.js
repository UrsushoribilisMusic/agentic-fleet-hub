
function fetchText(url) {
  return fetch(url, { cache: 'no-store', credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.text();
  });
}

let dailyStandupsIndex = [];
let activeDailyDate = '';
let MAIN_SECTION_BUTTONS = [];
let MAIN_SECTIONS = [];
let STATS_GROUP_BUTTONS = [];
let STATS_PANELS = [];
let MUSIC_TAB_BUTTONS = [];
let MUSIC_PANELS = [];
let SORTABLE_HEADERS = [];

let musicShortsCache = [];
let statusResolved = false;
const musicSortState = { field: 'yt_views', order: 'desc' };

const teamMembers = [
  {
    name: 'robotrosssalesman',
    role: 'Chief of Commerce & Salesman API',
    status: 'Cloud VM • always online • OpenAI GPT (OAuth)',
    tools: ['Shopify hook', 'Virtuals connector', 'Agentegra web rep'],
    location: 'Server (public)',
    memoryLink: '../docs/agent-salesman.md',
    uiLinks: [
      { label: 'Agentegra UI', url: 'https://api.robotross.art' },
      { label: 'Shopify Admin', url: 'https://robotross.art/admin' },
      { label: 'Virtuals Profile', url: 'https://app.virtuals.io/acp/agents/auj2pb60mizox9of81hcmyhm' }
    ]
  },
  {
    name: 'Robot Ross Artist',
    role: 'Mac Mini + Huenit robot arm',
    status: 'Haiku on Mac Mini • Ollama Apertus for Robot Ross',
    tools: ['Robot control UI', 'Audio & video capture'],
    location: 'Local studio',
    memoryLink: '../docs/agent-artist.md',
    uiLinks: [
      { label: 'Robot control', url: 'http://macmini.local/robotross' },
      { label: 'Scoreboard', url: 'https://api.robotross.art/scoreboard' }
    ]
  },
  {
    name: 'Clau (Claude Code)',
    role: 'Music & story video tools',
    status: 'Claude Code cloud runner',
    tools: ['Music tool (localhost:3001)', 'Story tool (localhost:3002)'],
    location: 'Cloud / local Mac',
    memoryLink: '../docs/agent-clau.md',
    uiLinks: [
      { label: 'Music video tool', url: 'http://localhost:3001/music' },
      { label: 'Story video tool', url: 'http://localhost:3002/story' }
    ]
  },
  {
    name: 'Gem (Gemini CLI)',
    role: 'Automation & infrastructure scripts',
    status: 'Gemini CLI subscription • laptop',
    tools: ['Automation CLI', 'Testing harness'],
    location: 'Cloud & local',
    memoryLink: '../docs/agent-gem.md',
    uiLinks: [
      { label: 'Gemini prompts log', url: '../docs/project-rules.md' }
    ]
  },
  {
    name: 'Codi (Codex)',
    role: 'QA scripting & API prototyping',
    status: 'Codex cloud runner',
    tools: ['API prototypes', 'CI helpers'],
    location: 'Cloud',
    memoryLink: '../docs/agent-codi.md',
    uiLinks: [
      { label: 'Codex notes', url: '../docs/project-goals.md' }
    ]
  }
];

const projects = [
  {
    title: 'Music video generation tool',
    owners: 'Clau (Claude Code)',
    status: 'Local UI • prepping cloud port',
    docs: ['../docs/project-music-video.md'],
    uiLinks: [{ label: 'Local UI', url: 'http://localhost:3001/music' }],
    kanban: 'https://trello.com/b/robotross-music'
  },
  {
    title: 'Story video generation tool',
    owners: 'Clau (Claude Code)',
    status: 'Narrative tuning',
    docs: ['../docs/project-story-video.md'],
    uiLinks: [{ label: 'Local UI', url: 'http://localhost:3002/story' }],
    kanban: 'https://trello.com/b/robotross-story'
  },
  {
    title: 'Robot Ross artist end',
    owners: 'Robot Ross Artist',
    status: 'Hardware + control stable',
    docs: ['../docs/project-robot-artist.md'],
    uiLinks: [
      { label: 'Robot control', url: 'http://macmini.local/robotross' },
      { label: 'Scoreboard', url: 'https://api.robotross.art/scoreboard' }
    ],
    kanban: 'https://trello.com/b/robotross-artist'
  },
  {
    title: 'Robot Ross salesman end',
    owners: 'robotrosssalesman',
    status: 'Salesman API online • monitoring Moltbook',
    docs: ['../docs/project-robot-sales.md'],
    uiLinks: [
      { label: 'Shopify dashboard', url: 'https://robotross.art/admin' },
      { label: 'Virtuals queue', url: 'https://app.virtuals.io/acp/jobs' }
    ],
    kanban: 'https://trello.com/b/robotross-sales'
  },
  {
    title: 'Agentegra pitch',
    owners: 'Salesman + design',
    status: 'Pitch deck framework',
    docs: ['../docs/project-agentegra.md'],
    uiLinks: [
      { label: 'Agentegra landing', url: 'https://api.robotross.art' }
    ],
    kanban: 'https://trello.com/b/agentegra'
  }
];

const docs = [
  {
    title: 'Salesman memory',
    description: 'Commerce flows, Shopify & Virtuals hooks, onboarding notes.',
    path: '../docs/agent-salesman.md',
    tags: ['memory', 'commerce']
  },
  {
    title: 'Artist memory',
    description: 'Haiku + robot arm setup, Apertus prompts.',
    path: '../docs/agent-artist.md',
    tags: ['memory', 'hardware']
  },
  {
    title: 'Clau memory',
    description: 'Video tool heuristics, music scaffolds.',
    path: '../docs/agent-clau.md',
    tags: ['memory', 'video']
  },
  {
    title: 'Gem memory',
    description: 'Automation shortcuts & CLI toolkits.',
    path: '../docs/agent-gem.md',
    tags: ['memory', 'automation']
  },
  {
    title: 'Codi memory',
    description: 'CI helpers, API experiments.',
    path: '../docs/agent-codi.md',
    tags: ['memory', 'code']
  },
  {
    title: 'Project goals & rules',
    description: 'Shared goals, docs-first workflow, guardrails.',
    path: '../docs/project-goals.md',
    tags: ['goals', 'rules']
  },
  {
    title: 'Project rules + Kanban map',
    description: 'Kanban board links and shared agreements.',
    path: '../docs/project-rules.md',
    tags: ['rules', 'process']
  },
  {
    title: 'Music video docs',
    description: 'Architecture and prompts.',
    path: '../docs/project-music-video.md',
    tags: ['project', 'video']
  },
  {
    title: 'Story video docs',
    description: 'Narrative pipeline notes.',
    path: '../docs/project-story-video.md',
    tags: ['project', 'video']
  },
  {
    title: 'Artist docs',
    description: 'Robot control, capture, safety.',
    path: '../docs/project-robot-artist.md',
    tags: ['project', 'hardware']
  },
  {
    title: 'Salesman docs',
    description: 'Shopify flow, Virtuals queue, Salesman API blueprint.',
    path: '../docs/project-robot-sales.md',
    tags: ['project', 'commerce']
  },
  {
    title: 'Agentegra pitch',
    description: 'Pitch strategy + assets.',
    path: '../docs/project-agentegra.md',
    tags: ['project', 'sales']
  },
  {
    title: 'Standup archive',
    description: 'Daily standup files stored under docs/standups/',
    path: '../docs/standups.md',
    tags: ['standup']
  }
];

let standupEntries = [
  {
    when: '2026-03-09 16:20 UTC',
    yesterday: 'Posted the Moltbook market-research question and triggered the postcards.',
    today: 'Watching responses, prepping Kanban updates, logging Virtuals queue.',
    blockers: 'Need a confirmed order before adding new Shopify product.'
  },
  {
    when: '2026-03-09 12:40 UTC',
    yesterday: 'Synced Shopify + Virtuals proofs through the Salesman API.',
    today: 'Documented the onboarding flow for claws using Virtuals and Shopify.',
    blockers: 'Waiting on the postcard media approval from the studio.'
  }
];

function activateSection(targetId) {
  if (!MAIN_SECTION_BUTTONS.length || !MAIN_SECTIONS.length) return;
  MAIN_SECTION_BUTTONS.forEach((button) => {
    const isTarget = button.dataset.sectionButton === targetId;
    button.classList.toggle('is-active', isTarget);
  });
  MAIN_SECTIONS.forEach((section) => {
    section.classList.toggle('is-active', section.id === targetId);
  });
}

function targetStatsGroup(name) {
  STATS_GROUP_BUTTONS.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.statsGroup === name);
  });
  STATS_PANELS.forEach((panel) => {
    panel.classList.toggle('is-active', panel.dataset.statsPanel === name);
  });
}

function targetMusicPanel(name) {
  MUSIC_TAB_BUTTONS.forEach((tab) => {
    tab.classList.toggle('is-active', tab.dataset.musicTab === name);
  });
  MUSIC_PANELS.forEach((panel) => {
    panel.classList.toggle('is-active', panel.dataset.musicPanel === name);
  });
}

function wireNavControls() {
  MAIN_SECTION_BUTTONS = Array.from(document.querySelectorAll('[data-section-button]'));
  MAIN_SECTIONS = Array.from(document.querySelectorAll('.section'));
  STATS_GROUP_BUTTONS = Array.from(document.querySelectorAll('[data-stats-group]'));
  STATS_PANELS = Array.from(document.querySelectorAll('[data-stats-panel]'));
  MUSIC_TAB_BUTTONS = Array.from(document.querySelectorAll('[data-music-tab]'));
  MUSIC_PANELS = Array.from(document.querySelectorAll('[data-music-panel]'));
  SORTABLE_HEADERS = Array.from(document.querySelectorAll('th[data-sortable]'));
  MAIN_SECTION_BUTTONS.forEach((button) => {
    button.addEventListener('click', () => activateSection(button.dataset.sectionButton));
  });
  STATS_GROUP_BUTTONS.forEach((button) => {
    button.addEventListener('click', () => targetStatsGroup(button.dataset.statsGroup));
  });
  MUSIC_TAB_BUTTONS.forEach((tab) => {
    tab.addEventListener('click', () => targetMusicPanel(tab.dataset.musicTab));
  });
  SORTABLE_HEADERS.forEach((header) => {
    header.addEventListener('click', () => {
      const field = header.dataset.sortable;
      if (musicSortState.field === field) {
        musicSortState.order = musicSortState.order === 'asc' ? 'desc' : 'asc';
      } else {
        musicSortState.field = field;
        musicSortState.order = field === 'title' ? 'asc' : 'desc';
      }
      SORTABLE_HEADERS.forEach((h) => h.classList.remove('sorted-asc', 'sorted-desc'));
      header.classList.add(musicSortState.order === 'asc' ? 'sorted-asc' : 'sorted-desc');
      renderShorts(musicShortsCache);
    });
  });
  targetStatsGroup('robotross');
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, { cache: 'no-store', credentials: 'include', ...options });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function setStatusMessage(message) {
  const text = document.getElementById('tracker-status-text');
  if (text) text.textContent = message;
}

function toChartSeries(raw) {
  if (!raw) return { labels: [], values: [] };
  if (Array.isArray(raw)) {
    return { labels: raw.map((item) => item.label || item.piece || item.name || 'Untitled'), values: raw.map((item) => Number(item.value ?? item.views ?? item.yt ?? 0)) };
  }
  if (typeof raw === 'object') {
    const entries = Object.entries(raw);
    return { labels: entries.map(([key]) => key), values: entries.map(([, value]) => Number(value || 0)) };
  }
  return { labels: [], values: [] };
}

function updateStatusIndicator(online) {
  const dot = document.getElementById('tracker-status-dot');
  const text = document.getElementById('tracker-status-text');
  if (online) {
    if (dot) dot.classList.remove('offline');
    if (text) text.textContent = 'Tracker live';
  } else {
    if (dot) dot.classList.add('offline');
    if (text) text.textContent = 'Tracker offline';
  }
  statusResolved = true;
}

async function loadStatus() {
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), 4000) : null;
  const fallback = setTimeout(() => {
    if (!statusResolved) {
      updateStatusIndicator(false);
      setStatusMessage('Tracker offline (timeout)');
    }
  }, 7500);
  try {
    const data = await fetchJson('/tracker/health', controller ? { signal: controller.signal } : undefined);
    updateStatusIndicator(Boolean(data?.sheets_online));
  } catch (err) {
    if (err.name === 'AbortError') {
      console.warn('Tracker health check timed out');
      setStatusMessage('Tracker offline (timeout)');
    } else {
      console.error('Health check failed', err);
      setStatusMessage('Tracker offline (error)');
    }
    updateStatusIndicator(false);
  } finally {
    if (timer) clearTimeout(timer);
    clearTimeout(fallback);
  }
}


function fillSummaryCards(data) {
  const mapping = {
    shorts: data?.Shorts ?? 0,
    videos: data?.Videos ?? 0,
    generated: data?.['Video Tracker'] ?? 0,
    uploaded: data?.['Upload Tracker'] ?? 0
  };
  Object.entries(mapping).forEach(([key, value]) => {
    const el = document.getElementById(`summary-${key}`);
    if (el) el.textContent = Number(value).toLocaleString();
  });
  const pendingValue = Number(data?.pending_sync || 0);
  const pendingEl = document.getElementById('pending-sync');
  if (pendingEl) pendingEl.textContent = pendingValue;
  const pendingCard = document.getElementById('pending-sync-card');
  if (pendingCard) {
    pendingCard.style.opacity = pendingValue > 0 ? '1' : '0.35';
    pendingCard.style.pointerEvents = pendingValue > 0 ? 'auto' : 'none';
  }
}

async function loadSummary() {
  try {
    const data = await fetchJson('/tracker/summary');
    fillSummaryCards(data.sheets);
  } catch (err) {
    console.error('Summary fetch failed', err);
  }
}

function formatShortDate(row) {
  if (row.date) return row.date;
  if (row.day) return row.day;
  return '—';
}

function sortShorts(items) {
  const { field, order } = musicSortState;
  const multiplier = order === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    if (field === 'title') {
      return multiplier * String(a.title || a.song || '').localeCompare(String(b.title || b.song || ''));
    }
    if (field === 'date') {
      const da = a.date ? new Date(a.date) : new Date(0);
      const db = b.date ? new Date(b.date) : new Date(0);
      return multiplier * (da - db);
    }
    const va = Number(a[field] || 0);
    const vb = Number(b[field] || 0);
    return multiplier * (va - vb);
  });
}

function renderShorts(items) {
  const body = document.getElementById('shorts-table');
  body.innerHTML = '';
  const filtered = (items || [])
    .filter((item) => !(item.theme || '').toLowerCase().includes('chapter'))
    .slice(0, 200);
  const sorted = sortShorts(filtered);
  if (!sorted.length) {
    body.innerHTML = '<tr><td colspan="5">No shorts yet.</td></tr>';
    return;
  }
  sorted.forEach((short) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${short.title || short.song || 'Untitled'}</td>
      <td>${formatShortDate(short)}</td>
      <td>${Number(short.yt_views || 0).toLocaleString()}</td>
      <td>${Number(short.tt_views || 0).toLocaleString()}</td>
      <td>${Number(short.insta_views || 0).toLocaleString()}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadShorts() {
  try {
    const data = await fetchJson('/tracker/shorts?limit=500');
    musicShortsCache = data.items || [];
    renderShorts(musicShortsCache);
  } catch (err) {
    console.error('Shorts fetch failed', err);
    document.getElementById('shorts-table').innerHTML = '<tr><td colspan="5">Unable to load shorts.</td></tr>';
  }
}

function renderVideos(items) {
  const body = document.getElementById('videos-table');
  body.innerHTML = '';
  const sorted = (items || []).sort((a, b) => (b.yt_views || 0) - (a.yt_views || 0));
  if (!sorted.length) {
    body.innerHTML = '<tr><td colspan="4">No long-form entries.</td></tr>';
    return;
  }
  sorted.forEach((video) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${video.title || video.song || 'Untitled'}</td>
      <td>${video.style || '—'}</td>
      <td>${video.date || '—'}</td>
      <td>${Number(video.yt_views || 0).toLocaleString()}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadVideos() {
  try {
    const data = await fetchJson('/tracker/videos?limit=200');
    renderVideos(data.items);
  } catch (err) {
    console.error('Videos fetch failed', err);
    document.getElementById('videos-table').innerHTML = '<tr><td colspan="4">Unable to load videos.</td></tr>';
  }
}

function renderStory(items) {
  const body = document.getElementById('story-table');
  body.innerHTML = '';
  const sorted = (items || []).sort((a, b) => (a.chapter || 0) - (b.chapter || 0));
  if (!sorted.length) {
    body.innerHTML = '<tr><td colspan="7">No story chapters yet.</td></tr>';
    return;
  }
  const maxViews = Math.max(...sorted.map((row) => Math.max(row.yt_views || 0, row.tt_views || 0)));
  sorted.forEach((row) => {
    const yt = Number(row.yt_views || 0);
    const tt = Number(row.tt_views || 0);
    const insta = Number(row.insta_views || 0);
    const ytPct = maxViews ? Math.min(100, (yt / maxViews) * 100) : 0;
    const ttPct = maxViews ? Math.min(100, (tt / maxViews) * 100) : 0;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row.chapter ?? '—'}</td>
      <td>${row.title || 'Untitled'}</td>
      <td>${row.date || '—'}</td>
      <td>${yt.toLocaleString()}</td>
      <td>${tt.toLocaleString()}</td>
      <td>${insta.toLocaleString()}</td>
      <td>
        <div class="story-bars">
          <div class="story-bar">
            <span class="bar-tt" style="width:${ttPct}%;"></span>
            <span class="bar-yt" style="width:${ytPct}%;"></span>
          </div>
          <div class="story-bar-labels">
            <span>YT ${yt.toLocaleString()}</span>
            <span>TT ${tt.toLocaleString()}</span>
          </div>
        </div>
      </td>
    `;
    body.appendChild(tr);
  });
}

async function loadStory() {
  try {
    const data = await fetchJson('/tracker/story');
    renderStory(data.items);
  } catch (err) {
    console.error('Story fetch failed', err);
    document.getElementById('story-table').innerHTML = '<tr><td colspan="7">Unable to load story data.</td></tr>';
  }
}

function summaryText(value) {
  return value ? Number(value).toLocaleString() : '0';
}

function populateRobotRossOrders(orders) {
  const table = document.getElementById('rr-orders-table');
  table.innerHTML = '';
  const slice = (orders || []).slice(0, 6);
  if (!slice.length) {
    table.innerHTML = '<tr><td colspan="5">No orders yet.</td></tr>';
    return;
  }
  slice.forEach((order) => {
    const slot = order.payload?.slot || '—';
    const buyer = order.payload?.buyer || 'Bot';
    const status = (order.status || 'unknown').replace('_', ' ');
    const price = Number(order.payload?.bid_amount || order.payload?.price || 0).toFixed(2);
    const proof = order.payload?.proofOfWorkUrl
      ? `<a href="${order.payload.proofOfWorkUrl}" target="_blank" rel="noreferrer">link</a>`
      : '—';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${slot}</td>
      <td>${buyer}</td>
      <td>${status}</td>
      <td>${price}</td>
      <td>${proof}</td>
    `;
    table.appendChild(tr);
  });
}

function updateRobotRossSummary(orders, grid) {
  const total = (orders || []).length;
  const complete = (orders || []).filter((order) => order.status === 'complete').length;
  const active = (orders || []).filter((order) => ['new', 'claimed', 'in_progress'].includes(order.status)).length;
  const occupied = (grid?.slots || []).filter((slot) => slot.status === 'occupied').length;
  document.getElementById('rr-total-orders').textContent = summaryText(total);
  document.getElementById('rr-complete').textContent = summaryText(complete);
  document.getElementById('rr-active').textContent = summaryText(active);
  document.getElementById('rr-grid').textContent = `${occupied} / 64`;
}

async function loadRobotRossData() {
  try {
    const [ordersData, gridData] = await Promise.all([
      fetchJson('/salesman/orders/all'),
      fetchJson('/salesman/grid')
    ]);
    const orders = ordersData.orders || [];
    const grid = gridData;
    updateRobotRossSummary(orders, grid);
    populateRobotRossOrders(orders);
  } catch (err) {
    console.error('Robot Ross fetch failed', err);
  }
}

function populateTeam() {
  const container = document.getElementById('team-grid');
  container.innerHTML = teamMembers
    .map((member) => {
      const toolList = member.tools.map((tool) => `<li>${tool}</li>`).join('');
      const uiLinks = member.uiLinks
        .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${link.label}</a>`)
        .join(' ');
      return `
        <article class="agent-card">
          <div>
            <h3>${member.name}</h3>
            <p class="muted">${member.role}</p>
          </div>
          <span class="badge">${member.status}</span>
          <ul>${toolList}</ul>
          <div class="project-links">
            ${uiLinks}
            <a href="${member.memoryLink}" target="_blank" rel="noreferrer">Memory file</a>
          </div>
        </article>
      `;
    })
    .join('');
}

function populateProjects() {
  const container = document.getElementById('projects-grid');
  container.innerHTML = projects
    .map((project) => {
      const docsLinks = project.docs
        .map((docPath) => `<a href="${docPath}" target="_blank" rel="noreferrer">Open doc</a>`)
        .join(' ');
      const uiLinks = project.uiLinks
        .map((link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${link.label}</a>`)
        .join(' ');
      return `
        <article class="project-card">
          <div>
            <h3>${project.title}</h3>
            <p class="muted">Owners: ${project.owners}</p>
          </div>
          <span class="badge">${project.status}</span>
          <div class="project-links">
            ${docsLinks}
            ${uiLinks}
            <a href="${project.kanban}" target="_blank" rel="noreferrer">Kanban board</a>
          </div>
        </article>
      `;
    })
    .join('');
}

function renderDocs(list) {
  const container = document.getElementById('docs-grid');
  if (!list.length) {
    container.innerHTML = '<p class="muted">No documents found.</p>';
    return;
  }
  container.innerHTML = list
    .map((doc) => `
      <article class="doc-card">
        <div>
          <h3>${doc.title}</h3>
          <p>${doc.description}</p>
        </div>
        <div class="tag-list">
          ${doc.tags.map((tag) => `<span class="tag">${tag}</span>`).join('')}
        </div>
        <a href="${doc.path}" target="_blank" rel="noreferrer">Open file →</a>
      </article>
    `)
    .join('');
}

function setupDocSearch() {
  const input = document.getElementById('docs-search');
  input.addEventListener('input', () => {
    const query = input.value.toLowerCase().trim();
    if (!query) {
      renderDocs(docs);
      return;
    }
    const filtered = docs.filter(
      (doc) =>
        doc.title.toLowerCase().includes(query) ||
        doc.description.toLowerCase().includes(query) ||
        doc.tags.some((tag) => tag.toLowerCase().includes(query))
    );
    renderDocs(filtered);
  });
}

function renderStandups() {
  const container = document.getElementById('standup-list');
  container.innerHTML = standupEntries
    .map(
      (entry) => `
        <article class="standup-entry">
          <header>
            <span>${entry.when}</span>
            <span>${entry.blockers ? 'Blockers noted' : 'No blockers'}</span>
          </header>
          <ul>
            <li><strong>Yesterday:</strong> ${entry.yesterday}</li>
            <li><strong>Today:</strong> ${entry.today}</li>
            ${entry.blockers ? `<li><strong>Blockers:</strong> ${entry.blockers}</li>` : ''}
          </ul>
        </article>
      `
    )
    .join('');
}

function setupStandupForm() {
  const form = document.getElementById('standup-form');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const entry = {
      when: new Date().toISOString().replace('T', ' ').replace('Z', ' UTC'),
      yesterday: data.get('yesterday').trim(),
      today: data.get('today').trim(),
      blockers: data.get('blockers').trim()
    };
    standupEntries.unshift(entry);
    renderStandups();
    form.reset();
  });
}
function renderDailyMarkdown(raw) {
  if (!raw) return '<p class="muted">No entries yet.</p>';
  const lines = raw.split(/\r?\n/);
  const sections = [];
  let current = null;
  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    if (trimmed.startsWith('## ')) {
      if (current) sections.push(current);
      current = { title: trimmed.slice(3).trim(), entries: [] };
    } else if (current) {
      current.entries.push(trimmed.replace(/^-\s?/, ''));
    }
  });
  if (current) sections.push(current);
  if (!sections.length) return '<p class="muted">No daily sections yet.</p>';
  return sections
    .map((section) => {
      const grouped = {};
      section.entries.forEach((line) => {
        const splitIndex = line.indexOf(':');
        const label = splitIndex !== -1 ? line.slice(0, splitIndex).trim() : 'Notes';
        const value = splitIndex !== -1 ? line.slice(splitIndex + 1).trim() : line.trim();
        if (!grouped[label]) grouped[label] = [];
        grouped[label].push(value || '•');
      });
      const details = Object.entries(grouped)
        .map(([label, values]) => `
          <p class="muted">${label}</p>
          <ul>${values.map((v) => `<li>${v}</li>`).join('')}</ul>`
        )
        .join('');
      return `<div class="daily-section"><h4>${section.title}</h4>${details}</div>`;
    })
    .join('');
}

function renderDailyButtons() {
  const container = document.getElementById('daily-buttons');
  if (!container) return;
  container.innerHTML = '';
  if (!dailyStandupsIndex.length) {
    document.getElementById('daily-view').innerHTML = '<p class="muted">No daily files yet.</p>';
    return;
  }
  dailyStandupsIndex.forEach((day) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'daily-button';
    btn.textContent = day.label || day.date;
    btn.dataset.date = day.date;
    if (day.date === activeDailyDate) btn.classList.add('is-active');
    btn.addEventListener('click', () => selectDaily(day));
    container.appendChild(btn);
  });
}

async function selectDaily(day) {
  activeDailyDate = day.date;
  renderDailyButtons();
  const view = document.getElementById('daily-view');
  if (!view) return;
  view.innerHTML = '<p class="muted">Loading…</p>';
  try {
    const raw = await fetchText(day.path);
    view.innerHTML = renderDailyMarkdown(raw);
  } catch (err) {
    console.error('Daily standup load failed', err);
    view.innerHTML = '<p class="muted">Unable to load this day.</p>';
  }
}

async function loadDailyStandups() {
  try {
    const data = await fetchJson('/docs/standups/index.json');
    dailyStandupsIndex = (data?.files || []).slice().sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    if (dailyStandupsIndex.length) {
      activeDailyDate = dailyStandupsIndex[0].date;
      renderDailyButtons();
      selectDaily(dailyStandupsIndex[0]);
    } else {
      const view = document.getElementById('daily-view');
      if (view) view.innerHTML = '<p class="muted">No daily standups yet.</p>';
    }
  } catch (err) {
    console.error('Daily standup index failed', err);
    const view = document.getElementById('daily-view');
    if (view) view.innerHTML = '<p class="muted">Unable to load daily standups.</p>';
  }
}

function normalizeCrossPlatform(data) {
  if (Array.isArray(data)) return data;
  if (!data || typeof data !== 'object') return [];
  return Object.entries(data).map(([piece, row]) => ({ piece, ...row }));
}


function renderHeatmap(id, pieces, styles, heatmap) {
  const el = document.getElementById(id);
  if (!el || !window.Plotly) return;
  const z = pieces.map((piece) =>
    styles.map((style) => {
      const value = heatmap?.[`${piece}|${style}`];
      return value ?? null;
    })
  );
  const text = pieces.map((piece) =>
    styles.map((style) => {
      const value = heatmap?.[`${piece}|${style}`];
      if (value === undefined || value === null) return '—';
      const formatted = Number(value).toLocaleString();
      return formatted;
    })
  );
  Plotly.newPlot(
    el,
    [
      {
        type: 'heatmap',
        z,
        x: styles,
        y: pieces,
        colorscale: 'RdBu',
        reversescale: true,
        zmid: 0,
        text,
        texttemplate: '%{text}',
        hoverongaps: false
      }
    ],
    {
      margin: { l: 160, t: 30 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    },
    { responsive: true }
  );
}


function renderBarPlot(elementId, labels, values) {
  const el = document.getElementById(elementId);
  if (!el || !window.Plotly) return;
  Plotly.newPlot(
    el,
    [
      {
        x: labels,
        y: values,
        type: 'bar',
        marker: { color: 'rgba(72, 199, 255, 0.8)' }
      }
    ],
    {
      margin: { t: 24, b: 40 },
      xaxis: { tickangle: -40, automargin: true },
      yaxis: { title: 'YT views' },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    },
    { responsive: true }
  );
}

function renderCrossPlatform(elementId, data) {
  const el = document.getElementById(elementId);
  if (!el || !window.Plotly) return;
  const normalized = normalizeCrossPlatform(data);
  if (!normalized.length) {
    el.innerHTML = '<p class="muted">No cross-platform data.</p>';
    return;
  }
  const labels = normalized.map((item) => item.piece || item.title || 'Untitled');
  const yt = normalized.map((item) => Number(item.yt_views ?? item.yt ?? 0));
  const tt = normalized.map((item) => Number(item.tt_views ?? item.tt ?? 0));
  const insta = normalized.map((item) => Number(item.yt_views ?? item.ig ?? item.insta ?? 0));
  Plotly.newPlot(
    el,
    [
      { x: labels, y: yt, name: 'YouTube', type: 'bar', marker: { color: 'rgba(72, 199, 255, 0.8)' } },
      { x: labels, y: tt, name: 'TikTok', type: 'bar', marker: { color: 'rgba(255, 155, 92, 0.85)' } },
      { x: labels, y: insta, name: 'Instagram', type: 'bar', marker: { color: 'rgba(150, 113, 255, 0.8)' } }
    ],
    {
      barmode: 'group',
      margin: { t: 30, b: 70 },
      yaxis: { title: 'Avg views' },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)'
    },
    { responsive: true }
  );
}

function renderLeaderboardTable(elementId, items, labelField, valueField) {
  const container = document.getElementById(elementId);
  if (!container) return;
  if (!Array.isArray(items) || !items.length) {
    container.innerHTML = '<p class="muted">No data.</p>';
    return;
  }
  const rows = items
    .map((item, idx) => {
      const base = item[labelField] || item.piece || item.title || item.song || `#${idx + 1}`;
      const style = item.style ? ` (${item.style})` : '';
      const label = `${base}${style}`;
      const value = Number(item[valueField] ?? item.views ?? item.value ?? 0).toLocaleString();
      return `<tr><td>${idx + 1}. ${label}</td><td>${value}</td></tr>`;
    })
    .join('');
  container.innerHTML = `<table><thead><tr><th>Item</th><th>Views</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderRecommendations(elementId, data) {
  const container = document.getElementById(elementId);
  if (!container) return;
  if (!Array.isArray(data) || !data.length) {
    container.innerHTML = '<p class="muted">No recommendations yet.</p>';
    return;
  }
  const rows = data
    .map((item) => {
      const piece = item.piece || item.title || 'Unknown';
      const style = item.style || item.theme || '—';
      const predicted = Number(item.predicted_avg ?? item.predicted_views ?? item.value ?? 0).toLocaleString();
      return `<tr><td>${piece}</td><td>${style}</td><td>${predicted}</td></tr>`;
    })
    .join('');
  container.innerHTML = `<table><thead><tr><th>Piece</th><th>Style</th><th>Predicted</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderVideoStats(elementId, avg, top) {
  const container = document.getElementById(elementId);
  if (!container) return;
  const avgText = avg ? Number(avg).toLocaleString() : '—';
  let html = `<p class="muted">Average YT views: ${avgText}</p>`;
  if (Array.isArray(top) && top.length) {
    const rows = top
      .map((video, idx) => {
        const title = video.piece || video.title || video.song || `Video ${idx + 1}`;
        const style = video.style ? ` (${video.style})` : '';
        const views = Number(video.yt_views ?? video.views ?? 0).toLocaleString();
        return `<tr><td>${idx + 1}. ${title}${style}</td><td>${views}</td></tr>`;
      })
      .join('');
    html += `<table><thead><tr><th>Video</th><th>YT views</th></tr></thead><tbody>${rows}</tbody></table>`;
  }
  container.innerHTML = html;
}

async function loadAnalytics() {
  try {
    const data = await fetchJson('/tracker/analytics');
    const styleSeries = toChartSeries(data.style_avg_yt ?? (data.style_avg || data.style_avg_youtube));
    const pieceSeries = toChartSeries(data.piece_avg_yt ?? (data.piece_avg || data.piece_avg_youtube));
    renderBarPlot('chart-style-average', styleSeries.labels, styleSeries.values);
    renderBarPlot('chart-piece-average', pieceSeries.labels, pieceSeries.values);
    const pieces = data.heatmap_pieces || data.heatmapRows || []; 
    const styles = data.heatmap_styles || data.heatmapCols || [];
    renderHeatmap('chart-heatmap', pieces, styles, data.heatmap);
    renderCrossPlatform('chart-cross-platform', data.cross_platform);
    renderLeaderboardTable('table-top-yt', data.top_yt_shorts, 'piece', 'yt');
    renderLeaderboardTable('table-top-tt', data.top_tt_shorts, 'piece', 'tt');
    renderRecommendations('table-recommendations', data.recommendations);
    renderVideoStats('table-top-videos', data.video_avg_yt ?? data.longform_avg, data.top_videos ?? data.long_form);
  } catch (err) {
    console.error('Analytics load failed', err);
    document.querySelectorAll('.chart-card').forEach((card) => {
      const el = card.querySelector('.chart-canvas, .leaderboard-table');
      if (el) {
        el.innerHTML = '<p class="muted">Unable to load analytics data.</p>';
      }
    });
  }
}


document.addEventListener('DOMContentLoaded', () => {
  wireNavControls();
  loadStatus();
  loadSummary();
  loadShorts();
  loadVideos();
  loadStory();
  loadRobotRossData();
  populateTeam();
  loadAnalytics();
  populateProjects();
  renderDocs(docs);
  setupDocSearch();
  renderStandups();
  setupStandupForm();
  loadDailyStandups();
});
