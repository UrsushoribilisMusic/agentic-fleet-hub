# Release Notes - create-flotilla v0.4.0

## Release Summary
**Version**: 0.4.0  
**Date**: 2026-04-05  
**Status**: Stable  

This release focuses on "Observability & Efficiency." We are introducing the **Schichtplan** (Shift Timeline) to visualize agent activity, and **Dispatcher v4.0** which brings a massive reduction in token consumption through the new Checksum Gate.

---

## 🚀 New Features

### 1. Schichtplan (Agent Shift Timeline)
- **Visual Activity Tracking**: A new swim-lane chart in the Engineering Dashboard.
- **Historical Windows**: Toggle between 24h, 7d, and 30d views.
- **Status Color Coding**:
    - `Green`: Agent is working/active.
    - `Grey`: Agent is idle/online.
    - `Red`: Dark/Quota (Gap > 2h detected during scheduled windows).
    - `Orange`: Agent is offline.
- **Pure CSS**: Highly performant, zero-dependency rendering.

### 2. Aggregate Stats Panel
- **Performance at a Glance**: New metrics section above the agent table.
- **Key Metrics**:
    - Total Tasks Completed (today vs all-time).
    - Aggregate Token Consumption estimates.
    - Average Session Duration.
    - Agent Success Rate (Approved vs Rejected tasks).

### 3. Dispatcher v4.0
- **Checksum Gate**: The dispatcher now calculates SHA-256 checksums for `MISSION_CONTROL.md` and `inbox.json`. If no changes are detected and no tasks are pending in PocketBase, agents stay in "Sleep" mode, saving thousands of tokens per day.
- **Dual Sync Strategy**: Native support for the "Option 1" workflow. `MISSION_CONTROL.md` remains the goal-setting source of truth, while PocketBase handles the execution state.
- **Task Event Logging**: Every status transition, reassignment, and circuit breaker event is now logged to a structured `task_events` collection for auditability.
- **Circuit Breaker**: Detects "ping-pong" reassignments (e.g., when two agents are offline and a task keeps bouncing) and auto-blocks the task after 5 attempts, notifying the human via Telegram.

### 4. Branch-Aware Reassignment
- When a task is reassigned (e.g., due to an agent hitting a context limit), the dispatcher now checks GitHub for a corresponding `task/{id}` branch.
- If found, it includes the branch URL in the handoff comment, allowing the next agent to `git checkout` and resume work seamlessly using the `WORKLOG.md`.

---

## 🛠️ Internal Improvements
- **Enhanced Agents Table**: Added "Last Seen" and "Idle Until" columns to the Engineering Dashboard.
- **Auto-Standup Metrics**: The dispatcher now automatically injects session and task counts into the daily standup file.
- **Migration Logic**: Added PocketBase migrations for the new `task_events` collection.

## 📦 How to Upgrade
1. Update your global `create-flotilla` or run via npx:
   ```bash
   npx create-flotilla@0.4.0 <project-dir>
   ```
2. Run the `/configure/` wizard to apply new PocketBase schema changes.
3. Restart your always-on services (dispatcher and heartbeats).

---
*Built with ❤️ by the Ursushoribilis Agentic Crew (Gem, Clau, Codi).*
