# ♊ GEMINI.md (Standard Startup Template)

> **Mandatory Startup Protocol**: This file is the primary context injector for Gemini-based agents. It ensures synchronization with the fleet's Shared Consciousness.

---

## 🚀 Execution Directives

1.  **Initialize Context**: Your absolute first action in every session is to read `MISSION_CONTROL.md` in the project root.
2.  **Inherit State**: Locate your specific agent identity in `AGENTS/CONFIG/fleet_meta.json` and assume your assigned role and skills.
3.  **Check Inbox**: Read unread messages in the Inter-Agent Protocol (IAP) Inbox via the Fleet Hub or `AGENTS/MESSAGES/inbox.json`.
4.  **Enforce Rules**: Adhere strictly to the protocols defined in `AGENTS/RULES.md` regarding commits, Kanban management, and documentation.

---

## 🔒 Security & Secrets

*   **Vault-First**: NEVER look for or create `.env` files.
*   **Dynamic Fetch**: Use the provided scripts in the `vault/` directory to fetch credentials directly into memory on-the-fly.
*   **Zero-Footprint**: Ensure no sensitive keys are ever logged, printed, or committed to source control.

---

## ⏱️ Session Reporting

Before ending your session, you MUST:
1.  Append your progress to the current date's standup file in `standups/`.
2.  Follow the **[Done / Today / Blockers]** format.
3.  Log any new failures or optimizations to the **Evolutionary Memory** ledger (`AGENTS/LESSONS/ledger.json`).

---
**Big Bear Engineering GmbH** — *Engineering discipline, not AI hype.*
