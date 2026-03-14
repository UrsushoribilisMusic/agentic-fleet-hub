#!/usr/bin/env python3
"""
Telegram Listener Bridge — polls Telegram for replies and updates PocketBase.
Enables Two-Way Command & Control.
"""

import time
import requests
import json
import os
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
    
    # Initialize with current time if never run and save it
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
    save_outbound_offset(ts)
    return ts

def save_outbound_offset(ts):
    global LAST_OUTBOUND_TS
    LAST_OUTBOUND_TS = ts
    with open(OUTBOUND_OFFSET_FILE, "w") as f:
        json.dump({"last_timestamp": ts}, f)

def post_to_pb(collection, data):
    try:
        r = requests.post(f"{PB_URL}/collections/{collection}/records", json=data)
        return r.json()
    except Exception as e:
        log(f"PB Error: {e}")
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

def send_to_tg(text):
    if not TELEGRAM_TOKEN: return
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

def poll_outbound_comments():
    last_ts = get_outbound_offset()
    try:
        # Fetch comments created after last_ts, excluding miguel's, sorted by creation
        url = f"{PB_URL}/collections/comments/records"
        params = {
            "filter": f"created > '{last_ts}' && agent != 'miguel'",
            "sort": "created"
        }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            log(f"PB Fetch Error ({r.status_code}): {r.text}")
            return

        items = r.json().get("items", [])
        for item in items:
            agent = item.get("agent", "unknown")
            content = item.get("content", "")
            task_id = item.get("task_id", "")
            
            title = get_task_title(task_id)
            if title:
                header = f"🤖 {agent} @ {title}"
            else:
                header = f"🤖 {agent} ({task_id})" if task_id else f"🤖 {agent}"
            
            msg = f"{header}:\n{content}"
            if send_to_tg(msg):
                log(f"Sent outbound comment from {agent} to TG")
                last_ts = item.get("created")
                save_outbound_offset(last_ts)
            else:
                log(f"Failed to send outbound comment {item.get('id')}")
                break # Stop and retry later if TG fails
                
    except Exception as e:
        log(f"Outbound Poll Error: {e}")

def update_backlog_to_todo():
    """Moves all backlog tasks to todo when a 'GO' signal is received."""
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
        text = msg.get("text", "")
        
        # Only process messages from Miguel
        if chat_id != TELEGRAM_CHAT_ID:
            log(f"Ignored message from unauthorized chat: {chat_id}")
            continue

        log(f"Received: {text}")

        # 1. Check for GO signal
        if text.strip().upper() == "GO":
            count = update_backlog_to_todo()
            post_to_pb("comments", {
                "task_id": "GLOBAL_SIGNAL", # A placeholder or logic to find latest goal
                "agent": "miguel",
                "content": f"GO signal received. {count} tasks activated.",
                "type": "approval"
            })
            log("GO signal processed")
        
        # 2. Check for spec/idea
        elif text.lower().startswith("spec:") or text.lower().startswith("idea:"):
            post_to_pb("comments", {
                "task_id": "ARCHITECT_INBOX",
                "agent": "miguel",
                "content": text,
                "type": "spec" # Matches Scout mandate
            })
            log("New spec posted for Architect")
        
        # 3. Check for questions
        elif text.lower().startswith("ask:") or "?" in text:
            post_to_pb("comments", {
                "task_id": "FLEET_QUERY",
                "agent": "miguel",
                "content": text,
                "type": "question"
            })
            log("New question posted for Fleet")
        
        # 4. Generic reply
        else:
            post_to_pb("comments", {
                "task_id": "GENERAL_REPLY",
                "agent": "miguel",
                "content": text,
                "type": "feedback"
            })

def main():
    if not TELEGRAM_TOKEN:
        log("ERROR: TELEGRAM_TOKEN not set")
        return

    log("Telegram Bridge started")
    offset = get_offset()
    
    while True:
        # 1. Handle Outbound (PB -> TG)
        poll_outbound_comments()

        # 2. Handle Inbound (TG -> PB)
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
