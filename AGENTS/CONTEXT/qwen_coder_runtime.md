# Qwen Coder Local Runtime

The legacy Gemma fleet slot has been replaced by Qwen Coder, but the operational
key remains `gemma`.

## Compatibility Contract

- PocketBase task owner / heartbeat key: `gemma`
- Launchd label: `fleet.gemma`
- Telegram command: `/gemma`
- User-facing name: `Qwen Coder`
- Local model: `qwen3-coder:30b`
- aichat alias: `ollama-gemma:qwen3-coder:30b`

Do not rename the heartbeat key until all historical PB records, dispatcher
filters, Telegram routing, and dashboard references have a migration path.

## Runtime Choice

The active runtime is local Ollama via aichat:

```sh
aichat -m ollama-gemma:qwen3-coder:30b "Say OK"
```

DashScope and Qwen Code CLI are hosted alternatives, not the current fleet
runtime. They can be reconsidered later if local latency, model quality, or
Mac Mini reliability becomes unacceptable, but that would be a deliberate
cloud-runtime change with new secret handling and cost controls.

## Ollama / MLX / Metal Notes

Use the Homebrew Ollama binary and service path:

```sh
/opt/homebrew/bin/ollama
/opt/homebrew/opt/ollama/bin/ollama
```

Avoid the macOS app `/usr/local/bin/ollama` path for this slot. It has crashed
during MLX/Metal initialization on the Mac Mini with an `NSRangeException`
before model commands could complete. The fleet slot should reach Ollama
through the already-running local service and aichat alias instead of starting
ad hoc Ollama processes.

## Execution Policy

Autonomous code execution remains disabled. The wrapper may process inbox
messages and smoke prompts, but it must not:

- approve peer-review tickets,
- claim todo tickets,
- edit repository files,
- run tests as proof of task completion,
- commit or push changes,
- move work to `peer_review`.

Those actions require a tool-safe non-interactive harness with explicit command
allowlists, timeouts, captured exit codes, diff inspection, test reporting, and
truthful failure handling.
