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

# Telegram settings from environment (Infisical)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "997912895")

os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

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

def post_to_pb(collection, data):
    try:
        r = requests.post(f"{PB_URL}/collections/{collection}/records", json=data)
        return r.json()
    except Exception as e:
        log(f"PB Error: {e}")
        return None

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
        elif text.startswith("spec:") or text.startswith("idea:"):
            post_to_pb("comments", {
                "task_id": "ARCHITECT_INBOX",
                "agent": "miguel",
                "content": text,
                "type": "output" # Scout scans for miguel + output to find specs
            })
            log("New spec posted for Architect")
        
        # 3. Generic reply
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
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"offset": offset + 1, "timeout": 30}
            r = requests.get(url, params=params, timeout=40)
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
