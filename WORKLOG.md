# WORKLOG — V05-PROFILE-006: Final v0.5.0 Release Prep

**Task ID**: qqivywhl6ehwd6w  
**Branch**: task/qqivywhl6ehwd6w  
**Agent**: Clau  
**Date**: 2026-05-17

---

## Objective

Write RELEASE_NOTES_v0.5.0.md and a final release checklist, confirming implemented features and documenting known limitations.

## Key Findings

### Dispatcher changes since v0.4.0
- v5 (8538352): parallel agent dispatch via non-blocking Popen; all agents run concurrently.
- v5 fix (3e5bdaa): corrected misty/gem AGENT_COMMANDS (bad CLI flags caused exit 2/55).
- v5 fix (43b126c): eliminated capture_output pipe deadlock; added 10MB log rotation.
- v6 (af3cf9a): agents must own their status transitions; dispatcher no longer auto-promotes exit-0 to peer_review.
- v7 (800d205): exit-0 → touch nothing; exit-nonzero → reset to todo; _reclaim_stale_tasks() every 10 cycles (2h+ stale in_progress with no live process → todo).
- timeout map (451b2b2): clau=1800s (30 min), others=1200s (20 min).
- MC→PB sync removed (451b2b2): PocketBase is authoritative for execution state; MC is human-readable overview only.

### GitHub sync fixes
- a2d491f: duplicate issue prevention; atomic inbound import; --state all (not open-only).
- b57907b: multi-repo inbound sync.

### Profile pack support
- V05-PROFILE-001 (approved): default-engineering profile pack at package/profiles/default-engineering/.
- V05-PROFILE-004 (approved): PROFILE_PACKS.md agent handoff spec written.

### V05 tasks NOT yet implemented (todo, assigned codi)
- V05-PROFILE-002: installer support for profile directory and zip overlay.
- V05-PROFILE-003: profile validator and safe overlay rules.
- V05-PROFILE-005: smoke tests for profile-pack install flow.

### Smoke check results (2026-05-17)
- PB health: PASS.
- Dispatcher process: NOT running (expected; managed by launchd per agent session).
- Heartbeat check (clau): PASS / exit-0 (action needed).
- Profile pack structure: PASS (all files present under package/profiles/default-engineering/).
- PROFILE_PACKS.md: PASS.
- package.json version: 0.4.0 — needs bump to 0.5.0 before npm publish.

## Steps

- [x] Orient, read MISSION_CONTROL.md, RULES.md, inbox, fetch task from PB
- [x] Create task branch task/qqivywhl6ehwd6w
- [x] Write WORKLOG.md
- [x] Audit dispatcher commits since v0.4.0
- [x] Verify profile pack artifacts
- [x] Run smoke checks
- [ ] Write RELEASE_NOTES_v0.5.0.md
- [ ] Update CHANGELOG.md
- [ ] Commit and push
- [ ] Post PB output comment + move to peer_review

---

# (Previous WORKLOG entry for V05-PROFILE-001 preserved below for reference)

# WORKLOG — V05-PROFILE-001: Create Default Engineering Instruction Profile

**Task ID**: 3z4r1bgw2prctog  
**Branch**: task/3z4r1bgw2prctog  
**Agent**: Clau  
**Date**: 2026-05-07

---

## Objective

Complete the `package/profiles/default-engineering/` profile pack so a new Flotilla install can bootstrap from it without any Miguel-specific paths or private project details.

## Current State (analysis at session start)

The profile directory already exists with most scaffolding from prior sessions (V05-PROFILE-004 wrote PROFILE_PACKS.md). Key gaps identified:

1. **`AGENTS/RULES.md` in the profile is under-specified** — the source `AGENTS/RULES.md` has evolved significantly with important protocols (Task Branch Protocol, Code Review Protocol, Build Verifier obligation, standup index.json rule, No Manual MC Edits, Branch Hygiene) that the profile version is missing.
2. **`AGENTS/CONFIG/growth_meta.json` is missing** — exists in the source already sanitized with `{{MAIN_REPO}}` placeholders; should be included in the profile as an optional marketing/growth fleet preset.
3. **`AGENTS/CONTEXT/pocketbase_schema.md` is missing** — the PocketBase collections schema is essential for any new install to configure the data layer.

No private paths found in existing profile files except `localhost:8090` in `fleet_settings.json` (acceptable — this is PocketBase's standard default port).

## Plan

1. **Update `AGENTS/RULES.md`** — extract all enriched protocols from source, sanitize:
   - Replace `/Users/miguelrodriguez/...` → `{{REPO_PATH}}`
   - Replace specific API URLs → `{{FLEET_API_URL}}`
   - Replace `master` → `{{DEFAULT_BRANCH}}`
   - Remove PrivateCore-specific code review paths → generic
   - Remove `@miguel` → `@coordinator`
   - Remove specific script paths → generic fleet/ references
   - Add: Code Review Protocol, Task Branch Protocol, No Self-Approval detail, Branch Hygiene, standup index.json rule, No Manual MC Edits, Build Verifier obligation

2. **Add `growth_meta.json`** — copy from source (already has placeholders), add to profile CONFIG

3. **Add `pocketbase_schema.md`** — distill PocketBase schema from flotilla_arxiv_spec.md into a clean context file

4. **Update `README.md`** — document the two new files

## Key Decisions

- Keep `localhost:8090` as the default `api_base_url` in `fleet_settings.json` — it is the standard PocketBase default, not a private path.
- Do NOT include `qwen_coder_runtime.md` — specific to local Ollama setup.
- Do NOT include project-specific CONTEXT files (music_video_tool.md, privatecore_ios.md, etc.) — private project details.
- Include `fleet_steering_architecture.md` and `kanban_format_spec.md` — already in profile, genuinely reusable.

## Steps

- [x] Create task branch
- [x] Write WORKLOG.md
- [ ] Update AGENTS/RULES.md
- [ ] Add growth_meta.json
- [ ] Add pocketbase_schema.md
- [ ] Update README.md
- [ ] Commit and push
