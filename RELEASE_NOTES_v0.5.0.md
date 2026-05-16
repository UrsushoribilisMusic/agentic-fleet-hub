# Release Notes — create-flotilla v0.5.0

## Release Summary

**Version**: 0.5.0  
**Date**: 2026-05-17  
**Status**: Release Candidate  

This release focuses on **Fleet Reliability & Profile Portability**. The dispatcher has been rewritten through four successive fix passes (v5–v7) to run all agents concurrently, make agents own their own status transitions, and reclaim stale work automatically. A first-class profile pack system ships `default-engineering` as a portable, sanitizable snapshot of the fleet instruction layer.

---

## New Features

### 1. Profile Pack System

A **profile pack** is a portable, sanitized snapshot of the fleet instruction layer — all the markdown and JSON files that tell agents how to behave. Profile packs contain no live operational data (tasks, heartbeats, comments) and no machine-specific paths or secrets.

**Shipped in this release:**

- **`package/profiles/default-engineering/`** — the first official Flotilla profile pack. Contains:
  - `AGENTS/RULES.md` — complete heartbeat protocol, Kanban rules, peer review, Git and secrets conventions, standup attribution rule, task branch protocol, no-self-approval rule, build verifier obligation.
  - Agent mandate templates: `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `MISTRAL.md`, `GEMMA.md`.
  - `AGENTS/CONFIG/fleet_meta.json` — roster template with `{{PLACEHOLDER}}` values.
  - `MISSION_CONTROL.md` and `ARCHITECTURE.md` — scaffolded templates.
  - Empty `AGENTS/MESSAGES/inbox.json` and `AGENTS/LESSONS/ledger.json`.

- **`package/PROFILE_PACKS.md`** — agent handoff spec documenting:
  - The four layers of fleet instructions (default rules / team-specific rules / agent-specific / project context).
  - What profile packs do NOT contain (tasks, heartbeats, comments, lessons — all stay local in PocketBase).
  - How to inspect your current instruction files.
  - How to compare against the default profile using `diff`.
  - Step-by-step export guide with a sanitization checklist.
  - How to install a profile pack into a new Flotilla repo.
  - A prompt template for asking your local agent to generate a profile pack automatically.

**PocketBase is always the local source of truth for execution state.** A profile pack distributes setup rules, not operational history. Two installs using the same pack are operationally independent.

---

## Dispatcher Improvements

The dispatcher has evolved from v4 (v0.4.0) through four successive improvements, collectively labelled v5–v7.

### 2. Parallel Agent Dispatch

Previously, the dispatcher launched agents one at a time via blocking `subprocess.run()`. Each agent blocked the entire main loop until it exited.

**v5**: Replaced with non-blocking `Popen` tracked in an `_active_agents` dictionary. The main loop now:
- Collects finished agents and posts their results each cycle.
- Dispatches one task per agent per cycle.
- Kills agents that exceed the per-agent timeout via `SIGTERM` on the process group.
- All agents run concurrently, restoring the parallelism the fleet depends on.

Companion fix: corrected `misty` and `gem` AGENT_COMMANDS that had invalid CLI flags (`-C` for vibe, missing `--skip-trust` for Gemini) causing exit 2 and exit 55 on every dispatch.

Additional fix: eliminated a `capture_output` pipe deadlock that could block the dispatcher when agent stdout/stderr buffers filled before the process exited. Added 10 MB rotating log with 5 backup files.

### 3. Agent-Owned Status Transitions

Previously, the dispatcher auto-promoted any agent that exited with code 0 to `peer_review`, regardless of whether the agent actually set that status in PocketBase. This created a rubber-stamp loop: agents doing orientation or WORKLOG commits without real implementation were marked done.

**v6**: After agent exit-0, the dispatcher reads the task's current PB status. If still `in_progress`, it resets to `todo`. Agents must explicitly set `peer_review` for work to count.

**v7 refinement**: The v6 logic was too aggressive — it reset `in_progress → todo` on *every* exit-0, breaking multi-session tasks where an agent legitimately parked mid-work. Corrected model:

- `exit-0` → dispatcher touches nothing. Agent owns its status.
- `exit-nonzero` → reset to `todo` (crash/quota recovery path, unchanged from v4).
- `_reclaim_stale_tasks()` runs every 10 cycles: any `in_progress` task with no live agent process and `updated > 2h ago` is reset to `todo`.

### 4. Per-Agent Timeout Map

Replaced the uniform 600s timeout with a per-agent map:

| Agent | Timeout |
|---|---|
| `clau` | 1800s (30 min) |
| `gem` | 1200s (20 min) |
| `misty` | 1200s (20 min) |
| `codi` | 1200s (20 min) |

The 600s limit was killing Clau mid-task on complex multi-file iOS work (exit 143/SIGTERM). Claude Code sessions routinely need 20–30 minutes for non-trivial tasks.

### 5. Mission Control as Overview, Not Source of Truth

`fleet_sync.py` previously overwrote PocketBase task statuses by reading the `Ticket Status` table in `MISSION_CONTROL.md`. This caused `todo` tasks to be reset to `in_progress` on every sync cycle — a state that blocked dispatch.

**Fixed**: `fleet_sync.py` no longer writes task status from MC. PocketBase is the authoritative execution state for all automation. Mission Control is the human-readable project overview and is managed by the dispatcher's `sync_mission_control()` (read-from-PB direction only).

---

## GitHub Sync Fixes

### 6. Duplicate Issue Prevention

`sync_outbound()` now calls `find_existing_issue_by_title()` before creating a new GitHub issue. If an open or closed issue with the same title already exists, it links the existing issue number to the PB task instead of opening a duplicate.

### 7. Atomic Inbound Import

`sync_inbound()` now checks the return code of `gh issue edit --add-label flotilla-managed`. On label failure it logs a WARNING but still advances `last_gh_issue` to prevent duplicate PB task creation on retry. Operator can apply the label manually if needed.

### 8. Closed Issues No Longer Silently Dropped

`get_new_human_issues()` changed from `--state open` to `--state all`. Issues that are closed before the poll runs are now imported into PocketBase rather than silently skipped.

### 9. Multi-Repo Inbound Sync

GitHub sync can now import issues from multiple GitHub repositories into a single PocketBase instance. `EXTRA_REPO_PREFIXES` in `fleet_sync.py` maps additional project repos to their label prefixes.

---

## Internal Improvements

- **Log rotation**: Dispatcher log is now capped at 10 MB with 5 rotating backups (`dispatcher.log.1`–`.5`).
- **Canonical runtime path guard**: `dispatcher.py` warns if run from the repo checkout instead of the canonical `~/fleet/dispatcher.py` path.
- **Heartbeat protocol consolidation**: All heartbeat-phase documentation lives in `AGENTS/RULES.md`. Agent mandate files (`CLAUDE.md`, `GEMINI.md`, etc.) are now thin identity cards pointing there.

---

## Known Limitations

### Multi-Computer Fleet

Two Flotilla installs running the same profile pack are operationally independent. PocketBase is always a local SQLite database. There is no native multi-machine state sharing.

Options for multi-machine teams (none automated in this release):
1. Host PocketBase on a shared server accessible to all machines.
2. Use the `fleet_push.py` hybrid connector (local PB → remote Fleet Hub).

### Profile Pack Install Is Manual

The `create-flotilla` setup wizard does not yet support installing from a profile pack via a directory or zip overlay. To apply a profile pack, copy files manually into the repo root (see `PROFILE_PACKS.md` for the step-by-step). Installer automation is tracked in V05-PROFILE-002 (pending, assigned to Codi).

### No Profile Validator

There is no automated check that a profile pack is well-formed, contains required files, or has had all `{{PLACEHOLDER}}` values replaced. Validation tooling is tracked in V05-PROFILE-003 (pending, assigned to Codi).

### Dispatcher Internal Label

The docstring in `dispatcher.py` still reads "Fleet Dispatcher v4" — a cosmetic artifact from when the file was first written. The actual behavior shipped in this release corresponds to the v7 fixes described above.

---

## Release Checklist

- [x] Parallel agent dispatch implemented and tested (v5)
- [x] Status ownership model implemented (v6/v7)
- [x] Stale task reclaim implemented (v7)
- [x] Per-agent timeout map implemented
- [x] MC→PB status sync removed from fleet_sync.py
- [x] GitHub sync: duplicate prevention, atomic import, `--state all`, multi-repo
- [x] Default engineering profile pack at `package/profiles/default-engineering/`
- [x] `PROFILE_PACKS.md` agent handoff spec written
- [x] Smoke checks pass (PB healthy, profile pack structure verified, heartbeat check exit-0)
- [ ] `package/package.json` version bumped to `0.5.0` (before npm publish)
- [ ] V05-PROFILE-002: installer zip overlay support (pending, Codi)
- [ ] V05-PROFILE-003: profile validator (pending, Codi)
- [ ] V05-PROFILE-005: profile-pack install smoke tests (pending, Codi)
- [ ] npm publish: `npx create-flotilla@0.5.0` (after checklist items above)

---

## How to Upgrade

```bash
npx create-flotilla@0.5.0 <project-dir>
```

Or to update an existing install, pull the latest dispatcher and scripts:

```bash
git pull origin master
bash fleet/sync_to_fleet.sh --restart
```

To apply the default engineering profile pack to an existing repo:

```bash
# See PROFILE_PACKS.md for full instructions
cp -r path/to/flotilla-package/profiles/default-engineering/* /path/to/your-fleet-repo/
```

---

*Built by the Ursushoribilis Agentic Crew (Gem, Clau, Codi, Misty).*
