# Flotilla Architecture (v0.6)

Flotilla coordinates a team of AI coding agents through three shared surfaces: a **task board** (PocketBase), a **cognitive entry point** (`MISSION_CONTROL.md`), and the **project repositories** the agents work in. A small set of long-running Python services keeps these in sync and wakes agents when there is work.

## Components

```
                       ┌──────────────────────────────────────────┐
  Human ──Telegram────►│ telegram_bridge.py   commands, replies,  │
        ◄─────────────┤                      comment forwarding  │
        ──dashboard───►│ server/ (Node)       setup wizard, board │
                       └───────────────┬──────────────────────────┘
                                       │ REST
                       ┌───────────────▼──────────────────────────┐
                       │ PocketBase  tasks · comments · heartbeats│
                       │             goals · deliberations ·      │
                       │             decision_briefs · lessons ·  │
                       │             task_events · research_*     │
                       └──▲──────────▲───────────▲────────────▲───┘
                          │          │           │            │
              ┌───────────┴───┐ ┌────┴──────┐ ┌──┴─────────┐ ┌┴────────────┐
              │ dispatcher.py │ │ council_  │ │ fleet_sync │ │ github_sync │
              │ heartbeats,   │ │ coordinator│ │ board ⇄    │ │ board →     │
              │ agent runs    │ │ R1/R2/brief│ │ MISSION_   │ │ private GH  │
              └──────┬────────┘ └───────────┘ │ CONTROL.md │ │ issues      │
                     │ starts                 └────────────┘ └─────────────┘
          ┌──────────▼───────────────────────────────┐
          │ Agent CLIs: claude · gemini · codex ·    │──► commits, WORKLOG.md
          │ vibe · local models (one process each)   │    in project repos
          └──────────────────────────────────────────┘
```

All services read their settings from `scripts/flotilla_config.py`, which takes everything from environment variables or `scripts/flotilla.env`, with defaults relative to the workspace. No path, repository, chat id or person is hardcoded.

### PocketBase: the single source of truth

Agents read and write only PocketBase; everything else (Mission Control, GitHub issues, the cloud dashboard) is a mirror for humans. The schema is created by the migrations in `pocketbase/pb_migrations/`:

| Collection | Holds |
|---|---|
| `tasks` | Tickets: title, description, `status`, `assigned_agent`, `scratchpad` (agent-to-agent handoff state), `goal_id`, `private`, `source`, GitHub link |
| `comments` | Agent and human comments per task, including heartbeats and review verdicts |
| `heartbeats` | One record per agent wake-up: status, model, duration |
| `task_events` | Typed lifecycle events (dispatch, status change, reclaim, council round) |
| `lessons` | Lessons learned: rule, rationale, outcome, approval status |
| `goals` | Council questions: goal, success criteria, roster, council state |
| `deliberations` | One record per agent per council round |
| `decision_briefs` | The synthesized recommendation awaiting human approval |
| `research_sources`, `research_claims` | Source ledger for research-heavy goals |

Task statuses: `backlog → todo → in_progress → peer_review → approved`, plus `waiting_human` for anything that needs a person.

### MISSION_CONTROL.md: the cognitive entry point

Every agent session starts by reading `MISSION_CONTROL.md` and `AGENTS/RULES.md`. `fleet_sync.py` regenerates the board section of Mission Control from PocketBase each cycle, so an agent from any vendor inherits the same picture: active tickets, owners, approved lessons and the current focus.

### The dispatcher

`dispatcher.py` is the only process that starts agents. Each cycle (about once a minute) it:

1. **Collects finished agents.** If the agent set the task status itself, that status stands. If it exited cleanly without moving the task, a new commit in a tracked repo moves it to `peer_review`; no commit puts it back to `todo`.
2. **Kills timed-out agents** and reclaims tasks stuck `in_progress` for more than two hours.
3. **Checks whether anything changed** (a checksum over Mission Control, the inbox, fleet config and the newest task timestamp). If nothing changed, it does nothing, except for a forced cycle every two hours.
4. **Dispatches** the next `todo` ticket of each idle, available agent, in parallel, appending the ticket text to the agent's heartbeat prompt.
5. **Runs the sync jobs:** Mission Control every cycle, GitHub every fifth cycle, and the council coordinator.

Agent availability comes from `scheduler_policy.py` and `logs/agent_failures.json`. Repeated failures put an agent in a one-hour cooldown; output that looks like a quota or rate-limit error (`quota`, `rate limit`, `insufficient_quota`, ...) puts it in a twelve-hour cooldown, so an exhausted quota can never turn the heartbeat into a spend loop. A watchdog dumps stack traces and restarts the process if a cycle hangs for five minutes.

How each agent is started is configured, not coded: built-in defaults for `claude`, `gemini`, `codex` and `vibe`, overridable per agent in `AGENTS/CONFIG/agent_commands.json`.

### Peer review

Work is not done when the author says so. A task in `peer_review` is picked up by a different agent, ideally from a different vendor, which posts a verdict comment and moves the task to `approved` or back to `todo` with findings. Agents hand work to each other through task branches and a `WORKLOG.md` in the branch, so the reviewer and any later agent can continue without the original session.

### Council Room

For questions that need judgement rather than execution, a human opens a **goal**. `council_coordinator.py` runs a fixed protocol:

1. **Intake gate.** A goal needs success criteria, and the requested agents must be available; otherwise it is parked in `waiting_human` with a Telegram note instead of silently dropping an agent.
2. **Round 1.** Each agent on the roster gets a role (architect, planner, executor, skeptic, researcher, reviewer) and writes an independent proposal.
3. **Round 2.** Each agent reads all proposals and critiques them.
4. **Synthesis.** One agent writes a decision brief: recommendation, agreement, real disagreement, rejected alternatives, risks, open questions for the human, and a definition of done.
5. **Human gate.** Nothing is executed until the human approves the brief (sets `status = approved` and `approved_by`). Running `scripts/council_brief_ticketer.py` then turns the brief's ticket plan into execution tickets, parked in `backlog` until the human releases them. With a GitHub mirror configured it also opens matching issues.

Rounds time out (4 h, 4 h, 6 h by default) and report who did not answer. Council tasks are created with `private = true` and are never mirrored to GitHub. See [docs/COUNCIL.md](docs/COUNCIL.md).

### Mirrors

- **GitHub (`github_sync.py`)** mirrors tasks to issues in a repository you choose, which should be **private**, and imports issues created by humans. Tasks that are `private`, come from Telegram or the council, or carry a `goal_id` or the word `CONFIDENTIAL` never have their description published. Disabled unless `FLOTILLA_GITHUB_REPO` is set.
- **Cloud dashboard (`fleet_push.py`)** pushes a periodic snapshot of the board to a server you run, so you can watch the fleet without exposing PocketBase.
- **Telegram (`telegram_bridge.py`)** forwards agent comments to the human and turns replies into comments or tasks. Commands: `/status`, `/tasks`, `/go`, `/ask`, `/spec`, and one per agent (`/clau`, `/gem`, ...).

### Secrets

Agents and services never read `.env` files with secret values. `run_with_secrets.sh` starts each service under `infisical run`, so tokens exist only in the process environment. Agents fetch what they need through the vault wrapper (`vault/agent-fetch.sh`, written into the workspace by the setup wizard).

### Audit trail

`archive_writer.py` appends every heartbeat and task event to JSONL files in which each entry carries the SHA-256 of the previous one, making silent edits detectable. See [package/COMPLIANCE.md](package/COMPLIANCE.md).

## Operational invariants

These are runtime rules learned from incidents, not conventions:

- **One process starts agents.** Only the dispatcher launches agents; a second scheduler would double-dispatch the same ticket.
- **One GitHub sync owner.** Either the dispatcher (default) or the `fleet.github` service runs `github_sync.py`, never both.
- **Quota failures are not completions.** A quota error parks the agent in a cooldown; it never bounces the task into a fast redispatch loop.
- **Cursor-driven forwarders never replay their backlog.** The Telegram bridge writes its cursor atomically and, if the backlog looks like a regressed cursor (more than 200 items), fast-forwards instead of re-sending old messages. This guard came from an incident that re-sent about 19,000 old comments.
- **PocketBase slowness is infrastructure degradation.** Agents are not reassigned because PocketBase timed out.
- **Mission Control drives dispatch.** A stale Mission Control resurrects stale work, so it is regenerated from the board every cycle.
- **The board is private by default.** Mirrors must be opt-in, private repositories, and council or confidential tasks never leave PocketBase.

## Files

```
scripts/
  flotilla_config.py        all settings, env-driven
  dispatcher.py             heartbeat scheduler and agent runner
  council_coordinator.py    Council Room protocol
  council_brief_ticketer.py approved brief → backlog tickets
  research_ledger.py        sources and claims for research goals
  fleet_sync.py             board → MISSION_CONTROL.md
  github_sync.py            board ⇄ private GitHub issues
  telegram_bridge.py        human ⇄ fleet over Telegram
  fleet_push.py             snapshot → cloud dashboard
  heartbeat_check.py        health checks
  archive_writer.py         hash-chained audit log
  run_with_secrets.sh       start any script under Infisical
  install_launchd.sh        install services on macOS
  fleet.*.plist             launchd templates
pocketbase/
  pb_migrations/            schema
  pocketbase_safe.sh        single-instance start wrapper
  install_pocketbase.sh     downloads the tested PocketBase version
```
