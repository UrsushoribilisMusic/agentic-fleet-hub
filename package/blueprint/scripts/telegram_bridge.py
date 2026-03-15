#!/usr/bin/env python3
"""
Telegram Listener Bridge — polls Telegram for replies and updates PocketBase.
Enables Two-Way Command & Control.
"""

import time
import requests
import json
import os
import subprocess
from datetime import datetime

PB_URL = "http://127.0.0.1:8090/api"
FLEET_DIR = "/Users/miguelrodriguez/fleet"
LOG_FILE = f"{FLEET_DIR}/logs/telegram_bridge.log"
OFFSET_FILE = f"{FLEET_DIR}/logs/tg_offset.json"
OUTBOUND_OFFSET_FILE = f"{FLEET_DIR}/logs/tg_outbound_offset.json"

# Telegram settings from environment (Infisical)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "997912895")

os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

TASK_CACHE = {}

# OpenClaw gateway settings
OPENCLAW_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://localhost:18789/v1/chat/completions")
OPENCLAW_GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN")

# Bot commands registered with Telegram
BOT_COMMANDS = [
    {"command": "clau",   "description": "Send a task to Clau (Claude Code)"},
    {"command": "gem",    "description": "Send a task to Gem (Gemini)"},
    {"command": "codi",   "description": "Send a task to Codi (Codex)"},
    {"command": "claw",   "description": "Talk to OpenClaw (Robot Ross artist agent)"},
    {"command": "ask",    "description": "Ask the fleet a question (routes to Clau)"},
    {"command": "spec",   "description": "Post a new spec or idea for the fleet"},
    {"command": "status", "description": "Show fleet heartbeat status"},
    {"command": "tasks",  "description": "List active tasks"},
    {"command": "go",     "description": "Activate all backlog tasks"},
    {"command": "help",   "description": "Show available commands"},
]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def get_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE, "r") as f:
            return json.load(f).get("offset", 0)
    return 0

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

LAST_OUTBOUND_TS = None

def get_outbound_offset():
    global LAST_OUTBOUND_TS
    if LAST_OUTBOUND_TS:
        return LAST_OUTBOUND_TS
    if os.path.exists(OUTBOUND_OFFSET_FILE):
        with open(OUTBOUND_OFFSET_FILE, "r") as f:
            ts = json.load(f).get("last_timestamp", "")
            if ts:
                LAST_OUTBOUND_TS = ts
                return ts
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
    save_outbound_offset(ts)
    return ts

def save_outbound_offset(ts):
    global LAST_OUTBOUND_TS
    LAST_OUTBOUND_TS = ts
    with open(OUTBOUND_OFFSET_FILE, "w") as f:
        json.dump({"last_timestamp": ts}, f)

def resolve_openclaw_token():
    if OPENCLAW_GATEWAY_TOKEN:
        return OPENCLAW_GATEWAY_TOKEN
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/openclaw", "config", "get", "gateway.auth.token"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        token = result.stdout.strip()
        return token or None
    except Exception as e:
        log(f"OpenClaw token lookup failed: {e}")
        return None

def send_to_tg(text):
    if not TELEGRAM_TOKEN: return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        if len(text) > 4096:
            text = text[:4093] + "..."
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        if r.status_code != 200:
            log(f"TG Send Error ({r.status_code}): {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        log(f"TG Send Error: {e}")
        return False

def register_bot_commands():
    """Register /commands with Telegram so they appear in the UI."""
    if not TELEGRAM_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
        r = requests.post(url, json={"commands": BOT_COMMANDS})
        if r.status_code == 200:
            log("Bot commands registered with Telegram")
        else:
            log(f"Failed to register bot commands: {r.text[:200]}")
    except Exception as e:
        log(f"Bot command registration error: {e}")

def create_task(title, assigned_agent, description=""):
    """Create a todo task in PocketBase assigned to an agent."""
    try:
        r = requests.post(f"{PB_URL}/collections/tasks/records", json={
            "title": title,
            "assigned_agent": assigned_agent,
            "status": "todo",
            "description": description,
        })
        task_id = r.json().get("id")
        log(f"Created task '{title}' -> {assigned_agent} (id: {task_id})")
        return task_id
    except Exception as e:
        log(f"PB Task Create Error: {e}")
        return None

def get_task_title(task_id):
    if not task_id or len(task_id) != 15 or "_" in task_id:
        return None
    if task_id in TASK_CACHE:
        return TASK_CACHE[task_id]
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records/{task_id}")
        if r.status_code == 200:
            title = r.json().get("title")
            TASK_CACHE[task_id] = title
            return title
    except:
        pass
    return None

def poll_outbound_comments():
    last_ts = get_outbound_offset()
    try:
        r = requests.get(f"{PB_URL}/collections/comments/records", params={
            "filter": f"created > '{last_ts}' && agent != 'miguel'",
            "sort": "created"
        })
        if r.status_code != 200:
            log(f"PB Fetch Error ({r.status_code}): {r.text}")
            return

        items = r.json().get("items", [])
        for item in items:
            agent = item.get("agent", "unknown")
            content = item.get("content", "")
            task_id = item.get("task_id", "")

            title = get_task_title(task_id)
            header = f"🤖 {agent} @ {title}" if title else (f"🤖 {agent} ({task_id})" if task_id else f"🤖 {agent}")

            if send_to_tg(f"{header}:\n{content}"):
                log(f"Sent outbound comment from {agent} to TG")
                last_ts = item.get("created")
                save_outbound_offset(last_ts)
            else:
                log(f"Failed to send outbound comment {item.get('id')}")
                break  # retry next cycle

    except Exception as e:
        log(f"Outbound Poll Error: {e}")

def cmd_status():
    """Query heartbeats and reply to Telegram."""
    try:
        r = requests.get(f"{PB_URL}/collections/heartbeats/records", params={"sort": "-updated", "perPage": 20})
        items = r.json().get("items", [])
        # Latest per agent
        seen = {}
        for h in items:
            a = h.get("agent", "?")
            if a not in seen:
                seen[a] = h
        if not seen:
            send_to_tg("No heartbeat data found.")
            return
        lines = ["🫀 Fleet Status:"]
        for agent, h in sorted(seen.items()):
            age_sec = (datetime.utcnow() - datetime.strptime(h["updated"][:19], "%Y-%m-%d %H:%M:%S")).total_seconds()
            age = f"{int(age_sec//3600)}h ago" if age_sec >= 3600 else f"{int(age_sec//60)}m ago"
            dot = "🟢" if h["status"] == "working" and age_sec < 3600 else ("🔵" if age_sec < 3600 else "⚫")
            lines.append(f"{dot} {agent}: {h['status']} ({age})")
        send_to_tg("\n".join(lines))
    except Exception as e:
        send_to_tg(f"Status error: {e}")

def cmd_tasks():
    """Query active tasks and reply to Telegram."""
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records", params={
            "filter": 'status != "done" && status != "approved"',
            "sort": "-created",
            "perPage": 20
        })
        items = r.json().get("items", [])
        if not items:
            send_to_tg("No active tasks.")
            return
        lines = [f"📋 Active Tasks ({len(items)}):"]
        for t in items:
            agent = t.get("assigned_agent", "unassigned")
            lines.append(f"• [{t['status']}] {t['title']} → {agent}")
        send_to_tg("\n".join(lines))
    except Exception as e:
        send_to_tg(f"Tasks error: {e}")

def cmd_claw(message):
    """Forward a message to OpenClaw via its gateway chat completions API."""
    token = resolve_openclaw_token()
    if not token:
        send_to_tg("OpenClaw error: gateway token not configured.")
        return
    try:
        r = requests.post(
            OPENCLAW_GATEWAY_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"model": "openclaw", "messages": [{"role": "user", "content": message}]},
            timeout=60,
        )
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            send_to_tg(f"🤖 OpenClaw:\n{content}")
        else:
            send_to_tg(f"OpenClaw error ({r.status_code}): {r.text[:200]}")
    except Exception as e:
        send_to_tg(f"OpenClaw error: {e}")

def update_backlog_to_todo():
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records", params={"filter": 'status = "backlog"'})
        tasks = r.json().get("items", [])
        for task in tasks:
            requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}", json={"status": "todo"})
            log(f"Task {task['id']} moved to TODO via GO signal")
        return len(tasks)
    except Exception as e:
        log(f"Error updating backlog: {e}")
        return 0

def process_updates(updates):
    for update in updates:
        msg = update.get("message")
        if not msg: continue

        chat_id = str(msg.get("chat", {}).get("id"))
        text = (msg.get("text") or "").strip()

        if chat_id != TELEGRAM_CHAT_ID:
            log(f"Ignored message from unauthorized chat: {chat_id}")
            continue

        log(f"Received: {text}")

        # Parse slash command and remainder
        cmd = ""
        remainder = ""
        if text.startswith("/"):
            parts = text[1:].split(None, 1)
            cmd = parts[0].lower().split("@")[0]  # strip @botname if present
            remainder = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "go" or text.strip().upper() == "GO":
            count = update_backlog_to_todo()
            send_to_tg(f"✅ GO: {count} task(s) activated.")

        elif cmd == "status":
            cmd_status()

        elif cmd == "tasks":
            cmd_tasks()

        elif cmd == "help":
            lines = ["🐻 Fleet commands:"]
            for c in BOT_COMMANDS:
                lines.append(f"/{c['command']} — {c['description']}")
            send_to_tg("\n".join(lines))

        elif cmd == "claw":
            if not remainder:
                send_to_tg("Usage: /claw <message>")
                continue
            send_to_tg("🦾 Sending to OpenClaw…")
            cmd_claw(remainder)

        elif cmd in ("clau", "gem", "codi"):
            if not remainder:
                send_to_tg(f"Usage: /{cmd} <task description>")
                continue
            task_id = create_task(remainder, cmd, description=f"From Telegram: /{cmd} {remainder}")
            send_to_tg(f"✅ Task queued for {cmd}: {remainder}")

        elif cmd == "ask":
            content = remainder or text
            if not content:
                send_to_tg("Usage: /ask <question>")
                continue
            task_id = create_task(f"Q: {content}", "clau", description=f"Question from Telegram: {content}")
            send_to_tg(f"✅ Question queued for Clau. She'll respond at next heartbeat (:04, :14, …).")

        elif cmd == "spec" or text.lower().startswith("spec:") or text.lower().startswith("idea:"):
            content = remainder or text
            task_id = create_task(f"Spec: {content[:80]}", "clau", description=content)
            send_to_tg(f"✅ Spec queued.")

        elif "?" in text:
            # Free-form question without /ask
            task_id = create_task(f"Q: {text[:80]}", "clau", description=f"Question from Telegram: {text}")
            send_to_tg(f"✅ Question queued for Clau.")

        else:
            # Generic message — log it but don't create noise tasks
            log(f"Unhandled message (no task created): {text[:100]}")

def main():
    if not TELEGRAM_TOKEN:
        log("ERROR: TELEGRAM_TOKEN not set")
        return

    log("Telegram Bridge started")
    register_bot_commands()
    offset = get_offset()

    while True:
        # 1. Outbound: PocketBase comments -> Telegram
        poll_outbound_comments()

        # 2. Inbound: Telegram -> PocketBase tasks
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": offset + 1, "timeout": 5}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

            if data.get("ok"):
                updates = data.get("result", [])
                if updates:
                    process_updates(updates)
                    offset = updates[-1]["update_id"]
                    save_offset(offset)

        except Exception as e:
            log(f"Polling error: {e}")
            time.sleep(5)

        time.sleep(1)

if __name__ == "__main__":
    main()
