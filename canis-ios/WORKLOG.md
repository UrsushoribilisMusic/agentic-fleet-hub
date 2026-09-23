# WORKLOG — CANIS-BONE-03

## Task
Write `BoneBuilder.swift`: given `[BoneChunk]` + doc metadata, write a SQLite bone whose schema
exactly matches what `KnowledgePackRetriever.loadSections()` queries.

## Schema (from robot-ross-atf.sqlite reference)
- `meta (key TEXT PRIMARY KEY, value TEXT)`
- `chunks (id TEXT PK, doc_id, doc_title, text, source_page, chunk_index, chunk_type, tfidf_json)`
- `wiki_sections (id, doc_id, doc_title, title, body, section_index INTEGER DEFAULT 0)`
- Indexes: `idx_chunks_doc` on chunks(doc_id), `idx_wiki_doc` on wiki_sections(doc_id)

## ID conventions (from reference data)
- `chunks.id`:       `c-{docId}-s{N}` (N = chunk.index + 1, 1-based)
- `wiki_sections.id`: `{docId}-s{N}`

## Plan
1. `BoneBuilder.swift` in `Canis/Services/`
   - `func build(chunks:docTitle:sourceName:) throws -> URL`
   - sqlite3_open_v2 + WAL mode
   - createSchema() → DDL matching reference
   - insertMeta() → version/user_id/created_at/doc_count/chunk_count/wiki_count
   - insertChunks() → one row per BoneChunk
   - insertWikiSections() → one row per BoneChunk, title = "<DocTitle> - p.<N>"
   - wal_checkpoint(FULL) before returning URL
   - Uses sqlite3_prepare_v2 + sqlite3_bind_text for safe user-data binding

2. `CanisTests/BoneBuilderTests.swift`
   - Schema shape tests
   - Chunk count matches input
   - Retriever integration test (acceptance criterion)
   - Section title format
   - Reproducibility

## Key decisions
- source_page stored as String(chunk.sourcePage) (page number, e.g. "1", "3")
- docId derived: lowercased, whitespace→"-", filter to letter/number/dash
- SQLITE_TRANSIENT (unsafeBitCast) used so SQLite copies strings before bind_text returns
- outputURL written to temporaryDirectory; caller moves to Documents/knowledge-packs/
