'use strict';

const { migrate } = require('../db/migrate');
const { extractText } = require('./extractor');
const { chunkText } = require('./chunker');
const { generateWikiSections } = require('./wiki');
const { buildPack } = require('./pack-builder');

const POLL_MS = parseInt(process.env.CANIS_WORKER_POLL_MS || '5000', 10);
const MAX_BATCH = parseInt(process.env.CANIS_WORKER_BATCH || '5', 10);

let _db;

function getDb() {
  if (!_db) _db = migrate();
  return _db;
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

/**
 * Full pipeline for a single document:
 *   extract → chunk → wiki → mark wiki_ready
 */
async function processDocument(doc, db) {
  const now = () => new Date().toISOString();

  db.prepare(
    "UPDATE canis_documents SET status='extracting', updated_at=? WHERE id=?"
  ).run(now(), doc.id);

  console.log('[canis-worker] processing', doc.id, '(' + doc.filename + ')');

  try {
    // Step 1: Extract text
    const { text, pageCount } = await extractText(doc.file_path, doc.filename);

    db.prepare(
      "UPDATE canis_documents SET page_count=?, word_count=?, updated_at=? WHERE id=?"
    ).run(pageCount, text.split(/\s+/).filter(Boolean).length, now(), doc.id);

    // Step 2: Chunk
    const chunks = chunkText(text, doc.id, doc.filename);
    console.log('[canis-worker] ' + doc.id + ' → ' + chunks.length + ' chunks (' + pageCount + ' pages)');

    const insertChunk = db.prepare(`
      INSERT INTO canis_chunks
        (id, doc_id, text, source_page, chunk_index, word_count, chunk_type, tfidf_json, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    db.transaction(() => {
      for (const c of chunks) {
        insertChunk.run(c.id, c.doc_id, c.text, c.source_page, c.chunk_index,
          c.word_count, c.chunk_type, c.tfidf_json, now());
      }
    })();

    db.prepare(
      "UPDATE canis_documents SET status='chunked', updated_at=? WHERE id=?"
    ).run(now(), doc.id);

    // Step 3: Wiki generation
    const sections = await generateWikiSections(doc.id, doc.filename, chunks);
    console.log('[canis-worker] ' + doc.id + ' → ' + sections.length + ' wiki sections');

    const insertSection = db.prepare(`
      INSERT INTO canis_wiki_sections
        (id, doc_id, title, body, section_index, chunk_ids, generated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    db.transaction(() => {
      for (const s of sections) {
        insertSection.run(s.id, s.doc_id, s.title, s.body, s.section_index,
          s.chunk_ids, s.generated_at);
      }
    })();

    db.prepare(
      "UPDATE canis_documents SET status='wiki_ready', updated_at=? WHERE id=?"
    ).run(now(), doc.id);

    return { success: true, userId: doc.user_id };
  } catch (err) {
    console.error('[canis-worker] failed', doc.id, ':', err.message);
    db.prepare(
      "UPDATE canis_documents SET status='failed', error_msg=?, updated_at=? WHERE id=?"
    ).run(err.message, now(), doc.id);
    return { success: false, userId: doc.user_id };
  }
}

/**
 * One poll cycle: pick pending documents, process them, then build packs for
 * users whose documents are all in a terminal state.
 */
async function tick() {
  const db = getDb();

  const docs = db.prepare(`
    SELECT * FROM canis_documents
    WHERE status = 'pending'
    LIMIT ?
  `).all(MAX_BATCH);

  if (docs.length === 0) return;

  // Reserve batch
  const stamp = db.prepare(
    "UPDATE canis_documents SET status='pending', updated_at=? WHERE id=?"
  );
  db.transaction(() => {
    for (const doc of docs) stamp.run(new Date().toISOString(), doc.id);
  })();

  const succeededUsers = new Set();

  for (const doc of docs) {
    const result = await processDocument(doc, db);
    if (result.success) succeededUsers.add(result.userId);
  }

  // Build pack for users whose docs are all settled (no pending/extracting/chunked)
  for (const userId of succeededUsers) {
    const inFlight = db.prepare(`
      SELECT COUNT(*) AS n FROM canis_documents
      WHERE user_id = ? AND status IN ('pending','extracting','chunked')
    `).get(userId).n;

    if (inFlight > 0) continue;

    const wikiReady = db.prepare(`
      SELECT COUNT(*) AS n FROM canis_documents
      WHERE user_id = ? AND status = 'wiki_ready'
    `).get(userId).n;

    if (wikiReady === 0) continue;

    try {
      const pack = await buildPack(userId, db);
      console.log(
        '[canis-worker] pack v' + pack.version + ' built for user ' + userId +
        ' — ' + pack.chunkCount + ' chunks, ' + pack.wikiCount + ' wiki sections'
      );
    } catch (err) {
      console.error('[canis-worker] pack build failed for user ' + userId + ':', err.message);
    }
  }
}

async function main() {
  console.log('[canis-worker] starting — poll=' + POLL_MS + 'ms');
  while (true) {
    try {
      await tick();
    } catch (err) {
      console.error('[canis-worker] tick error:', err.message);
    }
    await sleep(POLL_MS);
  }
}

if (require.main === module) {
  main().catch((err) => {
    console.error('[canis-worker] fatal:', err);
    process.exit(1);
  });
}

module.exports = { tick, processDocument };
