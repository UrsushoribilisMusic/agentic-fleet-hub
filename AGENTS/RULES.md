# Team Collaboration Rules (The Shared Memory System)

Welcome to the **Ursushoribilis Agentic Workspace**. These rules are followed by **Clau**, **Gem**, **Codi**, and **Misty**.

---

## GitHub & Commits

1.  **Branching Strategy**: Use clear, feature-based branches.
2.  **Commit Messages**: Standardize on prefixing (e.g., `feat:`, `fix:`, `docs:`).
3.  **Deploy Keys**: For SSH access, use the `github-clau`, `github-codi`, or `github-gem` aliases in your `~/.ssh/config`.
4.  **Action**: Every commit must be pushed immediately to ensure the next agent is up to date.

---

## Architecture & Memory

1.  **Project Root**: Every project MUST have an `ARCHITECTURE.md` file describing its core components and data flow.
2.  **README**: Every project MUST have a developer-friendly `README.md`.
3.  **Memory Updates**: If you learn something new or change an architectural pattern, update the corresponding file in `AGENTS/CONTEXT/` immediately.

---

## Kanban & Reporting

1.  **Standups**: All daily progress is reported in `standups/`.
2.  **Kanban Flow**: Ticket-based system tracked in `MISSION_CONTROL.md`.
    *   **In Progress**: Documented in the active session's standup.
    *   **Blocked**: Explicitly listed in the Blockers section of the standup.
3.  **Finalization**: A task is only "Done" when the code is pushed AND the standup is updated.
4.  **Ticket Authority**: The Ticket Status table in `MISSION_CONTROL.md` is the ONLY source of truth for open tickets. Do NOT pick up a ticket mentioned anywhere else -- examples, old standups, context docs. If it is not in that table, it does not exist for you.
5.  **Ticket Links**: Every new ticket added to the open ticket table in `MISSION_CONTROL.md` must include its GitHub issue or project URL in the notes/status columns so Flotilla can link the Kanban card back to the source item.

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
