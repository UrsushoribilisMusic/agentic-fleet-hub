# SM-004 Worklog

Task: RAG Index Generation Pipeline (`q72x5ftz5z4g9dx`)
Agent: codi

## Plan

1. Inspect the existing SM-002 backend schema and SM-003 console integration so the RAG pipeline uses current routes, storage layout, and status fields.
2. Add a backend index generator that ingests uploaded PDFs, extracts multi-page text, chunks into 512-1024 token windows, embeds locally with a deterministic fallback, serializes chunks/embeddings to a portable index, writes wiki and metadata files, and zips the package.
3. Wire an API trigger/status/download path into the existing web console backend and make failures visible in logs/admin-facing state.
4. Add focused tests for PDF ingestion/chunk retrieval and version distinctness.
5. Run the available test/build verifier, then commit, push, comment, and move the task to peer review.

## Key Decisions

- Prefer the existing project language/runtime and storage conventions over adding a separate service stack.
- Keep embedding local by default so the generated package is deterministic and does not require cloud credentials.
- Package format should remain easy for iOS to consume: SQLite index plus Markdown wiki plus JSON metadata in a zip.
