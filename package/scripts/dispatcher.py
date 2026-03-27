#!/usr/bin/env python3
"""
Fleet Dispatcher — routes tasks to agents based on status and assigned_agent.
Runs every 60 seconds via launchd. NOT an LLM — pure routing logic.
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
OFFLINE_AGENTS_FILE = f"{FLEET_DIR}/logs/offline_agents.json"

# Telegram settings from environment (Infisical)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "997912895")

# Configurable Cooldown (default 5 minutes)
COOLDOWN_SECONDS = int(os.environ.get("DISPATCHER_COOLDOWN", "300"))

# Ensure logs directory exists
os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

AGENT_COMMANDS = {
    "scout": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/scout", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "echo": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/echo", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "closer": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/closer", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
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

def is_agent_offline(agent_key):
    """Checks if an agent has been offline for more than 30 minutes."""
    try:
        r = requests.get(f"{PB_URL}/collections/heartbeats/records",
                         params={
                             "filter": f'agent = "{agent_key}"',
                             "sort": "-updated",
                             "perPage": 1
                         })
        items = r.json().get("items", [])
        
        now = datetime.utcnow()
        if not items:
            return True, "Never"
        
        hb = items[0]
        # PB updated time is like "2026-03-19 09:10:42.368Z"
        ts_part = hb["updated"].split('.')[0].replace('Z', '')
        dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
        age_seconds = (now - dt).total_seconds()
        last_seen_str = f"{int(age_seconds // 60)}m ago"
        return (age_seconds > 1800), last_seen_str # 30 min threshold
    except Exception as e:
        log(f"Error checking health for {agent_key}: {e}")
        return True, "Error"

def find_best_substitute(task, offline_agent_key, all_agents_meta, offline_skills):
    # task might have required_skills (list)
    required_skills = task.get("required_skills", [])
    if not required_skills:
        required_skills = list(offline_skills)
    
    required_skills_set = set(required_skills)
    
    best_agent = None
    max_score = -1
    
    offline_agent_meta = next((a for a in all_agents_meta if a["heartbeatKey"] == offline_agent_key), {})
    fallback_chain = offline_agent_meta.get("fallbackChain", [])

    for agent in all_agents_meta:
        if agent["heartbeatKey"] == offline_agent_key: continue
        
        agent_skills = set(agent.get("skills", []))
        score = len(required_skills_set.intersection(agent_skills))
        
        if score > max_score:
            max_score = score
            best_agent = agent
        elif score == max_score and best_agent:
            # Tie breaker: fallbackChain
            if agent["heartbeatKey"] in fallback_chain:
                if best_agent["heartbeatKey"] not in fallback_chain or \
                   fallback_chain.index(agent["heartbeatKey"]) < fallback_chain.index(best_agent["heartbeatKey"]):
                    best_agent = agent
                    
    return best_agent

def reassign_tasks(offline_agent_key, all_agents_meta):
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": f'assigned_agent = "{offline_agent_key}" && status = "todo"'})
        tasks = r.json().get("items", [])
        if not tasks:
            return

        log(f"Evaluating {len(tasks)} tasks from offline agent {offline_agent_key} for reassignment")
        
        offline_agent_meta = next((a for a in all_agents_meta if a["heartbeatKey"] == offline_agent_key), None)
        offline_skills = set(offline_agent_meta.get("skills", [])) if offline_agent_meta else set()

        for task in tasks:
            # 3. Cooldown between bounces
            last_reassign_str = task.get("last_reassignment_at")
            if last_reassign_str:
                ts_part = last_reassign_str.split('.')[0].replace('Z', '')
                last_dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
                age_seconds = (datetime.utcnow() - last_dt).total_seconds()
                if age_seconds < COOLDOWN_SECONDS:
                    log(f"Skipping reassignment for task '{task['title']}' (cooldown: {int(age_seconds)}s < {COOLDOWN_SECONDS}s)")
                    continue

            best_agent = find_best_substitute(task, offline_agent_key, all_agents_meta, offline_skills)
            if best_agent:
                new_agent_key = best_agent["heartbeatKey"]
                
                # 1. Target-online guard
                is_offline, last_seen = is_agent_offline(new_agent_key)
                if is_offline:
                    log(f"Skipping reassignment for task '{task['title']}' to {new_agent_key} (substitute also offline: last seen {last_seen})")
                    continue
                
                # 2. Reassignment counter + freeze (rolling 10m window)
                count = task.get("reassignment_count", 0)
                if last_reassign_str:
                    ts_part = last_reassign_str.split('.')[0].replace('Z', '')
                    last_dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
                    if (datetime.utcnow() - last_dt).total_seconds() < 600: # 10m
                        count += 1
                    else:
                        count = 1
                else:
                    count = 1
                
                now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
                
                if count >= 3:
                    log(f"🚨 BLOCKING task '{task['title']}' (too many reassignments: {count} in 10m)")
                    requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}",
                                   json={"status": "blocked", "reassignment_count": count, "last_reassignment_at": now_iso})
                    send_telegram(f"🚨 TASK BLOCKED: '{task['title']}' (too many reassignments). MANUAL INTERVENTION NEEDED.")
                    post_comment(task["id"], "dispatcher", f"Task blocked after {count} reassignments in 10m.", "comment")
                    continue

                log(f"Reassigning task '{task['title']}' to {new_agent_key}")
                requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}",
                               json={"assigned_agent": new_agent_key, 
                                     "reassignment_count": count, 
                                     "last_reassignment_at": now_iso})
                
                msg = f"Reassigned from {offline_agent_key} to {new_agent_key} ({offline_agent_key} offline)"
                post_comment(task["id"], "dispatcher", msg, "comment")
                
                send_telegram(f"⚠️ Task '{task['title']}' reassigned from {offline_agent_key} to {new_agent_key} (offline for >30m).")

    except Exception as e:
        log(f"ERROR reassigning tasks for {offline_agent_key}: {e}")

def get_offline_agents():
    if os.path.exists(OFFLINE_AGENTS_FILE):
        try:
            with open(OFFLINE_AGENTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_offline_agents(data):
    try:
        with open(OFFLINE_AGENTS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        log(f"ERROR saving offline_agents: {e}")

def check_agent_health():
    try:
        meta_path = os.path.join(CODEX_REPO_DIR, "AGENTS/CONFIG/fleet_meta.json")
        with open(meta_path, "r") as f:
            fleet_meta = json.load(f)
        
        agents = fleet_meta.get("team", [])
        offline_data = get_offline_agents()
        changed = False
        
        for agent_meta in agents:
            agent_key = agent_meta["heartbeatKey"]
            if agent_key == "openclaw": continue
            
            is_currently_offline, last_seen_str = is_agent_offline(agent_key)
            previously_offline = agent_key in offline_data
            
            if is_currently_offline and not previously_offline:
                log(f"Agent {agent_key} detected OFFLINE (last seen {last_seen_str})")
                offline_data[agent_key] = {"offline_since": datetime.utcnow().isoformat(), "last_seen": last_seen_str}
                changed = True
                reassign_tasks(agent_key, agents)
            elif not is_currently_offline and previously_offline:
                log(f"Agent {agent_key} RECOVERED (was offline since {offline_data[agent_key]['offline_since']})")
                send_telegram(f"✅ {agent_key.capitalize()} is back online (was offline {last_seen_str}).")
                del offline_data[agent_key]
                changed = True
            elif is_currently_offline and previously_offline:
                # Still offline, but we should periodically check for reassignment of tasks that 
                # might have been skipped previously (e.g. because of target-offline guard)
                reassign_tasks(agent_key, agents)
                
        if changed:
            save_offline_agents(offline_data)
                
    except Exception as e:
        log(f"ERROR in check_agent_health: {e}")

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
        
        if result.returncode == 0:
            post_comment(task["id"], agent_name, output[:5000]) # cap at 5000 chars
            update_task_status(task["id"], "peer_review")
            log(f"Task '{task['title']}' completed by {agent_name} -> peer_review")
        else:
            log(f"ERROR: Agent {agent_name} failed with return code {result.returncode}")
            post_comment(task["id"], agent_name, f"FAILED with return code {result.returncode}:\n{output[:1000]}", "feedback")
            update_task_status(task["id"], "todo")
            
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
                msg = f"🤖 HUMAN NEEDED: {task['title']}\nStatus: {task['status']}\nID: {task['id']}"
                log(f"HUMAN NEEDED: {task['title']} — sending Telegram")
                send_telegram(msg)
                notif_data[task_id] = now
                changed = True
                
                # If it was 'waiting_human', we can set it to 'waiting_human_notified'
                if task["status"] == "waiting_human":
                    update_task_status(task_id, "waiting_human_notified")

        if changed:
            save_notif_data(notif_data)
            
    except Exception as e:
        log(f"ERROR checking waiting_human: {e}")

def main():
    log("Dispatcher started")
    while True:
        check_agent_health()
        offline_agents = get_offline_agents()
        
        tasks = get_pending_tasks()
        for task in tasks:
            agent = task.get("assigned_agent")
            if agent:
                if agent in offline_agents:
                    # We already tried reassigning in check_agent_health
                    # If it's still assigned to an offline agent, it was likely skipped due to target-offline
                    continue
                run_agent(agent, task)
        
        check_waiting_human()
        time.sleep(60)

if __name__ == "__main__":
    main()
