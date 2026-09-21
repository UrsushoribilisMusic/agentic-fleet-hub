# Council Cloud Sync And Ticket Gate

Last updated: 2026-09-21

This document records the hybrid Fleet Hub work that made the Council Protocol visible on the public Fleet dashboard while keeping execution gated by Miguel.

## What Changed

The Fleet Hub now supports the hybrid deployment model:

- PocketBase and the agent fleet keep running locally on the Mac Mini.
- The public Fleet Hub runs on `https://api.robotross.art/fleet/`.
- The Mac pushes a read-only snapshot to the cloud through `fleet/fleet_push.py`.
- The cloud `salesman-api` serves Council data from that snapshot when it cannot reach local PocketBase.
- Council-generated work is created as backlog work, not dispatchable work.

The immediate goal was to make the public Fleet page useful without giving the cloud server uncontrolled write access to the local operational database.

## Repositories And Files

Local fleet runtime repository:

- `fleet/fleet_push.py`
- `fleet/council_brief_ticketer.py`
- `docs/council_pocketbase.md`
- `docs/council_cloud_sync_and_ticket_gate.md`

Cloud/API repository:

- `salesman-cloud-infra/opt/salesman-api/server.mjs`
- `salesman-cloud-infra/opt/salesman-api/fleet/dashboard.html`
- `salesman-cloud-infra/opt/salesman-api/fleet/assets/main.js`
- `salesman-cloud-infra/opt/salesman-api/fleet/README.md`

Cloud host paths:

- `/opt/salesman-api/server.mjs`
- `/opt/salesman-api/fleet/dashboard.html`
- `/opt/salesman-api/fleet/assets/main.js`
- `/opt/salesman-api/fleet/AGENTS/CONFIG/fleet_meta.json`
- `/var/lib/salesman-api/fleet_snapshot.json`

## Snapshot Sync

`fleet/fleet_push.py` now includes Council collections in the pushed snapshot:

- `goals`
- `deliberations`
- `decision_briefs`
- `research_sources`
- `research_claims`

These are pushed along with the existing heartbeats, tasks, comments, financial data, standups, and project metadata.

The live launchd job is `fleet.push`. It runs the push connector with:

- `FLEET_SYNC_INTERVAL_SEC=3600`
- `FLEET_SYNC_TOKEN` from the launchd environment
- destination defaulting to `https://api.robotross.art/fleet/snapshot`

Manual one-shot push:

```sh
FLEET_SYNC_TOKEN="<token from launchd>" \
python3 /Users/miguelrodriguez/projects/agentic-fleet-hub/fleet/fleet_push.py --once
```

Do not commit the token. To inspect the launchd job locally:

```sh
launchctl print gui/$(id -u)/fleet.push
```

## Cloud Read Fallback

The cloud server still tries PocketBase first for Council API reads. If PocketBase is unavailable, it falls back to `/var/lib/salesman-api/fleet_snapshot.json`.

Fallback-backed endpoints:

- `GET /fleet/api/council/goals`
- `GET /fleet/api/council/goals/:id`
- `GET /fleet/api/council/deliberations`
- `GET /fleet/api/council/decision-briefs`
- `GET /fleet/api/council/research/sources`
- `GET /fleet/api/council/research/claims`

The public API response includes `source: "fleet_snapshot"` when data comes from the pushed snapshot.

Useful public checks:

```sh
curl -sS 'https://api.robotross.art/fleet/api/council/goals?sort=-updated' \
  | jq '{source, count:(.items|length), items:[.items[]|{id,title,status}]}'

curl -sS 'https://api.robotross.art/fleet/api/council/decision-briefs?goal_id=9d65356kzd6w9hv' \
  | jq '{source, count:(.items|length), items:[.items[]|{id,status,approved_by,goal_id}]}'
```

Expected state after the cleanup on 2026-09-21:

- one canonical FCP-5 goal remains visible
- goal id: `9d65356kzd6w9hv`
- decision brief id: `twisju1b46j4723`
- brief status: `ticketed`

## Browser Write Path

The Fleet dashboard no longer writes directly from the browser to `http://localhost:8090`.

Removed browser-side fallbacks included direct writes for:

- goal intake
- decision brief approval/rejection/change requests
- research claim creation

The browser now calls the Fleet API only. This matters because a public browser cannot treat `localhost:8090` as Miguel's Mac Mini, and direct PocketBase fallbacks bypass server-side guardrails.

## Ticket Approval Gate

The intended workflow is:

1. Miguel creates or reviews a Council goal.
2. Agents deliberate and synthesize a decision brief.
3. Miguel reviews the synthesized brief and clicks `Approve Ticket Plan`.
4. `fleet/council_brief_ticketer.py` processes approved briefs.
5. Generated GitHub issues and PocketBase tasks are created in backlog.
6. Miguel explicitly releases selected tasks from backlog before the fleet works them.

The ticketer hard gate is:

- `decision_briefs.status == "approved"`
- `decision_briefs.approved_by` is non-empty
- `ticket_plan` is a parseable non-empty list
- every ticket has a title

If the ticket plan is ambiguous, the brief is moved back to `waiting_human`.

Generated GitHub issues use:

- `flotilla-managed`
- `flotilla:backlog`
- optional `agent:<agent>` label

Generated PocketBase tasks use:

- `status: "backlog"`
- `gh_issue_id`
- `github_issue_url`
- `github_repo`
- `goal_id`
- scratchpad text warning that the backlog gate is active

The dispatcher should not treat `backlog` as dispatchable.

## FCP-5 Cleanup

The earlier Council test run produced duplicate FCP-5 goals and briefs. Cleanup left the most advanced canonical record:

- kept goal: `9d65356kzd6w9hv`
- kept brief: `twisju1b46j4723`
- duplicate test goals were closed
- duplicate FCP-5 decision briefs were rejected

Generated FCP-5 tickets were parked in backlog:

- GitHub `#1089`: `FTS-1: SQLite schema and FTS5 virtual table`
- GitHub `#1090`: `FTS-2: Markdown parser and incremental tokenizer`
- GitHub `#1091`: `FTS-3: Fleet Hub search integration and CLI`

The corresponding PocketBase task records were created with status `backlog`.

## Project Portfolio Fixes

The public and local Fleet portfolio were reconciled to use the same metadata source.

Confirmed public state:

- 13 projects
- `Agentic Fleet Hub (Flotilla)` has `Arch`
- `Tech Shorts` has `Stats` and `Insights`
- standalone sidebar `Arch` and `Insights` entries were removed

The metadata source is:

```text
AGENTS/CONFIG/fleet_meta.json
```

On the cloud host it is deployed to:

```text
/opt/salesman-api/fleet/AGENTS/CONFIG/fleet_meta.json
```

## Deploy Notes

Cloud service:

```sh
systemctl status salesman-api
systemctl restart salesman-api
```

Files copied during the 2026-09-21 deployment:

```text
opt/salesman-api/server.mjs
opt/salesman-api/fleet/dashboard.html
opt/salesman-api/fleet/assets/main.js
AGENTS/CONFIG/fleet_meta.json
```

Post-deploy checks:

```sh
curl -sS 'https://api.robotross.art/fleet/api/config' \
  | jq '{project_count:(.projects|length), flotilla:(.projects[]|select((.title // "")|test("Agentic Fleet Hub"))|{title, webStats, archLink}), tech_shorts:(.projects[]|select(.title=="Tech Shorts")|{title, statsLink, insightsLink})}'

curl -sS 'https://api.robotross.art/fleet/api/council/goals?sort=-updated' \
  | jq -r '.source + " " + ((.items|length)|tostring)'
```

Expected output for the second check:

```text
fleet_snapshot 1
```

## Current Limitation

The cloud page has read sync, not full write sync.

The public Fleet dashboard can display Council state from snapshots. Creating goals, approving briefs, or adding research claims from the cloud still requires either:

- direct server access to local PocketBase, or
- a queued write bridge from cloud to Mac Mini.

The current implementation intentionally does not hide that gap with browser-side `localhost` fallbacks. The next hardening step is a command queue/write bridge so cloud actions can be submitted publicly and applied locally by an authenticated Mac-side worker.

