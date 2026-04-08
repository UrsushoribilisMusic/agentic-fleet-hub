# Team Collaboration Rules (The Shared Memory System)

Welcome to the **Ursushoribilis Agentic Workspace**. These rules are followed by **Clau**, **Gem**, **Codi**, and **Misty**.

---

## GitHub & Commits

1.  **Branching Strategy**: Use clear, feature-based branches.
2.  **Commit Messages**: Standardize on prefixing (e.g., `feat:`, `fix:`, `docs:`).
3.  **Deploy Keys**: For SSH access, use the `github-clau`, `github-codi`, or `github-gem` aliases in your `~/.ssh/config`.
4.  **Action**: Every commit must be pushed immediately to ensure the next agent is up to date.
5.  **Server = repo**: If you deploy a file directly to a production server (e.g. via SSH or `scp`), you MUST commit that same file to the repo in the same session. Never leave server-only changes uncomitted. The repo is the source of truth — if it is not in git, it does not exist.

---

## Architecture & Memory

1.  **Project Root**: Every project MUST have an `ARCHITECTURE.md` file describing its core components and data flow.
2.  **README**: Every project MUST have a developer-friendly `README.md`.
3.  **Memory Updates**: If you learn something new or change an architectural pattern, update the corresponding file in `AGENTS/CONTEXT/` immediately.

---

## Kanban & Reporting

1.  **Standups**: All daily progress is reported in `standups/`. Every entry heading MUST identify the agent — use the format `# Agent — Date (optional time UTC)`. Examples: `# Clau — 2026-04-06`, `# Codi — 2026-04-06 (14:32 UTC)`. Entries without an agent name in the heading are invalid and will be unattributable in the Fleet Hub dashboard. Do NOT use generic headings like `# Session (timestamp)`.
2.  **Kanban Flow**: Ticket-based system tracked in `MISSION_CONTROL.md`.
    *   **In Progress**: Documented in the active session's standup.
    *   **Blocked**: Explicitly listed in the Blockers section of the standup.
3.  **Finalization**: A task is only "Done" when the code is pushed AND the standup is updated.
4.  **Ticket Authority**: The Ticket Status table in `MISSION_CONTROL.md` is the ONLY source of truth for open tickets. Do NOT pick up a ticket mentioned anywhere else -- examples, old standups, context docs. If it is not in that table, it does not exist for you.
5.  **Ticket Links**: Every new ticket added to the open ticket table in `MISSION_CONTROL.md` must include its GitHub issue or project URL in the notes/status columns so Flotilla can link the Kanban card back to the source item.
6.  **Task Branch Protocol**: When you pick up a task, immediately create a branch named `task/{pb-task-id}` (e.g. `task/abc123xyz`) and push it. Before writing any code, commit a `WORKLOG.md` to that branch describing your plan: what you will do, in what order, and any key decisions. Commit incrementally as you work — each meaningful step gets its own commit. This ensures that if your session ends mid-task (context limit, quota, etc.), the next agent can check out the branch, read `WORKLOG.md` and the git log, and resume rather than starting from scratch. If you are resuming a task that already has a branch, check it out and continue from the last commit.
7.  **No Self-Approval**: An agent MUST NOT approve its own task. When you complete a task, move it to `peer_review` status and stop. A *different* agent must read the output, verify the work was actually done, and post the approval comment. If no peer is available in the same session, leave it in `peer_review` — it will be picked up at the next heartbeat. Marking your own work `approved` is a protocol violation regardless of how confident you are in the output.

---

## Data Integrity

1. **No fake data in real PocketBase**: When generating demo or example content (for `/demo/`, showcases, or testing), write it to static files under `opt/salesman-api/demo/` or to the hardcoded mock blocks in `server.mjs`. Never create fake tasks, heartbeats, or any records in the real PocketBase instance. The real PB is the live operational database — polluting it with hallucinated content breaks the kanban, the Fleet Hub dashboard, and audit logs.
2. **Demo data ownership**: The demo endpoints in `server.mjs` already have hardcoded mock blocks that bypass PocketBase entirely for `/demo/` requests. All demo data changes go there or in the static JSON files — not in PB.

---

## Secrets & Safety

1.  **Credential Protection**: Never commit secrets or API keys.
2.  **Vault Access**: Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows) to fetch secrets at runtime.
3.  **Communication**: Do not pass sensitive info in Markdown files.

---

## Inter-Agent Protocol (IAP)

- **Inbox**: Read `AGENTS/MESSAGES/inbox.json` at the start of every session. Messages from teammates may change your priorities.
- **Send**: Add a message object to `AGENTS/MESSAGES/inbox.json` and commit it.
- **Acknowledge**: Mark your messages as `"status": "read"` after acting on them and commit.
