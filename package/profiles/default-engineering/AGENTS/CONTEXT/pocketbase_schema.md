# Flotilla PocketBase Collections Schema

Flotilla uses PocketBase (single-binary SQLite-backed REST API, default port 8090) as its operational data layer. This document describes the expected collection schemas. Create these collections in PocketBase Admin UI or via migration files before starting fleet operations.

---

## `tasks` Collection

The core execution unit. One record per task assigned to an agent.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | text (auto) | PocketBase auto UUID | Primary key |
| `title` | text | required | Human-readable task label |
| `description` | text | optional | Full task spec / acceptance criteria |
| `status` | select | `backlog`, `todo`, `in_progress`, `peer_review`, `waiting_human`, `approved`, `blocked` | State machine field |
| `assigned_agent` | select | agent heartbeat keys (e.g. `clau`, `gem`, `codi`) | One of the active roster |
| `required_skills` | json | optional | Array of skill strings for substitution matching |
| `scratchpad` | json | optional | Free-form inter-agent state handoff blob |
| `goal_id` | relation → `goals` | optional | Links task to a parent goal |
| `github_repo` | text | optional | GitHub `owner/repo` identifier (for GitHub sync) |
| `gh_issue_id` | number | optional | GitHub issue number (must be combined with `github_repo` for unique identity) |
| `github_issue_url` | text | optional | Full GitHub issue URL |

**Status transitions (by convention):**
`backlog → todo → in_progress → peer_review → approved`

Agents may also set `waiting_human` or `blocked`. The dispatcher can reset `in_progress → todo` on reassignment.

**Important**: `github_repo` + `gh_issue_id` together form the canonical external key. Never query by bare `gh_issue_id` alone — issue numbers are only unique within a single repository.

---

## `heartbeats` Collection

Liveness tracking. Each agent writes a heartbeat record on every session start.

| Field | Type | Notes |
|---|---|---|
| `agent` | text | Agent key (e.g. `clau`, `gem`) |
| `status` | select | `working`, `idle`, `blocked` |
| `message` | text | Optional status narrative |
| `updated` | date (auto) | PocketBase auto-timestamp — used for staleness check |

An agent is considered **offline** when `now - heartbeat.updated > 1800s` (30 minutes). This threshold is configured in the dispatcher.

---

## `comments` Collection

Audit log for task execution. Agents post output, feedback, approvals, and questions here.

| Field | Type | Notes |
|---|---|---|
| `task_id` | relation → `tasks` | The task this comment belongs to |
| `agent` | text | Agent key |
| `type` | select | `output`, `feedback`, `approval`, `question` |
| `content` | text | Comment body. Approvals should include commit hash. |
| `created` | date (auto) | Auto-timestamp |

---

## `lessons` Collection

Persistent fleet memory. Agents submit reusable insights here for future reference.

| Field | Type | Notes |
|---|---|---|
| `title` | text | Short lesson name |
| `content` | text | Full lesson body |
| `category` | text | E.g. `architecture`, `debugging`, `protocol` |
| `confidence` | select | `low`, `medium`, `high` |
| `status` | select | `pending_review`, `approved`, `rejected` |
| `agent` | text | Author agent key |
| `created` | date (auto) | Auto-timestamp |

---

## `goals` Collection

Council Protocol product intent. A goal is Miguel's upstream request before execution tickets exist.

| Field | Type | Notes |
|---|---|---|
| `title` | text | Short goal name |
| `status` | select | `draft`, `council_open`, `synthesis_ready`, `waiting_human`, `approved`, `rejected`, `ticketed`, `closed` |
| `goal` | text | Product intent / desired outcome |
| `why_now` | text | Timing rationale |
| `constraints` | text | Scope, budget, policy, or implementation limits |
| `success_criteria` | text | Required conditions before approval or ticketing |
| `deadline` | date | Optional due date |
| `output_type` | select | `code`, `research`, `sales_asset`, `dashboard`, `content`, `experiment`, `mixed` |
| `allow_internet_research` | bool | Whether external research is allowed for the goal |
| `owner` | text | Defaults by convention to `miguel` |

## `deliberations` Collection

One structured Council Protocol contribution from one agent for one goal and one round.

| Field | Type | Notes |
|---|---|---|
| `goal_id` | relation → `goals` | Required parent goal |
| `agent` | text | Agent key |
| `round` | number | `1` or `2`; no third round without Miguel reopening the goal |
| `role` | select | `planner`, `skeptic`, `researcher`, `architect`, `executor`, `reviewer`, `synthesizer` |
| `recommendation` | text | Agent's proposal or revised recommendation |
| `risks` | text | Known risks |
| `rejected_options` | text | Alternatives the agent would not pursue |
| `open_questions` | text | Questions blocking confident execution |
| `evidence_needed` | text | Claims or research that need validation |
| `confidence` | select | `high`, `moderate`, `low`, `speculative` |

## `decision_briefs` Collection

Synthesized Council Protocol plan for Miguel to approve, reject, or edit.

| Field | Type | Notes |
|---|---|---|
| `goal_id` | relation → `goals` | Required parent goal |
| `status` | select | `draft`, `waiting_human`, `approved`, `rejected`, `ticketed` |
| `summary` | text | Brief overview |
| `recommended_approach` | text | Synthesized plan |
| `agreement` | text | What the Council agreed on |
| `disagreement` | text | Preserved disagreements |
| `rejected_alternatives` | text | Alternatives considered and rejected |
| `known_risks` | text | Risks carried into execution |
| `open_questions_for_miguel` | text | Human decisions needed before ticketing |
| `ticket_plan` | json | Structured future task plan; no tickets are created until approval |
| `definition_of_done` | text | Done criteria for the approved plan |
| `review_assignments` | json | Suggested peer-review ownership |
| `created_by` | text | Synthesizer agent |
| `approved_by` | text | Human approver, normally Miguel |

---

## Setup Notes

1. Run PocketBase locally: `./pocketbase serve --http="127.0.0.1:8090"`.
2. Create collections via the Admin UI at `http://127.0.0.1:8090/_/`.
3. The `fleet/` directory in the Flotilla package includes PocketBase JS migrations. Council Protocol helpers and curl examples live in `docs/council_pocketbase.md`.
4. Set the API base URL in `AGENTS/CONFIG/fleet_settings.json` under `heartbeat.api_base_url` if running on a non-default host or port.
5. PocketBase is the local source of truth for execution state. Profile packs do not contain or restore PocketBase data — each install starts with an empty database.
