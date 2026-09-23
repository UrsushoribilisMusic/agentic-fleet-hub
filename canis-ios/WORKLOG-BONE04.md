# WORKLOG — CANIS-BONE-04

## Task
Background model enrichment pass: generate a short (≤6 word) title per chunk using the
on-device MLX model and write it back to `wiki_sections.title` in the bone SQLite.

## Plan

1. Add `generateTitle(from:model:) async throws -> String` to `CanisMLXEngine`
   - Reuses existing thermal/battery guards
   - Temperature 0.3 (deterministic), maxTokens 20
   - Does NOT set `currentTask` (avoids interfering with chat cancellation)
   - Stops streaming at first newline or 6+ words collected

2. Write `Canis/Services/BoneEnricher.swift`
   - Actor `BoneEnricher` with `static let shared`
   - `enrich(boneURL:model:onProgress:) async` — runs the full enrichment pass
   - `cancel()` — cancels the running task
   - `isRunning: Bool` — observable state
   - Opens the bone SQLite READWRITE, reads all wiki_sections, generates title per row,
     updates wiki_sections.title in-place
   - Checks `Task.isCancelled` between each row
   - Reports progress via `onProgress(completedCount, totalCount)`
   - Gracefully handles backgroundExecution + thermal errors (stops quietly)

3. Write `CanisTests/BoneEnricherTests.swift`
   - Unit tests with a real SQLite bone (no MLX needed)
   - Tests: enrichment writes non-default titles, progress reported correctly,
     cancel stops early, respects Task cancellation, handles empty bone

## Key decisions
- Enrichment does NOT need the app foregrounded for SQLite reads/writes, only for MLX.
  The `generateTitle` method checks `UIApplication.shared.applicationState` itself.
- No new dependencies (SQLite3 C API only, same as BoneBuilder).
- `BoneEnricher` is entirely responsible for its own Task lifecycle. ChatViewModel
  calls `BoneEnricher.shared.cancel()` when the user starts a chat, if desired (optional wire-up).
- Default titles ("DocTitle - p.N") remain until enrichment completes that row.
