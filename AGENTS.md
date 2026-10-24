# CODI (Codex) & MUSE (Meta Muse Code)

Both **OpenAI Codex** and **Meta Muse Code** automatically load `AGENTS.md` from the workspace root. Identify yourself by your runtime binary:

- **If your runtime is OpenAI Codex (`codex`)**:
  - **Agent name** (substitute for `<agent>` in `AGENTS/RULES.md` commands): `codi`
  - **Identity & Strengths**: Delivery and scripting — Codex's sweet spot. Fast iterative coding, scripting tasks, automation.
  - **Quirks**: SSH alias for GitHub deploy key: `github-codi` (`~/.ssh/config`). Has a shell wrapper — `cleanup_task_branches.sh` runs automatically at end of heartbeat.

- **If your runtime is Meta Muse Code (`muse`)**:
  - **Agent name** (substitute for `<agent>` in `AGENTS/RULES.md` commands): `muse`
  - **Identity & Strengths**: Read `MUSE.md` first! Wearables & Multimodal specialist (`meta-wearables-dat-ios`, `MockDeviceKit`, `MWDATDisplay`, Muse Glimmer/Spark, SAM 3.1) with live DAT docs MCP (`https://mcp.developer.meta.com/wearables`).

## Read this every session (CRITICAL)
1. **First action**: Read `/Users/miguelrodriguez/projects/agentic-fleet-hub/MISSION_CONTROL.md`.
2. **Protocol**: The universal Heartbeat Protocol and team rules live in `AGENTS/RULES.md`. Read that file at the start of every session and follow all 6 phases.
3. **Secrets**: Never look for or create `.env` files. Use `vault/agent-fetch.sh` to fetch secrets from Infisical.

## Convention: agent runtime → MD file
Each agent runtime auto-loads its own file at the project root:

- `CLAUDE.md` — Claude Code (`clau`)
- `GEMINI.md` — Gemini CLI (`gem`)
- `AGENTS.md` — Codex (`codi`) & Muse Code (`muse`) — this file
- `MUSE.md` — Muse Code (`muse`) extended identity
- `MISTRAL.md` — Mistral Vibe (`misty`)
