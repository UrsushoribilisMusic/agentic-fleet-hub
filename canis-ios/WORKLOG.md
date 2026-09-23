# CANIS-BONE-02 Worklog

Task: Add BoneChunker.swift — deterministic chunker (spec-matched, lossless, reproducible)

## Plan

1. Add `Canis/Services/BoneChunker.swift`
   - `BoneChunk` struct: `{index: Int, text: String, sourcePage: Int}` (0 = no page)
   - `BoneChunker.chunk(_ pages: [ExtractedPage]) -> [BoneChunk]`
   - Token estimate: `ceil(utf8_byte_count / 4)` (documented in code)
   - Pre-segment: split on `^#{1,6} ` headings and blank-line paragraphs per page
   - Expand oversized segments > 512 tokens at sentence boundaries; hard-split as last resort
   - Greedy pack: 400-token target, 60-token overlap (tail of previous window), 50-token min
   - Heading carry-forward: heading goes first in new window, then overlap
   - Merge trailing remnant < 50 tokens into previous chunk
   - Pure value algorithm: same input → byte-identical output (no random, no date)

2. Add `CanisTests/BoneChunkerTests.swift`
   - Determinism: run twice, compare byte-for-byte
   - Token bounds: all chunks within [50, 512] estimated tokens (except single-segment doc < 50)
   - Overlap: chunk[i+1] shares at least some content with end of chunk[i]
   - Losslessness: every pre-segment appears in at least one chunk
   - Source page carry: PDF pages produce non-zero sourcePage; txt/md produces 0
   - Edge cases: empty input, single short page, single very long paragraph

3. Build verify: `xcodegen generate && xcodebuild -scheme Canis -destination 'platform=iOS Simulator,name=iPhone 17' build`

## Status
- [ ] BoneChunker.swift
- [ ] BoneChunkerTests.swift
- [ ] BUILD SUCCEEDED
