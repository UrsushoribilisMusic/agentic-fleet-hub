'use strict';

/**
 * test-c107-wiki-review.js
 *
 * Test suite for WP1 C-107: Wiki review screen (consumer-simplified).
 * Verifies:
 *   1. Generated wiki pages listed & readable (GET /wiki/sections, GET /wiki/sections/:id)
 *   2. Wiki page edit (PATCH /wiki/sections/:id) persists title and markdown body
 *   3. Wiki page delete (DELETE /wiki/sections/:id) removes section cleanly
 *   4. Re-index trigger (POST /pack/reindex) produces a NEW pack version (v1 -> v2)
 *   5. SQLite pack v2 verification (contains updated content, excludes deleted page)
 *   6. Cross-user security / tenant isolation (user2 cannot read/modify user1 wiki pages)
 */

const http = require('http');
const path = require('path');
const fs = require('fs');
const os = require('os');
const Database = require('better-sqlite3');
const express = require('express');
const { v4: uuidv4 } = require('uuid');

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log('  PASS:', message);
    passed++;
  } else {
    console.error('  FAIL:', message);
    failed++;
  }
}

// Create temporary working directory for test
const testTmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'canis-c107-test-'));
const testDbPath = path.join(testTmpDir, 'canis-test.db');
const testPacksDir = path.join(testTmpDir, 'packs');
const testUploadsDir = path.join(testTmpDir, 'uploads');

process.env.CANIS_PACKS_DIR = testPacksDir;
process.env.CANIS_UPLOADS_DIR = testUploadsDir;

// Initialize DB schema
const db = new Database(testDbPath);
const schemaSql = fs.readFileSync(path.join(__dirname, '..', 'db', 'schema.sql'), 'utf8');
db.exec(schemaSql);

const { buildRouter } = require('../api/router');
const app = express();
app.use(express.json({ limit: '30mb' }));
app.use('/api', buildRouter(db));
app.use('/', buildRouter(db));

let server;
let baseUrl;

function request(method, pathUrl, body = null, token = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(pathUrl, baseUrl);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = 'Bearer ' + token;

    const req = http.request(url, { method, headers }, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(data); } catch (_) {}
        resolve({ status: res.statusCode, headers: res.headers, body: json, text: data });
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function run() {
  console.log('=== WP1 C-107 Wiki Review Screen — Test Suite ===\n');

  await new Promise((resolve) => {
    server = app.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      baseUrl = 'http://127.0.0.1:' + port;
      resolve();
    });
  });

  try {
    // ── Setup: User 1 & Documents ───────────────────────────────────────────────
    console.log('--- Step 1: User 1 Auth & Document Seeding ---');
    const authRes1 = await request('POST', '/api/auth/apple', {
      sub: 'apple-user-c107-001',
      email: 'user1@canis.local',
      givenName: 'Canis',
      familyName: 'Tester'
    });

    assert(authRes1.status === 200, 'User 1 authenticated (HTTP 200)');
    const token1 = authRes1.body.token;
    const user1Id = authRes1.body.user.id;
    assert(Boolean(token1 && user1Id), 'Received token and user.id for User 1');

    // Seed 1 document, 4 chunks, and 2 wiki sections for User 1
    const docId1 = uuidv4();
    const now = new Date().toISOString();
    db.prepare(`
      INSERT INTO canis_documents (id, user_id, filename, status, page_count, word_count, created_at, updated_at)
      VALUES (?, ?, 'User_Guide_v1.pdf', 'wiki_ready', 10, 2500, ?, ?)
    `).run(docId1, user1Id, now, now);

    const chunk1Id = uuidv4();
    const chunk2Id = uuidv4();
    db.prepare(`
      INSERT INTO canis_chunks (id, doc_id, text, chunk_index, word_count, tfidf_json)
      VALUES (?, ?, 'Introduction to Canis on-device privacy architecture and local models.', 0, 10, '{"canis":1.5,"privacy":2.0}')
    `).run(chunk1Id, docId1);
    db.prepare(`
      INSERT INTO canis_chunks (id, doc_id, text, chunk_index, word_count, tfidf_json)
      VALUES (?, ?, 'Jacobian Lens forward-only readout and emotion disposition states.', 1, 10, '{"jacobian":2.1,"disposition":1.8}')
    `).run(chunk2Id, docId1);

    const wiki1Id = uuidv4();
    const wiki2Id = uuidv4();
    db.prepare(`
      INSERT INTO canis_wiki_sections (id, doc_id, title, body, section_index, chunk_ids, generated_at)
      VALUES (?, ?, 'Overview of On-Device Architecture', 'Canis provides fully private, on-device intelligence without cloud dependency.', 0, ?, ?)
    `).run(wiki1Id, docId1, JSON.stringify([chunk1Id]), now);

    db.prepare(`
      INSERT INTO canis_wiki_sections (id, doc_id, title, body, section_index, chunk_ids, generated_at)
      VALUES (?, ?, 'Jacobian Emotion Engine', 'The Jacobian lens monitors internal activations to express LLM internal state.', 1, ?, ?)
    `).run(wiki2Id, docId1, JSON.stringify([chunk2Id]), now);

    // Initial pack build (version 1)
    const { buildPack } = require('../ingestion/pack-builder');
    const pack1 = await buildPack(user1Id, db);
    assert(pack1.version === 1, 'Initial Pack v1 built successfully');
    assert(pack1.wikiCount === 2, 'Pack v1 contains 2 wiki sections');

    // ── AC 1: Pages Listed & Readable ──────────────────────────────────────────
    console.log('\n--- Step 2: AC-1 Pages Listed & Readable ---');
    const listRes = await request('GET', '/api/wiki/sections', null, token1);
    assert(listRes.status === 200, 'GET /api/wiki/sections returned HTTP 200');
    assert(Array.isArray(listRes.body), 'Response is an array of wiki sections');
    assert(listRes.body.length === 2, 'Found 2 wiki sections for User 1');

    const first = listRes.body.find(x => x.id === wiki1Id);
    assert(first !== undefined, 'First wiki section found in listing');
    assert(first.title === 'Overview of On-Device Architecture', 'Wiki title matches seeded value');
    assert(first.docFilename === 'User_Guide_v1.pdf', 'Document filename joined correctly');
    assert(first.body.includes('Canis provides fully private'), 'Wiki body content readable');
    assert(Array.isArray(first.chunkIds) && first.chunkIds.length === 1, 'Chunk IDs parsed correctly');

    const singleRes = await request('GET', `/api/wiki/sections/${wiki1Id}`, null, token1);
    assert(singleRes.status === 200, 'GET /api/wiki/sections/:id returned HTTP 200');
    assert(singleRes.body.id === wiki1Id, 'Fetched correct section by ID');
    assert(singleRes.body.title === 'Overview of On-Device Architecture', 'Fetched section title matches');

    // ── AC 2: Page Editing & Persistence ───────────────────────────────────────
    console.log('\n--- Step 3: AC-2 Wiki Page Editing ---');
    const editRes = await request('PATCH', `/api/wiki/sections/${wiki1Id}`, {
      title: 'Privacy Architecture — Core Principles (Edited)',
      body: 'Updated body: Canis executes forward-only MLX models directly on Apple Silicon with zero telemetry.'
    }, token1);

    assert(editRes.status === 200, 'PATCH /api/wiki/sections/:id returned HTTP 200');
    assert(editRes.body.updated === true, 'Response confirms update');
    assert(editRes.body.title === 'Privacy Architecture — Core Principles (Edited)', 'Updated title in response');

    // Verify in database
    const dbRow = db.prepare('SELECT title, body FROM canis_wiki_sections WHERE id = ?').get(wiki1Id);
    assert(dbRow.title === 'Privacy Architecture — Core Principles (Edited)', 'Database title updated');
    assert(dbRow.body.includes('zero telemetry'), 'Database body updated');

    // Empty title validation
    const badEdit = await request('PATCH', `/api/wiki/sections/${wiki1Id}`, { title: '   ' }, token1);
    assert(badEdit.status === 400, 'Empty title rejected with HTTP 400');

    // ── AC 3: Page Deletion ────────────────────────────────────────────────────
    console.log('\n--- Step 4: AC-2 Wiki Page Deletion ---');
    const deleteRes = await request('DELETE', `/api/wiki/sections/${wiki2Id}`, null, token1);
    assert(deleteRes.status === 204, 'DELETE /api/wiki/sections/:id returned HTTP 204');

    const listAfterDelete = await request('GET', '/api/wiki/sections', null, token1);
    assert(listAfterDelete.body.length === 1, 'Wiki sections list now contains exactly 1 page');
    assert(!listAfterDelete.body.some(x => x.id === wiki2Id), 'Deleted section no longer in list');

    // ── AC 4: Re-Index Trigger & Pack Version Increment ────────────────────────
    console.log('\n--- Step 5: AC-3 Re-Index Trigger (Pack v2) ---');
    const reindexRes = await request('POST', '/api/pack/reindex', {}, token1);
    assert(reindexRes.status === 200, 'POST /api/pack/reindex returned HTTP 200');
    assert(reindexRes.body.ok === true, 'Re-index reported ok: true');
    assert(reindexRes.body.version === 2, 'New pack version is v2 (incremented from v1)');
    assert(reindexRes.body.wikiCount === 1, 'Pack v2 contains 1 wiki section (deleted section excluded)');
    assert(fs.existsSync(reindexRes.body.packPath), 'Pack v2 SQLite file exists on disk');

    // Inspect SQLite pack v2 directly
    const pack2Db = new Database(reindexRes.body.packPath);
    const metaVer = pack2Db.prepare("SELECT value FROM meta WHERE key = 'version'").get().value;
    assert(metaVer === '2', 'SQLite pack meta table confirms version 2');

    const packWikiRows = pack2Db.prepare('SELECT title, body FROM wiki_sections').all();
    assert(packWikiRows.length === 1, 'SQLite pack has 1 wiki section');
    assert(packWikiRows[0].title === 'Privacy Architecture — Core Principles (Edited)', 'SQLite pack contains EDITED title');
    assert(packWikiRows[0].body.includes('zero telemetry'), 'SQLite pack contains EDITED body');
    pack2Db.close();

    // Verify GET /pack/status reflects new version
    const packStatus = await request('GET', '/api/pack/status', null, token1);
    assert(packStatus.body.version === 2, 'GET /pack/status returns version 2');
    assert(packStatus.body.wikiSectionCount === 1, 'GET /pack/status returns wikiSectionCount = 1');

    // ── AC 5: Tenant Isolation & Security ──────────────────────────────────────
    console.log('\n--- Step 6: Security & Cross-User Isolation ---');
    const authRes2 = await request('POST', '/api/auth/apple', {
      sub: 'apple-user-c107-002',
      email: 'user2@canis.local',
      givenName: 'Other',
      familyName: 'User'
    });
    const token2 = authRes2.body.token;

    // User 2 cannot list user 1's wiki sections
    const user2List = await request('GET', '/api/wiki/sections', null, token2);
    assert(user2List.body.length === 0, 'User 2 sees 0 wiki sections (isolation confirmed)');

    // User 2 cannot access user 1's wiki section by ID
    const user2Get = await request('GET', `/api/wiki/sections/${wiki1Id}`, null, token2);
    assert(user2Get.status === 404, 'User 2 GET user1 section returns 404');

    // User 2 cannot edit user 1's section
    const user2Patch = await request('PATCH', `/api/wiki/sections/${wiki1Id}`, { title: 'Hacked' }, token2);
    assert(user2Patch.status === 404, 'User 2 PATCH user1 section returns 404');

    // User 2 cannot delete user 1's section
    const user2Del = await request('DELETE', `/api/wiki/sections/${wiki1Id}`, null, token2);
    assert(user2Del.status === 404, 'User 2 DELETE user1 section returns 404');

    // ── AC 6: Web Console HTML Serving ─────────────────────────────────────────
    console.log('\n--- Step 7: Web Console HTML Rendering ---');
    const consoleRes = await request('GET', '/console?token=' + token1);
    assert(consoleRes.status === 200, 'GET /console returns HTTP 200');
    assert(consoleRes.text.includes('Canis Wiki'), 'Console HTML contains Canis branding');
    assert(consoleRes.text.includes('Rebuild Knowledge Pack'), 'Console HTML contains Rebuild button');
    assert(consoleRes.text.includes('Wiki Pages'), 'Console HTML contains Wiki Pages tab');

  } catch (err) {
    console.error('Unexpected error during test execution:', err);
    failed++;
  } finally {
    db.close();
    server.close();
    try { fs.rmSync(testTmpDir, { recursive: true, force: true }); } catch (_) {}
  }

  console.log(`\n=== Results ===\nPassed: ${passed}\nFailed: ${failed}\n`);
  if (failed > 0) {
    process.exit(1);
  }
}

run().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
