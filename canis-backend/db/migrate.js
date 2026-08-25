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

  console.log('[canis-migrate] schema applied to', resolvedPath);
  return db;
}

if (require.main === module) {
  migrate();
}

module.exports = { migrate, DB_PATH };
