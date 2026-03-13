# CLAU CORE MANDATE (Claude Code -- Shared Context Hub)

## Startup Protocol -- follow this order every session, no exceptions

1. `git pull origin master` -- get the latest state from the team.
2. Read `MISSION_CONTROL.md` -- live ticket status and current priorities.
3. Read `AGENTS/RULES.md` -- team rules.
4. **Check your IAP inbox**: Read `AGENTS/MESSAGES/inbox.json` -- messages from teammates are committed here. Read ALL unread messages before proceeding. They may change your priorities entirely.
5. Only then: pick up the first open ticket from the Ticket Status table in `MISSION_CONTROL.md`.

## Team Protocols (The Shared Memory System)

1.  **Rules**: Read and follow the instructions in `AGENTS/RULES.md`.
2.  **Reporting**: Record your progress in the daily standup file located in `standups/`.
3.  **Communication**: Use clear Markdown headers and ticket IDs in your session reporting.
4.  **Action**: Commit and push your changes to ensure the next agent is up to date.

## Source of Truth

- **Context**: Refer to `AGENTS/CONTEXT/` for deep project history and architectural context.
- **Goal**: Keep the Mission Control and Standup files updated to ensure the next agent is fully up to speed.
- **Secrets Management**: NEVER look for or create `.env` files. Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows). See `vault/README.md` for details.
