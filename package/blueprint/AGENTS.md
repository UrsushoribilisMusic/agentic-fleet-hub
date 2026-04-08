# {{ORG_NAME}} Shared Agent Mandate

## Startup Protocol -- follow this order every session, no exceptions

1. `git pull` -- get the latest state from the team.
2. Run: `python scripts/heartbeat_check.py --agent YOUR_ID` (if available)
3. Run: `python scripts/active_context.py` -- prints ALL active project blocks.
4. For EACH active project block:
   - If it is a non-hub project, `cd` to its `repo_path` and `git pull`.
   - Read the **Mission Control** at the path from that block.
   - Note ALL open tickets assigned to you across all active projects.
5. Read `AGENTS/RULES.md` -- team rules.
6. Check your IAP inbox: read the inbox path from the first block (always hub inbox). Read all unread messages before proceeding.
7. Only then: pick up the first open ticket across all active project Mission Controls you read.

## Team Protocols

1. Rules: read and follow `AGENTS/RULES.md`.
2. Reporting: record progress in the daily standup file in `standups/`.
3. Communication: use clear markdown headers and ticket IDs in session reporting.
4. Action: commit and push your changes so the next agent is up to date.

## Source Of Truth

- Context: `AGENTS/CONTEXT/` for project history and architectural context.
- Goal: keep Mission Control and Standup files updated so the next agent is fully up to speed.
- Secrets management: never create or look for `.env` files. Use `vault/agent-fetch.sh` or `vault/agent-fetch.ps1`.

## Model-Specific Files

If a model-specific mandate file exists for your runtime, read it after this file:

- `CLAUDE.md` for Claude Code
- `GEMINI.md` for Gemini CLI
- `MISTRAL.md` for Mistral Vibe
