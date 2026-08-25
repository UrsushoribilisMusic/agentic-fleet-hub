'use strict';

const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

const DB_PATH = process.env.CANIS_DB_PATH
  || path.join(__dirname, '..', 'canis.db');

const SCHEMA_PATH = path.join(__dirname, 'schema.sql');

function migrate(dbPath) {
  const resolvedPath = dbPath || DB_PATH;
  const db = new Database(resolvedPath);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');

  const sql = fs.readFileSync(SCHEMA_PATH, 'utf8');
  db.exec(sql);

  // Older local databases may predate C-106. Keep these additive migrations
  // idempotent so schema.sql remains the canonical shape for fresh installs.
  db.exec(`
    CREATE TABLE IF NOT EXISTS canis_device_tokens (
      id          TEXT PRIMARY KEY,
      user_id     TEXT NOT NULL REFERENCES canis_users (id) ON DELETE CASCADE,
      token       TEXT NOT NULL,
      platform    TEXT NOT NULL DEFAULT 'ios' CHECK (platform IN ('ios')),
      enabled     INTEGER NOT NULL DEFAULT 1,
      created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
      updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
      UNIQUE (user_id, token)
    );

    CREATE INDEX IF NOT EXISTS idx_canis_device_tokens_user
      ON canis_device_tokens (user_id, enabled);

    CREATE TABLE IF NOT EXISTS canis_push_notifications (
      id             TEXT PRIMARY KEY,
      user_id        TEXT NOT NULL REFERENCES canis_users (id) ON DELETE CASCADE,
      device_token   TEXT NOT NULL,
      event_type     TEXT NOT NULL CHECK (event_type IN ('pack_ready','processing_failed')),
      title          TEXT NOT NULL,
      body           TEXT NOT NULL,
      status         TEXT NOT NULL CHECK (status IN ('delivered','skipped','failed')),
      failure_reason TEXT,
      created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );

    CREATE INDEX IF NOT EXISTS idx_canis_push_notifications_user
      ON canis_push_notifications (user_id, created_at);
  `);

  console.log('[canis-migrate] schema applied to', resolvedPath);
  return db;
}

if (require.main === module) {
  migrate();
}

module.exports = { migrate, DB_PATH };
