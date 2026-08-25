'use strict';

const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

const UPLOADS_DIR = process.env.CANIS_UPLOADS_DIR
  || path.join(__dirname, '..', 'uploads');

const MAX_UPLOAD_BYTES = 25_000_000; // 25 MB (covers a 30-page PDF)
const SESSION_MAX_AGE_MS = 90 * 24 * 60 * 60 * 1000; // 90 days

function sanitizeFilename(name) {
  return path.basename(name).replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 200);
}

function issueToken(userId, db) {
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + SESSION_MAX_AGE_MS).toISOString();
  db.prepare(
    'INSERT INTO canis_sessions (token, user_id, expires_at) VALUES (?, ?, ?)'
  ).run(token, userId, expiresAt);
  return token;
}

function requireAuth(db) {
  return (req, res, next) => {
    const auth = req.headers.authorization || '';
    const token = auth.startsWith('Bearer ') ? auth.slice(7).trim() : null;
    if (!token) return res.status(401).json({ error: 'Unauthorized' });

    const now = new Date().toISOString();
    const session = db.prepare(`
      SELECT cs.user_id, cu.email, cu.display_name
      FROM canis_sessions cs
      JOIN canis_users cu ON cu.id = cs.user_id
      WHERE cs.token = ? AND cs.expires_at > ?
    `).get(token, now);

    if (!session) return res.status(401).json({ error: 'Unauthorized' });

    req.canisUser = { id: session.user_id, email: session.email, displayName: session.display_name };
    return next();
  };
}

/**
 * Build the CANIS Express router.
 * @param {import('better-sqlite3').Database} db
 */
function buildRouter(db) {
  fs.mkdirSync(UPLOADS_DIR, { recursive: true });

  const router = express.Router();
  const auth = requireAuth(db);

  // ── POST /auth/apple ─────────────────────────────────────────────────────────
  // In test mode (TEST_CANIS_MODE=1, non-prod), accepts { sub, email } directly.
  // In production, would verify the Apple JWT (not implemented in this prototype).

  router.post('/auth/apple', (req, res) => {
    const { sub, email, givenName, familyName } = req.body || {};
    if (!sub) return res.status(400).json({ error: 'sub is required' });

    const displayName = [givenName, familyName].filter(Boolean).join(' ') || null;
    const newId = uuidv4();
    const now = new Date().toISOString();

    db.prepare(`
      INSERT OR IGNORE INTO canis_users (id, apple_sub, email, display_name, created_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(newId, sub, email || null, displayName, now);

    const user = db.prepare('SELECT * FROM canis_users WHERE apple_sub = ?').get(sub);
    if (!user) return res.status(500).json({ error: 'Failed to resolve user' });

    const token = issueToken(user.id, db);
    return res.json({ token, user: { id: user.id, email: user.email, displayName: user.display_name } });
  });

  // ── GET /auth/me ─────────────────────────────────────────────────────────────

  router.get('/auth/me', auth, (req, res) => {
    const user = db.prepare(
      'SELECT id, email, display_name, created_at FROM canis_users WHERE id = ?'
    ).get(req.canisUser.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    return res.json({ id: user.id, email: user.email, displayName: user.display_name });
  });

  // ── POST /documents ───────────────────────────────────────────────────────────
  // Accept a base64-encoded file body: { filename, content, mimeType? }

  router.post('/documents', auth, (req, res) => {
    try {
      const { filename, content, mimeType } = req.body || {};
      if (!filename) return res.status(400).json({ error: 'filename is required' });
      if (!content || typeof content !== 'string') {
        return res.status(400).json({ error: 'content must be a base64 string' });
      }

      if (content.length * 0.75 >= MAX_UPLOAD_BYTES) {
        return res.status(400).json({ error: 'File too large (max 25 MB)' });
      }

      const docId = uuidv4();
      const safe = sanitizeFilename(filename);
      const filePath = path.join(UPLOADS_DIR, docId + '-' + safe);

      fs.writeFileSync(filePath, Buffer.from(content, 'base64'));

      const now = new Date().toISOString();
      db.prepare(`
        INSERT INTO canis_documents
          (id, user_id, filename, mime_type, file_path, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
      `).run(docId, req.canisUser.id, filename, mimeType || 'application/octet-stream', filePath, now, now);

      return res.status(201).json({ id: docId, filename, status: 'pending', createdAt: now });
    } catch (err) {
      console.error('[canis-api/documents POST]', err.message);
      return res.status(500).json({ error: 'Internal server error' });
    }
  });

  // ── GET /documents ────────────────────────────────────────────────────────────

  router.get('/documents', auth, (req, res) => {
    const docs = db.prepare(`
      SELECT id, filename, status, page_count, word_count, created_at, updated_at
      FROM canis_documents WHERE user_id = ? ORDER BY created_at DESC
    `).all(req.canisUser.id);

    return res.json(docs.map((d) => ({
      id: d.id,
      filename: d.filename,
      status: d.status,
      pageCount: d.page_count,
      wordCount: d.word_count,
      createdAt: d.created_at,
      updatedAt: d.updated_at,
    })));
  });

  // ── GET /documents/:id/status ─────────────────────────────────────────────────

  router.get('/documents/:id/status', auth, (req, res) => {
    const doc = db.prepare(`
      SELECT id, filename, status, page_count, word_count, error_msg, updated_at
      FROM canis_documents WHERE id = ? AND user_id = ?
    `).get(req.params.id, req.canisUser.id);

    if (!doc) return res.status(404).json({ error: 'Not found' });

    const chunkCount = db.prepare(
      'SELECT COUNT(*) AS n FROM canis_chunks WHERE doc_id = ?'
    ).get(doc.id).n;

    const wikiCount = db.prepare(
      'SELECT COUNT(*) AS n FROM canis_wiki_sections WHERE doc_id = ?'
    ).get(doc.id).n;

    return res.json({
      id: doc.id,
      filename: doc.filename,
      status: doc.status,
      pageCount: doc.page_count,
      wordCount: doc.word_count,
      chunkCount,
      wikiSectionCount: wikiCount,
      errorMsg: doc.error_msg,
      updatedAt: doc.updated_at,
    });
  });

  // ── GET /pack/status ──────────────────────────────────────────────────────────

  router.get('/pack/status', auth, (req, res) => {
    const pack = db.prepare(`
      SELECT version, chunk_count, doc_count, wiki_count, created_at
      FROM canis_packs WHERE user_id = ?
      ORDER BY version DESC LIMIT 1
    `).get(req.canisUser.id);

    if (!pack) return res.json({ version: 0, status: 'none' });

    const inFlight = db.prepare(`
      SELECT COUNT(*) AS n FROM canis_documents
      WHERE user_id = ? AND status IN ('pending','extracting','chunked','wiki_ready')
    `).get(req.canisUser.id).n;

    return res.json({
      version: pack.version,
      chunkCount: pack.chunk_count,
      docCount: pack.doc_count,
      wikiSectionCount: pack.wiki_count,
      createdAt: pack.created_at,
      status: inFlight > 0 ? 'building' : 'ready',
    });
  });

  // ── GET /pack/download ────────────────────────────────────────────────────────

  router.get('/pack/download', auth, (req, res) => {
    const pack = db.prepare(`
      SELECT pack_path, version FROM canis_packs WHERE user_id = ?
      ORDER BY version DESC LIMIT 1
    `).get(req.canisUser.id);

    if (!pack) return res.status(404).json({ error: 'No pack available' });
    if (!fs.existsSync(pack.pack_path)) {
      return res.status(404).json({ error: 'Pack file not found on disk' });
    }

    res.setHeader('Content-Type', 'application/octet-stream');
    res.setHeader('Content-Disposition', `attachment; filename="canis_pack_v${pack.version}.sqlite"`);
    fs.createReadStream(pack.pack_path).pipe(res);
  });

  return router;
}

module.exports = { buildRouter };
