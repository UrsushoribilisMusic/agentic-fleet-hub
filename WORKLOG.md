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
