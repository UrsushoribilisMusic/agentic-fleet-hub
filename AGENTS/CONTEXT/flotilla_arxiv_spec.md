# Flotilla v0.4.0 — Technical Specification for arXiv Paper
*Prepared by Clau, 2026-04-06. Covers implementation details for the paper on autonomous multi-agent management planes.*

---

## 1. PocketBase Collections Schema

Flotilla uses PocketBase (single-binary SQLite-backed REST API, port 8090) as its operational data layer. All schema changes are captured as versioned migration files under `fleet/pocketbase/pb_migrations/`.

### 1.1 `tasks` Collection

Core execution unit. Status field is a constrained select — no free-form states.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | text (auto) | 15-char alphanumeric PB UUID | Primary key |
| `title` | text | required | Human-readable task label |
| `description` | text | optional | Full task spec |
| `status` | select | `backlog`, `todo`, `in_progress`, `peer_review`, `waiting_human`, `waiting_human_notified`, `approved`, `blocked` | State machine field |
| `assigned_agent` | select | `clau`, `gem`, `codi`, `scout`, `echo`, `closer` | One of the active roster |
| `required_skills` | json | optional | Array of skill strings for substitution matching |
| `scratchpad` | json | optional | Free-form inter-agent state handoff blob |
| `reassignment_count` | number | integer ≥ 0 | Increments on each reassign within 10-minute window |
| `last_reassignment_at` | date | optional | ISO timestamp of last reassignment |
| `goal_id` | relation → `goals` | optional | Links task to parent goal |

Status transitions enforced by convention (not DB constraints): `todo → in_progress → peer_review → approved`. Agents may also set `waiting_human` or `blocked`. The dispatcher can reset `in_progress → todo` on reassignment.

### 1.2 `heartbeats` Collection

Liveness tracking. Each agent writes a heartbeat record on every session start.

| Field | Type | Notes |
|---|---|---|
| `agent` | text | Agent key (e.g. `clau`, `gem`) |
| `status` | select | `working`, `idle`, `blocked` |
| `message` | text | Optional status narrative |
| `updated` | date (auto) | PocketBase auto-timestamp — used for staleness check |

The dispatcher considers an agent **offline** when `now - heartbeat.updated > 1800s` (30 minutes). This threshold is hard-coded in `is_agent_offline()`.

### 1.3 `comments` Collection

Append-only activity feed. Agents post output here; the Telegram bridge forwards new records outbound.

| Field | Type | Notes |
|---|---|---|
| `task_id` | text | Foreign key → tasks.id (soft reference) |
| `agent` | text | Author agent key |
| `content` | text | Up to 5000 chars |
| `type` | select | `output`, `feedback`, `comment`, `approved` |

### 1.4 `lessons` Collection

Structured evolutionary memory ledger. Agents write here after each session; top lessons are injected into subsequent session prompts.

| Field | Type | Notes |
|---|---|---|
| `agent` | text | Authoring agent |
| `decision` | text | What was decided |
| `rationale` | text | Why |
| `outcome` | text | Observed result |
| `confidence_score` | number | 0.0–1.0 |
| `tags` | json | Array of keyword strings |

### 1.5 `task_events` Collection (v0.4.0 — Telemetry)

Append-only structured event log. Powers the Fleet Performance Panel (MTBF, MTTR, circuit-breaker rate, false wake rate). Every status transition, reassignment, and circuit-breaker trigger writes one record here.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `task_id` | text | required | PB task UUID, or `"dispatcher"` for queue snapshots |
| `event_type` | select | `status_transition`, `reassignment`, `circuit_breaker`, `queue_snapshot` | Indexed |
| `from_status` | text | optional | Previous task status |
| `to_status` | text | optional | New task status |
| `agent` | text | optional | Acting agent or `"dispatcher"` |
| `meta` | json | maxSize: 5000 | Structured context blob (see below) |
| `timestamp` | date | required | UTC write time |

**Indexes:** `task_id`, `event_type`, `timestamp` — all three indexed for analytics queries.

**`meta` payloads by event type:**

```json
// status_transition
{ "note": "optional free text" }

// reassignment
{
  "from_agent": "clau",
  "to_agent": "gem",
  "reassignment_count": 2,
  "reason": "agent offline / likely context limit hit",
  "branch": "https://github.com/…/tree/task/abc123xyz"  // null if no branch
}

// circuit_breaker
{
  "reassignment_count": 3,
  "last_agent": "clau",
  "reason": "blocked after 3 reassignments in 10m"
}

// queue_snapshot
{
  "queue_depth": 4,
  "cycle_ts": "2026-04-06 14:00:00"
}
```

**Implementation note:** PocketBase JSON fields default `maxSize` to `0` (unlimited) when the `options` object is omitted in a migration. If `options: {}` is passed explicitly, PocketBase interprets this as `maxSize: 0` which silently rejects all writes. Migration `1775900001_fix_task_events_meta.js` corrects this by explicitly setting `maxSize: 5000`.

---

## 2. Dispatcher Logic — Reassignment Decision Flow

The dispatcher (`fleet/dispatcher.py`) runs as a persistent process (60-second polling loop). The reassignment subsystem is the most complex decision path.

### 2.1 Pseudocode

```
every 60 seconds:
  create_daily_standup()
  check_agent_health()        # → may trigger reassign_tasks()
  log_queue_snapshot()
  sync_mission_control()

  if _state_changed():        # SHA-256 checksum gate
    tasks = get_pending_tasks()  # status = "todo"
    for task in tasks:
      agent = task.assigned_agent
                               or auto_assign(task, all_agents)
      if agent not in offline_agents:
        run_agent(agent, task)
    check_waiting_human()
  else:
    check_waiting_human()
```

### 2.2 `check_agent_health()` → `reassign_tasks()`

```
check_agent_health():
  for each agent in fleet_meta.team:
    is_offline = (now - last_heartbeat.updated) > 1800s
    if is_offline and not previously_offline:
      mark agent offline, log transition
    if is_offline:
      reassign_tasks(agent)
    elif previously_offline:
      mark agent recovered, send Telegram alert

reassign_tasks(offline_agent):
  tasks = PB.tasks where assigned_agent = offline_agent
                    and status in ("todo", "in_progress")
  for task in tasks:
    # Cooldown gate: skip if reassigned < COOLDOWN_SECONDS ago (default 300s)
    if task.last_reassignment_at and age(last_reassignment_at) < 300s:
      continue

    best = find_best_substitute(task, offline_agent)
    if best is None or best is also offline:
      continue

    # Circuit breaker: count reassignments within the last 10 minutes
    count = task.reassignment_count (if last_reassign was < 10m ago, else reset to 1)
    if count >= 3:
      task.status = "blocked"
      log circuit_breaker event
      send Telegram alert
      continue

    # Reset in_progress tasks so new agent starts clean
    new_status = "todo" if task.status == "in_progress" else task.status
    reason = "agent offline / likely context limit hit" if in_progress else "agent offline"

    # Branch handoff check
    branch_url = None
    if git ls-remote origin task/{task.id} returns a ref:
      branch_url = "https://github.com/…/tree/task/{task.id}"

    # Commit reassignment
    task.assigned_agent = best.heartbeatKey
    task.status = new_status
    task.reassignment_count = count
    task.last_reassignment_at = now

    log reassignment event (includes branch_url in meta)
    post comment: "Reassigned from X to Y (reason).
                   Branch: {branch_url} — checkout, read WORKLOG.md, continue."
                   OR "No branch found — start fresh on task/{id}."
```

### 2.3 `find_best_substitute()`

```
find_best_substitute(task, offline_agent):
  required_skills = task.required_skills or offline_agent.skills
  best = None
  max_score = -1

  for candidate in all_agents (excluding offline_agent):
    score = |required_skills ∩ candidate.skills|
    if score > max_score:
      best = candidate; max_score = score
    elif score == max_score:
      # Prefer agents listed earlier in offline_agent.fallbackChain
      if candidate in fallbackChain and candidate appears before best:
        best = candidate

  return best
```

### 2.4 SHA-256 Checksum Gate (`_state_changed()`)

Prevents idle LLM wakeups. On each cycle, the dispatcher computes SHA-256 of:

1. `~/fleet/MISSION_CONTROL.md`
2. `AGENTS/MESSAGES/inbox.json`
3. PocketBase `tasks` latest `updated` timestamp (single REST call)

Results are cached in `fleet/logs/dispatcher_cache.json`. If all three match the previous cycle, no agents are dispatched and no LLM tokens are consumed.

---

## 3. Heartbeat Protocol — Timing and Two-Layer Gate

### 3.1 Schedule (launchd `StartCalendarInterval`)

Each agent runs on a fixed minute stagger within every 10-minute window:

| Agent | Minutes past the hour |
|---|---|
| Gem | :00, :10, :20, :30, :40, :50 |
| Codi | :02, :12, :22, :32, :42, :52 |
| Clau | :04, :14, :24, :34, :44, :54 |
| Gemma | :08, :18, :28, :38, :48, :58 |
| Misty | :06, :16, :26, :36, :46, :56 |

Stagger prevents concurrent LLM sessions from saturating the host. No two agents overlap within the same 2-minute window.

### 3.2 Phase 0 — Pre-LLM Checksum Gate (`heartbeat_check.py`)

Runs before any LLM process is spawned. Reads:

- `MISSION_CONTROL.md` (hub)
- `AGENTS/MESSAGES/inbox.json`
- Active project's `MISSION_CONTROL.md` (if `fleet_meta.json` has `is_active: true` on a non-hub project)

Computes SHA-256 of each watched file and compares to a per-agent cache at `.fleet_cache/heartbeat_{agent}.json`.

**Relevance filter (second gate):** Even on a file change, the agent only wakes if:
- MISSION_CONTROL.md OPEN section contains the agent's name/alias, OR
- `inbox.json` has an `"unread"` message with `to` matching the agent's aliases

Exit codes:
- `0` → proceed, launch LLM session
- `1` → nothing relevant, exit immediately (zero LLM tokens)

### 3.3 Wrapper Script Phases

```
heartbeat_wrapper.sh:
  Phase 0: python heartbeat_check.py --agent clau --repo $REPO
           exit 1 → print "No changes detected. Skipping." && exit 0

  Phase 1: summarize_session.py --pre
           Refreshes active_lessons.txt from PocketBase top lessons

  Phase 2: Build prompt
           BASE_PROMPT + injected lessons block (if active_lessons.txt non-empty)

  Phase 3: claude --dangerously-skip-permissions -p "$FULL_PROMPT"

  Phase 4: summarize_session.py --post
           Extracts lessons from session log, writes to PocketBase lessons collection
```

---

## 4. Circuit Breaker — Layer Map

The circuit breaker prevents ping-pong reassignment loops (two offline agents bouncing a task indefinitely).

| Concern | Layer | Location |
|---|---|---|
| Offline detection | Dispatcher | `is_agent_offline()` — heartbeat staleness > 30m |
| Cooldown gate | Dispatcher | `last_reassignment_at` field on task; skip if age < 300s |
| Reassignment counter | Dispatcher | `reassignment_count` field on task; resets if last reassign > 10m ago |
| **Trip condition** | **Dispatcher** | **`reassignment_count >= 3`** |
| State write on trip | Dispatcher | `PATCH /tasks/{id}` → `status: "blocked"` |
| Event log on trip | Dispatcher | `log_task_event("circuit_breaker", ...)` → `task_events` |
| Human notification | Dispatcher | `send_telegram()` → operator Telegram DM |
| Schema enforcement | PocketBase | `status` select includes `"blocked"` value |
| Human recovery path | Telegram bridge | Operator sets status back to `todo` via Telegram command |

The counter and cooldown live on the task record in PocketBase (fields `reassignment_count` and `last_reassignment_at`) — not in memory — so the circuit breaker survives dispatcher restarts.

**Key behaviour:** The 10-minute window check (`last_reassign < 600s`) means a task that stops bouncing (e.g., a substitute agent comes online and works on it) resets its counter on the next reassignment event. This prevents accidental trips from legitimate sequential reassignments spread over hours.

---

## 5. Infisical Integration — Runtime Secret Injection

Flotilla follows a zero-disk-secrets model: no `.env` files, no hardcoded credentials in any committed file. Secrets are fetched at runtime from Infisical EU (`https://eu.infisical.com/api`).

### 5.1 Agent-Facing Interface (`vault/agent-fetch.sh`)

```bash
#!/bin/bash
SECRET_NAME=$1
ENV=${2:-dev}

SECRET=$(infisical secrets get "$SECRET_NAME" \
    --domain="https://eu.infisical.com/api" \
    --env="$ENV" \
    --plain 2>/dev/null)

echo "$SECRET"
```

Usage from agent scripts:
```bash
API_KEY=$(bash vault/agent-fetch.sh YOUTUBE_API_KEY production)
```

### 5.2 Dispatcher Pattern

The dispatcher reads `TELEGRAM_TOKEN` from environment variables injected by launchd (see §6). This is the exception to the Infisical pattern — the dispatcher runs before any LLM and cannot interactively authenticate. The token is injected via the plist `EnvironmentVariables` dict at service load time.

For all other secrets (YouTube, GitHub, etc.), agents call `vault/agent-fetch.sh` within their LLM session.

### 5.3 Authentication

The Infisical CLI must be authenticated on the host before any agent session:
```bash
infisical login --domain=https://eu.infisical.com/api
```

Authentication is cached in the system keychain. Agents do not store or re-authenticate credentials.

---

## 6. launchd Plist Structure — Always-On Services

All fleet services are managed by macOS `launchd` via plists in `~/Library/LaunchAgents/`. There are two structural patterns:

### 6.1 Always-On Services (`KeepAlive: true`)

Used for: PocketBase, Dispatcher, Telegram Bridge, fleet_push.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>fleet.dispatcher</string>

  <key>ProgramArguments</key>
  <array>
    <string>/Users/miguelrodriguez/fleet/.venv/bin/python3</string>
    <string>/Users/miguelrodriguez/fleet/dispatcher.py</string>
  </array>

  <key>EnvironmentVariables</key>
  <dict>
    <key>TELEGRAM_TOKEN</key>    <string>…</string>
    <key>TELEGRAM_CHAT_ID</key>  <string>997912895</string>
  </dict>

  <key>RunAtLoad</key>   <true/>
  <key>KeepAlive</key>   <true/>

  <key>StandardOutPath</key>
  <string>/Users/miguelrodriguez/fleet/logs/dispatcher.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/miguelrodriguez/fleet/logs/dispatcher_err.log</string>
</dict>
</plist>
```

**PocketBase stability note:** `fleet.pocketbase` additionally sets `<key>ThrottleInterval</key><integer>10</integer>` to prevent rapid restart bind conflicts on port 8090 during crash loops.

### 6.2 Scheduled Agent Sessions (`StartCalendarInterval`)

Used for: Clau, Gem, Codi, Gemma, Misty. Fires on fixed minute marks; does **not** use `KeepAlive` (sessions are bounded by LLM completion).

```xml
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>fleet.clau</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/miguelrodriguez/fleet/clau/heartbeat_wrapper.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/miguelrodriguez/fleet/clau</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/Users/miguelrodriguez/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>

  <!-- Fire at :04, :14, :24, :34, :44, :54 past every hour -->
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Minute</key><integer>4</integer></dict>
    <dict><key>Minute</key><integer>14</integer></dict>
    <dict><key>Minute</key><integer>24</integer></dict>
    <dict><key>Minute</key><integer>34</integer></dict>
    <dict><key>Minute</key><integer>44</integer></dict>
    <dict><key>Minute</key><integer>54</integer></dict>
  </array>

  <key>RunAtLoad</key>   <false/>

  <key>StandardOutPath</key>
  <string>/Users/miguelrodriguez/fleet/logs/clau.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/miguelrodriguez/fleet/logs/clau_err.log</string>
</dict>
</plist>
```

### 6.3 Service Inventory

| Label | Type | Process |
|---|---|---|
| `fleet.pocketbase` | always-on | PocketBase binary, port 8090 |
| `fleet.dispatcher` | always-on | dispatcher.py, 60s poll loop |
| `fleet.bridge` | always-on | telegram_bridge.py |
| `fleet.push` | always-on | fleet_push.py, 60s snapshot push |
| `fleet.clau` | scheduled | heartbeat_wrapper.sh → claude CLI |
| `fleet.gem` | scheduled | heartbeat_wrapper.sh → gemini CLI |
| `fleet.codi` | scheduled | heartbeat_wrapper.sh → codex CLI |
| `fleet.gemma` | scheduled | heartbeat_wrapper.sh → aichat (Ollama) |
| `fleet.misty` | scheduled | heartbeat_wrapper.sh → mistral CLI |
| `fleet.github` | always-on | github_sync.py |

---

## 7. Hybrid Deployment Architecture (Mac Mini + DO Server)

Included because the paper's evaluation uses this topology.

PocketBase runs exclusively on the Mac Mini (not exposed publicly). The Fleet Hub dashboard is served from a DigitalOcean droplet. Data flows via a push-cache pattern:

```
Mac Mini:
  fleet_push.py (every 60s)
    → reads heartbeats, tasks, comments from PB (localhost:8090)
    → POST /fleet/snapshot to DO server
    → signed with FLEET_SYNC_TOKEN (env var)

DO Server (server.mjs):
  /fleet/snapshot endpoint
    → validates token, writes to /var/lib/salesman-api/fleet_snapshot.json

  All /fleet/api/* endpoints:
    → try PocketBase first (fails in hybrid mode — PB not reachable)
    → fall back to fleet_snapshot.json
```

`LIVE_REPO_PATH` auto-detection in `server.mjs`:
```javascript
const LIVE_REPO_PATH = process.env.LIVE_REPO_PATH
  || (fs.existsSync("/Users/miguelrodriguez/projects/agentic-fleet-hub/MISSION_CONTROL.md")
      ? "/Users/miguelrodriguez/projects/agentic-fleet-hub"
      : "/opt/salesman-api/live-repo");
```

The DO server uses a 5-minute cron to pull the live-repo:
```
*/5 * * * * git -C /opt/salesman-api/live-repo pull --ff-only origin master
```

This provides the Fleet Hub with fresh standups, memory docs, and MISSION_CONTROL.md without requiring PocketBase to be publicly accessible.
