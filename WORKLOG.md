# WORKLOG — V05-PROFILE-002: Add Installer Support for Profile Directory and Zip Overlay

**Task ID**: fwxfhcprzb6g2oc
**Branch**: task/fwxfhcprzb6g2oc requested; branch creation blocked by `.git` write permissions
**Agent**: Codi
**Date**: 2026-05-17

---

## Objective

Allow `create-flotilla` installation/bootstrap to select an instruction profile pack from a local directory or local zip archive, while falling back to the built-in default profile.

## Plan

1. Add CLI flags for `--profile-dir <path>` and `--profile-zip <path>`.
2. Resolve and validate the selected profile before creating the target install directory.
3. Overlay profile files only into the intended instruction/config destinations.
4. Print clear installer output naming the selected profile and overlay result.
5. Document CLI help and installer docs for default, directory, and zip profile usage.
6. Verify with dry-run and smoke coverage.

## Results

- Updated `package/bin/create-flotilla.mjs` with profile argument parsing, mutual-exclusion checks, default profile fallback, zip extraction, profile overlay, and user-facing installer output.
- Reused `package/lib/profile-validator.mjs` for required file checks, safe relative paths, JSON parsing, symlink rejection, zip entry traversal checks, and allowed overlay destinations.
- Updated `package/tools/verify-dry-run.mjs` to exercise default, directory, zip, skipped unsafe paths, invalid profile path, missing required files, invalid JSON, symlink rejection, and zip traversal rejection.
- Updated `package/INSTALL.md`, `package/README.md`, and `package/PROFILE_PACKS.md` with the new CLI flags and safe overlay behavior.

## Verification

- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/bin/create-flotilla.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/lib/profile-validator.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/tools/verify-dry-run.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/tools/smoke-profile-install.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node package/bin/create-flotilla.mjs --help`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin npm --prefix package run verify:dry-run`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin npm --prefix package run smoke:profile-install`

## Blockers

- PocketBase unavailable on `localhost:8090`; could not post heartbeat, output comment, or move task to `peer_review`.
- Git metadata writes blocked; could not pull, create the task branch, commit, or push.

---

# WORKLOG — V05-PROFILE-003: Add Profile Validator and Safe Overlay Rules

**Task ID**: j5hbqnn05s7niwv
**Branch**: task/j5hbqnn05s7niwv requested; branch creation blocked by `.git` write permissions
**Agent**: Codi
**Date**: 2026-05-17

---

## Objective

Prevent malformed or unsafe profile packs from damaging the generated install layout.

## Plan

1. Add a reusable profile validator module with required files, optional files, safe path rules, JSON parsing, symlink rejection, and zip entry traversal checks.
2. Wire `create-flotilla` so validation runs before target install writes begin.
3. Add profile fixtures and dry-run assertions for valid/default, missing required, invalid JSON, path escape, and extension-area behavior.
4. Document the strict overlay rules in `PROFILE_PACKS.md`.

## Results

- Added `package/lib/profile-validator.mjs`.
- Updated `package/bin/create-flotilla.mjs` to call validation before scaffold writes and before zip extraction.
- Added fixtures under `package/test-fixtures/profiles/`.
- Extended `package/tools/verify-dry-run.mjs`.
- Updated `package/PROFILE_PACKS.md` and package file allowlist.

## Verification

- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin npm run verify:dry-run`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/lib/profile-validator.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/bin/create-flotilla.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/tools/verify-dry-run.mjs`

## Blockers

- PocketBase unavailable on `localhost:8090`; could not post heartbeat, output comment, or move task to peer_review.
- Git metadata writes blocked; could not pull, create the task branch, commit, or push.
- `~/fleet/codi/PROGRESS.md` outside writable roots; update attempt failed with `operation not permitted`.

---

# WORKLOG — V05-PROFILE-005: Add Smoke Tests for Profile-Pack Install Flow

**Task ID**: weekr00w2dscsse
**Branch**: task/weekr00w2dscsse requested; branch creation blocked by `.git` write permissions
**Agent**: Codi
**Date**: 2026-05-17

---

## Objective

Add release smoke coverage for the profile-pack install paths before v0.5.0.

## Plan

1. Add a focused smoke script that invokes the real `create-flotilla` CLI in temporary directories.
2. Verify default built-in profile install writes the expected instruction files.
3. Verify custom `--profile-dir` install overlays expected files.
4. Verify invalid profiles fail before leaving partial install state.
5. Verify `--profile-zip` install while zip support is present.
6. Wire the script into npm scripts and document the release command.

## Results

- Added `package/tools/smoke-profile-install.mjs`.
- Added `npm run smoke:profile-install`.
- Added the profile smoke command to `prepublishOnly` after `verify:dry-run`.
- Documented the command in `package/README.md` and `package/INSTALL.md`.

## Verification

- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin node --check package/tools/smoke-profile-install.mjs`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin npm --prefix package run smoke:profile-install`
- [x] `PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin npm --prefix package run verify:dry-run`

## Blockers

- PocketBase unavailable on `localhost:8090`; could not post heartbeat, output comment, or move task to peer_review.
- Git metadata writes blocked; could not pull, create the task branch, commit, or push.
- `~/fleet/codi/PROGRESS.md` outside writable roots; update not attempted because prior attempt in this session failed with `operation not permitted`.

---

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
