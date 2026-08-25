'use strict';

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

const testTmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'canis-c106-test-'));
const testDbPath = path.join(testTmpDir, 'canis-test.db');
const testPacksDir = path.join(testTmpDir, 'packs');
const testUploadsDir = path.join(testTmpDir, 'uploads');

process.env.CANIS_DB_PATH = testDbPath;
process.env.CANIS_PACKS_DIR = testPacksDir;
process.env.CANIS_UPLOADS_DIR = testUploadsDir;
process.env.CANIS_WORKER_BATCH = '5';

fs.mkdirSync(testPacksDir, { recursive: true });
fs.mkdirSync(testUploadsDir, { recursive: true });

const { migrate } = require('../db/migrate');
const db = migrate(testDbPath);
const { buildRouter } = require('../api/router');
const { tick, processDocument } = require('../ingestion/worker');
const { setApnsTransportForTest } = require('../notifications/apns');

let server;
let baseUrl;
let pushAttempts = [];

function request(method, pathUrl, body = null, token = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(pathUrl, baseUrl);
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = 'Bearer ' + token;

    const req = http.request(url, { method, headers }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(data); } catch (_) {}
        resolve({ status: res.statusCode, body: json, text: data });
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function run() {
  console.log('=== WP1 C-106 Job Status & APNs Completion Push Test ===\n');

  setApnsTransportForTest(async (deviceToken, payload) => {
    pushAttempts.push({ deviceToken, payload });
    return { status: 'delivered' };
  });

  const app = express();
  app.use(express.json({ limit: '30mb' }));
  app.use('/api', buildRouter(db));
  app.use('/', buildRouter(db));

  await new Promise((resolve) => {
    server = app.listen(0, '127.0.0.1', () => {
      baseUrl = 'http://127.0.0.1:' + server.address().port;
      resolve();
    });
  });

  try {
    console.log('--- Step 1: Auth and APNs Registration ---');
    const authRes = await request('POST', '/api/auth/apple', {
      sub: 'apple-user-c106-001',
      email: 'user1@canis.local',
      givenName: 'Canis',
      familyName: 'Tester',
    });
    assert(authRes.status === 200, 'User authenticated');
    const token = authRes.body.token;
    const userId = authRes.body.user.id;

    const deviceToken = 'a'.repeat(64);
    const registerRes = await request('POST', '/api/devices/apns', { token: deviceToken }, token);
    assert(registerRes.status === 201, 'APNs token registration returned HTTP 201');
    assert(registerRes.body.enabled === true, 'Registered APNs token is enabled');

    console.log('\n--- Step 2: Upload and Visible Processing Status ---');
    const text = Array.from({ length: 240 }, (_, i) => 'canis privacy knowledge pack word' + i).join(' ');
    const uploadRes = await request('POST', '/api/documents', {
      filename: 'canis-notes.txt',
      content: Buffer.from(text, 'utf8').toString('base64'),
      mimeType: 'text/plain',
    }, token);
    assert(uploadRes.status === 201, 'Document upload returned HTTP 201');
    const docId = uploadRes.body.id;

    const initialStatus = await request('GET', `/api/documents/${docId}/status`, null, token);
    assert(initialStatus.body.status === 'pending', 'Initial document status is pending');
    assert(initialStatus.body.statusLabel === 'Queued', 'Initial document status has human label');

    console.log('\n--- Step 3: Worker Builds Pack and Sends Completion Push ---');
    await tick();

    const afterStatus = await request('GET', `/api/documents/${docId}/status`, null, token);
    assert(afterStatus.body.status === 'packed', 'Document status becomes packed');
    assert(afterStatus.body.errorReason === null, 'Successful document has no error reason');

    const jobsStatus = await request('GET', '/api/jobs/status', null, token);
    assert(jobsStatus.status === 200, 'GET /api/jobs/status returned HTTP 200');
    assert(jobsStatus.body.status === 'ready', 'Consolidated job status is ready');
    assert(jobsStatus.body.pack.version === 1, 'Pack v1 is visible in job status');
    assert(jobsStatus.body.documents[0].statusLabel === 'Ready', 'Packed document has readable status label');

    assert(pushAttempts.length === 1, 'One APNs push was attempted');
    assert(pushAttempts[0].payload.canis.event === 'pack_ready', 'Completion push event is pack_ready');
    assert(pushAttempts[0].payload.canis.packVersion === 1, 'Completion push includes pack version');

    const pushRows = db.prepare('SELECT * FROM canis_push_notifications').all();
    assert(pushRows.length === 1, 'Push attempt was recorded');
    assert(pushRows[0].status === 'delivered', 'Push audit status is delivered');

    console.log('\n--- Step 4: Failure Reason Is Human-Readable ---');
    const badDocId = uuidv4();
    const now = new Date().toISOString();
    db.prepare(`
      INSERT INTO canis_documents
        (id, user_id, filename, mime_type, file_path, status, created_at, updated_at)
      VALUES (?, ?, 'missing.txt', 'text/plain', ?, 'pending', ?, ?)
    `).run(badDocId, userId, path.join(testUploadsDir, 'missing.txt'), now, now);

    const badDoc = db.prepare('SELECT * FROM canis_documents WHERE id = ?').get(badDocId);
    const failedResult = await processDocument(badDoc, db);
    assert(failedResult.success === false, 'Missing file processing fails');

    const badStatus = await request('GET', `/api/documents/${badDocId}/status`, null, token);
    assert(badStatus.body.status === 'failed', 'Failed document status is failed');
    assert(badStatus.body.errorReason === 'The uploaded file could not be found. Please upload it again.',
      'Failure reason is human-readable');
    assert(!/Error:| at |ENOENT/.test(badStatus.body.errorReason), 'Failure reason is not a stack trace');

    assert(pushAttempts.length === 2, 'Failure push was attempted');
    assert(pushAttempts[1].payload.canis.event === 'processing_failed', 'Failure push event is processing_failed');

    const invalidToken = await request('POST', '/api/devices/apns', { token: 'not-a-token' }, token);
    assert(invalidToken.status === 400, 'Invalid APNs token rejected');

    console.log('\n=== Results ===');
    console.log('Passed:', passed);
    console.log('Failed:', failed);
    if (failed > 0) process.exitCode = 1;
  } finally {
    if (server) await new Promise((resolve) => server.close(resolve));
    setApnsTransportForTest(null);
    db.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
