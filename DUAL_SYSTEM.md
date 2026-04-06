# Dual Sync Strategy: MISSION_CONTROL.md & PocketBase

As of 2026-04-05, the Ursushoribilis Agentic Fleet utilizes a **Dual Sync Strategy** (Option 1) to manage project state and task execution.

## 1. Core Principles

- **MISSION_CONTROL.md**: The source of truth for **Project Goals**, high-level status, and manual project context. It is designed for human readability and high-level alignment.
- **PocketBase (PB)**: The source of truth for **Task Execution**, real-time state tracking, and automated agent routing. It provides the granular data needed for the Fleet Dispatcher.

## 2. Synchronization Logic

The Fleet Dispatcher (`dispatcher.py`) monitors both sources to ensure the fleet remains responsive:
1. **File Watcher**: Monitors `MISSION_CONTROL.md` and `inbox.json` using SHA-256 checksums.
2. **PB Watcher**: Monitors the `tasks` collection in PocketBase by tracking the latest `updated` timestamp.
3. **Trigger**: Any change in either system triggers a full dispatch cycle.

## 3. Workflow for Agents

- **Startup**: Agents must read `MISSION_CONTROL.md` to synchronize with the latest project goals.
- **Execution**: Agents fetch their assigned tasks from PocketBase and update status (`in_progress`, `peer_review`, etc.) via the PB API.
- **Reporting**: Agents post session summaries and task outputs as comments in PocketBase.
- **Closing**: Agents update `MISSION_CONTROL.md` only when a major milestone or ticket status change occurs (though the primary execution tracking is in PB).

## 4. Why Option 1?

We chose the Dual System over a single-source-of-truth approach to:
- Maintain high-level project context that is difficult to capture in a database schema.
- Allow for manual "human in the loop" adjustments in Markdown.
- Provide a robust, API-driven execution layer for the agents.

---
*Status: Implemented in Dispatcher v4.0.0 (2026-04-05)*
