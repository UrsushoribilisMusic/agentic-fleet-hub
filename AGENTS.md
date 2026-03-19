# CODI SHARED MANDATE (Codex and Shared Context Hub)

## Startup Protocol -- follow this order every session, no exceptions

1. `git pull origin master` -- get the latest state from the team.
2. Run: `python fleet/heartbeat_check.py --agent codi`
   - **Exit 1**: nothing relevant changed -- post idle heartbeat and stop. Do NOT read any further files. Do NOT commit.
   - **Exit 0**: changes need your attention -- continue with steps 3-6 below.
3. Run: `python fleet/active_context.py` -- prints the active project, the correct MISSION_CONTROL.md path, inbox path, and lessons paths. Note them.
4. Read the **Mission Control** at the path from step 3 -- live ticket status and current priorities.
   - If a non-hub project is active, also `cd` to that repo and `git pull origin master`.
5. Read `AGENTS/RULES.md` -- team rules.
6. Check your IAP inbox: read the inbox path from step 3. Read all unread messages before proceeding.
7. Only then: pick up the first open ticket from the Ticket Status table in the Mission Control you read.

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
