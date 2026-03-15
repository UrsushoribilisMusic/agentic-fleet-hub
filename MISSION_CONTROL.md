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

## Ticket Status (as of 2026-03-15)

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
- **#41**: Codi fleet mandate + heartbeat protocol -- Codi. `~/fleet/codi/CLAUDE.md` created with 6-phase heartbeat protocol, `~/fleet/codi/PROGRESS.md` initialized.
- **#44**: Live Fleet auth/bootstrap and dashboard recovery -- Codi. Fixed `api.robotross.art/fleet` login loop, restored lessons/inbox/standups/user management, redeployed `salesman-api`, and documented the auth failure in lessons learned.
- **#42**: Clau fleet mandate + heartbeat protocol -- Clau. `~/fleet/clau/CLAUDE.md` created with 6-phase heartbeat protocol.
- **#43**: Fleet Hub: Tasks tab + Activity feed + Heartbeat indicators -- Gem. Board, activity feed, and heartbeat dots (PocketBase REST) live.
- **#32**: Mission Control format hardening -- Clau. `**#N**` format normalized, closed rows purged from OPEN table, status values corrected to spec. v1 Kanban contract documented in `AGENTS/CONTEXT/kanban_format_spec.md`.
- **#45**: Telegram Listener Bridge (Two-Way Chat) -- Gem. `telegram_bridge.py` deployed to `~/fleet/`, `fleet.bridge` launchd service running with Infisical secret injection. Two-way: inbound TG→PB, outbound PB comments→TG.
- **#46**: Telegram Bridge outbound truncation fix -- Clau. Fixed bridge stuck in retry loop on comments >4096 chars (Telegram limit). Truncates to 4096 with `...` suffix. Bridge restarted clean.
- **#47**: Big Bear homepage: Flotilla CTA and positioning refresh -- Codi. Hero repositioned around “The Docker of AI Agents,”
- **#48**: Telegram bot `/commands` + real PocketBase task routing -- Clau. Registered 9 slash commands via setMyCommands. All commands (/clau /gem /codi /ask /spec /go /status /tasks /help) now create real PocketBase tasks or query/reply inline. Bridge restarted.
- **#49**: Fix Codi launchd invocation — trusted directory error -- Codi+Clau. Codi updated `dispatcher.py` with `-C agentic-fleet-hub --add-dir fleet` flags. Clau applied same fix to `fleet.codi.plist`. Both invocation paths now match; error resolved.
- **#50**: Add `/claw` Telegram command → OpenClaw gateway -- Clau. Enabled `gateway.http.endpoints.chatCompletions` in `~/.openclaw/openclaw.json`. Added `/claw` to fleet bridge — forwards message to `localhost:18789/v1/chat/completions`, replies inline synchronously.
- **#52**: Vault-safe OpenClaw bridge token resolution + docs sync -- Codi. Removed hardcoded gateway token from telegram bridge, resolve token from Infisical-injected env or local OpenClaw config, synced live/package/blueprint bridge code, and documented Telegram command routing plus secret-handling rules.
- **#51**: Fix dispatcher `waiting_human` notification spam -- Gem. Added de-dup cooldown (1h) and verified human-reply-to-todo-flip logic. Dispatcher live in `~/fleet/`.
- **#54**: Update demo page -- showcase new Agentic CRM fleet features -- Gem. Updated `api.robotross.art/demo/` with Kanban board, live heartbeat indicators, and activity feed.
- **#55**: Update growth page -- reflect new fleet capabilities in Sales & Marketing demo -- Gem. Updated `api.robotross.art/growth/` with live tracking and coordination highlights.
- **#56**: Sync /demo and /growth UI assets to match /fleet redesign -- Gem. Copied updated dashboard.html, assets/main.js, assets/style.css from /fleet/ to /demo/ and /growth/ on DO server.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#53** | Release create-flotilla v0.2.0 -- include new fleet features | Codi | in_work | Consolidates PB tasks #47 and #50. Includes PocketBase schema, Dispatcher, Telegram Bridge, and Kanban UI. |
| **#57** | GitHub Issues ↔ PocketBase two-way sync | Clau | planned | Outbound: task create/update → open/label/close GitHub Issue (tag `flotilla-managed`). Inbound: poll GH for human-written issues → create PB task. Add gh_issue_id field to tasks collection. Closes gap between product promise and actual behavior. |
| **#56** | Sync /demo and /growth UI assets to match /fleet redesign | Gem | done | ✓ Completed. |
| **#62** | /demo polish — kanban, memory, standups, user mgmt, modal scroll | Gem | todo | BEFORE #60. A) Fix phantom kanban ticket + 5 demo tickets. B) Memory links raw + emoji mojibake (check server utf-8 + strip emojis from docs). C) Remove duplicate Mar-13 standup. D) /demo+/growth only: mock emails, intercept Add actions with "would've done" modal. E) Modal scroll fix (max-height+overflow) — applies to /fleet too. |
| **#60** | Populate /demo with realistic mock data (4 agents) | Gem | todo | AFTER #62. Consistent mock data: fleet_meta (Aria/Rex/Nova/Sage), inbox, lessons, standups (2 days), kanban. ShopFlow project. Must feel like a real working team. |
| **#61** | Fleet Hub UI redesign — tool aesthetic + dark/light mode | Gem | todo | AFTER #60. 3 phases: (1) CSS token system + dark/light toggle, (2) sidebar nav + layout restructure, (3) component polish. /fleet is reference; /fleet UI is also the main install package UI. /demo+/growth keep warmer palette but inherit toggle. |
| **#63** | Fix hybrid deployment — push connector Mac Mini → DO server | Codi | todo | fleet_push.py posts PB snapshot to DO server every 60s via FLEET_SYNC_TOKEN. server.mjs caches and serves it. Fixes our grey dots. Packaged as optional Scenario 3 setup. |
| **#64** | Heartbeat dots — mock status in /demo+/growth, tooltip on all | Gem | todo | A) /demo+/growth: generate mock working/idle status when API returns empty. B) All pages: styled tooltip on hover showing agent + status + last seen. Mobile-friendly. |
| **#65** | Document 3 deployment scenarios in getting-started guide | Gem | todo | Local (default), Cloud VPS (single server), Hybrid (agents local + dashboard remote). Scenario 3 CTA: contact us. Add to README or docs/DEPLOYMENT.md. |
| **#58** | Dynamic Telegram bot commands from fleet_meta.json | Codi | todo | Generate BOT_COMMANDS at runtime from fleet_meta agent roster (heartbeatKey = command name). Re-register with setMyCommands on each bridge restart. |
| **#59** | Make OpenClaw integration optional in package and bridge | Codi | todo | Bridge: ping gateway at startup, skip /claw if unreachable (silent degradation). Installer: opt-in prompt for OpenClaw. Docs: mark as optional. Corporate environments must work without it. |


**Status: OPEN-SOURCE PACKAGE PUBLISHED. `create-flotilla@0.1.0` is live on npm. Fleet always-on infrastructure live on Mac Mini.**
