# CLAUDE CORE MANDATE (Shared Context Hub)

## 🚀 Startup Protocol
**Your absolute first action in every session is to read `MISSION_CONTROL.md` in this directory.** This file contains the live state of all projects, team rules, and current priorities for the Ursushoribilis crew (Gemini, Codi, and yourself).

## 🤝 Team Protocols (The Shared Memory System)
1.  **Rules**: Read and follow the instructions in `AGENTS/RULES.md`.
2.  **Reporting**: Record your progress in the daily standup file located in `standups/`.
3.  **Communication**: Use clear Markdown headers and ticket IDs (#1, #2) in your session reporting.
4.  **Action**: Commit and push your changes to ensure the next agent is up to date.

## 📂 Source of Truth
- **Context**: Refer to `AGENTS/CONTEXT/` for deep project history and architectural context.
- **Goal**: Keep the Mission Control and Standup files updated to ensure the next agent is fully "up to speed."
- **Secrets Management**: NEVER look for or create `.env` files. To fetch API keys or credentials, use `vault/agent-fetch.sh` (for Unix) or `.ps1` (for Windows). See `vault/README.md` for details.
