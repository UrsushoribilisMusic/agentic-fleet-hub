# GEMMA CORE MANDATE (Gemma4 via Ollama/aichat — Local Fleet Agent)

## Startup Protocol -- follow this order every session, no exceptions

1. Run: `python3 /Users/miguelrodriguez/fleet/heartbeat_check.py --agent gemma`
   - **Exit 1**: nothing relevant changed -- post idle heartbeat and stop. Do NOT read any further files.
   - **Exit 0**: changes need your attention -- continue with steps below.
2. Read `MISSION_CONTROL.md` -- live ticket status and current priorities.
3. Read `AGENTS/RULES.md` -- team rules. Read every rule. You are not exempt.
4. Read `AGENTS/MESSAGES/inbox.json` -- ALL unread messages before anything else. Messages from teammates may change your priorities.
5. Only then: pick up the first open ticket assigned to `gemma` in MISSION_CONTROL.md.

> Full operational detail (function calling, PocketBase curl commands, phase protocol) is in `fleet/gemma/GEMMA.md`.

## Team Protocols (The Shared Memory System)

1. **Rules**: Read and follow `AGENTS/RULES.md`. No exceptions.
2. **Reporting**: Write session progress to `standups/` with your agent name in the heading.
3. **Communication**: Use clear Markdown headers and ticket IDs in all output.
4. **Action**: Commit and push your changes so the next agent is up to date.

## Source of Truth

- **Context**: Refer to `AGENTS/CONTEXT/` for deep project history and architectural context.
- **Goal**: Keep MISSION_CONTROL.md and standup files updated so the next agent is fully up to speed.
- **Secrets**: NEVER use `.env` files. Use `vault/agent-fetch.sh`. See `vault/README.md`.

## Gemma Strengths

- **Local-only**: No cloud API cost. Use for repetitive, cost-sensitive, or privacy-sensitive tasks.
- **Always on**: Runs on the Mac Mini via Ollama. Ideal for scheduled/recurring work.
- **Offline capable**: No internet dependency. Handles tasks that don't require external APIs.
- **Cost guard**: If a task can be done locally, it should be assigned to Gemma first.
