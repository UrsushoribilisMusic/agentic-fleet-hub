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

## Ticket Status (as of 2026-03-14)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
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
- **#42**: Clau fleet mandate + heartbeat protocol -- Clau. `~/fleet/clau/CLAUDE.md` created with 6-phase heartbeat protocol.
- **#43**: Fleet Hub: Tasks tab + Activity feed + Heartbeat indicators -- Gem. Board, activity feed, and heartbeat dots (PocketBase REST) live.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#32** | Mission Control format hardening | Clau | in_work | Normalize `**#N**` format, purge `status=closed` rows, document v1 Kanban contract |
| **#41** | Codi fleet mandate + heartbeat protocol | Codi | in_work | Create `~/fleet/codi/CLAUDE.md` with 6-phase heartbeat protocol |

**Status: OPEN-SOURCE PACKAGE PUBLISHED. `create-flotilla@0.1.0` is live on npm. Fleet always-on infrastructure live on Mac Mini.**

