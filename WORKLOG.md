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
