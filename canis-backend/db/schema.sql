-- CANIS Consumer Backend — canonical schema
-- Completely isolated from Sovereign Mind: no shared tables, no shared DB file.
-- Run via: node db/migrate.js

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── Users (Apple Sign In) ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS canis_users (
  id           TEXT PRIMARY KEY,
  apple_sub    TEXT NOT NULL UNIQUE,
  email        TEXT,
  display_name TEXT,
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- ── Sessions ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS canis_sessions (
  token      TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES canis_users (id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_canis_sessions_user    ON canis_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_canis_sessions_expires ON canis_sessions (expires_at);

-- ── Documents ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS canis_documents (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES canis_users (id) ON DELETE CASCADE,
  filename   TEXT NOT NULL,
  mime_type  TEXT NOT NULL DEFAULT 'application/octet-stream',
  file_path  TEXT NOT NULL DEFAULT '',
  page_count INTEGER NOT NULL DEFAULT 0,
  word_count INTEGER NOT NULL DEFAULT 0,
  -- Pipeline status: pending → extracting → chunked → wiki_ready → packed | failed
  status     TEXT NOT NULL DEFAULT 'pending'
             CHECK (status IN ('pending','extracting','chunked','wiki_ready','packed','failed')),
  error_msg  TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_canis_docs_user   ON canis_documents (user_id);
CREATE INDEX IF NOT EXISTS idx_canis_docs_status ON canis_documents (status);

-- ── Chunks ────────────────────────────────────────────────────────────────────
-- Text segments produced by the chunker. Also materialized into pack files.

CREATE TABLE IF NOT EXISTS canis_chunks (
  id          TEXT PRIMARY KEY,
  doc_id      TEXT NOT NULL REFERENCES canis_documents (id) ON DELETE CASCADE,
  text        TEXT NOT NULL,
  source_page TEXT NOT NULL DEFAULT '',
  chunk_index INTEGER NOT NULL DEFAULT 0,
  word_count  INTEGER NOT NULL DEFAULT 0,
  chunk_type  TEXT NOT NULL DEFAULT 'document_text',
  tfidf_json  TEXT NOT NULL DEFAULT '{}',
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_canis_chunks_doc ON canis_chunks (doc_id);

-- ── Wiki Sections ─────────────────────────────────────────────────────────────
-- LLM-generated structured summaries. One or more sections per document.

CREATE TABLE IF NOT EXISTS canis_wiki_sections (
  id            TEXT PRIMARY KEY,
  doc_id        TEXT NOT NULL REFERENCES canis_documents (id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  section_index INTEGER NOT NULL DEFAULT 0,
  chunk_ids     TEXT NOT NULL DEFAULT '[]',
  generated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_canis_wiki_doc ON canis_wiki_sections (doc_id);

-- ── Packs ─────────────────────────────────────────────────────────────────────
-- Versioned SQLite packs ready for iOS download.

CREATE TABLE IF NOT EXISTS canis_packs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id       TEXT    NOT NULL REFERENCES canis_users (id) ON DELETE CASCADE,
  version       INTEGER NOT NULL,
  pack_path     TEXT    NOT NULL,
  chunk_count   INTEGER NOT NULL DEFAULT 0,
  doc_count     INTEGER NOT NULL DEFAULT 0,
  wiki_count    INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  UNIQUE (user_id, version)
);

CREATE INDEX IF NOT EXISTS idx_canis_packs_user ON canis_packs (user_id);
