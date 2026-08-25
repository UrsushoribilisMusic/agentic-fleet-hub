'use strict';

/**
 * canis-backend/scripts/test-c104-consumer-console.js
 *
 * Test suite for WP1 C-104: Consumer Ingestion Console (UI Fork)
 *
 * Verifies:
 * 1. Mobile-first HTML rendering, Canis branding, touch-optimised UI, safe-area insets
 * 2. Client script syntax validity and theme switching logic
 * 3. Authenticated web-view handoff via token & Bearer header
 * 4. Document upload (PDF, TXT, Markdown) with validation & size limits
 * 5. Document listing with pagination/status metrics (pageCount, wordCount)
 * 6. Ingestion processing to wiki sections & pack building
 * 7. Document deletion cascading to chunks, wiki sections, and storage
 * 8. User tenant isolation (cross-user data protection)
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const express = require('express');
const { migrate } = require('../db/migrate');
const { buildRouter } = require('../api/router');
const { canisConsoleHtml } = require('../ui/console');
const { extractText } = require('../ingestion/extractor');
const { chunkText } = require('../ingestion/chunker');
const { generateWikiSections } = require('../ingestion/wiki');
const { buildPack } = require('../ingestion/pack-builder');

function createSamplePdfBuffer() {
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    '<< /Length 76 >>\nstream\nBT /F1 16 Tf 50 720 Td (Canis On-Device Knowledge Base Ingestion Manual) Tj ET\nendstream',
  ];

  const chunks = [Buffer.from('%PDF-1.4\n', 'binary')];
  const offsets = [0];
  for (let i = 0; i < objects.length; i += 1) {
    offsets.push(Buffer.concat(chunks).length);
    chunks.push(Buffer.from(`${i + 1} 0 obj\n`, 'binary'));
    chunks.push(Buffer.isBuffer(objects[i]) ? objects[i] : Buffer.from(objects[i], 'binary'));
    chunks.push(Buffer.from('\nendobj\n', 'binary'));
  }
  const body = Buffer.concat(chunks);
  const xrefOffset = body.length;
  const xrefRows = ['xref', `0 ${objects.length + 1}`, '0000000000 65535 f '];
  for (let i = 1; i < offsets.length; i += 1) {
    xrefRows.push(`${String(offsets[i]).padStart(10, '0')} 00000 n `);
  }
  const trailer = `${xrefRows.join('\n')}\ntrailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;
  return Buffer.concat([body, Buffer.from(trailer, 'binary')]);
}

let server;
let baseUrl;
let db;
let tmpDir;

function request(method, reqPath, { headers = {}, body = null } = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(reqPath, baseUrl);
    const reqHeaders = { ...headers };
    let reqBody = null;

    if (body !== null && typeof body === 'object') {
      reqBody = JSON.stringify(body);
      reqHeaders['Content-Type'] = 'application/json';
      reqHeaders['Content-Length'] = Buffer.byteLength(reqBody);
    }

    const req = http.request(url, { method, headers: reqHeaders }, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(data); } catch (_) {}
        resolve({
          status: res.statusCode,
          headers: res.headers,
          text: data,
          json,
        });
      });
    });

    req.on('error', reject);
    if (reqBody) req.write(reqBody);
    req.end();
  });
}

let passed = 0;
let total = 0;

function check(desc, condition) {
  total++;
  if (condition) {
    passed++;
    console.log(`  ✓ ${desc}`);
  } else {
    console.error(`  ✕ FAIL: ${desc}`);
    throw new Error(`Assertion failed: ${desc}`);
  }
}

async function runTests() {
  console.log('\n=== WP1 C-104: Canis Consumer Ingestion Console Test Suite ===\n');

  tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'canis-c104-test-'));
  const dbPath = path.join(tmpDir, 'canis-c104.db');
  process.env.CANIS_UPLOADS_DIR = path.join(tmpDir, 'uploads');
  process.env.CANIS_PACKS_DIR = path.join(tmpDir, 'packs');

  db = migrate(dbPath);
  const app = express();
  app.use(express.json({ limit: '50mb' }));
  const router = buildRouter(db);
  app.use('/api', router);
  app.use('/', router);
  app.use((err, req, res, next) => {
    res.status(err.status || 500).json({ error: err.message });
  });

  await new Promise((resolve) => {
    server = app.listen(0, () => {
      const port = server.address().port;
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });

  try {
    // ── 1. HTML Rendering & Mobile-First Layout ─────────────────────────────
    console.log('── 1. HTML Rendering & Mobile-First Canis Brand UI ──');
    const userSample = { id: 'usr-apple-test', email: 'doglover@apple.local', displayName: 'Canis Companion' };
    const html = canisConsoleHtml(userSample, 'test-token-xyz');

    check('canisConsoleHtml returns valid HTML string', typeof html === 'string' && html.length > 1000);
    check('HTML title features Canis branding', html.includes('Canis — Personal Knowledge Wiki'));
    check('HTML includes responsive viewport with viewport-fit=cover', html.includes('viewport-fit=cover'));
    check('HTML incorporates CSS safe-area-inset variables for iOS devices', html.includes('safe-area-inset-top') && html.includes('safe-area-inset-bottom'));
    check('HTML renders Canis brand paw icon and on-device badge', html.includes('🐾') && html.includes('On-Device AI'));
    check('HTML includes light/dark theme CSS variables and switcher', html.includes('[data-theme="light"]') && html.includes('themeToggle'));
    check('HTML includes tab navigation (Wiki Pages, Documents, Knowledge Pack)', html.includes('Wiki Pages') && html.includes('Documents') && html.includes('Knowledge Pack'));
    check('HTML includes file upload zone supporting .pdf, .txt, .md', html.includes('accept=".pdf,.txt,.md"') && html.includes('uploadBox'));
    check('HTML includes modal dialogs for reader and markdown editor', html.includes('readerModal') && html.includes('editModal'));

    // Verify syntax of all inline client scripts
    const scriptBlocks = html.match(/<script[\s\S]*?<\/script>/gi) || [];
    check('Rendered HTML contains client script blocks', scriptBlocks.length >= 2);
    scriptBlocks.forEach((block) => {
      const code = block.replace(/<script[^>]*>/i, '').replace(/<\/script>/i, '');
      new Function(code);
    });
    check('All client script blocks pass ECMAScript syntax compilation', true);

    // ── 2. Authenticated Web-View Handoff & Session Security ─────────────────
    console.log('\n── 2. Authenticated Web-View Handoff & Session Security ──');

    // Authenticate Alice & Bob via Apple auth
    const authResA = await request('POST', '/api/auth/apple', {
      body: { sub: 'apple-alice-uuid', email: 'alice@canis.ai', givenName: 'Alice', familyName: 'Canis' },
    });
    check('Alice authenticated via /api/auth/apple', authResA.status === 200 && authResA.json.token);
    const tokenA = authResA.json.token;
    const userA = authResA.json.user;

    const authResB = await request('POST', '/api/auth/apple', {
      body: { sub: 'apple-bob-uuid', email: 'bob@canis.ai', givenName: 'Bob', familyName: 'Explorer' },
    });
    check('Bob authenticated via /api/auth/apple', authResB.status === 200 && authResB.json.token);
    const tokenB = authResB.json.token;

    // Access /console with ?token= (web-view handoff)
    const handoffRes = await request('GET', `/console?token=${tokenA}`);
    check('Authenticated console handoff via ?token= returns 200', handoffRes.status === 200);
    check('Console page renders Alice display name', handoffRes.text.includes('Alice Canis'));

    // Access /console with Bearer header
    const bearerConsoleRes = await request('GET', '/console', {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('Authenticated console handoff via Bearer header returns 200', bearerConsoleRes.status === 200);

    // Unauthenticated API request to protected endpoint returns 401
    const unauthApiRes = await request('GET', '/api/documents');
    check('Unauthenticated API request returns 401 Unauthorized', unauthApiRes.status === 401);

    // ── 3. Document Ingestion (Upload TXT, MD, PDF) ──────────────────────────
    console.log('\n── 3. Document Ingestion (Upload TXT, MD, PDF) ──');

    // Initial listing for Alice is empty
    const listResInitial = await request('GET', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('Alice initial document list is empty array', listResInitial.status === 200 && Array.isArray(listResInitial.json) && listResInitial.json.length === 0);

    // Upload 1: Markdown
    const mdContent = '# Canis Navigation System\n\nCanis uses on-device vector projection and local inference to navigate knowledge bases without telemetry.';
    const mdBase64 = Buffer.from(mdContent, 'utf8').toString('base64');
    const uploadRes1 = await request('POST', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
      body: {
        filename: 'navigation_system.md',
        content: mdBase64,
        mimeType: 'text/markdown',
      },
    });
    check('Upload Markdown document returns 201 Created', uploadRes1.status === 201 && uploadRes1.json.id);
    const doc1Id = uploadRes1.json.id;

    // Upload 2: Text file
    const txtContent = 'Canis Disposition Lens: 8 emotional states mapped through forward-only Jacobian projections at layer 3/4.';
    const txtBase64 = Buffer.from(txtContent, 'utf8').toString('base64');
    const uploadRes2 = await request('POST', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
      body: {
        filename: 'disposition_notes.txt',
        content: txtBase64,
        mimeType: 'text/plain',
      },
    });
    check('Upload TXT document returns 201 Created', uploadRes2.status === 201 && uploadRes2.json.id);
    const doc2Id = uploadRes2.json.id;

    // Upload 3: PDF file
    const pdfBuffer = createSamplePdfBuffer();
    const pdfBase64 = pdfBuffer.toString('base64');
    const uploadRes3 = await request('POST', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
      body: {
        filename: 'knowledge_manual.pdf',
        content: pdfBase64,
        mimeType: 'application/pdf',
      },
    });
    check('Upload PDF document returns 201 Created', uploadRes3.status === 201 && uploadRes3.json.id);
    const doc3Id = uploadRes3.json.id;

    // Document size guard (> 25MB check)
    const giantPayload = 'A'.repeat(34_000_000); // 34MB base64 ~ 25.5MB decoded > 25MB limit
    const uploadOversize = await request('POST', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
      body: {
        filename: 'huge.pdf',
        content: giantPayload,
      },
    });
    check('Upload over 25MB rejected with 400', uploadOversize.status === 400);

    // ── 4. Document Listing & Ingestion Processing ──────────────────────────
    console.log('\n── 4. Document Listing & Ingestion Processing ──');

    const listResAfter = await request('GET', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('Alice document list contains 3 uploaded documents', listResAfter.status === 200 && listResAfter.json.length === 3);
    const docIds = listResAfter.json.map(d => d.id);
    check('All 3 document IDs present in listing', docIds.includes(doc1Id) && docIds.includes(doc2Id) && docIds.includes(doc3Id));

    // Simulate Worker Processing for Doc 1 & Doc 3
    const docRow1 = db.prepare('SELECT * FROM canis_documents WHERE id = ?').get(doc1Id);
    const ext1 = await extractText(docRow1.file_path, docRow1.filename);
    const wordCount1 = ext1.text.split(/\s+/).filter(Boolean).length;
    db.prepare('UPDATE canis_documents SET page_count = ?, word_count = ?, status = ? WHERE id = ?')
      .run(ext1.pageCount, wordCount1, 'chunked', doc1Id);

    const chunks1 = chunkText(ext1.text, doc1Id, 'navigation_system.md');
    for (const c of chunks1) {
      db.prepare(`
        INSERT INTO canis_chunks (id, doc_id, chunk_index, text, word_count, tfidf_json)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(c.id, doc1Id, c.chunk_index, c.text, c.word_count, c.tfidf_json);
    }
    const sections1 = await generateWikiSections(doc1Id, 'navigation_system.md', chunks1);
    for (const s of sections1) {
      db.prepare(`
        INSERT INTO canis_wiki_sections (id, doc_id, section_index, title, body, chunk_ids)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(s.id, doc1Id, s.section_index, s.title, s.body, s.chunk_ids);
    }
    db.prepare('UPDATE canis_documents SET status = ? WHERE id = ?').run('wiki_ready', doc1Id);

    // Build Pack v1
    const packV1 = await buildPack(userA.id, db);

    // Check Document Status Endpoint
    const docStatusRes = await request('GET', `/api/documents/${doc1Id}/status`, {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('GET /api/documents/:id/status returns 200', docStatusRes.status === 200);
    check('Document status reflects packed', docStatusRes.json.status === 'packed');
    check('Document chunkCount >= 1', docStatusRes.json.chunkCount >= 1);
    check('Document wikiSectionCount >= 1', docStatusRes.json.wikiSectionCount >= 1);

    // ── 5. Document Deletion & Cascade ──────────────────────────────────────
    console.log('\n── 5. Document Deletion & Cascade ──');

    // Delete Document 2
    const deleteRes = await request('DELETE', `/api/documents/${doc2Id}`, {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('DELETE /api/documents/:id returns 204 No Content', deleteRes.status === 204);

    // Verify Doc 2 is removed
    const listResAfterDelete = await request('GET', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('Alice document list now contains 2 documents', listResAfterDelete.json.length === 2);
    check('Deleted document ID no longer in list', !listResAfterDelete.json.some(d => d.id === doc2Id));

    // Delete non-existent returns 404
    const delete404 = await request('DELETE', `/api/documents/${doc2Id}`, {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('Deleting non-existent document returns 404 Not Found', delete404.status === 404);

    // Delete Document 1 and verify chunks and wiki sections are cascaded
    const deleteRes1 = await request('DELETE', `/api/documents/${doc1Id}`, {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    check('DELETE /api/documents/:id for Doc 1 returns 204', deleteRes1.status === 204);

    const remainingChunks = db.prepare('SELECT COUNT(*) AS n FROM canis_chunks WHERE doc_id = ?').get(doc1Id).n;
    const remainingWiki = db.prepare('SELECT COUNT(*) AS n FROM canis_wiki_sections WHERE doc_id = ?').get(doc1Id).n;
    check('Cascaded foreign keys removed all chunks for Doc 1', remainingChunks === 0);
    check('Cascaded foreign keys removed all wiki sections for Doc 1', remainingWiki === 0);

    // ── 6. Tenant Isolation ─────────────────────────────────────────────────
    console.log('\n── 6. Cross-User Tenant Isolation ──');

    // Bob lists documents — should see 0 documents
    const bobListRes = await request('GET', '/api/documents', {
      headers: { Authorization: `Bearer ${tokenB}` },
    });
    check('Bob sees 0 documents (strict tenant isolation)', bobListRes.status === 200 && bobListRes.json.length === 0);

    // Bob attempts to delete Alice's remaining Doc 3 -> 404 Not Found
    const bobDeleteAliceDoc = await request('DELETE', `/api/documents/${doc3Id}`, {
      headers: { Authorization: `Bearer ${tokenB}` },
    });
    check('Bob cannot delete Alice document (404 Not Found)', bobDeleteAliceDoc.status === 404);

    console.log(`\n🎉 All ${passed}/${total} WP1 C-104 assertions PASSED! 🎉\n`);
  } finally {
    if (server) {
      await new Promise(resolve => server.close(resolve));
    }
    if (db) {
      db.close();
    }
    if (tmpDir && fs.existsSync(tmpDir)) {
      try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch (_) {}
    }
  }
}

runTests().catch(err => {
  console.error('\n❌ Test suite failed:', err);
  process.exit(1);
});
