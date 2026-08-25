'use strict';

const crypto = require('crypto');
const http2 = require('http2');
const { v4: uuidv4 } = require('uuid');

const APNS_TOPIC = process.env.CANIS_APNS_TOPIC || '';
const APNS_KEY_ID = process.env.CANIS_APNS_KEY_ID || '';
const APNS_TEAM_ID = process.env.CANIS_APNS_TEAM_ID || '';
const APNS_PRIVATE_KEY = (process.env.CANIS_APNS_PRIVATE_KEY || '').replace(/\\n/g, '\n');
const APNS_ENV = process.env.CANIS_APNS_ENV || 'sandbox';

let transportOverride = null;

function setApnsTransportForTest(transport) {
  transportOverride = transport;
}

function base64url(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function apnsConfigured() {
  return Boolean(APNS_TOPIC && APNS_KEY_ID && APNS_TEAM_ID && APNS_PRIVATE_KEY);
}

function makeProviderToken() {
  const header = base64url(JSON.stringify({ alg: 'ES256', kid: APNS_KEY_ID }));
  const claims = base64url(JSON.stringify({ iss: APNS_TEAM_ID, iat: Math.floor(Date.now() / 1000) }));
  const signingInput = header + '.' + claims;
  const signature = crypto.sign('sha256', Buffer.from(signingInput), {
    key: APNS_PRIVATE_KEY,
    dsaEncoding: 'ieee-p1363',
  });
  return signingInput + '.' + base64url(signature);
}

function sendApns(deviceToken, payload) {
  if (transportOverride) return transportOverride(deviceToken, payload);

  if (!apnsConfigured()) {
    return Promise.resolve({
      status: 'skipped',
      reason: 'APNs credentials are not configured',
    });
  }

  const host = APNS_ENV === 'production'
    ? 'https://api.push.apple.com'
    : 'https://api.sandbox.push.apple.com';

  return new Promise((resolve) => {
    const client = http2.connect(host);
    const body = JSON.stringify(payload);
    const req = client.request({
      ':method': 'POST',
      ':path': '/3/device/' + deviceToken,
      authorization: 'bearer ' + makeProviderToken(),
      'apns-topic': APNS_TOPIC,
      'apns-push-type': 'alert',
      'content-type': 'application/json',
      'content-length': Buffer.byteLength(body),
    });

    let statusCode = 0;
    let responseBody = '';

    req.setEncoding('utf8');
    req.on('response', (headers) => {
      statusCode = Number(headers[':status'] || 0);
    });
    req.on('data', (chunk) => {
      responseBody += chunk;
    });
    req.on('end', () => {
      client.close();
      if (statusCode >= 200 && statusCode < 300) {
        resolve({ status: 'delivered' });
        return;
      }
      let reason = 'APNs rejected the notification';
      try {
        const parsed = JSON.parse(responseBody);
        if (parsed && parsed.reason) reason = 'APNs rejected the notification: ' + parsed.reason;
      } catch (_) {}
      resolve({ status: 'failed', reason });
    });
    req.on('error', (err) => {
      client.close();
      resolve({ status: 'failed', reason: humanizePushError(err) });
    });
    client.on('error', (err) => {
      resolve({ status: 'failed', reason: humanizePushError(err) });
    });

    req.end(body);
  });
}

function humanizePushError(err) {
  const msg = err && err.message ? String(err.message) : '';
  if (msg.includes('ENOTFOUND') || msg.includes('EAI_AGAIN')) {
    return 'Could not reach APNs. Check network connectivity.';
  }
  if (msg.includes('certificate') || msg.includes('PEM')) {
    return 'APNs signing key is invalid.';
  }
  return 'APNs delivery failed.';
}

function notificationPayload(eventType, data) {
  if (eventType === 'processing_failed') {
    return {
      title: 'Canis could not process your document',
      body: data.reason || 'Please check the document and try again.',
      aps: {
        alert: {
          title: 'Canis could not process your document',
          body: data.reason || 'Please check the document and try again.',
        },
        sound: 'default',
      },
      canis: {
        event: eventType,
        documentId: data.documentId || '',
      },
    };
  }

  return {
    title: 'Your Canis knowledge pack is ready',
    body: 'Version ' + data.version + ' is ready to download for offline use.',
    aps: {
      alert: {
        title: 'Your Canis knowledge pack is ready',
        body: 'Version ' + data.version + ' is ready to download for offline use.',
      },
      sound: 'default',
    },
    canis: {
      event: eventType,
      packVersion: data.version,
    },
  };
}

async function notifyUser(db, userId, eventType, data) {
  const devices = db.prepare(`
    SELECT token FROM canis_device_tokens
    WHERE user_id = ? AND enabled = 1
    ORDER BY updated_at DESC
  `).all(userId);

  if (devices.length === 0) return [];

  const payload = notificationPayload(eventType, data);
  const now = new Date().toISOString();
  const insert = db.prepare(`
    INSERT INTO canis_push_notifications
      (id, user_id, device_token, event_type, title, body, status, failure_reason, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const attempts = [];
  for (const device of devices) {
    const result = await sendApns(device.token, payload);
    const status = ['delivered', 'skipped', 'failed'].includes(result.status)
      ? result.status
      : 'failed';
    const reason = result.reason || null;
    insert.run(uuidv4(), userId, device.token, eventType, payload.title, payload.body, status, reason, now);
    attempts.push({ token: device.token, status, reason });
  }
  return attempts;
}

function registerDeviceToken(db, userId, token) {
  const clean = String(token || '').trim();
  if (!/^[0-9a-fA-F]{32,}$/.test(clean)) {
    const err = new Error('APNs device token is invalid');
    err.statusCode = 400;
    throw err;
  }

  const now = new Date().toISOString();
  db.prepare(`
    INSERT INTO canis_device_tokens (id, user_id, token, platform, enabled, created_at, updated_at)
    VALUES (?, ?, ?, 'ios', 1, ?, ?)
    ON CONFLICT(user_id, token) DO UPDATE SET enabled = 1, updated_at = excluded.updated_at
  `).run(uuidv4(), userId, clean, now, now);

  return { token: clean, platform: 'ios', enabled: true, updatedAt: now };
}

module.exports = {
  notifyUser,
  registerDeviceToken,
  setApnsTransportForTest,
};
