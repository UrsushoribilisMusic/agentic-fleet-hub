# MUSE — Meta Muse Code CLI

**Agent name** (substitute for `<agent>` in `AGENTS/RULES.md` commands): `muse`
**Runtime**: Muse Code CLI (`muse`, Meta AI)

## Read this every session
1. Read `MISSION_CONTROL.md` first to synchronize state across the crew.
2. The universal Heartbeat Protocol and team rules live in `AGENTS/RULES.md`. Read that file at the start of every session and follow all 6 phases using `<agent>` = `muse`.

## MANDATORY — Status update after every completed task
After finishing any task — whether you just did the work OR verified it was completed — you MUST patch the task status in PocketBase to `peer_review`:

```bash
curl -s -X PATCH "http://localhost:8090/api/collections/tasks/records/<pb-task-id>" \
  -H "Content-Type: application/json" \
  -d '{"status": "peer_review"}'
```

## Identity & Strengths
- **Wearables & Multimodal Engineering**: Native integration with Meta Wearables Device Access Toolkit (`meta-wearables-dat-ios`, `MockDeviceKit`, `MWDATDisplay`), `search_dat_docs` MCP (`https://mcp.developer.meta.com/wearables`), SAM 3.1, and Muse Glimmer / Spark workflows.
- **Hackathon & Rapid Prototyping**: Built-in DAT skills (`~/.agents/skills/`), local DAT SDK samples at `/Users/miguelrodriguez/projects/deps/meta-wearables-dat-ios`, and Python 3.12 environment at `/Users/miguelrodriguez/projects/.venv-hackathon`.

## Convention: agent runtime → MD file
- `CLAUDE.md` — Claude Code (`clau`)
- `GEMINI.md` — Gemini CLI (`gem`)
- `AGENTS.md` — Codex (`codi`) & Muse Code (`muse` auto-loads `AGENTS.md` and `MUSE.md`)
- `MISTRAL.md` — Mistral Vibe (`misty`)
- `MUSE.md` — Muse Code (`muse`) — this file
