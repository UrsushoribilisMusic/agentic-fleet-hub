# WORKLOG - #225: Fleet Hub — namespace GitHub issue identity in PocketBase tasks

**Task ID:** r8c8381ddac0886
**Agent:** codi
**Status:** peer_review

## Task Description
PocketBase currently keys GitHub-linked tasks by bare `gh_issue_id`, which collides across repositories because issue numbers are only unique inside a repo. Add `github_repo`, treat `(github_repo, gh_issue_id)` as the canonical external key, populate `github_issue_url`, and update sync/review tooling plus any persisted offset state that assumed a flat issue-number identity.

## Plan
- [x] Inspect the in-progress hub sync changes and identify broken code paths.
- [x] Update runtime sync scripts to populate `github_repo` / `github_issue_url` and to stop closing or deduping issues by bare number alone.
- [x] Update Mission Control sync so hub tasks backfill repo-scoped GitHub identity and ignore extra-repo tasks when reconciling the hub table.
- [x] Mirror the same identity changes into packaged script copies used for deployment/blueprint generation.
- [x] Verify syntax of every touched Python script with `python3 -m py_compile`.

## Notes
- Resumed this task from an existing dirty worktree on `master`, then moved the session onto branch `task/r8c8381ddac0886` before further edits.
- Preserved the previous `WORKLOG.md` content below because it pre-existed in the repo and may still be useful historical context.

# WORKLOG - PC-066 [P1]: Board focus mode — scoped daily note + Smart Spaces

**Task ID:** synu3lzco282zxf
**Agent:** misty
**Status:** in_progress

## Task Description
Boards with focusModeEnabled=true gain a Focus tab: board-scoped daily note (persists per board per day), Smart Spaces tagged with #boardname, quick capture button pre-selecting the board. Toggle via long-press → Settings. type=.list defaults true; type=.visual defaults false. Depends on PC-063.

## Plan

### Phase 1: Understand Dependencies (PC-063)
- [ ] Read PC-063 Unified Board model implementation
- [ ] Verify Board table structure and migration from PC-063
- [ ] Confirm BoardMember table schema

### Phase 2: Focus Mode Feature Implementation
- [ ] Add `focusModeEnabled` field to Board model (default: true for type=.list, false for type=.visual)
- [ ] Create Focus tab in Board detail view
- [ ] Implement board-scoped daily note system:
  - Persist per board per day (key: boardId + date)
  - Card type: daily-note with boardId field
  - Auto-create on first access
- [ ] Smart Spaces integration:
  - Filter Smart Spaces tagged with #boardname
  - Display in Focus tab
- [ ] Quick capture button:
  - Pre-select current board
  - Open Capture view with board pre-selected

### Phase 3: Toggle UI
- [ ] Long-press → Settings context menu
- [ ] Toggle for focusModeEnabled
- [ ] Persist setting to Board record

### Phase 4: Testing
- [ ] Test with type=.list board (should default to true)
- [ ] Test with type=.visual board (should default to false)
- [ ] Verify daily note persistence per board per day
- [ ] Verify quick capture pre-selects board
- [ ] Verify Smart Spaces filtering by #boardname

## Notes
- Handover ID: PC-037-C
- Depends on PC-063 (Unified Board model) - should already be complete
- Need to verify Board model in PrivateCore codebase

## Next Steps
1. Read PC-063 implementation in PrivateCore repo
2. Check Board model in ~/projects/private-core/PrivateCore/
3. Implement focusModeEnabled field addition
4. Build Focus tab UI components
