# Changelog

## [0.5.0] - 2026-05-17

### Added
- **Profile Pack System**: `package/profiles/default-engineering/` — first official Flotilla profile pack. Contains fully sanitized AGENTS/RULES.md, all five agent mandate templates (CLAUDE.md, GEMINI.md, AGENTS.md, MISTRAL.md, GEMMA.md), fleet_meta.json template, MISSION_CONTROL.md and ARCHITECTURE.md scaffolds, and empty inbox/lessons starters.
- **PROFILE_PACKS.md**: Agent handoff spec covering the four instruction layers, what profile packs cannot transfer (PB execution state), inspect/compare/export/install workflows, and a prompt template for agent-assisted profile export.
- **Per-agent timeout map**: `clau=1800s`, others=`1200s`. Previous uniform 600s was killing Clau mid-task (exit 143). Configurable via `AGENT_TIMEOUT_SECONDS` dict in dispatcher.
- **`_reclaim_stale_tasks()`**: Runs every 10 dispatcher cycles. Any `in_progress` task with no live agent process and `updated > 2h ago` is reset to `todo`.
- **Multi-repo GitHub sync**: `EXTRA_REPO_PREFIXES` in `fleet_sync.py` enables importing issues from multiple GitHub repos into a single PocketBase instance.
- **Log rotation**: Dispatcher log capped at 10 MB with 5 rotating backups.
- **Canonical runtime path guard**: Dispatcher warns if executed from the repo checkout instead of `~/fleet/dispatcher.py`.

### Changed
- **Parallel agent dispatch (v5)**: All agents now run concurrently via non-blocking `Popen` tracked in `_active_agents`. Main loop collects finished agents and dispatches new ones each cycle without blocking. Replaces the blocking `subprocess.run()` model from v4.
- **Agent-owned status transitions (v6→v7)**: Dispatcher no longer auto-promotes exit-0 runs to `peer_review`. On exit-0, PB status is untouched — agents must explicitly set it. On exit-nonzero, task resets to `todo` (crash/quota recovery).
- **Mission Control is overview only**: `fleet_sync.py` no longer overwrites PocketBase task status from MC. PB is the authoritative execution state; MC is the human-readable project board (dispatcher writes MC from PB, not the reverse).
- **GitHub sync `--state all`**: `get_new_human_issues()` changed from `--state open` to include closed issues so none are silently dropped.
- **Heartbeat protocol consolidation**: All 6-phase protocol docs moved to `AGENTS/RULES.md`. Agent mandate files are now thin identity cards.

### Fixed
- Parallel dispatch restored after v4 accidentally serialized all agents through blocking subprocess calls.
- `misty` AGENT_COMMAND used `-C` (invalid vibe flag) → exit 2; fixed to `--workdir`.
- `gem` AGENT_COMMAND missing `--skip-trust` → exit 55 trust error; flag added.
- `capture_output` pipe deadlock in dispatcher when agent stdout/stderr buffers filled before exit.
- GitHub sync: duplicate outbound issue creation when a PB task had no `gh_issue_id`.
- GitHub sync: non-atomic inbound import where `gh issue edit` failure left issues in inconsistent state.
- `fleet_sync.py` MC→PB sync was resetting `todo` tasks to `in_progress` every cycle, blocking dispatch.

## [0.4.0] - 2026-04-06

### Added
- **Schichtplan (Shift Timeline)**: Swim-lane timeline on the Fleet Hub dashboard showing agent activity over 24h/7d/30d windows. Colour-coded segments: green=working, grey=idle, red=dark/quota, orange=offline. Pure CSS, no external chart library.
- **Extended Agents Table**: New table on the Team section showing last seen, idle until, tasks completed, estimated tokens, agent type (Cloud/Local), and average session duration per agent.
- **Aggregate Stats Panel**: Six fleet-wide metric cards — Tasks (24h), Reassignments, Circuit Breaker, MTBF, MTTR, False Wake Rate. Cards show `—` until `task_events` data matures.
- **`task_events` PocketBase collection**: Structured event log with fields `task_id`, `event_type`, `from_status`, `to_status`, `agent`, `meta` (JSON), `timestamp`. Event types: `status_transition`, `reassignment`, `circuit_breaker`, `queue_snapshot`. Indexed for fast analytics queries.
- **Dispatcher event logging**: `log_task_event()` wired into `update_task_status()`, `reassign_tasks()`, and a 60s `log_queue_snapshot()` tick.
- **Gemma agent**: Local Gemma4 (Ollama/aichat) onboarded as cost-free, offline-capable fleet member. Heartbeat wrapper with checksum gate. Added to `fleet_meta.json` with `runtime: Local (Ollama/Mac Mini)`.
- **Task branch + WORKLOG handoff protocol**: Agents must create `task/{pb-task-id}` branch and commit `WORKLOG.md` before working. On reassignment, dispatcher checks for the branch via `git ls-remote` and includes the URL in the handoff comment so the new agent can resume mid-work.
- **MISSION_CONTROL.md auto-sync**: Dispatcher's `sync_mission_control()` runs every cycle, detects approved PocketBase-UUID tasks, removes them from the OPEN table, and commits + pushes automatically.

### Changed
- **Dispatcher v4**: SHA-256 checksum gate (`_state_changed()`) — dispatcher only dispatches when MISSION_CONTROL.md, inbox.json, or PocketBase task state has actually changed. Eliminates idle LLM cycles.
- **Heartbeat wrappers**: All three wrappers (Clau, Gem, Codi) now run `heartbeat_check.py` as Phase 0 before launching any LLM. Exit 1 = skip session entirely. Zero tokens on idle cycles.
- **`in_progress` reassignment**: When an offline agent's `in_progress` task is reassigned, status resets to `todo` and includes branch URL if one exists, so the new agent can resume cleanly.
- **Fleet Hub static path**: `staticBase` in `server.mjs` now uses `import.meta.url` — no more hardcoded Mac Mini paths breaking DO server deployments.
- **`LIVE_REPO_PATH` auto-detection**: `server.mjs` detects Mac Mini vs DO server and resolves repo-relative paths accordingly (`fleet_meta.json`, `inbox.json`, `standups/`, `lessons/`).
- **Agent runtime labels**: `fleet_meta.json` agents now carry accurate `runtime` strings with provider — e.g. `Cloud (Anthropic)`, `Cloud (Google)`, `Local (Ollama/Mac Mini)`.
- **Standup attribution rule**: `AGENTS/RULES.md` requires every standup heading to identify the agent — format `# AgentName — YYYY-MM-DD`.
- **live-repo auto-pull cron**: DO server pulls `agentic-fleet-hub` every 5 minutes so Fleet Hub never shows stale standups or memory docs.

### Fixed
- Fleet Hub returning 404 after Google auth (hardcoded absolute path in `staticBase`).
- PB Viewer showing "No tasks found" for all filter values (server ignored filter param; returned raw array instead of `{items: []}`).
- Agent type column showing all agents as "Local".
- `task_events` meta JSON field created with `maxSize: 0` blocking all event writes — fixed via migration `1775900001_fix_task_events_meta.js`.
- `sync_mission_control` eating human ticket numbers — restricted to PocketBase UUID-format IDs only.
- Misty's launchd plist referencing wrong `mistral-vibe` version path.

## [0.2.0] - 2026-03-16

### Added
- Heartbeat dot tooltips and mock status for demo and growth dashboards
- Demo intercept modal for write actions with Big Bear CTA
- GitHub Issues ↔ PocketBase two-way sync (github_sync.py launchd service)
- Dynamic Telegram bot commands from fleet_meta.json (9 commands: /clau /gem /codi /ask /spec /go /status /tasks /help)
- Misty (Mistral Vibe) onboarding: MISTRAL.md mandate, heartbeat protocol, fleet workspace
- Package sync: dashboard assets, plists, and scripts to package/scripts/ and package/blueprint/
- Hybrid deployment support: fleet_push.py connector for local PocketBase → remote Fleet Hub
- Agent health monitoring: skill-based task reassignment on stale heartbeats (>30m)
- Deployment scenarios documentation: Local/Cloud/Hybrid comparison in README

### Changed
- Updated ARCHITECTURE.md to v0.2.0 with new component diagrams
- Improved demo and growth dashboard UI/UX with dark/light mode support
- Fleet Doctor: added Telegram/OpenClaw/GitHub Sync/Hybrid script verification
- Setup wizard: added deployment/integration steps for v0.2.0

### Fixed
- Fixed PocketBase bind conflict (removed duplicate com.flotilla.pocketbase service)
- Resolved Telegram bridge outbound truncation for messages >4096 characters
- Fixed dispatcher trusted directory error for Codi fleet invocation
- Fixed Codi launchd invocation with proper node path
- Fixed github_sync.py duplicate issue creation and non-atomic inbound import

## [0.1.0] - 2026-03-13

### Added
- Initial release of create-flotilla.
- Basic fleet management and dashboard features.
