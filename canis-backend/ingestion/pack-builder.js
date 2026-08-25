'use strict';

const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

const PACKS_DIR = process.env.CANIS_PACKS_DIR
  || path.join(__dirname, '..', 'packs');

/**
 * Build a versioned SQLite knowledge pack for the given user.
 * Reads all packed-ready documents, their chunks, and wiki sections from the
 * main CANIS DB and materializes them into a self-contained SQLite file at:
 *   PACKS_DIR/<userId>/v<N>.sqlite
 *
 * Pack schema (read by iOS CANIS app):
 *   meta          key-value store (version, user_id, created_at, …)
 *   chunks        text segments + TF-IDF weights
 *   wiki_sections structured summaries
 *
 * @param {string} userId
 * @param {import('better-sqlite3').Database} db  — main CANIS DB
 * @returns {{ version, chunkCount, docCount, wikiCount, packPath }}
 */
async function buildPack(userId, db) {
  const docs = db.prepare(`
    SELECT id, filename FROM canis_documents
    WHERE user_id = ? AND status IN ('wiki_ready', 'packed')
  `).all(userId);

  if (docs.length === 0) {
    throw new Error('No wiki-ready documents found for user ' + userId);
  }

  const versionRow = db.prepare(
    'SELECT MAX(version) AS maxV FROM canis_packs WHERE user_id = ?'
  ).get(userId);
  const version = (versionRow && versionRow.maxV != null)
    ? versionRow.maxV + 1
    : 1;

  const userDir = path.join(PACKS_DIR, userId);
  fs.mkdirSync(userDir, { recursive: true });
  const packPath = path.join(userDir, 'v' + version + '.sqlite');

  const packDb = new Database(packPath);
  packDb.exec(`
    CREATE TABLE meta (
      key   TEXT PRIMARY KEY,
      value TEXT
    );
    CREATE TABLE chunks (
      id          TEXT PRIMARY KEY,
      doc_id      TEXT NOT NULL,
      doc_title   TEXT NOT NULL,
      text        TEXT NOT NULL,
      source_page TEXT NOT NULL DEFAULT '',
      chunk_index INTEGER NOT NULL DEFAULT 0,
      chunk_type  TEXT NOT NULL DEFAULT 'document_text',
      tfidf_json  TEXT NOT NULL DEFAULT '{}'
    );
    CREATE TABLE wiki_sections (
      id            TEXT PRIMARY KEY,
      doc_id        TEXT NOT NULL,
      doc_title     TEXT NOT NULL,
      title         TEXT NOT NULL,
      body          TEXT NOT NULL,
      section_index INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX idx_chunks_doc      ON chunks (doc_id);
    CREATE INDEX idx_wiki_doc        ON wiki_sections (doc_id);
  `);

  const insertChunk = packDb.prepare(`
    INSERT INTO chunks (id, doc_id, doc_title, text, source_page, chunk_index, chunk_type, tfidf_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const insertWiki = packDb.prepare(`
    INSERT INTO wiki_sections (id, doc_id, doc_title, title, body, section_index)
    VALUES (?, ?, ?, ?, ?, ?)
  `);
  const insertMeta = packDb.prepare('INSERT INTO meta (key, value) VALUES (?, ?)');

  let totalChunks = 0;
  let totalWiki = 0;

  const fillPack = packDb.transaction(() => {
    for (const doc of docs) {
      const chunks = db.prepare(
        'SELECT * FROM canis_chunks WHERE doc_id = ? ORDER BY chunk_index'
      ).all(doc.id);

      for (const c of chunks) {
        insertChunk.run(c.id, c.doc_id, doc.filename, c.text, c.source_page,
          c.chunk_index, c.chunk_type, c.tfidf_json);
      }
      totalChunks += chunks.length;

      const sections = db.prepare(
        'SELECT * FROM canis_wiki_sections WHERE doc_id = ? ORDER BY section_index'
      ).all(doc.id);

      for (const s of sections) {
        insertWiki.run(s.id, s.doc_id, doc.filename, s.title, s.body, s.section_index);
      }
      totalWiki += sections.length;
    }
  });

  fillPack();

  const now = new Date().toISOString();
  packDb.transaction(() => {
    insertMeta.run('version', String(version));
    insertMeta.run('user_id', userId);
    insertMeta.run('created_at', now);
    insertMeta.run('doc_count', String(docs.length));
    insertMeta.run('chunk_count', String(totalChunks));
    insertMeta.run('wiki_count', String(totalWiki));
  })();

  packDb.close();

  db.prepare(`
    INSERT INTO canis_packs (user_id, version, pack_path, chunk_count, doc_count, wiki_count, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(userId, version, packPath, totalChunks, docs.length, totalWiki, now);

  db.prepare(`
    UPDATE canis_documents SET status = 'packed', updated_at = ?
    WHERE user_id = ? AND status = 'wiki_ready'
  `).run(now, userId);

  return { version, chunkCount: totalChunks, docCount: docs.length, wikiCount: totalWiki, packPath };
}

module.exports = { buildPack, PACKS_DIR };
