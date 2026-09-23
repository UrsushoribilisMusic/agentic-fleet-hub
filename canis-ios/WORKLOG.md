# CANIS-BONE-07 Worklog

## Goal
Expose title enrichment as a manual, user-initiated action. Import stays lightweight (no model load). Enrichment only runs on explicit user action with visible progress and cancellation.

## Plan

### 1. BoneIngestionManager.swift
- Add `@Published var enrichingBoneID: String?` — tracks which bone is currently being enriched (nil = none).
- Add `enrichBone(_ entry: BoneEntry, model: CanisModel)` — new public API that kicks off `BoneEnricher.shared.enrich(...)` for a specific bone, sets `enrichingBoneID` + `enrichmentProgress`, and cleans up when done or cancelled.
- Update `skipEnrichment()` to also clear `enrichingBoneID`.
- Update `cancel()` to also clear `enrichingBoneID`.
- No change to `ingest` signature or default; `enrichTitles: false` stays.

### 2. BoneListView.swift
- Add `@AppStorage("canis.activeModelID")` + `activeModel` to `BoneListView` (mirrors GiveABoneView).
- Add "Generate Titles" swipe action per row (hidden while that bone is already enriching).
- Pass enrichment state to `BoneRowView` as optional parameters.
- `BoneRowView` gets inline progress bar + Cancel button when enriching.

### 3. GiveABoneView.swift
- In the `.done(entry)` success state, add a "Generate Titles" button so users can opt-in immediately after import.
- Button hidden when enrichment for that bone is already running.
- Existing `enrichmentSection` shows progress (unchanged).

### Key decisions
- `enrichBone` replaces any running enrichment (cancel-then-start).
- `skipEnrichment()` / `cancel()` both clear `enrichingBoneID`.
- When "Done" is tapped while enriching from GiveABoneView, `reset()` cancels enrichment — user can re-trigger from BoneListView.
- BoneEnricher.swift: no changes needed (thermal + memory guards already in place).
