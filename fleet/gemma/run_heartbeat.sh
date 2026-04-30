#!/usr/bin/env bash
# Qwen Coder heartbeat wrapper (legacy key: gemma).
# This wrapper intentionally does not perform peer review or code-task work.

set -euo pipefail

FLEET_DIR="/Users/miguelrodriguez/fleet"
GEMMA_DIR="$FLEET_DIR/gemma"
PB_URL="http://localhost:8090/api"
AGENT="gemma"
MODEL="${QWEN_CODER_MODEL:-ollama-gemma:qwen3-coder:30b}"
INBOX_FILE="/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json"
MC_FILE="$FLEET_DIR/MISSION_CONTROL.md"
CHECKSUM_FILE="$GEMMA_DIR/workspace/.last_checksum"

export QWEN_CODER_MODEL="$MODEL"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

post_heartbeat() {
  local status="$1"
  curl -s -X POST "$PB_URL/collections/heartbeats/records" \
    -H "Content-Type: application/json" \
    -d "{\"agent\":\"$AGENT\",\"status\":\"$status\"}" >/dev/null || true
}

mkdir -p "$GEMMA_DIR/workspace"

mc_sum=$(md5 -q "$MC_FILE" 2>/dev/null || echo "missing")
inbox_sum=$(md5 -q "$INBOX_FILE" 2>/dev/null || echo "missing")
new_checksum="${mc_sum}|${inbox_sum}|model=${MODEL}"

if [ -f "$CHECKSUM_FILE" ] && [ "$(cat "$CHECKSUM_FILE")" = "$new_checksum" ]; then
  log "No changes detected; posting idle heartbeat and exiting."
  post_heartbeat idle
  exit 0
fi
echo "$new_checksum" > "$CHECKSUM_FILE"

log "Phase 1: posting working heartbeat"
post_heartbeat working

log "Phase 2: peer review disabled (#149)"

log "Phase 2.5: processing inbox only"
python3 <<'PYEOF'
import datetime
import json
import os
import subprocess
import sys

inbox_file = "/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json"
model = os.environ.get("QWEN_CODER_MODEL", "ollama-gemma:qwen3-coder:30b")

try:
    with open(inbox_file, "r", encoding="utf-8") as f:
        inbox = json.load(f)
except Exception as exc:
    print(f"Error reading inbox: {exc}")
    sys.exit(0)

unread = [m for m in inbox if m.get("to") == "gemma" and m.get("status") == "unread"]
if not unread:
    print("No unread messages for Qwen Coder.")
    sys.exit(0)

for msg in unread:
    prompt = f"""You are Qwen Coder, a local fleet coding model running through the legacy gemma compatibility slot.

You may answer inbox messages, but peer review and autonomous code execution are disabled.

From: {msg.get("from")}
Subject: {msg.get("subject")}
Body: {msg.get("body")}

Reply concisely in plain text. If the message asks you to perform code work, state that the safe execution harness is not enabled."""

    result = subprocess.run(
        ["/opt/homebrew/bin/aichat", "-m", model, prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    reply = result.stdout.strip() if result.returncode == 0 else f"Qwen Coder could not answer: {result.stderr.strip()[:500]}"
    if not reply:
        reply = "Qwen Coder received the message, but produced no reply."

    msg["status"] = "read"
    inbox.append({
        "id": f"msg-qwen-coder-reply-{int(datetime.datetime.now().timestamp())}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "from": "gemma",
        "to": msg.get("from"),
        "subject": f"Re: {msg.get('subject')}",
        "body": reply,
        "status": "unread",
        "priority": "normal",
        "ref_ticket": msg.get("ref_ticket"),
        "source": "system",
    })

try:
    with open(inbox_file, "w", encoding="utf-8") as f:
        json.dump(inbox, f, indent=2)
    print("Inbox updated.")
except Exception as exc:
    print(f"Error updating inbox: {exc}")
PYEOF

log "Phase 3: code-task execution disabled (#148)"

log "Phase 6: signing off"
post_heartbeat idle

cat > "$GEMMA_DIR/PROGRESS.md" <<EOF
# Qwen Coder Session - $(date '+%Y-%m-%d %H:%M')

- Model: $MODEL
- Heartbeat key: gemma
- Peer review: disabled (#149)
- Code-task execution: disabled (#148)
- Runtime: local aichat -> Ollama
- Status: idle
EOF

log "Session complete."
