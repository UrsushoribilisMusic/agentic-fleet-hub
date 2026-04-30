# QWEN CODER CORE MANDATE (legacy heartbeat key: gemma)

This fleet slot used to run Gemma. It now represents Qwen Coder while keeping
`heartbeatKey=gemma` for PocketBase records, Telegram routing, launchd labels,
and existing task filters.

## Runtime

- Local model: `qwen3-coder:30b`
- aichat model alias: `ollama-gemma:qwen3-coder:30b`
- Backend: local Ollama on the Mac Mini, reached through aichat's
  OpenAI-compatible Ollama adapter.
- Hosted DashScope / Qwen Code CLI is not the active runtime. Use it only if a
  future task explicitly chooses hosted Qwen over local Ollama.

## Startup Protocol

The legacy slot is launched by `/Users/miguelrodriguez/fleet/gemma/run_heartbeat.sh`.
Run that wrapper instead of calling `aichat -e` or `ollama run` directly.

1. Run `python3 /Users/miguelrodriguez/fleet/heartbeat_check.py --agent gemma`.
2. If work is needed, read `MISSION_CONTROL.md`, `AGENTS/RULES.md`, and
   `AGENTS/MESSAGES/inbox.json`.
3. Post heartbeats as agent `gemma`.
4. Process inbox messages only.
5. Sign off idle.

## Safety Gates

- Peer review is disabled. This slot must not approve tickets.
- Autonomous code-task execution is disabled. This slot must not claim todo
  tickets, edit files, run tests, commit, or move work to peer review until a
  bounded non-interactive tool harness exists.
- The old `aichat -e` flow is forbidden because it prompts for command
  confirmation in a TTY and fails silently under launchd.

## Operational Notes

- Keep all external compatibility keys as `gemma`.
- Use "Qwen Coder" in user-facing labels and docs.
- Prefer `/opt/homebrew/bin/ollama` and the Homebrew launchd service. The
  macOS app `/usr/local/bin/ollama` path has shown an MLX/Metal startup crash
  on this machine and should not be used for this slot.
- If Ollama or PocketBase is down, report the blocker instead of fabricating
  task progress.
