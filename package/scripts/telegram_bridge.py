#!/usr/bin/env python3
"""
Telegram Listener Bridge — polls Telegram for replies and updates PocketBase.
Enables Two-Way Command & Control.
"""

import time
import requests
import json
import os
import shutil
import subprocess
import re
from datetime import datetime

from flotilla_config import (
    PB_URL, FLEET_DIR as _FLEET_DIR, WORKSPACE_DIR, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
)

FLEET_DIR = str(_FLEET_DIR)
CODEX_REPO_DIR = str(WORKSPACE_DIR)
LOG_FILE = f"{FLEET_DIR}/logs/telegram_bridge.log"
OFFSET_FILE = f"{FLEET_DIR}/logs/tg_offset.json"
OUTBOUND_OFFSET_FILE = f"{FLEET_DIR}/logs/tg_outbound_offset.json"
# Name stored as the comment author for messages from the human manager.
HUMAN_AGENT = os.environ.get("FLOTILLA_HUMAN_AGENT", "human")

os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

TASK_CACHE = {}

# OpenClaw gateway settings
OPENCLAW_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://localhost:18789/v1/chat/completions")
OPENCLAW_GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN")

# Bot commands registered with Telegram
BOT_COMMANDS = [
    {"command": "clau",   "description": "Message Clau (Claude Code)"},
    {"command": "gem",    "description": "Message Gem (Gemini)"},
    {"command": "codi",   "description": "Message Codi (Codex)"},
    {"command": "misty",  "description": "Message Misty (Mistral Vibe)"},
    {"command": "gemma",  "description": "Message Gemma (local Gemma4 via aichat)"},
    {"command": "claw",   "description": "Talk to an OpenClaw gateway agent"},
    {"command": "ask",    "description": "Ask the fleet a question (routes to Clau inbox)"},
    {"command": "spec",   "description": "Post a new spec or idea (routes to Clau inbox)"},
    {"command": "status", "description": "Show fleet heartbeat status"},
    {"command": "tasks",  "description": "List active tasks"},
    {"command": "go",     "description": "Activate all backlog tasks"},
    {"command": "help",   "description": "Show available commands"},
]

AGENT_LIST = ["clau", "gem", "codi", "misty", "gemma", "openclaw"]

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
    # Atomic write so a crash mid-write cannot corrupt/regress the cursor.
    tmp = OUTBOUND_OFFSET_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"last_timestamp": ts}, f)
    os.replace(tmp, OUTBOUND_OFFSET_FILE)

# If the outbound cursor ever falls this far behind, assume it regressed
# (see the 2026-08-04 flood: cursor jumped back and re-forwarded ~18.8k old
# comments to Telegram). Fast-forward instead of re-sending the backlog.
OUTBOUND_BACKLOG_GUARD = 200

def get_newest_comment_ts():
    try:
        r = requests.get(f"{PB_URL}/collections/comments/records",
                         params={"sort": "-created", "perPage": 1}, timeout=5)
        items = r.json().get("items", [])
        return items[0]["created"] if items else None
    except Exception:
        return None

def resolve_openclaw_token():
    if OPENCLAW_GATEWAY_TOKEN:
        return OPENCLAW_GATEWAY_TOKEN
    try:
        result = subprocess.run(
            [shutil.which("openclaw") or "openclaw", "config", "get", "gateway.auth.token"],
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

def create_task(title, assigned_agent, description="", source="telegram"):
    """Create a todo task in PocketBase assigned to an agent."""
    try:
        r = requests.post(f"{PB_URL}/collections/tasks/records", json={
            "title": title,
            "assigned_agent": assigned_agent,
            "status": "todo",
            "description": description,
            "source": source,
            "private": source == "telegram",  # Telegram chats never go to GitHub
        })
        task_id = r.json().get("id")
        log(f"Created task '{title}' -> {assigned_agent} (id: {task_id}, source: {source})")
        return task_id
    except Exception as e:
        log(f"PB Task Create Error: {e}")
        return None


def create_followup_task_if_referenced(body, assigned_agent):
    """
    Scan message body for ticket references (#NNN or 8-char PB UUID).
    If a matching PB task exists, create a follow-up task unless one already
    exists for the same reference and agent with status todo/in_progress.
    """
    num_matches = re.findall(r'#(\d+)', body)
    uuid_matches = re.findall(r'\b([a-z0-9]{8})\b', body)

    refs = [(m, 'num') for m in num_matches] + [(m, 'uuid') for m in uuid_matches]
    if not refs:
        return

    for ref, ref_type in refs:
        ref_label = f"#{ref}" if ref_type == 'num' else ref
        try:
            # Verify the referenced task exists in PocketBase
            if ref_type == 'num':
                r = requests.get(f"{PB_URL}/collections/tasks/records", params={
                    "filter": f'gh_issue_id = {ref}',
                    "perPage": 1
                }, timeout=5)
                items = r.json().get('items', [])
            else:
                r = requests.get(f"{PB_URL}/collections/tasks/records/{ref}", timeout=5)
                items = [r.json()] if r.status_code == 200 and 'id' in r.json() else []

            if not items:
                log(f"No PB task found for {ref_label}, skipping follow-up")
                continue

            # Guard: skip if an active follow-up task already exists for same ref + agent
            guard_r = requests.get(f"{PB_URL}/collections/tasks/records", params={
                "filter": f'assigned_agent = "{assigned_agent}" && (status = "todo" || status = "in_progress") && title ~ "Follow-up on {ref_label}"',
                "perPage": 1
            }, timeout=5)
            if guard_r.json().get('items'):
                log(f"Follow-up for {ref_label} -> {assigned_agent} already exists, skipping")
                continue

            title = f"Follow-up on {ref_label}: {body[:60].strip()}"
            r2 = requests.post(f"{PB_URL}/collections/tasks/records", json={
                "title": title,
                "assigned_agent": assigned_agent,
                "status": "todo",
                "description": body,
                "source": "telegram",
                "private": True
            }, timeout=5)
            if r2.status_code in (200, 201):
                log(f"Created follow-up task {r2.json().get('id')} for {ref_label} -> {assigned_agent}")
            else:
                log(f"Failed to create follow-up task for {ref_label}: {r2.status_code} {r2.text[:100]}")

        except Exception as e:
            log(f"Error creating follow-up task for {ref_label}: {e}")


def post_to_inbox(from_user, to_agent, subject, body):
    """Route a message directly to the agent's inbox.json instead of creating a task."""
    inbox_path = os.path.join(CODEX_REPO_DIR, "AGENTS/MESSAGES/inbox.json")
    try:
        inbox = []
        if os.path.exists(inbox_path):
            with open(inbox_path, "r") as f:
                inbox = json.load(f)
        
        msg_id = f"msg-tg-{int(time.time())}"
        new_msg = {
            "id": msg_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "from": from_user,
            "to": to_agent,
            "subject": subject,
            "body": body,
            "status": "unread",
            "priority": "normal",
            "ref_ticket": None,
            "source": "telegram"
        }
        inbox.append(new_msg)
        
        with open(inbox_path, "w") as f:
            json.dump(inbox, f, indent=2)
        log(f"✅ INBOX: {from_user} -> {to_agent}: {subject}")
        return True
    except Exception as e:
        log(f"❌ INBOX ERROR: Failed to post to {to_agent} inbox: {e}")
        log(f"    Message: {body[:100]}")
        return False

def update_task_status(task_id, status):
    """Update task status in PocketBase."""
    try:
        requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}",
                       json={"status": status})
        return True
    except Exception as e:
        log(f"PB Task Update Error: {e}")
        return False

def post_comment(task_id, agent, content, comment_type="output"):
    """Post a comment to a task in PocketBase."""
    try:
        requests.post(f"{PB_URL}/collections/comments/records",
                      json={"task_id": task_id, "agent": agent,
                            "content": content, "type": comment_type})
        return True
    except Exception as e:
        log(f"PB Comment Post Error: {e}")
        return False

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


def is_noop_comment(content):
    if not content:
        return False
    markers = [
        "No changes detected. Skipping session.",
        "Heartbeat gate returned exit 1: no relevant changes.",
        "No changes. Going idle.",
        "You're out of extra usage",
        "run out of credits",
        "insufficient balance",
        "API provider returned a billing error",
    ]
    return any(marker in content for marker in markers)

def poll_outbound_comments():
    last_ts = get_outbound_offset()
    try:
        r = requests.get(f"{PB_URL}/collections/comments/records", params={
            "filter": f"created > '{last_ts}' && agent != '{HUMAN_AGENT}' && type != 'feedback'",
            "sort": "created",
            "perPage": 100
        })
        if r.status_code != 200:
            log(f"PB Fetch Error ({r.status_code}): {r.text}")
            return

        body = r.json()
        # BACKLOG GUARD: a healthy cursor never has hundreds pending. A large
        # backlog means the cursor regressed -> fast-forward instead of
        # re-forwarding thousands of old comments to Telegram (2026-08-04 flood).
        total_pending = body.get("totalItems", 0)
        if total_pending > OUTBOUND_BACKLOG_GUARD:
            newest = get_newest_comment_ts()
            if newest:
                save_outbound_offset(newest)
                log(f"⚠ BACKLOG GUARD: {total_pending} pending comments (cursor regressed) -> fast-forwarded to {newest}, skipped re-send")
            return

        items = body.get("items", [])
        for item in items:
            agent = item.get("agent", "unknown")
            content = item.get("content", "")
            task_id = item.get("task_id", "")

            if is_noop_comment(content):
                last_ts = item.get("created")
                save_outbound_offset(last_ts)
                continue

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
        lines = ["🛰 Fleet Status:"]
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
        from_user = msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name", HUMAN_AGENT)
        text = (msg.get("text") or "").strip()

        if chat_id != TELEGRAM_CHAT_ID:
            log(f"Ignored message from unauthorized chat: {chat_id}")
            continue

        log(f"Received from {from_user}: {text}")

        # Check for reply to HUMAN NEEDED
        reply_to = msg.get("reply_to_message")
        if reply_to:
            orig_text = reply_to.get("text", "")
            if "HUMAN NEEDED" in orig_text:
                match = re.search(r"ID: ([a-z0-9]{15})", orig_text)
                if match:
                    task_id = match.group(1)
                    log(f"Handling reply for task {task_id}")
                    # Post human's reply as feedback
                    post_comment(task_id, HUMAN_AGENT, text, comment_type="feedback")
                    # Flip status back to todo
                    update_task_status(task_id, "todo")
                    send_to_tg(f"✅ Received response for {task_id}. Task moved back to TODO.")
                    continue # processed as reply

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
            lines = ["🛸 Fleet commands:"]
            for c in BOT_COMMANDS:
                lines.append(f"/{c['command']} — {c['description']}")
            send_to_tg("\n".join(lines))

        elif cmd == "claw":
            if not remainder:
                send_to_tg("Usage: /claw <message>")
                continue
            send_to_tg("🦦 Sending to OpenClaw…")
            cmd_claw(remainder)

        elif cmd in AGENT_LIST:
            if not remainder:
                send_to_tg(f"Usage: /{cmd} <message>")
                continue
            # Always route direct agent messages to inbox, never create tasks
            success = post_to_inbox(from_user, cmd, f"Telegram: {remainder[:30]}...", remainder)
            if success:
                send_to_tg(f"✅ Message routed to {cmd} inbox.")
                log(f"DIRECT MESSAGE: {from_user} -> {cmd}: {remainder[:100]}")
                create_followup_task_if_referenced(remainder, cmd)
            else:
                send_to_tg(f"❌ Failed to route message to {cmd} inbox. Check logs for details.")
                log(f"ERROR: Failed to route message to {cmd} inbox: {remainder[:100]}")
                # Do NOT create task as fallback - this causes GitHub issues

        elif cmd == "ask":
            content = remainder or text
            if not content:
                send_to_tg("Usage: /ask <question>")
                continue
            if post_to_inbox(from_user, "clau", "Question via Telegram", content):
                send_to_tg(f"✅ Question routed to Clau inbox.")
            else:
                send_to_tg(f"❌ Failed to route question.")

        elif cmd == "spec" or text.lower().startswith("spec:") or text.lower().startswith("idea:"):
            content = remainder or text
            if post_to_inbox(from_user, "clau", "New Spec/Idea", content):
                send_to_tg(f"✅ Spec routed to Clau inbox.")
            else:
                send_to_tg(f"❌ Failed to route spec.")

        elif "?" in text:
            # Free-form question without /ask
            if post_to_inbox(from_user, "clau", "Question via Telegram", text):
                send_to_tg(f"✅ Question routed to Clau inbox.")
            else:
                send_to_tg(f"❌ Failed to route question.")

        else:
            if not text:
                log("Non-text update (photo/sticker/etc), ignoring")
                continue
            # Plain-text message → route to Clau inbox as a general instruction
            log(f"Plain message from {from_user}, routing to clau: {text[:100]}")
            if post_to_inbox(from_user, "clau", "Message via Telegram", text):
                send_to_tg("✅ Message routed to Clau.")
            else:
                send_to_tg("❌ Failed to route message.")

def main():
    if not TELEGRAM_TOKEN:
        log("ERROR: TELEGRAM_TOKEN not BlueBearEngineering GmbH")
        return

    log("Telegram Bridge started")
    register_bot_commands()
    offset = get_offset()

    while True:
        # 1. Outbound: PocketBase comments -> Telegram
        poll_outbound_comments()

        # 2. Inbound: Telegram -> PocketBase tasks (or inbox)
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
