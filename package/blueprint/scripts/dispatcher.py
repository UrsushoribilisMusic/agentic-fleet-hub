#!/usr/bin/env python3
"""
Fleet Dispatcher â€” routes tasks to agents based on status and assigned_agent.
Runs every 60 seconds via launchd. NOT an LLM â€” pure routing logic.
"""

import subprocess
import time
import requests
import json
import os
from datetime import datetime

PB_URL = "http://127.0.0.1:8090/api"
FLEET_DIR = "/Users/miguelrodriguez/fleet"
CODEX_REPO_DIR = "/Users/miguelrodriguez/projects/agentic-fleet-hub"
LOG_FILE = f"{FLEET_DIR}/logs/dispatcher.log"
NOTIF_FILE = f"{FLEET_DIR}/logs/notifications.json"

# Telegram settings from environment (Infisical)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "997912895")

# Ensure logs directory exists
os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

AGENT_COMMANDS = {
    "scout": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/scout", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "echo": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/echo", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "closer": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/closer", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "misty": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/misty", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    # Claude Code, Gemini CLI, Codex commands use their respective CLI binaries
    "clau": ["/Users/miguelrodriguez/.local/bin/claude", "--dangerously-skip-permissions", "-p", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "gem": ["/opt/homebrew/bin/node", "/opt/homebrew/bin/gemini", "--yolo", "-p", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "codi": [
        "/opt/homebrew/bin/node",
        "/opt/homebrew/bin/codex",
        "exec",
        "-C",
        CODEX_REPO_DIR,
        "--add-dir",
        FLEET_DIR,
        "Run your heartbeat protocol. Read MISSION_CONTROL.md first."
    ],
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def send_telegram(message):
    if not TELEGRAM_TOKEN:
        log("Telegram not configured (TELEGRAM_TOKEN missing)")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
        )
    except Exception as e:
        log(f"Telegram error: {e}")

def get_pending_tasks():
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": 'status = "todo"', "perPage": 50})
        return r.json().get("items", [])
    except Exception as e:
        log(f"ERROR fetching tasks: {e}")
        return []

def update_task_status(task_id, status):
    try:
        requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}",
                       json={"status": status})
    except Exception as e:
        log(f"ERROR updating task {task_id}: {e}")

def post_comment(task_id, agent, content, comment_type="output"):
    try:
        requests.post(f"{PB_URL}/collections/comments/records",
                      json={"task_id": task_id, "agent": agent,
                            "content": content, "type": comment_type})
    except Exception as e:
        log(f"ERROR posting comment: {e}")

def run_agent(agent_name, task):
    if agent_name not in AGENT_COMMANDS:
        log(f"No command configured for agent: {agent_name}")
        return

    log(f"Dispatching task '{task['title']}' to {agent_name}")
    update_task_status(task["id"], "in_progress")

    cmd = AGENT_COMMANDS[agent_name]
    try:
        # We use a timeout to prevent runaway processes
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        output = result.stdout or result.stderr or "No output"
        
        post_comment(task["id"], agent_name, output[:5000]) # cap at 5000 chars
        update_task_status(task["id"], "peer_review")
        log(f"Task '{task['title']}' completed by {agent_name} -> peer_review")
    except subprocess.TimeoutExpired:
        update_task_status(task["id"], "todo") # put back in queue
        log(f"TIMEOUT: task '{task['title']}' returned to queue")
    except Exception as e:
        log(f"ERROR running {agent_name}: {e}")
        update_task_status(task["id"], "todo")

def get_notif_data():
    if os.path.exists(NOTIF_FILE):
        try:
            with open(NOTIF_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_notif_data(data):
    try:
        with open(NOTIF_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        log(f"ERROR saving notif_data: {e}")

def check_waiting_human():
    """Ping Telegram if any task is waiting for human input."""
    try:
        # Check both 'waiting_human' and 'waiting_human_notified'
        # to ensure we keep notifying if needed, but with a cooldown
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": 'status = "waiting_human" || status = "waiting_human_notified"'})
        tasks = r.json().get("items", [])
        if not tasks:
            return

        notif_data = get_notif_data()
        now = time.time()
        changed = False
        
        for task in tasks:
            task_id = task['id']
            last_sent = notif_data.get(task_id, 0)
            
            # Cooldown: 1 hour (3600 seconds)
            if now - last_sent > 3600:
                msg = f"ðŸ¤– HUMAN NEEDED: {task['title']}\nStatus: {task['status']}\nID: {task['id']}"
                log(f"HUMAN NEEDED: {task['title']} â€” sending Telegram")
                send_telegram(msg)
                notif_data[task_id] = now
                changed = True
                
                # If it was 'waiting_human', we can set it to 'waiting_human_notified'
                # but now it's mostly for informational purposes since we use the cooldown.
                if task["status"] == "waiting_human":
                    update_task_status(task_id, "waiting_human_notified")

        if changed:
            save_notif_data(notif_data)
            
    except Exception as e:
        log(f"ERROR checking waiting_human: {e}")

def main():
    log("Dispatcher started")
    while True:
        tasks = get_pending_tasks()
        for task in tasks:
            agent = task.get("assigned_agent")
            if agent:
                run_agent(agent, task)
        
        check_waiting_human()
        time.sleep(60)

if __name__ == "__main__":
    main()
