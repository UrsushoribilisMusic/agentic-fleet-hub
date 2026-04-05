#!/usr/bin/env python3
"""
Fleet Dispatcher v4 — routes tasks to agents based on status and assigned_agent.
Implements Option 1: Dual Sync Strategy (Checks both Files and PocketBase).
"""

import subprocess
import time
import requests
import json
import os
import hashlib
from datetime import datetime

PB_URL = "http://127.0.0.1:8090/api"
FLEET_DIR = "/Users/miguelrodriguez/fleet"
CODEX_REPO_DIR = "/Users/miguelrodriguez/projects/agentic-fleet-hub"
LOG_FILE = f"{FLEET_DIR}/logs/dispatcher.log"
NOTIF_FILE = f"{FLEET_DIR}/logs/notifications.json"
OFFLINE_AGENTS_FILE = f"{FLEET_DIR}/logs/offline_agents.json"
DISPATCHER_CACHE_FILE = f"{FLEET_DIR}/logs/dispatcher_cache.json"

# Telegram settings from environment (Infisical)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "997912895")

# Configurable Cooldown (default 5 minutes)
COOLDOWN_SECONDS = int(os.environ.get("DISPATCHER_COOLDOWN", "300"))

# Ensure logs directory exists
os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

# Files to watch for changes
WATCHED_FILES = [
    "/Users/miguelrodriguez/fleet/MISSION_CONTROL.md",
    "/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json"
]

AGENT_COMMANDS = {
    "scout": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/scout", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "echo": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/echo", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
    "closer": ["/opt/homebrew/bin/openclaw", "--dir", f"{FLEET_DIR}/closer", "--prompt", "Run your heartbeat protocol. Read MISSION_CONTROL.md first."],
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
    "gemma": ["/opt/homebrew/bin/aichat", "--rag", ".", "Run your heartbeat protocol. Read GEMMA.md first."],
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def log_task_event(event_type, task_id, agent=None, from_status=None, to_status=None, meta=None):
    """Write a structured event record to the task_events PocketBase collection."""
    try:
        payload = {
            "task_id": task_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z"),
        }
        if agent is not None:
            payload["agent"] = agent
        if from_status is not None:
            payload["from_status"] = from_status
        if to_status is not None:
            payload["to_status"] = to_status
        if meta is not None:
            payload["meta"] = meta
        requests.post(f"{PB_URL}/collections/task_events/records", json=payload, timeout=5)
    except Exception as e:
        log(f"WARN log_task_event({event_type}, {task_id}): {e}")

def _file_checksum(file_path):
    """Calculate SHA-256 checksum of a file."""
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        log(f"Error calculating checksum for {file_path}: {e}")
        return None

def _load_dispatcher_cache():
    """Load dispatcher cache from file."""
    try:
        if os.path.exists(DISPATCHER_CACHE_FILE):
            with open(DISPATCHER_CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        log(f"Error loading dispatcher cache: {e}")
    return {"checksums": {}, "pb_tasks_updated": ""}

def _save_dispatcher_cache(cache):
    """Save dispatcher cache to file."""
    try:
        with open(DISPATCHER_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        log(f"Error saving dispatcher cache: {e}")

def _state_changed():
    """Check if any watched files or PocketBase tasks have changed."""
    cache = _load_dispatcher_cache()
    current_checksums = {}
    changed = False
    
    # 1. Check Files
    for file_path in WATCHED_FILES:
        current_checksum = _file_checksum(file_path)
        current_checksums[file_path] = current_checksum
        
        if current_checksum is None:
            continue
            
        if file_path not in cache["checksums"] or cache["checksums"][file_path] != current_checksum:
            log(f"Detected change in file: {file_path}")
            changed = True
    
    # 2. Check PocketBase
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"sort": "-updated", "perPage": 1, "fields": "updated"})
        items = r.json().get("items", [])
        if items:
            current_pb_ts = items[0]["updated"]
            if cache.get("pb_tasks_updated") != current_pb_ts:
                log(f"Detected change in PocketBase tasks: {current_pb_ts}")
                changed = True
                cache["pb_tasks_updated"] = current_pb_ts
    except Exception as e:
        log(f"Error checking PocketBase changes: {e}")
    
    # Update cache
    cache["checksums"] = current_checksums
    _save_dispatcher_cache(cache)
    
    return changed

def send_telegram(message):
    if not TELEGRAM_TOKEN:
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
                         params={"filter": 'status = "todo"', "perPage": 50}, timeout=10)
        return r.json().get("items", [])
    except Exception as e:
        log(f"ERROR fetching tasks: {e}")
        return []

def update_task_status(task_id, status, from_status=None, agent=None):
    try:
        requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}",
                       json={"status": status}, timeout=10)
        log_task_event("status_transition", task_id,
                       agent=agent or "dispatcher",
                       from_status=from_status,
                       to_status=status)
    except Exception as e:
        log(f"ERROR updating task {task_id}: {e}")

def update_task_agent(task_id, agent):
    try:
        requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}",
                       json={"assigned_agent": agent}, timeout=10)
    except Exception as e:
        log(f"ERROR updating task {task_id} agent: {e}")

def post_comment(task_id, agent, content, comment_type="output"):
    try:
        requests.post(f"{PB_URL}/collections/comments/records",
                      json={"task_id": task_id, "agent": agent,
                            "content": content, "type": comment_type}, timeout=10)
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
                         }, timeout=10)
        items = r.json().get("items", [])
        
        now = datetime.utcnow()
        if not items:
            return True, "Never"
        
        hb = items[0]
        ts_part = hb["updated"].split('.')[0].replace('Z', '')
        dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
        age_seconds = (now - dt).total_seconds()
        last_seen_str = f"{int(age_seconds // 60)}m ago"
        return (age_seconds > 1800), last_seen_str # 30 min threshold
    except Exception as e:
        log(f"Error checking health for {agent_key}: {e}")
        return True, "Error"

def find_best_substitute(task, offline_agent_key, all_agents_meta, offline_skills):
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
            if agent["heartbeatKey"] in fallback_chain:
                if best_agent["heartbeatKey"] not in fallback_chain or \
                   fallback_chain.index(agent["heartbeatKey"]) < fallback_chain.index(best_agent["heartbeatKey"]):
                    best_agent = agent
                    
    return best_agent

def reassign_tasks(offline_agent_key, all_agents_meta):
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": f'assigned_agent = "{offline_agent_key}" && (status = "todo" || status = "in_progress")'})
        tasks = r.json().get("items", [])
        if not tasks:
            return

        log(f"Evaluating {len(tasks)} tasks from offline agent {offline_agent_key} for reassignment")
        
        offline_agent_meta = next((a for a in all_agents_meta if a["heartbeatKey"] == offline_agent_key), None)
        offline_skills = set(offline_agent_meta.get("skills", [])) if offline_agent_meta else set()

        for task in tasks:
            last_reassign_str = task.get("last_reassignment_at")
            if last_reassign_str:
                ts_part = last_reassign_str.split('.')[0].replace('Z', '')
                last_dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
                age_seconds = (datetime.utcnow() - last_dt).total_seconds()
                if age_seconds < COOLDOWN_SECONDS:
                    continue

            best_agent = find_best_substitute(task, offline_agent_key, all_agents_meta, offline_skills)
            if best_agent:
                new_agent_key = best_agent["heartbeatKey"]
                is_offline, _ = is_agent_offline(new_agent_key)
                if is_offline:
                    continue
                
                count = task.get("reassignment_count", 0)
                if last_reassign_str:
                    ts_part = last_reassign_str.split('.')[0].replace('Z', '')
                    last_dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
                    if (datetime.utcnow() - last_dt).total_seconds() < 600:
                        count += 1
                    else:
                        count = 1
                else:
                    count = 1
                
                now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")
                
                if count >= 3:
                    log(f"BLOCKING task '{task['title']}' (too many reassignments)")
                    requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}",
                                   json={"status": "blocked", "reassignment_count": count, "last_reassignment_at": now_iso})
                    log_task_event("circuit_breaker", task["id"],
                                   agent="dispatcher",
                                   from_status=task.get("status"),
                                   to_status="blocked",
                                   meta={"reassignment_count": count,
                                         "last_agent": offline_agent_key,
                                         "reason": f"blocked after {count} reassignments in 10m"})
                    send_telegram(f"🚨 TASK BLOCKED: '{task['title']}' (too many reassignments).")
                    post_comment(task["id"], "dispatcher", f"Task blocked after {count} reassignments in 10m.", "comment")
                    continue

                log(f"Reassigning task '{task['title']}' to {new_agent_key}")
                requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}",
                               json={"assigned_agent": new_agent_key,
                                     "reassignment_count": count,
                                     "last_reassignment_at": now_iso})
                log_task_event("reassignment", task["id"],
                               agent="dispatcher",
                               meta={"from_agent": offline_agent_key,
                                     "to_agent": new_agent_key,
                                     "reassignment_count": count,
                                     "reason": "agent offline"})
                post_comment(task["id"], "dispatcher", f"Reassigned from {offline_agent_key} to {new_agent_key}", "comment")
    except Exception as e:
        log(f"ERROR in reassign_tasks: {e}")

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
            
            if is_currently_offline:
                if not previously_offline:
                    log(f"Agent {agent_key} detected OFFLINE")
                    offline_data[agent_key] = {"offline_since": datetime.utcnow().isoformat(), "last_seen": last_seen_str}
                    changed = True
                reassign_tasks(agent_key, agents)
            elif previously_offline:
                log(f"Agent {agent_key} RECOVERED")
                send_telegram(f"✅ {agent_key.capitalize()} is back online.")
                del offline_data[agent_key]
                changed = True
                
        if changed:
            save_offline_agents(offline_data)
    except Exception as e:
        log(f"ERROR in check_agent_health: {e}")

def run_agent(agent_name, task):
    if agent_name not in AGENT_COMMANDS:
        return

    log(f"Dispatching task '{task['title']}' to {agent_name}")
    update_task_status(task["id"], "in_progress", from_status=task.get("status"), agent=agent_name)

    cmd = list(AGENT_COMMANDS[agent_name])

    # Enrich prompt for LLM agents
    if agent_name in ["clau", "gem", "codi"]:
        task_prompt = f"\n\nYOUR TASK: {task['title']}\nDescription: {task.get('description', '')}"
        cmd[-1] = cmd[-1] + task_prompt

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        output = result.stdout or result.stderr or "No output"

        if result.returncode == 0:
            post_comment(task["id"], agent_name, output[:5000])
            update_task_status(task["id"], "peer_review", from_status="in_progress", agent=agent_name)
        else:
            log(f"ERROR: Agent {agent_name} failed")
            post_comment(task["id"], agent_name, f"FAILED with return code {result.returncode}:\n{output[:1000]}", "feedback")
            update_task_status(task["id"], "todo", from_status="in_progress", agent=agent_name)
    except Exception as e:
        log(f"ERROR running {agent_name}: {e}")
        update_task_status(task["id"], "todo", from_status="in_progress", agent=agent_name)

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
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": 'status = "waiting_human" || status = "waiting_human_notified"'},
                         timeout=10)
        tasks = r.json().get("items", [])
        if not tasks:
            return

        notif_data = get_notif_data()
        now = time.time()
        changed = False
        
        for task in tasks:
            task_id = task['id']
            last_sent = notif_data.get(task_id, 0)
            if now - last_sent > 3600:
                send_telegram(f"🤖 HUMAN NEEDED: {task['title']}\nID: {task['id']}")
                notif_data[task_id] = now
                changed = True
                if task["status"] == "waiting_human":
                    update_task_status(task_id, "waiting_human_notified")

        if changed:
            save_notif_data(notif_data)
    except Exception as e:
        log(f"ERROR checking waiting_human: {e}")

def get_today_stats():
    """Fetch today's metrics from PocketBase."""
    today = datetime.now().strftime("%Y-%m-%d 00:00:00")
    try:
        # 1. Sessions (working heartbeats today)
        r_hb = requests.get(f"{PB_URL}/collections/heartbeats/records",
                            params={"filter": f'updated >= "{today}" && status = "working"', "perPage": 100},
                            timeout=10)
        hb_items = r_hb.json().get("items", [])
        sessions = len(hb_items)
        agents = sorted(list(set(item["agent"] for item in hb_items)))
        
        # 2. Tasks completed (approved today)
        r_tasks = requests.get(f"{PB_URL}/collections/tasks/records",
                               params={"filter": f'updated >= "{today}" && status = "approved"', "perPage": 100},
                               timeout=10)
        tasks_completed = r_tasks.json().get("totalItems", 0)
        
        return {
            "sessions": sessions,
            "agents": agents,
            "tasks_completed": tasks_completed
        }
    except Exception as e:
        log(f"ERROR fetching today stats: {e}")
        return {"sessions": 0, "agents": [], "tasks_completed": 0}

def create_daily_standup():
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        standup_dir = f"{CODEX_REPO_DIR}/standups"
        os.makedirs(standup_dir, exist_ok=True)
        file_path = f"{standup_dir}/{today_date}.md"
        
        stats = get_today_stats()
        agents_list = ", ".join(stats["agents"]) if stats["agents"] else "None"
        
        summary_header = "## Activity Summary\n"
        summary_content = (
            f"- Agents called: {len(stats['agents'])} ({agents_list})\n"
            f"- Sessions: {stats['sessions']}\n"
            f"- Tasks completed: {stats['tasks_completed']}\n"
        )
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()
            
            # Check if Activity Summary section exists
            if "## Activity Summary" in content:
                # Update only the list items under Activity Summary
                import re
                # Pattern matches from ## Activity Summary until the next header or end of file
                pattern = r"(## Activity Summary\n)(.*?)(\n##|$)"
                replacement = f"\\1{summary_content}\\3"
                new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            else:
                # Prepend the Activity Summary after the first H1 header
                lines = content.split("\n")
                if lines and lines[0].startswith("# "):
                    new_content = lines[0] + "\n\n" + summary_header + summary_content + "\n" + "\n".join(lines[1:])
                else:
                    new_content = summary_header + summary_content + "\n" + content
            
            if new_content != content:
                with open(file_path, "w") as f:
                    f.write(new_content)
                log(f"Updated daily standup metrics: {file_path}")
        else:
            new_content = f"# Standup: {today_date}\n\n" + summary_header + summary_content + "\n## Notes\nNo activity today - all agents idle\n"
            with open(file_path, "w") as f:
                f.write(new_content)
            log(f"Created new daily standup: {file_path}")
            
    except Exception as e:
        log(f"ERROR updating standup: {e}")

def log_queue_snapshot():
    """Write a queue_snapshot event with pending task count and cycle timestamp."""
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": 'status = "todo"', "perPage": 1, "fields": "id"},
                         timeout=10)
        queue_depth = r.json().get("totalItems", 0)
        log_task_event("queue_snapshot", "dispatcher",
                       agent="dispatcher",
                       meta={"queue_depth": queue_depth,
                             "cycle_ts": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")})
    except Exception as e:
        log(f"WARN log_queue_snapshot: {e}")

def main():
    log("Dispatcher v4 started")
    while True:
        create_daily_standup()
        check_agent_health()
        log_queue_snapshot()
        
        if _state_changed():
            log("State change detected (Files or PB)")
            offline_agents = get_offline_agents()
            
            try:
                meta_path = os.path.join(CODEX_REPO_DIR, "AGENTS/CONFIG/fleet_meta.json")
                with open(meta_path, "r") as f:
                    fleet_meta = json.load(f)
                all_agents_meta = fleet_meta.get("team", [])
            except:
                all_agents_meta = []

            tasks = get_pending_tasks()
            for task in tasks:
                agent = task.get("assigned_agent")
                
                if not agent and all_agents_meta:
                    best_agent = find_best_substitute(task, "", all_agents_meta, [])
                    if best_agent:
                        agent = best_agent["heartbeatKey"]
                        log(f"Auto-assigned task '{task['title']}' to {agent}")
                        update_task_agent(task["id"], agent)
                
                if agent and agent not in offline_agents:
                    run_agent(agent, task)
            
            check_waiting_human()
        else:
            check_waiting_human()
        
        time.sleep(60)

if __name__ == "__main__":
    main()
