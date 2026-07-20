# SM-305 Worklog

Task: SM-305 S5 - Sovereign Mind ingestion pipeline.

Plan:
- Inspect the existing Sovereign Mind backend and web assets.
- Add a backend ingestion pipeline for PDF/DOCX/TXT text extraction, 256-512 token chunking, capped chunks, 384-dimensional embeddings, FAISS-compatible index metadata, wiki generation, and versioned collection artefacts.
- Persist explicit per-document progress and failure states so one bad document does not fail the whole batch.
- Add tests that exercise successful ingestion, per-document failure reporting, max chunk enforcement, and queryable collection output.
- Update standup/progress and PocketBase status after verification.

Decisions:
- D1/OCR: implement text-layer extraction only for PDF/DOCX in this ticket and mark scanned/no-text PDFs with per-document `needs_ocr` failure state. OCR can be attached later without changing artefact schema.
- D4/embeddings: use deterministic local 384-dimensional hashed embeddings for the backend artifact path so tests and demo ingest are dependency-free. The artifact records `embedding_dim: 384` and can be swapped to a selected production model behind the same interface.
