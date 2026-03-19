# CODI SHARED MANDATE (Codex and Shared Context Hub)

## Startup Protocol -- follow this order every session, no exceptions

1. `git pull origin master` -- get the latest state from the team.
2. Run: `python fleet/heartbeat_check.py --agent codi`
   - **Exit 1**: nothing relevant changed -- post idle heartbeat and stop. Do NOT read any further files. Do NOT commit.
   - **Exit 0**: changes need your attention -- continue with steps 3-5 below.
3. Read `MISSION_CONTROL.md` -- live ticket status and current priorities.
4. Read `AGENTS/RULES.md` -- team rules.
5. Check your IAP inbox: read `AGENTS/MESSAGES/inbox.json`. Read all unread messages before proceeding.
6. Only then: pick up the first open ticket from the Ticket Status table in `MISSION_CONTROL.md`.

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
