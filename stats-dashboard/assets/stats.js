
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
let musicVideosCache = [];
let storyCache = [];
const musicSortState = { field: 'yt_views', order: 'desc' };
const shortsSortState = { field: 'date', order: 'desc' };
const storySortState = { field: 'date', order: 'desc' };
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
  const filtered = (items || []).filter(i => !(i.theme || '').toLowerCase().includes('chapter'));
  const sorted = sortShorts(filtered).slice(0, 100);
  sorted.forEach((s) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${s.title || s.song || 'Untitled'}</td><td>${s.date || '—'}</td><td>${Number(s.yt_views || 0).toLocaleString()}</td><td>${Number(s.tt_views || 0).toLocaleString()}</td><td>${Number(s.insta_views || 0).toLocaleString()}</td>`;
    body.appendChild(tr);
  });
}

function sortShorts(items) {
  const { field, order } = shortsSortState;
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
    const va = Number(a[field] ?? -1);
    const vb = Number(b[field] ?? -1);
    return multiplier * (va - vb);
  });
}

async function loadShorts() {
  try {
    const data = await fetchJson('/tracker/shorts?limit=500');
    musicShortsCache = data.items || [];
    renderShorts(musicShortsCache);
  } catch (err) { console.error(err); }
}

function sortVideos(items) {
  const { field, order } = musicSortState;
  const multiplier = order === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    if (field === 'title') return multiplier * String(a.title || a.song || '').localeCompare(String(b.title || b.song || ''));
    if (field === 'style') return multiplier * String(a.style || '').localeCompare(String(b.style || ''));
    if (field === 'visibility') return multiplier * String(a.visibility || '').localeCompare(String(b.visibility || ''));
    if (field === 'traffic_light') return multiplier * String(a.traffic_light || '').localeCompare(String(b.traffic_light || ''));
    if (field === 'date') {
      const da = a.date ? new Date(a.date) : new Date(0);
      const db = b.date ? new Date(b.date) : new Date(0);
      return multiplier * (da - db);
    }
    const va = Number(a[field] ?? -1);
    const vb = Number(b[field] ?? -1);
    return multiplier * (va - vb);
  });
}

function renderRetention(value, status) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '<span class="muted">—</span>';
  }
  const pct = Number(value);
  let tone = 'neutral';
  if (pct >= 50) tone = 'good';
  if (pct < 35) tone = 'weak';
  const label = status === 'above_typical' ? 'above' : status === 'below_typical' ? 'below' : '';
  const suffix = label ? `<span class="retention-status">${label}</span>` : '';
  return `<span class="retention-pill retention-${tone}"><span>${pct.toFixed(1)}%</span>${suffix}</span>`;
}

function renderRetentionTrend(video) {
  const history = Array.isArray(video.retention_30s_history) ? video.retention_30s_history : [];
  const usable = history.filter((entry) => entry.retention_30s_pct !== null && entry.retention_30s_pct !== undefined);
  if (usable.length < 2) return '';
  const previous = Number(usable[usable.length - 2].retention_30s_pct);
  const current = Number(usable[usable.length - 1].retention_30s_pct);
  if (Number.isNaN(previous) || Number.isNaN(current)) return '';
  const delta = current - previous;
  if (Math.abs(delta) < 0.05) return '<span class="retention-trend">flat</span>';
  const sign = delta > 0 ? '+' : '';
  const direction = delta > 0 ? 'up' : 'down';
  return `<span class="retention-trend retention-trend-${direction}">${sign}${delta.toFixed(1)} pts</span>`;
}

function renderPercent(value, weakBelow = null) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '<span class="muted">—</span>';
  }
  const pct = Number(value);
  const weak = weakBelow !== null && pct < weakBelow ? ' metric-weak' : '';
  return `<span class="metric-value${weak}">${pct.toFixed(1)}%</span>`;
}

function renderNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '<span class="muted">—</span>';
  }
  return `<span class="metric-value">${Number(value).toFixed(digits)}</span>`;
}

function renderCompactNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '<span class="muted">—</span>';
  }
  return `<span class="metric-value">${Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })}</span>`;
}

function renderEfficiency(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '<span class="muted">—</span>';
  }
  return `<span class="metric-value">${Number(value).toFixed(4)}</span>`;
}

function renderVisibility(value) {
  const label = value || 'Unknown';
  const code = label.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return `<span class="visibility-pill visibility-${code}">${label}</span>`;
}

function renderTrafficLight(label, code) {
  const normalized = code || String(label || 'unknown').toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return `<span class="traffic-pill traffic-${normalized}">${label || 'Unknown'}</span>`;
}

function renderCategory(value, label) {
  const code = String(value || 'RT').toUpperCase();
  const normalized = code.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  return `<span class="category-pill category-${normalized}" title="${label || code}">${code}</span>`;
}

function renderFormat(value) {
  const label = value === 'short' ? 'Short' : value === 'long' ? 'Long' : '—';
  const code = String(value || 'unknown').toLowerCase();
  return `<span class="format-pill format-${code}">${label}</span>`;
}

function renderVideoTitle(video) {
  const title = video.title || video.song || 'Untitled';
  if (!video.studio_url) return title;
  return `<a class="table-link" href="${video.studio_url}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}

function renderStoryTitle(row) {
  const title = row.title || 'Untitled';
  const url = row.studio_url || row.youtube_url;
  if (!url) return title;
  return `<a class="table-link" href="${url}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}

function renderVideos(items) {
  const body = document.getElementById('videos-table');
  if (!body) return;
  body.innerHTML = '';
  const sorted = sortVideos(items || []).slice(0, 100);
  sorted.forEach((v) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="video-title-cell">${renderVideoTitle(v)}</td>
      <td>${renderVisibility(v.visibility)}</td>
      <td class="compact-text">${v.style || '—'}</td>
      <td class="nowrap">${v.date || '—'}</td>
      <td>${renderRetention(v.retention_30s_pct, v.retention_30s_status)} ${renderRetentionTrend(v)}</td>
      <td>${renderPercent(v.avg_view_percentage, 15)}</td>
      <td>${renderNumber(v.watch_hours_7d, 1)}</td>
      <td>${renderCompactNumber(v.total_watch_hours, 1)}</td>
      <td>${renderEfficiency(v.efficiency_index)}</td>
      <td>${renderTrafficLight(v.traffic_light, v.traffic_light_code)}</td>
      <td>${Number(v.yt_views || 0).toLocaleString()}</td>`;
    body.appendChild(tr);
  });
}

async function loadVideos() {
  try {
    const data = await fetchJson('/tracker/videos?limit=200');
    musicVideosCache = data.items || [];
    renderVideos(musicVideosCache);
  } catch (err) { console.error(err); }
}

function storyWinner(row) {
  const yt = Number(row.yt_views || 0);
  const tt = Number(row.tt_views || 0);
  const insta = Number(row.insta_views || 0);
  const values = [
    ['YT', yt],
    ['TT', tt],
    ['Insta', insta],
  ].sort((a, b) => b[1] - a[1]);
  return values[0][1] > 0 ? values[0][0] : '—';
}

function sortStory(items) {
  const { field, order } = storySortState;
  const multiplier = order === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    if (field === 'title') return multiplier * String(a.title || '').localeCompare(String(b.title || ''));
    if (field === 'category') return multiplier * String(a.category || '').localeCompare(String(b.category || ''));
    if (field === 'format') return multiplier * String(a.format || '').localeCompare(String(b.format || ''));
    if (field === 'visibility') return multiplier * String(a.visibility || '').localeCompare(String(b.visibility || ''));
    if (field === 'winner') return multiplier * storyWinner(a).localeCompare(storyWinner(b));
    if (field === 'date') {
      const da = a.date ? new Date(a.date) : new Date(0);
      const db = b.date ? new Date(b.date) : new Date(0);
      return multiplier * (da - db);
    }
    const va = Number(a[field] ?? -1);
    const vb = Number(b[field] ?? -1);
    return multiplier * (va - vb);
  });
}

function renderStory(items) {
  const body = document.getElementById('story-table');
  if (!body) return;
  body.innerHTML = '';
  sortStory(items || []).forEach((row) => {
    const yt = Number(row.yt_views || 0);
    const tt = Number(row.tt_views || 0);
    const insta = Number(row.insta_views || 0);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${renderCategory(row.category, row.category_label)}</td>
      <td>${renderFormat(row.format)}</td>
      <td class="story-title-cell">${renderStoryTitle(row)}</td>
      <td>${renderVisibility(row.visibility)}</td>
      <td class="nowrap">${row.date || '—'}</td>
      <td>${yt.toLocaleString()}</td>
      <td>${tt.toLocaleString()}</td>
      <td>${insta.toLocaleString()}</td>
      <td>${storyWinner(row)}</td>`;
    body.appendChild(tr);
  });
}

async function loadStory() {
  try {
    const data = await fetchJson('/tracker/story');
    storyCache = data.items || [];
    renderStory(storyCache);
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
  SORTABLE_HEADERS = Array.from(document.querySelectorAll('th[data-sortable]'));
  STATS_GROUP_BUTTONS.forEach(btn => btn.addEventListener('click', () => targetStatsGroup(btn.dataset.statsGroup)));
  MUSIC_TAB_BUTTONS.forEach(tab => tab.addEventListener('click', () => targetMusicPanel(tab.dataset.musicTab)));
  SORTABLE_HEADERS.forEach((header) => {
    header.addEventListener('click', () => {
      const field = header.dataset.sortable;
      const table = header.closest('table');
      const isShortsHeader = Boolean(table?.querySelector('#shorts-table'));
      const isStoryHeader = Boolean(table?.querySelector('#story-table'));
      const state = isStoryHeader ? storySortState : isShortsHeader ? shortsSortState : musicSortState;
      if (state.field === field) {
        state.order = state.order === 'asc' ? 'desc' : 'asc';
      } else {
        state.field = field;
        state.order = field === 'title' ? 'asc' : 'desc';
      }
      SORTABLE_HEADERS
        .filter((h) => h.closest('table') === table)
        .forEach((h) => h.classList.remove('sorted-asc', 'sorted-desc'));
      header.classList.add(state.order === 'asc' ? 'sorted-asc' : 'sorted-desc');
      if (isStoryHeader) renderStory(storyCache);
      else if (isShortsHeader) renderShorts(musicShortsCache);
      else renderVideos(musicVideosCache);
    });
  });
  
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
