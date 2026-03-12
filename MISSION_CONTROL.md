# 🚀 MISSION_CONTROL

Welcome to the **Ursushoribilis Agentic Workspace**. This is the primary entry point for **Clau**, **Codi**, and **Gem**. Read this first to synchronize state across the multi-agent crew.

---

## 🤝 Team Protocols (Shared Memory)

1.  **Rules & Guidelines**: Read and follow the [Team Rules](./AGENTS/RULES.md).
    *   **GitHub**: Commit and push all changes immediately.
    *   **Kanban**: Use ticket IDs (#1, #2, #9, #10) in your session reporting.
2.  **Daily Standups**: All logs are in the [standups/](./standups/) directory.
    *   **Action**: Update the standup before closing your session.
3.  **Core Context (The Source of Truth)**: All project-level architectural documentation is located in [AGENTS/CONTEXT/](./AGENTS/CONTEXT/).

---

## 📂 Project Manifest

| Project | Local Path | Description | Docs / Reference |
| :--- | :--- | :--- | :--- |
| **1. Salesman Infra** | `../salesman-cloud-infra/` | Cloud-side scripts, Caddy proxy. | [Infra Docs](../salesman-cloud-infra/README.md) |
| **2. Music Video Tool** | `../music-video-tool/` | Tooling for creating music videos and content. | [Project MD](./AGENTS/CONTEXT/music_video_tool.md) |
| **3. CRM-POC** | `../customer-mgmt/` | Customer & Agent relational management system. | [Context MD](./AGENTS/CONTEXT/crm_poc_context.md) |
| **4. The Lost Coins** | `../the-lost-coins/` | Narrative/Story-driven project. | [Story MD](./AGENTS/CONTEXT/the_lost_coins_story.md) |
| **5. Robot Ross** | *(Mac mini)* | **Master control** for the robot arm & painting. | [Artist MD](./AGENTS/CONTEXT/robot_ross_artist.md) |
| **6. Salesman (OpenClaw)** | `DigitalOcean` | OpenClaw gateway & **BobRossSkill** (public). | [Salesman MD](./AGENTS/CONTEXT/robot_ross_salesman.md) |

---

## 🔧 Core Infrastructure

*   **Command Center (Dashboard)**: Source: `./command-center/`. Focus: Management, Team, Projects, Rules, Standups.
*   **Stats Dashboard**: *Coming Soon* at `api.robotross.art/stats`.
*   **Key Manager**: Standardize on SSH Deploy Keys for GitHub. Use `github-codi` or `github-clau` aliases in `~/.ssh/config`.
*   **KeyVault**: **Infisical** (Standard for secrets management).

---

## 📍 Current Session Goals (2026-03-11)
- [x] Initial Hub Consolidation (`agentic-fleet-hub`).
- [x] Migrate Brains, Logs, and UI to the Hub.
- [ ] **Ticket #10: KeyVault (Infisical)**: Research and implement the secrets management layer (High Priority).
- [ ] **Ticket #9: Stats UI Extraction**: Move the Stats tab to `api.robotross.art/stats`.
- [ ] **Ticket #8**: Finalize `renderHeatmap` status (Verify with Codi).
- [ ] Clean up GitHub credentials for all agents.

**Status: HUB INITIALIZED. READY FOR SECRETS INTEGRATION.**
