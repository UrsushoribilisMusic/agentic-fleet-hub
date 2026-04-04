# MISSION_CONTROL

Welcome to the **Ursushoribilis Agentic Workspace**. This is the primary entry point for **Clau**, **Gem**, **Codi**, and **Misty**. Read this first to synchronize state across the multi-agent crew.

---

## Team Protocols (Shared Memory)

1.  **Rules & Guidelines**: Read and follow the [Team Rules](./AGENTS/RULES.md).
    *   **GitHub**: Commit and push all changes immediately.
    *   **Kanban**: Use ticket IDs in your session reporting. Check the **Ticket Status** section below for what is currently open -- do not work on tickets not listed there.
2.  **Daily Standups**: All logs are in the [standups/](./standups/) directory.
    *   **Action**: Update the standup before closing your session.
3.  **Core Context (The Source of Truth)**: All project-level architectural documentation is located in [AGENTS/CONTEXT/](./AGENTS/CONTEXT/).

---

## Project Manifest

| Project | Local Path | Description | Docs / Reference |
| :--- | :--- | :--- | :--- |
| **1. Salesman Infra** | `../salesman-cloud-infra/` | Cloud-side scripts, Caddy proxy. | [Infra Docs](../salesman-cloud-infra/README.md) |
| **2. Music Video Tool** | `../music-video-tool/` | Tooling for creating music videos and content. | [Project MD](./AGENTS/CONTEXT/music_video_tool.md) |
| **3. CRM-POC** | `../crm-poc/` | Customer & Agent relational management system. | [Context MD](./AGENTS/CONTEXT/crm_poc_context.md) |
| **4. The Lost Coins** | `../the-lost-coins/` | Narrative/Story-driven project. | [Story MD](./AGENTS/CONTEXT/the_lost_coins_story.md) |
| **5. Robot Ross** | *(Mac mini)* | **Master control** for the robot arm & painting. | [Artist MD](./AGENTS/CONTEXT/robot_ross_artist.md) |
| **6. Salesman (OpenClaw)** | `DigitalOcean` | OpenClaw gateway & **BobRossSkill** (public). | [Salesman MD](./AGENTS/CONTEXT/robot_ross_salesman.md) |

---

## Core Infrastructure

*   **Fleet Hub**: `api.robotross.art/fleet/` (private, OAuth). Source: `salesman-cloud-infra/opt/salesman-api/`.
*   **Public Demo**: `api.robotross.art/demo/` -- generic Agentic CRM showcase (North Star demo).
*   **Growth Template**: `api.robotross.art/growth/` -- Sales & Marketing fleet demo.
*   **Stats Dashboard**: `api.robotross.art/stats/` -- live content analytics.
*   **Key Manager**: SSH Deploy Keys per agent (`github-clau`, `github-codi` in `~/.ssh/config`).
*   **KeyVault**: Infisical EU (`https://eu.infisical.com/api`). Use `vault/agent-fetch.sh` or `vault.py`. **Never commit secrets or `.env` files.**
*   **IAP Inbox**: Read `AGENTS/MESSAGES/inbox.json` at session start. Post messages by committing to the same file.

---

## Ticket Status (as of 2026-03-27)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
- **#83**: Sync ~/fleet/gem/ — Synced workspace scripts with root versions to ensure latest circuit breaker logic is active. — Gem. Approved.
- **#82**: Fleet Hub: Add "Blocked" filter — Added "Blocked" column to Kanban board for tasks marked as blocked or caught in the circuit breaker. — Gem. Approved.
- **#81**: [bug] dispatcher: circuit breaker — Implemented circuit breaker (target-online guard, cooldown, freeze) and Telegram command bypass. — Gem. Approved.
- **#80**: Release create-flotilla v0.3.0 to npm -- Performed pre-publish verification and closed at user request. -- Gem. Approved.
- **#79**: Sync /demo and /growth with v0.3.0 Features — Updated public-facing demo and growth pages to reflect the latest fleet capabilities (Kanban, snapshots, monitoring). -- Gem. Approved.
- **#78**: Fleet Hub UI: Dark/Light Mode & Redesign — Applied the developer tool aesthetic, CSS token system, and dark/light mode toggle to all fleet dashboards. -- Gem. Approved.
- **#77**: Update create-flotilla to v0.3.0 — integrated dispatcher health, dynamic Telegram commands, GitHub sync v2, and project switching. Passed verify:dry-run. -- Gem. Approved.
- **#66**: Agent health monitoring + skill-based task reassignment -- Gem. Implemented in dispatcher.py and workspace UI. Approved.
- **#1-#6**: Sheets migration, tracker API, OAuth wired -- Team.
- **#7-#9**: Stats UI, heatmap, dashboard extraction -- Gem.
- **#10**: KeyVault (Infisical EU) -- wired into music-video-tool and CRM -- Clau.
- **#14-#19**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake -- Team.
- **#23**: README + docs overhaul -- Gem.
- **#24**: Onboarding wizard + Doctor + commit step -- Codi.
- **#25**: Demo cleanup -- generic agents, Agentic CRM as North Star -- Gem.
- **#26**: EU Compliance Review -- Misty. COMPLIANCE.md v2 with gap table for audit logs, multi-agent transparency, Cybersecurity Act classification.
- **#27**: Fleet config -- absorbed into #24. meta.installation block in fleet_meta.json -- Codi.
- **#28**: Fleet Doctor -- absorbed into #24 -- Codi.
- **#29**: GEMINI.md template -- Gem. Added to blueprint.
- **#22**: npx create-flotilla installer -- Codi. Published as create-flotilla@0.1.0.
- **#30**: Flotilla Kanban parser + normalized ticket model -- Codi. GET /fleet/api/kanban live.
- **#31**: Flotilla Kanban UI tab -- Gem. 3-column unified board + refresh logic live.
- **#33**: Add search to Memory Tree -- Gem. Dynamic filtering for docs and lessons live.
- **#34**: Install PocketBase + create DB schema -- Gem. ARM binary installed, 5 collections with API rules live.
- **#35**: Create `~/fleet/` directory structure -- Clau. All agent workspace dirs created, MISSION_CONTROL in position.
- **#36**: Build `dispatcher.py` + Telegram notifications -- Gem. Dispatcher live with Mac Mini paths, Telegram notify for waiting_human.
- **#37**: Create fleet Python venv -- Clau. `~/fleet/.venv` created with `requests`.
- **#40**: Gem fleet mandate + heartbeat protocol -- Gem. `~/fleet/gem/GEMINI.md` created with 6-phase heartbeat protocol.
- **#38**: launchd plists: PocketBase + dispatcher -- Clau. Both KeepAlive services running. Dispatcher live via infisical run (TELEGRAM_TOKEN injected from vault).
- **#39**: launchd heartbeat plists: Gem + Codi -- Clau. Staggered at :00 and :02, node path fixed for launchd limited PATH.
- **#41**: Codi fleet mandate + heartbeat protocol -- Codi. `~/fleet/codi/CLAUDE.md` created with 6-phase heartbeat protocol, `~/fleet/codi/PROGRESS.md` initialized.
- **#44**: Live Fleet auth/bootstrap and dashboard recovery -- Codi. Fixed `api.robotross.art/fleet` login loop, restored lessons/inbox/standups/user management, redeployed `salesman-api`, and documented the auth failure in lessons learned.
- **#42**: Clau fleet mandate + heartbeat protocol -- Clau. `~/fleet/clau/CLAUDE.md` created with 6-phase heartbeat protocol.
- **#43**: Fleet Hub: Tasks tab + Activity feed + Heartbeat indicators -- Gem. Board, activity feed, and heartbeat dots (PocketBase REST) live.
- **#32**: Mission Control format hardening -- Clau. `**#N**` format normalized, closed rows purged from OPEN table, status values corrected to spec. v1 Kanban contract documented in `AGENTS/CONTEXT/kanban_format_spec.md`.
- **#45**: Telegram Listener Bridge (Two-Way Chat) -- Gem. `telegram_bridge.py` deployed to `~/fleet/`, `fleet.bridge` launchd service running with Infisical secret injection. Two-way: inbound TG→PB, outbound PB comments→TG.
- **#46**: Telegram Bridge outbound truncation fix -- Clau. Fixed bridge stuck in retry loop on comments >4096 chars (Telegram limit). Truncates to 4096 with `...` suffix. Bridge restarted clean.
- **#47**: Big Bear homepage: Flotilla CTA and positioning refresh -- Codi. Hero repositioned around “The Docker of AI Agents,”
- **#70**: UI for project activation (toggle-based) -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Misty. Approved.
- **#72**: Service restart logic for project switching -- Misty. Approved.
- **#73**: Optimize heartbeat token usage -- checksum caching for MISSION_CONTROL.md -- Misty. Approved. (Superseded by #74 — partial, single-file, hard-coded paths)
- **#74**: Proper heartbeat gate -- `fleet/heartbeat_check.py` watches MISSION_CONTROL.md + inbox.json, checks agent relevance, exits 0/1. Wired into CLAUDE.md, GEMINI.md, MISTRAL.md startup protocols. Clutter scripts removed. .fleet_cache/ gitignored. -- Clau. Approved.
- **#69**: Add project-switching endpoint to the fleet API -- Misty. Partial: `POST /fleet/api/activate-project` sets `is_active` in fleet_meta.json. Superseded by #75. Approved.
- **#70**: UI for project activation (toggle-based) -- Misty. Partial: server-side only, dashboard reads active project MC. Full UI deferred to #75. Approved.
- **#75**: Fleet Steering -- proper project switching. `fleet/active_context.py` resolves active project paths at runtime. `heartbeat_check.py` extended to watch active project MC. `repo_path` added to all projects in fleet_meta.json. All 4 mandate files updated. ARCHITECTURE.md + fleet_steering_architecture.md written. -- Clau. Approved.
- **#zs9ch0t61fxivdn**: Review of Heartbeat Gate (#74) and Fleet Steering (#75). Fixed Python 3.9 compatibility and added dynamic alias loading. -- Gem. Approved.
- **#76**: Fleet Hub UI: project-switch toggle. POST /fleet/api/activate-project added to server.mjs. Projects grid shows ACTIVE badge + SET ACTIVE button. Git sync attempted on activate (graceful fail if no deploy key). Package engineering dashboard updated. -- Clau. Approved.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#84** | Hybrid Sync - MISSION_CONTROL.md <=> PocketBase | Gem | todo | Implement fleet_sync.py to bi-directionally sync the Markdown execution table with PocketBase state. |

**Status: `create-flotilla@0.3.0` live on npm as of 2026-03-24. Planning for v0.4.0 in progress.**

