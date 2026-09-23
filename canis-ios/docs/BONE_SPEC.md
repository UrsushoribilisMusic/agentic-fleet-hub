# BONE_SPEC — Canis / Sovereign Mind Chunking & Bone Schema

**Version**: 1.0  
**Status**: Living — update before CANIS-BONE-02 implementation begins  
**Gates**: CANIS-BONE-02 (on-device chunker), CANIS-BONE-03 (server-side ingestion)

This spec defines the contract that both the Canis on-device ingestion pipeline and the Sovereign Mind server-side ingestion pipeline must follow. A bone built in either place must produce an identical SQLite schema that `KnowledgePackRetriever.swift` can read without modification.

---

## 1. Supported Input Formats

| Format | Extension | Page tracking | Notes |
|---|---|---|---|
| PDF | `.pdf` | Yes — 1-based page number | Use PDFKit (iOS) / pdfminer or pdfplumber (server) |
| Plain text | `.txt` | No | UTF-8; treat the entire file as one page |
| Markdown | `.md` | No | UTF-8; headings are structural boundary hints |

Binary formats (DOCX, EPUB, HTML) are out of scope for v1. Strip null bytes (`\0`) and Private Use Area (PUA) Unicode before processing.

---

## 2. Token Budget

| Parameter | Value | Rationale |
|---|---|---|
| **Target window** | 400 tokens | Fits comfortably in MLX context; leaves headroom for prompt + overlap |
| **Overlap** | 60 tokens (~15%) | Preserves sentence context at split points |
| **Minimum chunk** | 50 tokens | Trailing remnants shorter than this are merged into the previous chunk |
| **Hard cap** | 512 tokens | A single chunk must never exceed this |

**Token estimation (on-device)**: No BPE tokenizer is available at ingestion time. Use `ceil(utf8_byte_count / 4)` as a conservative approximation. This slightly over-counts relative to actual subword tokens, which keeps chunks safely within budget.

**Token estimation (server-side)**: Use actual BPE tokenization (e.g., `tiktoken` with `cl100k_base` or the model's native tokenizer). The on-device approximation is allowed to differ by ±10% without requiring a re-chunk — differences larger than that require a re-sync of the bone.

---

## 3. Boundary Rules

Splitting is a two-stage process: **segment** then **pack**.

### Stage 1 — Pre-segmentation

Split the extracted text into *segments* using the following boundaries, in priority order:

1. **Markdown headings** (`^#{1,6} ` at line start) — each heading and its following body is one segment. A heading always starts a new segment; never split inside a heading's own line.
2. **Blank-line paragraphs** (`\n\n` or `\r\n\r\n`) — each paragraph is a segment.
3. **PDF page breaks** — treat a PDF form-feed or a new PDFPage boundary as a paragraph break if no structural heading is present.

After pre-segmentation the document is a flat ordered list of string segments.

### Stage 2 — Greedy packing into windows

```
window_tokens = 0
window_text   = ""
chunk_start_page = page_of_first_segment_in_window

for each segment S in segments:
    seg_tokens = estimate_tokens(S)

    if window_tokens + seg_tokens > 400 AND window_tokens >= 50:
        emit_chunk(window_text, chunk_start_page)
        # Rewind: carry the tail of the current window as overlap context
        overlap_text = tail_tokens(window_text, 60)
        window_text   = overlap_text + "\n\n" + S
        window_tokens = estimate_tokens(window_text)
        chunk_start_page = page_of(S)
    else:
        window_text   += ("\n\n" if window_text else "") + S
        window_tokens += seg_tokens

# Flush final window
if estimate_tokens(window_text) >= 50:
    emit_chunk(window_text, chunk_start_page)
elif window_text and chunks exist:
    append window_text to last chunk  # merge short tail
```

**Heading carry-forward**: If the split boundary falls immediately before or inside a heading segment, include the heading text at the start of the next window so the LLM always sees the section title that frames the chunk's content.

**Oversized single paragraph**: If a paragraph alone exceeds 512 tokens, split it at sentence boundaries (`. ` / `! ` / `? ` followed by a Unicode uppercase letter). As a last resort (no sentence boundary found within 512 tokens), hard-split at the 512-token byte position.

---

## 4. Source Page Tracking

| Input type | `source_page` value | Example |
|---|---|---|
| PDF | 1-based integer, stored as string | `"3"` |
| TXT / MD | Empty string | `""` |

Record the page where the chunk **begins**. If the chunk spans a page boundary, `source_page` is the page of the first byte of the chunk.

---

## 5. SQLite Schema Contract

The schema below is the **contract** that `KnowledgePackRetriever.loadSections()` reads. Do not rename columns or change types; the retriever uses raw column positions.

Reference SQL (from `Canis/Services/KnowledgePackRetriever.swift`):

```sql
SELECT
  w.id,
  w.doc_title,
  w.title,
  w.body,
  COALESCE((
    SELECT c.source_page
    FROM chunks c
    WHERE c.doc_id = w.doc_id
    ORDER BY c.chunk_index ASC
    LIMIT 1
  ), '') AS source_page
FROM wiki_sections w
ORDER BY w.doc_title ASC, w.section_index ASC
```

### 5.1 `wiki_sections` table

```sql
CREATE TABLE wiki_sections (
    id            TEXT    PRIMARY KEY,
    doc_id        TEXT    NOT NULL,
    doc_title     TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    body          TEXT    NOT NULL,
    section_index INTEGER NOT NULL,
    source        TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX idx_wiki_sections_doc ON wiki_sections (doc_id, section_index);
```

### 5.2 `chunks` table

```sql
CREATE TABLE chunks (
    chunk_index  INTEGER NOT NULL,
    doc_id       TEXT    NOT NULL,
    text         TEXT    NOT NULL,
    source_page  TEXT    NOT NULL DEFAULT '',
    PRIMARY KEY (doc_id, chunk_index)
);
```

### 5.3 Field Mapping for Auto-Ingested User Bones

For each chunk **N** produced from a file with display name **DISPLAY** and filename **FILENAME**:

| Field | Value |
|---|---|
| `chunks.doc_id` | UUID v4 — **unique per chunk** (see note below) |
| `chunks.chunk_index` | `N` (0-based, sequential within the source file) |
| `chunks.text` | Raw chunk text — verbatim, no summarisation |
| `chunks.source_page` | PDF page as string (1-based), or `""` for txt/md |
| `wiki_sections.id` | `"user-bone-" + chunks.doc_id` |
| `wiki_sections.doc_id` | Same UUID as `chunks.doc_id` |
| `wiki_sections.doc_title` | **DISPLAY** (file name without extension, e.g. `"Service Manual"`) |
| `wiki_sections.title` | `"<DISPLAY> §<N+1>"` — auto-generated; replaced during enrichment (CANIS-BONE-03) |
| `wiki_sections.body` | Same text as `chunks.text` |
| `wiki_sections.section_index` | `N` — same as `chunks.chunk_index` |
| `wiki_sections.source` | **FILENAME** (original file name, e.g. `"service-manual.pdf"`) |

> **Why `doc_id` is unique per chunk, not per document**
>
> The retriever's `source_page` subquery uses `WHERE c.doc_id = w.doc_id ORDER BY c.chunk_index ASC LIMIT 1`. If all chunks from one file shared the same `doc_id`, the subquery would always return the *first* chunk's page number for *every* wiki_section in that file — incorrect for mid-document sections. Giving each chunk a unique `doc_id` makes the join 1:1, so `source_page` is accurate for every section.
>
> Document-level grouping is still recoverable: all chunks from the same source file share the same `doc_title` and `wiki_sections.source` values.

---

## 6. Reproducibility & Losslessness

1. **Deterministic**: the same input bytes MUST produce the same chunk boundaries and UUIDs across runs on the same platform. Use a seeded PRNG keyed on `sha256(file_bytes + chunk_index)` to generate reproducible UUIDs rather than random UUIDs.
2. **Lossless**: concatenating all chunks in `chunk_index` order (deduplicating the 60-token overlapping tails) MUST reconstruct the full source text, modulo whitespace normalisation (collapsing runs of `\n` to `\n\n`, trimming leading/trailing whitespace).
3. **No generation**: chunk `text` and `body` are always verbatim extracts. No summarisation, paraphrasing, or LLM-generated content at ingestion time.

---

## 7. Pack-Level Metadata Table

```sql
CREATE TABLE IF NOT EXISTS pack_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Seed these rows on pack creation:

| key | value |
|---|---|
| `version` | `"1"` |
| `source_type` | `"user_bone"` |
| `bone_spec_version` | `"1.0"` |
| `created_at` | ISO 8601 timestamp, UTC (e.g. `"2026-09-23T13:04:00Z"`) |
| `doc_count` | Number of distinct source files ingested |
| `chunk_count` | Total number of chunks = total `wiki_sections` rows |

---

## 8. Implementation Checklist (for CANIS-BONE-02 and server-side)

- [ ] Extract text from PDF preserving page boundaries
- [ ] Extract text from TXT/MD as UTF-8, strip null bytes and PUA codepoints
- [ ] Pre-segment into heading / paragraph segments
- [ ] Greedy-pack segments into 400-token windows with 60-token overlap
- [ ] Merge trailing remnant < 50 tokens into the previous chunk
- [ ] Generate reproducible UUIDs per chunk (seeded on file hash + chunk index)
- [ ] Write one `chunks` row and one `wiki_sections` row per chunk
- [ ] Verify `doc_id` is unique per chunk (not shared across chunks from the same file)
- [ ] Verify `chunks.source_page` reflects the chunk's *start* page
- [ ] Write `pack_meta` rows
- [ ] Smoke-test with `KnowledgePackRetriever.retrieve(question:)` against a 3-file sample bone
