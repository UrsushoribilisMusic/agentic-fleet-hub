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
| **3. CRM-POC** | `../customer-mgmt/` | Customer & Agent relational management system. | [Context MD](./AGENTS/CONTEXT/crm_poc_context.md) |
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

## Ticket Status (as of 2026-03-13)

### CLOSED
- **#1-#6**: Sheets migration, tracker API, OAuth wired.
- **#7-#9**: Stats UI, heatmap, dashboard extraction.
- **#10**: KeyVault (Infisical EU) -- wired into music-video-tool and CRM.
- **#14-#19**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake.
- **#23**: README + docs overhaul (Gem).
- **#25**: Demo cleanup -- generic agents, Agentic CRM as North Star (Gem).
- **#26**: EU Compliance Review -- Misty. COMPLIANCE.md v2 complete: gap table with amber/open items for audit logs, multi-agent transparency, Cybersecurity Act classification.
- **#27**: Fleet config -- absorbed into #24. Codi implemented as meta.installation block inside fleet_meta.json.

### OPEN
| Ticket | Description | Owner | Notes |
| :--- | :--- | :--- | :--- |
| **#22** | `npx create-agentfleet` installer | Codi | Waiting on #24 |
| **#24** | Onboarding wizard (`/setup`) + Doctor | Codi | In progress. Scope: agent bootstrap, DACH naming check, fleet_config generation, doctor validation. |
| **#28** | Fleet Doctor (`doctor.py --fix`) | Codi | Absorbed into #24 final step. [GitHub issue](https://github.com/UrsushoribilisMusic/agentic-fleet-hub/issues/9) |
| **#29** | GEMINI.md template | Gem | Missing from blueprint. Needed for onboarding when Gemini is selected. |

**Status: OPEN-SOURCE PACKAGE IN PROGRESS.**
