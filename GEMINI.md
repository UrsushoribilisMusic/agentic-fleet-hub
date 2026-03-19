# GEM CORE MANDATE (Gemini CLI -- Shared Context Hub)

## Startup Protocol -- follow this order every session, no exceptions

1. `git pull origin master` -- get the latest state from the team.
2. Run: `python fleet/heartbeat_check.py --agent gem`
   - **Exit 1**: nothing relevant changed -- post idle heartbeat and stop. Do NOT read any further files.
   - **Exit 0**: changes need your attention -- continue with steps 3-6 below.
3. Run: `python fleet/active_context.py` -- prints the active project, the correct MISSION_CONTROL.md path, inbox path, and lessons paths. Note them.
4. Read the **Mission Control** at the path from step 3 -- live ticket status and current priorities.
   - If a non-hub project is active, also `cd` to that repo and `git pull origin master`.
5. Read `AGENTS/RULES.md` -- team rules.
6. **Check your IAP inbox**: Read the inbox path from step 3. Read ALL unread messages before proceeding.
7. Only then: pick up the first open ticket from the Ticket Status table in the Mission Control you read.

## Team Protocols (The Shared Memory System)

1.  **Rules**: Read and follow the instructions in `AGENTS/RULES.md`.
2.  **Reporting**: Record your progress in the daily standup file located in `standups/`.
3.  **Communication**: Use clear Markdown headers and ticket IDs in your session reporting.
4.  **Action**: Commit and push your changes to ensure the next agent is up to date.

## Source of Truth

- **Context**: Refer to `AGENTS/CONTEXT/` for deep project history and architectural context.
- **Goal**: Keep the Mission Control and Standup files updated to ensure the next agent is fully up to speed.
- **Secrets Management**: NEVER look for or create `.env` files. Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows). See `vault/README.md` for details.

## Gemini Strengths
- **Context Handling**: Use for large-context synthesis, architectural mapping, and documentation-heavy tasks.
- **Infrastructure**: Use for cross-project integration and complex build/infra reasoning.
