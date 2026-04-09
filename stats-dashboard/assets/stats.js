
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

let STATS_GROUP_BUTTONS = [];
let STATS_PANELS = [];
let MUSIC_TAB_BUTTONS = [];
let MUSIC_PANELS = [];
let SORTABLE_HEADERS = [];
let musicShortsCache = [];
const musicSortState = { field: 'yt_views', order: 'desc' };
let statusResolved = false;

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
  try {
    const data = await fetchJson('/tracker/health');
    updateStatusIndicator(Boolean(data?.sheets_online));
  } catch (err) {
    updateStatusIndicator(false);
  }
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

function renderBarPlot(elementId, labels, values) {
  const el = document.getElementById(elementId);
  if (!el || !window.Plotly) return;
  Plotly.newPlot(el, [{ x: labels, y: values, type: 'bar', marker: { color: 'rgba(72, 199, 255, 0.8)' } }], { margin: { t: 24, b: 40 }, xaxis: { tickangle: -40, automargin: true }, yaxis: { title: 'YT views' }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }, { responsive: true });
}

function renderHeatmap(id, pieces, styles, heatmap) {
  const el = document.getElementById(id);
  if (!el || !window.Plotly) return;
  const z = pieces.map((piece) => styles.map((style) => heatmap?.[`${piece}|${style}`] ?? null));
  const text = pieces.map((piece) => styles.map((style) => (heatmap?.[`${piece}|${style}`] ?? '—').toLocaleString()));
  Plotly.newPlot(el, [{ type: 'heatmap', z, x: styles, y: pieces, colorscale: 'RdBu', reversescale: true, zmid: 0, text, texttemplate: '%{text}', hoverongaps: false }], { margin: { l: 160, t: 30 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }, { responsive: true });
}

function renderCrossPlatform(elementId, data) {
  const el = document.getElementById(elementId);
  if (!el || !window.Plotly) return;
  const normalized = Array.isArray(data) ? data : Object.entries(data || {}).map(([piece, row]) => ({ piece, ...row }));
  const labels = normalized.map((item) => item.piece || item.title || 'Untitled');
  Plotly.newPlot(el, [
    { x: labels, y: normalized.map((i) => Number(i.yt_views ?? i.yt ?? 0)), name: 'YouTube', type: 'bar', marker: { color: 'rgba(72, 199, 255, 0.8)' } },
    { x: labels, y: normalized.map((i) => Number(i.tt_views ?? i.tt ?? 0)), name: 'TikTok', type: 'bar', marker: { color: 'rgba(255, 155, 92, 0.85)' } },
    { x: labels, y: normalized.map((i) => Number(i.insta_views ?? i.ig ?? 0)), name: 'Instagram', type: 'bar', marker: { color: 'rgba(150, 113, 255, 0.8)' } }
  ], { barmode: 'group', margin: { t: 30, b: 70 }, yaxis: { title: 'Avg views' }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }, { responsive: true });
}

function renderLeaderboardTable(elementId, items, labelField, valueField) {
  const container = document.getElementById(elementId);
  if (!container) return;
  const rows = (items || []).map((item, idx) => `<tr><td>${idx + 1}. ${item[labelField] || 'Item'}</td><td>${Number(item[valueField] || 0).toLocaleString()}</td></tr>`).join('');
  container.innerHTML = `<table><thead><tr><th>Item</th><th>Views</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderRecommendations(elementId, data) {
  const container = document.getElementById(elementId);
  if (!container) return;
  const rows = (data || []).map((item) => `<tr><td>${item.piece || '—'}</td><td>${item.style || '—'}</td><td>${Number(item.predicted_avg || 0).toLocaleString()}</td></tr>`).join('');
  container.innerHTML = `<table><thead><tr><th>Piece</th><th>Style</th><th>Predicted</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function loadAnalytics() {
  try {
    const data = await fetchJson('/tracker/analytics');
    const styleSeries = toChartSeries(data.style_avg_yt);
    const pieceSeries = toChartSeries(data.piece_avg_yt);
    renderBarPlot('chart-style-average', styleSeries.labels, styleSeries.values);
    renderBarPlot('chart-piece-average', pieceSeries.labels, pieceSeries.values);
    renderHeatmap('chart-heatmap', data.heatmap_pieces || [], data.heatmap_styles || [], data.heatmap);
    renderCrossPlatform('chart-cross-platform', data.cross_platform);
    renderLeaderboardTable('table-top-yt', data.top_yt_shorts, 'piece', 'yt');
    renderLeaderboardTable('table-top-tt', data.top_tt_shorts, 'piece', 'tt');
    renderRecommendations('table-recommendations', data.recommendations);
  } catch (err) { console.error(err); }
}

function renderShorts(items) {
  const body = document.getElementById('shorts-table');
  if (!body) return;
  body.innerHTML = '';
  const filtered = (items || []).filter(i => !(i.theme || '').toLowerCase().includes('chapter')).slice(0, 100);
  filtered.forEach((s) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${s.title || s.song || 'Untitled'}</td><td>${s.date || '—'}</td><td>${Number(s.yt_views || 0).toLocaleString()}</td><td>${Number(s.tt_views || 0).toLocaleString()}</td><td>${Number(s.insta_views || 0).toLocaleString()}</td>`;
    body.appendChild(tr);
  });
}

async function loadShorts() {
  try {
    const data = await fetchJson('/tracker/shorts?limit=500');
    renderShorts(data.items);
  } catch (err) { console.error(err); }
}

function renderVideos(items) {
  const body = document.getElementById('videos-table');
  if (!body) return;
  body.innerHTML = '';
  (items || []).slice(0, 100).forEach((v) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${v.title || 'Untitled'}</td><td>${v.style || '—'}</td><td>${v.date || '—'}</td><td>${Number(v.yt_views || 0).toLocaleString()}</td>`;
    body.appendChild(tr);
  });
}

async function loadVideos() {
  try {
    const data = await fetchJson('/tracker/videos?limit=200');
    renderVideos(data.items);
  } catch (err) { console.error(err); }
}

function renderStory(items) {
  const body = document.getElementById('story-table');
  if (!body) return;
  body.innerHTML = '';
  (items || []).forEach((row) => {
    const yt = Number(row.yt_views || 0);
    const tt = Number(row.tt_views || 0);
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.chapter ?? '—'}</td><td>${row.title || 'Untitled'}</td><td>${row.date || '—'}</td><td>${yt.toLocaleString()}</td><td>${tt.toLocaleString()}</td><td>${Number(row.insta_views || 0).toLocaleString()}</td><td>${tt > yt ? 'TikTok Wins' : 'YT Wins'}</td>`;
    body.appendChild(tr);
  });
}

async function loadStory() {
  try {
    const data = await fetchJson('/tracker/story');
    renderStory(data.items);
  } catch (err) { console.error(err); }
}

async function loadRobotRossData() {
  try {
    const [ordersData, gridData] = await Promise.all([
      fetchJson('/salesman/orders/all'),
      fetchJson('/salesman/grid')
    ]);
    const orders = ordersData.orders || [];
    const grid = gridData;
    document.getElementById('rr-total-orders').textContent = orders.length;
    document.getElementById('rr-complete').textContent = orders.filter(o => o.status === 'complete').length;
    document.getElementById('rr-active').textContent = orders.filter(o => ['new', 'claimed', 'in_progress'].includes(o.status)).length;
    document.getElementById('rr-grid').textContent = `${(grid.slots || []).filter(s => s.status === 'occupied').length} / 64`;
    
    const table = document.getElementById('rr-orders-table');
    table.innerHTML = orders.slice(0, 10).map(o => `<tr><td>${o.payload?.slot || '—'}</td><td>${o.payload?.buyer || '—'}</td><td>${o.status}</td><td>${Number(o.payload?.bid_amount || 0).toFixed(2)}</td><td>${o.payload?.proofOfWorkUrl ? 'Yes' : 'No'}</td></tr>`).join('');
  } catch (err) { console.error(err); }
}

function getQueryParam(name) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(name);
}

function handleProjectFilter() {
  const project = getQueryParam('project');
  if (project === 'music') {
    return 'music';
  } else if (project === 'story') {
    return 'story';
  }
  return 'robotross'; // default
}

document.addEventListener('DOMContentLoaded', () => {
  STATS_GROUP_BUTTONS = Array.from(document.querySelectorAll('[data-stats-group]'));
  STATS_PANELS = Array.from(document.querySelectorAll('[data-stats-panel]'));
  MUSIC_TAB_BUTTONS = Array.from(document.querySelectorAll('[data-music-tab]'));
  MUSIC_PANELS = Array.from(document.querySelectorAll('[data-music-panel]'));
  STATS_GROUP_BUTTONS.forEach(btn => btn.addEventListener('click', () => targetStatsGroup(btn.dataset.statsGroup)));
  MUSIC_TAB_BUTTONS.forEach(tab => tab.addEventListener('click', () => targetMusicPanel(tab.dataset.musicTab)));
  
  loadStatus();
  loadAnalytics();
  loadShorts();
  loadVideos();
  loadStory();
  loadRobotRossData();
  
  // Use project filter from URL if present, otherwise default to robotross
  const initialGroup = handleProjectFilter();
  targetStatsGroup(initialGroup);
});
