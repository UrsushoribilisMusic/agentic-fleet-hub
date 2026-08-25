'use strict';

/**
 * canis-backend/ui/console.js — Canis Consumer Web Console & Wiki Review
 *
 * WP1 C-107: Wiki review screen (consumer-simplified)
 * Mobile-first, consumer-simplified interface for reviewing, editing, deleting
 * generated wiki pages, and rebuilding on-device knowledge packs.
 */

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function canisConsoleHtml(user = {}, token = '') {
  const bootUser = {
    id: user.id || '',
    email: user.email || '',
    displayName: user.displayName || (user.email ? user.email.split('@')[0] : 'Canis User'),
  };

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>Canis — Personal Knowledge Wiki</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script>
    (function() {
      var saved = localStorage.getItem('canis_theme');
      if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
      }
    })();
  </script>
  <style>
    :root {
      --bg: #0b0d14;
      --bg-surface: #141724;
      --bg-card: #1b1f30;
      --bg-card-hover: #22273d;
      --border: rgba(255, 255, 255, 0.08);
      --border-lit: rgba(99, 102, 241, 0.45);
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --accent: #6366f1;
      --accent-lit: #818cf8;
      --accent-glow: rgba(99, 102, 241, 0.2);
      --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
      --success: #22c55e;
      --success-bg: rgba(34, 197, 94, 0.12);
      --success-border: rgba(34, 197, 94, 0.3);
      --warning: #f59e0b;
      --warning-bg: rgba(245, 158, 11, 0.12);
      --danger: #ef4444;
      --danger-bg: rgba(239, 68, 68, 0.12);
      --danger-border: rgba(239, 68, 68, 0.3);
      --input-bg: #111420;
      --shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --radius-full: 9999px;
      --safe-top: env(safe-area-inset-top, 0px);
      --safe-bottom: env(safe-area-inset-bottom, 0px);
    }

    [data-theme="light"] {
      --bg: #f8fafc;
      --bg-surface: #ffffff;
      --bg-card: #f1f5f9;
      --bg-card-hover: #e2e8f0;
      --border: #e2e8f0;
      --border-lit: rgba(99, 102, 241, 0.5);
      --text: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;
      --accent: #4f46e5;
      --accent-lit: #6366f1;
      --accent-glow: rgba(79, 70, 229, 0.15);
      --accent-gradient: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
      --input-bg: #ffffff;
      --shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.08);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding-top: var(--safe-top);
      padding-bottom: var(--safe-bottom);
      transition: background-color 0.2s ease, color 0.2s ease;
    }

    .app-container {
      max-width: 960px;
      margin: 0 auto;
      width: 100%;
      padding: 16px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    /* Header */
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-md);
      background: var(--accent-gradient);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 4px 12px var(--accent-glow);
    }
    .brand-info h1 {
      font-size: 19px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .brand-badge {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: var(--radius-full);
      background: var(--accent-glow);
      color: var(--accent-lit);
      border: 1px solid var(--border-lit);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .brand-info p {
      font-size: 12px;
      color: var(--text-dim);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .icon-btn {
      width: 38px;
      height: 38px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
      background: var(--bg-card);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 16px;
      transition: all 0.15s ease;
    }
    .icon-btn:hover {
      background: var(--bg-card-hover);
      border-color: var(--border-lit);
    }

    /* Tabs */
    .tabs {
      display: flex;
      gap: 8px;
      background: var(--bg-surface);
      padding: 6px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }
    .tab-btn {
      flex: 1;
      padding: 10px 14px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      border-radius: var(--radius-sm);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.15s ease;
    }
    .tab-btn.active {
      background: var(--bg-card);
      color: var(--text);
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      border: 1px solid var(--border);
    }
    .tab-badge {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: var(--radius-full);
      background: var(--accent-glow);
      color: var(--accent-lit);
    }

    /* Primary Rebuild Banner */
    .action-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      background: var(--bg-surface);
      border: 1px solid var(--border-lit);
      border-radius: var(--radius-md);
      box-shadow: 0 4px 16px var(--accent-glow);
      gap: 16px;
      flex-wrap: wrap;
    }
    .action-banner-info h3 {
      font-size: 15px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .action-banner-info p {
      font-size: 12px;
      color: var(--text-muted);
    }
    .btn-primary {
      padding: 10px 18px;
      background: var(--accent-gradient);
      color: #fff;
      border: none;
      border-radius: var(--radius-md);
      font-family: inherit;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 12px var(--accent-glow);
      transition: all 0.15s ease;
    }
    .btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
    }
    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }
    .btn-secondary {
      padding: 8px 14px;
      background: var(--bg-card);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-secondary:hover {
      background: var(--bg-card-hover);
      border-color: var(--border-lit);
    }
    .btn-danger {
      padding: 8px 14px;
      background: var(--danger-bg);
      color: var(--danger);
      border: 1px solid var(--danger-border);
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .btn-danger:hover {
      background: var(--danger);
      color: #fff;
    }

    /* Content Cards Grid */
    .tab-content { display: none; flex-direction: column; gap: 16px; }
    .tab-content.active { display: flex; }

    .wiki-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 14px;
    }

    .wiki-card {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: var(--shadow);
      transition: all 0.2s ease;
    }
    .wiki-card:hover {
      border-color: var(--border-lit);
      transform: translateY(-2px);
    }
    .wiki-card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
    }
    .wiki-card-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text);
      line-height: 1.3;
    }
    .wiki-doc-tag {
      font-size: 11px;
      color: var(--text-dim);
      background: var(--bg-card);
      padding: 2px 6px;
      border-radius: 4px;
      max-width: 140px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .wiki-card-body {
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      max-height: 90px;
      overflow: hidden;
      position: relative;
      word-break: break-word;
    }
    .wiki-card-body::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 32px;
      background: linear-gradient(transparent, var(--bg-surface));
    }
    .wiki-card-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding-top: 10px;
      border-top: 1px solid var(--border);
      gap: 8px;
    }

    /* Reader & Edit Modals */
    .modal-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 1000;
    }
    .modal-backdrop.active { display: flex; }
    .modal {
      background: var(--bg-surface);
      border: 1px solid var(--border-lit);
      border-radius: var(--radius-lg);
      max-width: 680px;
      width: 100%;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 10px 40px rgba(0,0,0,0.8);
      overflow: hidden;
      animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes modalPop {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
    }
    .modal-header h2 { font-size: 17px; font-weight: 700; }
    .modal-body {
      padding: 20px;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .modal-footer {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      padding: 14px 20px;
      border-top: 1px solid var(--border);
      background: var(--bg-card);
    }

    /* Form Fields */
    .field-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .field-group label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .field-input, .field-textarea {
      background: var(--input-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text);
      font-family: inherit;
      font-size: 14px;
      padding: 10px 12px;
      outline: none;
      transition: border-color 0.15s ease;
    }
    .field-input:focus, .field-textarea:focus {
      border-color: var(--accent);
    }
    .field-textarea {
      min-height: 200px;
      resize: vertical;
      line-height: 1.5;
    }

    /* Upload & Document Cards */
    .upload-box {
      border: 2px dashed var(--border-lit);
      border-radius: var(--radius-md);
      padding: 30px 20px;
      text-align: center;
      background: var(--bg-surface);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      transition: all 0.15s ease;
    }
    .upload-box:hover {
      background: var(--bg-card);
      border-color: var(--accent-lit);
    }
    .upload-icon { font-size: 32px; }

    .doc-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .doc-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      gap: 12px;
    }
    .doc-info h4 { font-size: 14px; font-weight: 600; }
    .doc-meta { font-size: 12px; color: var(--text-dim); display: flex; gap: 8px; }
    .doc-error {
      margin-top: 6px;
      color: var(--danger);
      font-size: 12px;
      line-height: 1.4;
    }

    /* Toast */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--bg-card);
      border: 1px solid var(--border-lit);
      border-radius: var(--radius-md);
      padding: 12px 20px;
      box-shadow: var(--shadow);
      font-size: 13px;
      font-weight: 600;
      color: var(--text);
      display: none;
      align-items: center;
      gap: 10px;
      z-index: 2000;
      animation: toastIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .toast.active { display: flex; }
    @keyframes toastIn {
      from { transform: translateY(10px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }

    .empty-state {
      text-align: center;
      padding: 48px 20px;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }
    .empty-icon { font-size: 40px; }
  </style>
</head>
<body>
  <div class="app-container">
    <!-- Header -->
    <header>
      <div class="brand">
        <div class="brand-icon">🐾</div>
        <div class="brand-info">
          <h1>Canis Wiki <span class="brand-badge">On-Device AI</span></h1>
          <p id="userLabel">${escapeHtml(bootUser.displayName)} · <span id="packVersionHeader">Pack: Loading…</span></p>
        </div>
      </div>
      <div class="header-actions">
        <button class="icon-btn" id="themeToggle" title="Toggle Theme">🌓</button>
      </div>
    </header>

    <!-- Top Action Banner -->
    <div class="action-banner">
      <div class="action-banner-info">
        <h3>✨ On-Device Knowledge Pack</h3>
        <p>Your wiki pages are synthesized and packaged for 100% offline querying in the Canis iOS app.</p>
      </div>
      <button class="btn-primary" id="reindexBtn">
        🔄 Rebuild Knowledge Pack
      </button>
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs">
      <button class="tab-btn active" data-tab="wikiTab">
        📖 Wiki Pages <span class="tab-badge" id="wikiCountBadge">0</span>
      </button>
      <button class="tab-btn" data-tab="docsTab">
        📄 Documents <span class="tab-badge" id="docCountBadge">0</span>
      </button>
      <button class="tab-btn" data-tab="packTab">
        📦 Knowledge Pack
      </button>
    </div>

    <!-- TAB 1: Wiki Pages (WP1 C-107) -->
    <div class="tab-content active" id="wikiTab">
      <div class="wiki-grid" id="wikiGrid">
        <!-- Rendered dynamically -->
      </div>
      <div class="empty-state" id="wikiEmpty" style="display:none;">
        <div class="empty-icon">📚</div>
        <h3>No wiki pages generated yet</h3>
        <p>Upload documents in the Documents tab to automatically extract topics and build your wiki.</p>
      </div>
    </div>

    <!-- TAB 2: Documents -->
    <div class="tab-content" id="docsTab">
      <div class="upload-box" id="uploadBox">
        <div class="upload-icon">📤</div>
        <h4>Drop PDF, TXT, or Markdown files here</h4>
        <p style="font-size:12px; color:var(--text-dim);">Tap to select file (up to 25 MB)</p>
        <input type="file" id="fileInput" accept=".pdf,.txt,.md" style="display:none;">
      </div>
      <div class="doc-list" id="docList">
        <!-- Rendered dynamically -->
      </div>
      <div class="empty-state" id="docsEmpty" style="display:none;">
        <div class="empty-icon">📄</div>
        <h3>No documents uploaded</h3>
        <p>Add your personal manuals, research, or notes above.</p>
      </div>
    </div>

    <!-- TAB 3: Knowledge Pack -->
    <div class="tab-content" id="packTab">
      <div class="wiki-card" style="padding:24px;">
        <h3 style="font-size:17px; margin-bottom:12px;">📦 On-Device SQLite Pack Status</h3>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; margin-bottom:20px;">
          <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">Version</div>
            <div style="font-size:22px; font-weight:700;" id="packStatVersion">-</div>
          </div>
          <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">Documents</div>
            <div style="font-size:22px; font-weight:700;" id="packStatDocs">0</div>
          </div>
          <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">Chunks</div>
            <div style="font-size:22px; font-weight:700;" id="packStatChunks">0</div>
          </div>
          <div style="background:var(--bg-card); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-size:11px; color:var(--text-dim); text-transform:uppercase;">Wiki Pages</div>
            <div style="font-size:22px; font-weight:700;" id="packStatWiki">0</div>
          </div>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <a class="btn-primary" id="downloadPackBtn" href="/api/pack/download" style="text-decoration:none;">
            ⬇️ Download SQLite Pack
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Reader Modal -->
  <div class="modal-backdrop" id="readerModal">
    <div class="modal">
      <div class="modal-header">
        <h2 id="readerTitle">Page Reader</h2>
        <button class="icon-btn" onclick="closeModal('readerModal')">✕</button>
      </div>
      <div class="modal-body">
        <div id="readerDocBadge" class="wiki-doc-tag" style="align-self:flex-start;"></div>
        <div id="readerBody" style="line-height:1.6; font-size:14px; color:var(--text); white-space:pre-wrap;"></div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" onclick="closeModal('readerModal')">Close</button>
        <button class="btn-primary" id="readerEditBtn">✏️ Edit Page</button>
      </div>
    </div>
  </div>

  <!-- Edit Modal -->
  <div class="modal-backdrop" id="editModal">
    <div class="modal">
      <div class="modal-header">
        <h2>Edit Wiki Page</h2>
        <button class="icon-btn" onclick="closeModal('editModal')">✕</button>
      </div>
      <div class="modal-body">
        <input type="hidden" id="editPageId">
        <div class="field-group">
          <label for="editTitleInput">Page Title</label>
          <input type="text" class="field-input" id="editTitleInput" placeholder="Enter page title">
        </div>
        <div class="field-group">
          <label for="editBodyInput">Markdown Content</label>
          <textarea class="field-textarea" id="editBodyInput" placeholder="Enter page summary and knowledge details..."></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" onclick="closeModal('editModal')">Cancel</button>
        <button class="btn-primary" id="saveEditBtn">💾 Save Changes</button>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div class="toast" id="toast"></div>

  <script>
    const AUTH_TOKEN = ${JSON.stringify(token)};
    let currentSections = [];
    let currentDocs = [];
    let currentPack = null;

    function getHeaders() {
      const headers = { 'Content-Type': 'application/json' };
      if (AUTH_TOKEN) headers['Authorization'] = 'Bearer ' + AUTH_TOKEN;
      return headers;
    }

    function showToast(msg) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('active');
      setTimeout(() => t.classList.remove('active'), 3200);
    }

    function closeModal(id) {
      document.getElementById(id).classList.remove('active');
    }

    function openModal(id) {
      document.getElementById(id).classList.add('active');
    }

    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', current);
      localStorage.setItem('canis_theme', current);
    });

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.getAttribute('data-tab')).classList.add('active');
      });
    });

    // Load Wiki Sections
    async function loadWiki() {
      try {
        const res = await fetch('/api/wiki/sections', { headers: getHeaders() });
        if (!res.ok) return;
        currentSections = await res.json();
        renderWiki();
      } catch (err) {
        console.error('Failed to load wiki:', err);
      }
    }

    function renderWiki() {
      const grid = document.getElementById('wikiGrid');
      const empty = document.getElementById('wikiEmpty');
      const badge = document.getElementById('wikiCountBadge');
      badge.textContent = currentSections.length;

      if (!currentSections || currentSections.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'flex';
        return;
      }
      empty.style.display = 'none';

      grid.innerHTML = currentSections.map(s => {
        const title = escapeHtml(s.title);
        const docName = escapeHtml(s.docFilename || 'Document');
        const bodyPreview = escapeHtml(s.body || '');
        const wordCount = (s.body || '').split(/\\s+/).filter(Boolean).length;

        return \`
          <div class="wiki-card" data-id="\${s.id}">
            <div class="wiki-card-header">
              <div class="wiki-card-title">\${title}</div>
              <div class="wiki-doc-tag" title="\${docName}">📄 \${docName}</div>
            </div>
            <div class="wiki-card-body">\${bodyPreview}</div>
            <div class="wiki-card-actions">
              <span style="font-size:11px; color:var(--text-dim);">\${wordCount} words</span>
              <div style="display:flex; gap:6px;">
                <button class="btn-secondary" onclick="openReader('\${s.id}')">Read</button>
                <button class="btn-secondary" onclick="openEdit('\${s.id}')">Edit</button>
                <button class="btn-danger" onclick="deleteSection('\${s.id}')">Delete</button>
              </div>
            </div>
          </div>
        \`;
      }).join('');
    }

    function openReader(id) {
      const s = currentSections.find(x => x.id === id);
      if (!s) return;
      document.getElementById('readerTitle').textContent = s.title;
      document.getElementById('readerDocBadge').textContent = '📄 ' + (s.docFilename || 'Document');
      document.getElementById('readerBody').textContent = s.body;
      document.getElementById('readerEditBtn').onclick = () => {
        closeModal('readerModal');
        openEdit(id);
      };
      openModal('readerModal');
    }

    function openEdit(id) {
      const s = currentSections.find(x => x.id === id);
      if (!s) return;
      document.getElementById('editPageId').value = s.id;
      document.getElementById('editTitleInput').value = s.title;
      document.getElementById('editBodyInput').value = s.body;
      openModal('editModal');
    }

    document.getElementById('saveEditBtn').addEventListener('click', async () => {
      const id = document.getElementById('editPageId').value;
      const title = document.getElementById('editTitleInput').value.trim();
      const body = document.getElementById('editBodyInput').value.trim();

      if (!title) {
        alert('Page title is required');
        return;
      }

      try {
        const res = await fetch('/api/wiki/sections/' + id, {
          method: 'PATCH',
          headers: getHeaders(),
          body: JSON.stringify({ title, body }),
        });

        if (!res.ok) {
          const err = await res.json();
          alert(err.error || 'Failed to save changes');
          return;
        }

        closeModal('editModal');
        showToast('✅ Wiki page saved');
        await loadWiki();
      } catch (err) {
        alert('Network error while saving');
      }
    });

    async function deleteSection(id) {
      if (!confirm('Are you sure you want to delete this wiki page?')) return;
      try {
        const res = await fetch('/api/wiki/sections/' + id, {
          method: 'DELETE',
          headers: getHeaders(),
        });
        if (!res.ok) {
          alert('Failed to delete section');
          return;
        }
        showToast('🗑️ Wiki page deleted');
        await loadWiki();
      } catch (err) {
        alert('Network error while deleting');
      }
    }

    // Documents
    async function loadDocs() {
      try {
        const res = await fetch('/api/documents', { headers: getHeaders() });
        if (!res.ok) return;
        currentDocs = await res.json();
        renderDocs();
      } catch (err) {
        console.error('Failed to load docs:', err);
      }
    }

    function renderDocs() {
      const list = document.getElementById('docList');
      const empty = document.getElementById('docsEmpty');
      const badge = document.getElementById('docCountBadge');
      badge.textContent = currentDocs.length;

      if (!currentDocs || currentDocs.length === 0) {
        list.innerHTML = '';
        empty.style.display = 'flex';
        return;
      }
      empty.style.display = 'none';

      list.innerHTML = currentDocs.map(d => {
        const name = escapeHtml(d.filename);
        const status = escapeHtml(d.status);
        const label = escapeHtml(d.statusLabel || d.status);
        const statusColor = d.status === 'failed'
          ? 'var(--danger)'
          : (d.status === 'packed' || d.status === 'wiki_ready' ? 'var(--success)' : 'var(--warning)');
        const error = d.errorReason
          ? '<div class="doc-error">' + escapeHtml(d.errorReason) + '</div>'
          : '';

        return \`
          <div class="doc-card">
            <div class="doc-info">
              <h4>\${name}</h4>
              <div class="doc-meta">
                <span style="color:\${statusColor}; font-weight:600;" title="\${status}">\${label}</span> ·
                <span>\${d.pageCount || 0} pages</span> ·
                <span>\${d.wordCount || 0} words</span>
              </div>
              \${error}
            </div>
            <button class="btn-danger" onclick="deleteDoc('\${d.id}')">Delete</button>
          </div>
        \`;
      }).join('');
    }

    async function deleteDoc(id) {
      if (!confirm('Delete this document and all its wiki sections?')) return;
      try {
        const res = await fetch('/api/documents/' + id, {
          method: 'DELETE',
          headers: getHeaders(),
        });
        if (!res.ok) return alert('Failed to delete document');
        showToast('🗑️ Document deleted');
        await loadDocs();
        await loadWiki();
        await loadPack();
      } catch (err) {
        alert('Error deleting document');
      }
    }

    // Upload
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    uploadBox.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        try {
          showToast('⏳ Uploading ' + file.name + '…');
          const res = await fetch('/api/documents', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
              filename: file.name,
              content: base64,
              mimeType: file.type,
            }),
          });
          if (!res.ok) {
            const err = await res.json();
            alert(err.error || 'Upload failed');
            return;
          }
          showToast('✅ Uploaded ' + file.name);
          fileInput.value = '';
          await loadDocs();
        } catch (err) {
          alert('Upload failed');
        }
      };
      reader.readAsDataURL(file);
    });

    // Pack
    async function loadPack() {
      try {
        const res = await fetch('/api/pack/status', { headers: getHeaders() });
        if (!res.ok) return;
        currentPack = await res.json();
        renderPack();
      } catch (err) {
        console.error('Failed to load pack status:', err);
      }
    }

    function renderPack() {
      if (!currentPack) return;
      const v = currentPack.version ? 'v' + currentPack.version : 'None';
      document.getElementById('packVersionHeader').textContent = 'Pack: ' + v;
      document.getElementById('packStatVersion').textContent = v;
      document.getElementById('packStatDocs').textContent = currentPack.docCount || 0;
      document.getElementById('packStatChunks').textContent = currentPack.chunkCount || 0;
      document.getElementById('packStatWiki').textContent = currentPack.wikiSectionCount || 0;
    }

    // Reindex Trigger (C-107)
    document.getElementById('reindexBtn').addEventListener('click', async () => {
      const btn = document.getElementById('reindexBtn');
      btn.disabled = true;
      btn.textContent = '⏳ Rebuilding Pack…';
      try {
        const res = await fetch('/api/pack/reindex', {
          method: 'POST',
          headers: getHeaders(),
        });
        const data = await res.json();
        if (!res.ok) {
          alert(data.error || 'Failed to rebuild pack');
          return;
        }
        showToast('🚀 Rebuilt Knowledge Pack v' + data.version);
        await loadPack();
        await loadWiki();
      } catch (err) {
        alert('Network error while rebuilding pack');
      } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Rebuild Knowledge Pack';
      }
    });

    // Initial load
    loadWiki();
    loadDocs();
    loadPack();
    setInterval(() => {
      loadDocs();
      loadPack();
      loadWiki();
    }, 5000);
  </script>
</body>
</html>`;
}

module.exports = { canisConsoleHtml };
