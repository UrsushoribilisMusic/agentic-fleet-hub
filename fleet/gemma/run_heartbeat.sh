#!/usr/bin/env bash
# Qwen Coder Heartbeat Wrapper (formerly Gemma)
# Handles all deterministic PocketBase/shell operations.
# Calls Ollama API directly for inbox replies and code-gen tasks.

set -euo pipefail

# This legacy slot runs Qwen Coder. Respect its deliberate sleep in every entrypoint.
if ! /usr/bin/python3 /Users/miguelrodriguez/fleet/scheduler_policy.py --agent qwen; then exit 0; fi

FLEET_DIR="/Users/miguelrodriguez/fleet"
GEMMA_DIR="$FLEET_DIR/gemma"
PB_URL="http://localhost:8090/api"
AGENT="qwen"
AGENT_LABEL="Qwen Coder"
MODEL="${QWEN_CODER_MODEL:-ollama-gemma:qwen3-coder:30b}"
export QWEN_CODER_MODEL="$MODEL"
LOG="$FLEET_DIR/logs/gemma.log"
CONTEXT_FILE="$GEMMA_DIR/workspace/context.md"

# Fixed: remove tee to avoid double logs in launchd
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

mkdir -p "$GEMMA_DIR/workspace"

# ── Lockfile guard — prevent parallel launchd invocations ───────────────────
LOCKFILE="$GEMMA_DIR/workspace/.heartbeat.lock"
if [ -f "$LOCKFILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCKFILE" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -lt 7200 ]; then
        log "Another heartbeat is running (lock age ${LOCK_AGE}s) — exiting."
        exit 0
    fi
    log "Stale lock (${LOCK_AGE}s) — removing and continuing."
fi
echo $$ > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"' EXIT

# ── Phase 0: Checksum guard (skip if nothing changed) ───────────────────────
CHECKSUM_FILE="$GEMMA_DIR/workspace/.last_checksum"
MC_FILE="$FLEET_DIR/MISSION_CONTROL.md"
INBOX_FILE="/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json"

mc_sum=$(md5 -q "$MC_FILE" 2>/dev/null || echo "missing")
inbox_sum=$(md5 -q "$INBOX_FILE" 2>/dev/null || echo "missing")
pb_tasks=$(curl -s "$PB_URL/collections/tasks/records?filter=assigned_agent%3D'qwen'%26%26(status%3D'todo'%7C%7Cstatus%3D'in_progress')&perPage=1" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('totalItems',0))" 2>/dev/null || echo "0")
new_checksum="${mc_sum}|${inbox_sum}|pb_active=${pb_tasks}"

# When the dispatcher injects a task directly, skip the checksum gate entirely.
if [ -z "${QWEN_TASK_ID:-}" ]; then
    if [ -f "$CHECKSUM_FILE" ] && [ "$(cat $CHECKSUM_FILE)" = "$new_checksum" ]; then
        log "No changes detected — posting idle heartbeat and exiting."
        curl -s -X POST "$PB_URL/collections/heartbeats/records" \
            -H "Content-Type: application/json" \
            -d "{\"agent\": \"$AGENT\", \"status\": \"idle\"}" > /dev/null
        exit 0
    fi
    echo "$new_checksum" > "$CHECKSUM_FILE"
fi

# ── Phase 1: Post working heartbeat ──────────────────────────────────────────
log "Phase 1: Posting working heartbeat"
curl -s -X POST "$PB_URL/collections/heartbeats/records" \
    -H "Content-Type: application/json" \
    -d "{\"agent\": \"$AGENT\", \"status\": \"working\"}" > /dev/null

# ── Phase 2: DISABLED (#149) ─────────────────────────────────────────────────
# Previously this phase fetched all peer_review tickets where assigned_agent != 'gemma'
# and unconditionally PATCHed status='approved' after asking aichat for an approval blurb.
# No diff inspection, no build, no test — pure rubber-stamp. This was the source of every
# "approved without shipping" lie in PocketBase (PC-086/087/088/089/098 etc). Disabled
# per ticket #149: gemma is not a competent reviewer; route peer_review through clau or
# a Claude Code review subagent instead.
PEER_COUNT=0

# ── Phase 2.5: Inbox Processing ─────────────────────────────────────────────
log "Phase 2.5: Checking inbox for unread messages"
python3 << 'PYEOF'
import sys, json, subprocess, datetime, os, urllib.request

inbox_file = "/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json"
agent = "qwen"
ollama_model = os.environ.get("QWEN_CODER_MODEL", "ollama-gemma:qwen3-coder:30b").replace("ollama-gemma:", "")

try:
    with open(inbox_file, 'r') as f:
        inbox = json.load(f)
except Exception as e:
    print(f"Error reading inbox: {e}")
    sys.exit(0)

unread = [m for m in inbox if m.get('to') == agent and m.get('status') == 'unread']

if not unread:
    print("No unread messages for Qwen.")
    sys.exit(0)

print(f"Found {len(unread)} unread messages.")

for msg in unread:
    print(f"Processing message from {msg.get('from')}: {msg.get('subject')}")

    prompt = f"""You are Qwen Coder, a local fleet coding agent running through the legacy gemma fleet slot. You received a message from {msg.get('from')}.
Subject: {msg.get('subject')}
Body: {msg.get('body')}

Reply to this message. If it's a test, acknowledge it. If it's a task or question, answer or explain what you are doing.
Keep it professional and concise. Reply strictly in plain text."""

    payload = json.dumps({
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7},
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            reply = json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception as e:
        print(f"Ollama request failed: {e}")
        reply = ""

    if reply:
        print(f"Qwen Coder Reply: {reply}")
        msg['status'] = 'read'

        # Post a reply back to the inbox
        new_msg = {
            "id": f"msg-qwen-coder-reply-{int(datetime.datetime.now().timestamp())}",
            "timestamp": datetime.datetime.now().isoformat() + "Z",
            "from": "qwen",
            "to": msg.get('from'),
            "subject": f"Re: {msg.get('subject')}",
            "body": reply,
            "status": "unread",
            "priority": "normal",
            "ref_ticket": msg.get('ref_ticket'),
            "source": "system"
        }
        inbox.append(new_msg)

# Save updated inbox
try:
    with open(inbox_file, 'w') as f:
        json.dump(inbox, f, indent=2)
    print("Inbox updated (replies posted and marked as read).")
except Exception as e:
    print(f"Error updating inbox: {e}")
PYEOF

# ── Phase 3: Task execution loop ─────────────────────────────────────────────
# Pick up one todo task assigned to qwen, ask aichat to generate a Python
# script that solves it, execute it sandboxed to ~/fleet/analytics/, capture
# stdout/stderr, post as a comment, move to peer_review (or waiting_human).
log "Phase 3: Checking for qwen todo tasks"
python3 << 'PYEOF'
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

PB_URL = "http://localhost:8090/api"
MODEL = os.environ.get("QWEN_CODER_MODEL", "ollama-gemma:qwen3-coder:30b")
ANALYTICS_DIR = os.path.expanduser("~/fleet/analytics")
os.makedirs(ANALYTICS_DIR, exist_ok=True)


def pb_request(method, path, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{PB_URL}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def add_comment(task_id, kind, content):
    pb_request("POST", "/collections/comments/records", {
        "task_id": task_id,
        "agent": "qwen",
        "type": kind,
        "content": content[:4000],
    })


# Use dispatcher-injected task if present; otherwise self-scan PocketBase.
injected_id = os.environ.get("QWEN_TASK_ID", "")
if injected_id:
    task_id = injected_id
    title = os.environ.get("QWEN_TASK_TITLE", "(no title)")
    description = os.environ.get("QWEN_TASK_DESC", "")
    print(f"Picked up injected task {task_id}: {title}")
else:
    query = urllib.parse.urlencode({
        "filter": 'assigned_agent="qwen" && (status="todo" || status="in_progress")',
        "perPage": "1",
        "sort": "created",
    })
    tasks = pb_request("GET", f"/collections/tasks/records?{query}").get("items", [])
    if not tasks:
        print("No active tasks for qwen.")
        sys.exit(0)
    task_obj = tasks[0]
    task_id = task_obj["id"]
    title = task_obj.get("title", "(no title)")
    description = task_obj.get("description", "")
    print(f"Picked up task {task_id}: {title}")

pb_request("PATCH", f"/collections/tasks/records/{task_id}", {"status": "in_progress"})

try:
    plan_prompt = f"""You are Qwen Coder, a local Python analytics agent.
Your only output channel is stdout — you cannot open browser windows or interactive GUIs.
Write only Python 3 code. No markdown fences, no explanations, just the script.

Constraints:
- Output directory: {ANALYTICS_DIR}
- Write all output files (charts, CSVs, text reports) to that directory.
- Use only stdlib + pandas, matplotlib, vaderSentiment if available; nothing else.
- The script must run non-interactively (no plt.show(), no input()).
- End the script by printing a one-line summary of what was produced.

Task title: {title}
Task description:
{description}
"""

    ollama_model = os.environ.get("QWEN_CODER_MODEL", "qwen3-coder:30b").replace("ollama-gemma:", "")
    payload = json.dumps({
        "model": ollama_model,
        "prompt": plan_prompt,
        "stream": False,
        "think": False,          # disable chain-of-thought — qwen3 burns tokens here
        "options": {"temperature": 0.1},
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=1800) as resp:
        raw_code = json.loads(resp.read().decode("utf-8")).get("response", "").strip()

    raw_code = re.sub(r"^```[a-z]*\n?", "", raw_code, flags=re.M)
    raw_code = re.sub(r"^```\s*$", "", raw_code, flags=re.M)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=ANALYTICS_DIR) as tf:
        tf.write(raw_code)
        script_path = tf.name

    run = subprocess.run(
        [sys.executable, script_path],
        capture_output=True, text=True, timeout=300,
        env={**os.environ, "PYTHONPATH": ""},
    )
    output = (run.stdout + run.stderr).strip()
    if run.returncode != 0:
        raise RuntimeError(f"Script exited {run.returncode}:\n{output[:2000]}")

    add_comment(task_id, "output", f"Qwen Coder completed task.\n\n{output[:3500]}")
    pb_request("PATCH", f"/collections/tasks/records/{task_id}", {"status": "peer_review"})
    print(f"Task {task_id} done — moved to peer_review.")
except Exception as exc:
    add_comment(task_id, "question", f"Qwen blocked on task '{title}': {exc}")
    pb_request("PATCH", f"/collections/tasks/records/{task_id}", {"status": "waiting_human"})
    print(f"Task {task_id} blocked: {exc}")
PYEOF

# ── Phase 6: Sign off ────────────────────────────────────────────────────────
log "Phase 6: Signing off"
curl -s -X POST "$PB_URL/collections/heartbeats/records" \
    -H "Content-Type: application/json" \
    -d "{\"agent\": \"$AGENT\", \"status\": \"idle\"}" > /dev/null

cat > "$GEMMA_DIR/PROGRESS.md" << EOF
# Qwen Coder Session — $(date '+%Y-%m-%d %H:%M')

- Heartbeat protocol ran successfully via wrapper script
- Model: $MODEL
- Peer reviews: disabled (#149)
- Code-task work: ENABLED (Ollama API codegen + sandboxed exec, output to ~/fleet/analytics/)
- Inbox messages processed: OK
- Status: idle
EOF

log "Session complete."
