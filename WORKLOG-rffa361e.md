# rffa361e - Qwen Coder Fleet Slot

Task: Fleet: Replace legacy Gemma slot with Qwen Coder safely.

Branch note: `git switch -c task/rffa361e` failed because this environment could
not create `.git/refs/heads/task/rffa361e`. Work is kept scoped to this worklog,
the runtime mandate/docs, and dispatcher safety routing.

Plan:

1. Preserve `heartbeatKey=gemma` for PocketBase, Telegram, launchd, and dashboard compatibility.
2. Replace user-facing Gemma labels with Qwen Coder where they describe the live slot.
3. Route dispatcher launches through the existing safe heartbeat wrapper instead of direct `aichat`.
4. Document the active local runtime choice: aichat -> Ollama -> `qwen3-coder:30b`.
5. Keep peer review and autonomous code execution disabled until a bounded non-interactive harness exists.
6. Record Ollama path guidance: prefer Homebrew Ollama; avoid the macOS app path that has shown MLX/Metal startup crashes.
7. Add the safe `fleet/gemma/run_heartbeat.sh` wrapper to the repo and include it in `fleet/deploy_runtime.sh` so runtime deploys preserve the disabled execution policy.
