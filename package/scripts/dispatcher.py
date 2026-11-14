#!/usr/bin/env python3
"""
Fleet Dispatcher v4 — routes tasks to agents based on status and assigned_agent.
Implements Option 1: Dual Sync Strategy (Checks both Files and PocketBase).
"""

import subprocess
import sys
import time
import requests
import json
import os
import signal
import tempfile
import hashlib
import faulthandler
from datetime import datetime, timedelta
from scheduler_policy import availability, quota_retry_seconds

try:
    from council_coordinator import run_council_cycle as _run_council_cycle
    _COUNCIL_ENABLED = True
except ImportError:
    _COUNCIL_ENABLED = False

from flotilla_config import (
    PB_URL, FLEET_DIR as _FLEET_DIR, WORKSPACE_DIR, RUNTIME_DIR, FLEET_META_PATH as _FLEET_META_PATH,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GITHUB_REPO, load_agent_commands, github_repo_url,
)

FLEET_DIR = str(_FLEET_DIR)
CODEX_REPO_DIR = str(WORKSPACE_DIR)
FLEET_META_PATH = str(_FLEET_META_PATH)
LOG_FILE = f"{FLEET_DIR}/logs/dispatcher.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
LOG_BACKUP_COUNT = 5               # keep dispatcher.log.1 … .5
NOTIF_FILE = f"{FLEET_DIR}/logs/notifications.json"
OFFLINE_AGENTS_FILE = f"{FLEET_DIR}/logs/offline_agents.json"
DISPATCHER_CACHE_FILE = f"{FLEET_DIR}/logs/dispatcher_cache.json"
AGENT_FAILURES_FILE = f"{FLEET_DIR}/logs/agent_failures.json"

# Tracks currently-running agent subprocesses for parallel dispatch.
# agent_name -> (proc, task_dict, out_path, start_time)
_active_agents = {}


# Configurable Cooldown (default 5 minutes)
COOLDOWN_SECONDS = int(os.environ.get("DISPATCHER_COOLDOWN", "300"))
FAILURE_COOLDOWN_SECONDS = int(os.environ.get("DISPATCHER_FAILURE_COOLDOWN", "3600"))
TOKEN_FAILURE_COOLDOWN_SECONDS = int(os.environ.get("DISPATCHER_TOKEN_FAILURE_COOLDOWN", str(12 * 3600)))
TOKEN_FAILURE_PATTERNS = (
    "quota",
    "rate limit",
    "resource_exhausted",
    "exceeded",
    "out of tokens",
    "token limit",
    "insufficient_quota",
)

# Ensure logs directory exists
os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)

# Agent CLIs: built-in defaults, overridable in AGENTS/CONFIG/agent_commands.json.
AGENT_COMMANDS = load_agent_commands()

# Force a dispatch cycle every N hours even if no changes detected.
# Ensures heartbeats and health checks run regularly.
FORCE_DISPATCH_INTERVAL_SEC = 2 * 3600  # 2 hours

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > LOG_MAX_BYTES:
            for i in range(LOG_BACKUP_COUNT - 1, 0, -1):
                src = f"{LOG_FILE}.{i}"
                dst = f"{LOG_FILE}.{i+1}"
                if os.path.exists(src):
                    os.rename(src, dst)
            os.rename(LOG_FILE, f"{LOG_FILE}.1")
    except OSError:
        pass
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line, end="")

def log_idle_heartbeat(agent_key):
    """Log an 'idle' heartbeat to PocketBase on behalf of a skipped agent."""
    try:
        payload = {
            "agent": agent_key,
            "status": "idle",
            "note": "Logged by Dispatcher (Checksum Gate: No changes)"
        }
        requests.post(f"{PB_URL}/collections/heartbeats/records", json=payload, timeout=5)
    except Exception as e:
        log(f"WARN log_idle_heartbeat for {agent_key}: {e}")

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

def _load_fleet_meta():
    try:
        with open(FLEET_META_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading fleet_meta.json: {e}")
        return {}

def _parse_utc(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None

def _load_agent_failures():
    try:
        if os.path.exists(AGENT_FAILURES_FILE):
            with open(AGENT_FAILURES_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        log(f"Error loading agent failures: {e}")
    return {}

def _save_agent_failures(data):
    try:
        with open(AGENT_FAILURES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Error saving agent failures: {e}")

def _agent_meta_by_key(agent_key, all_agents_meta=None):
    if all_agents_meta is None:
        all_agents_meta = _load_fleet_meta().get("team", [])
    return next((a for a in all_agents_meta if a.get("heartbeatKey") == agent_key), {})

def is_agent_available(agent_key, agent_meta=None):
    """Explicit availability gate: token exhaustion beats heartbeat freshness."""
    meta = _load_fleet_meta()
    if agent_meta:
        meta = dict(meta, team=[agent_meta] + [a for a in meta.get('team', [])
                                             if a.get('heartbeatKey') != agent_meta.get('heartbeatKey')])
    return availability(agent_key, meta=meta, failures=_load_agent_failures())

def mark_agent_unavailable(agent_key, reason, cooldown_seconds):
    blocked_until = datetime.utcnow() + timedelta(seconds=cooldown_seconds)
    failures = _load_agent_failures()
    failures[agent_key] = {
        "blocked_until": blocked_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _save_agent_failures(failures)
    log(f"Marked {agent_key} unavailable until {failures[agent_key]['blocked_until']}: {reason}")

def classify_agent_failure(output):
    text = (output or "").lower()
    if any(pattern in text for pattern in TOKEN_FAILURE_PATTERNS):
        return "token/quota failure", quota_retry_seconds(output, TOKEN_FAILURE_COOLDOWN_SECONDS)
    return "invocation failure", FAILURE_COOLDOWN_SECONDS

def _active_project_watch_files():
    watched = [
        os.path.join(CODEX_REPO_DIR, "MISSION_CONTROL.md"),
        os.path.join(CODEX_REPO_DIR, "AGENTS/MESSAGES/inbox.json"),
        FLEET_META_PATH,
    ]

    meta = _load_fleet_meta()
    for project in meta.get("projects", []):
        if not project.get("is_active"):
            continue
        repo_path = str(project.get("repo_path", ".")).strip()
        if repo_path in (".", ""):
            continue
        watched.append(os.path.normpath(os.path.join(CODEX_REPO_DIR, repo_path, "MISSION_CONTROL.md")))

    return list(dict.fromkeys(watched))

def _state_changed():
    """Check if any watched files, PocketBase tasks have changed, or if interval exceeded."""
    cache = _load_dispatcher_cache()
    current_checksums = {}
    changed = False
    watched_files = _active_project_watch_files()

    if cache.get("watched_files", []) != watched_files:
        log("Detected change in active project watch set.")
        changed = True

    # 1. Check Files
    for file_path in watched_files:
        current_checksum = _file_checksum(file_path)
        current_checksums[file_path] = current_checksum

        if current_checksum is None:
            continue

        if file_path not in cache.get("checksums", {}) or cache["checksums"][file_path] != current_checksum:
            log(f"Detected change in file: {file_path}")
            changed = True

    # 2. Check PocketBase
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"sort": "-updated", "perPage": 1, "fields": "updated"},
                         timeout=10)
        items = r.json().get("items", [])
        if items:
            current_pb_ts = items[0]["updated"]
            if cache.get("pb_tasks_updated") != current_pb_ts:
                log(f"Detected change in PocketBase tasks: {current_pb_ts}")
                changed = True
                cache["pb_tasks_updated"] = current_pb_ts
    except Exception as e:
        log(f"Error checking PocketBase changes: {e}")

    # 3. Check forced interval
    now_ts = datetime.utcnow().timestamp()
    last_dispatch = cache.get("last_dispatch_ts", 0)
    if (now_ts - last_dispatch) > FORCE_DISPATCH_INTERVAL_SEC:
        log(f"Forced dispatch cycle (interval {FORCE_DISPATCH_INTERVAL_SEC}s exceeded)")
        changed = True
        cache["last_dispatch_ts"] = now_ts

    # Update cache
    cache["checksums"] = current_checksums
    cache["watched_files"] = watched_files
    if changed:
        # If we are dispatching, update the timestamp
        cache["last_dispatch_ts"] = now_ts

    _save_dispatcher_cache(cache)
    return changed

def send_telegram(message):
    if not TELEGRAM_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
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
    """Checks if an agent has been offline, ignoring dispatcher-synthesized idle heartbeats."""
    try:
        r = requests.get(f"{PB_URL}/collections/heartbeats/records",
                         params={
                             "filter": f'agent = "{agent_key}"',
                             "sort": "-updated",
                             "perPage": 20
                         }, timeout=10)
        items = r.json().get("items", [])
        items = [hb for hb in items if hb.get("status") != "idle"]

        now = datetime.utcnow()
        if not items:
            # Dispatcher model: no heartbeat just means agent hasn't been
            # dispatched yet — not an offline signal.
            return False, "No non-idle heartbeat (assumed online)"
        
        hb = items[0]
        ts_part = hb["updated"].split('.')[0].replace('Z', '')
        dt = datetime.strptime(ts_part, "%Y-%m-%d %H:%M:%S")
        age_seconds = (now - dt).total_seconds()
        last_seen_str = f"{int(age_seconds // 60)}m ago"
        # Dispatcher-led model: agents only post heartbeats when dispatched,
        # so heartbeat age is not a reliable offline signal. Use 7 days so
        # only truly abandoned agents are flagged; failures are tracked via
        # agent_failures.json instead.
        return (age_seconds > 604800), last_seen_str
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
        available, _ = is_agent_available(agent["heartbeatKey"], agent)
        if not available:
            continue
        
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

def reclaim_tasks_for_returning_agent(returning_agent_key):
    """When an agent comes back online, reclaim recently reassigned-away tasks
    that the substitute agent never started. Prevents the gem-pile-up that
    happened 2026-04-28 when codi was sandbox-blocked for ~2 hours and all her
    capture-flow P0s ended up on gem."""
    try:
        # Find recent reassignment events where this agent was the original owner.
        # 24h window — older reassignments are stale; respect that the substitute
        # may have made progress.
        since = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        r = requests.get(
            f"{PB_URL}/collections/task_events/records",
            params={
                "filter": f'event_type="reassignment" && timestamp >= "{since}"',
                "perPage": 200,
                "sort": "-created",
            }, timeout=10
        )
        events = r.json().get("items", [])
        candidates = [
            e for e in events
            if (e.get("meta") or {}).get("from_agent") == returning_agent_key
        ]
        if not candidates:
            return

        # Dedupe by task_id (most recent event per task)
        seen = {}
        for e in candidates:
            tid = e.get("task_id")
            if tid and tid not in seen:
                seen[tid] = e

        reclaimed = 0
        for tid, ev in seen.items():
            # Fetch current task. Only reclaim if:
            #   - assigned_agent is still the substitute (no further reassign)
            #   - status is still 'todo' (substitute didn't start work)
            try:
                t = requests.get(f"{PB_URL}/collections/tasks/records/{tid}", timeout=10).json()
            except Exception:
                continue
            current_agent = t.get("assigned_agent")
            substitute    = (ev.get("meta") or {}).get("to_agent")
            if current_agent != substitute:
                continue  # already moved further; leave it
            if t.get("status") != "todo":
                continue  # substitute already in_progress / shipped — respect their work

            try:
                requests.patch(f"{PB_URL}/collections/tasks/records/{tid}",
                               json={"assigned_agent": returning_agent_key}, timeout=10)
                log_task_event("reclaim", tid,
                               agent="dispatcher",
                               meta={"from_agent": substitute,
                                     "to_agent": returning_agent_key,
                                     "reason": "original owner returned online",
                                     "original_reassignment": ev.get("id")})
                reclaimed += 1
            except Exception as e:
                log(f"ERROR reclaiming task {tid}: {e}")

        if reclaimed:
            log(f"Reclaimed {reclaimed} task(s) back to {returning_agent_key} on recovery")
            send_telegram(f"♻️ Reclaimed {reclaimed} task(s) for {returning_agent_key.capitalize()} on return.")
    except Exception as e:
        log(f"ERROR in reclaim_tasks_for_returning_agent: {e}")


def reassign_tasks(offline_agent_key, all_agents_meta):
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records",
                         params={"filter": f'assigned_agent = "{offline_agent_key}" && status = "in_progress"'}, timeout=10)
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
                                   json={"status": "blocked", "reassignment_count": count, "last_reassignment_at": now_iso}, timeout=10)
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

                prev_status = task.get("status", "todo")
                # If task was in_progress, reset to todo so new agent starts clean
                new_status = "todo" if prev_status == "in_progress" else prev_status
                reason = "agent offline / likely context limit hit" if prev_status == "in_progress" else "agent offline"

                # Check if a task branch exists on GitHub
                branch_name = f"task/{task['id']}"
                branch_url = None
                try:
                    result = subprocess.run(
                        ["git", "ls-remote", "--heads", "origin", branch_name],
                        cwd=CODEX_REPO_DIR, capture_output=True, text=True, timeout=10
                    )
                    if result.stdout.strip():
                        branch_url = github_repo_url(f"/tree/{branch_name}")
                except Exception as e:
                    log(f"WARN branch check failed for {branch_name}: {e}")

                log(f"Reassigning task '{task['title']}' ({prev_status} → {new_status}) to {new_agent_key}")
                requests.patch(f"{PB_URL}/collections/tasks/records/{task['id']}",
                               json={"assigned_agent": new_agent_key,
                                     "status": new_status,
                                     "reassignment_count": count,
                                     "last_reassignment_at": now_iso},
                               timeout=10)
                log_task_event("reassignment", task["id"],
                               agent="dispatcher",
                               meta={"from_agent": offline_agent_key,
                                     "to_agent": new_agent_key,
                                     "reassignment_count": count,
                                     "reason": reason,
                                     "branch": branch_url})
                comment = f"Reassigned from {offline_agent_key} to {new_agent_key} ({reason})."
                if prev_status == "in_progress":
                    if branch_url:
                        comment += f" Branch with partial work: {branch_url} — check out branch, read WORKLOG.md and git log, then continue."
                    else:
                        comment += f" No branch found — start fresh on task/{task['id']}."
                post_comment(task["id"], "dispatcher", comment, "comment")
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
            
            is_available, availability_reason = is_agent_available(agent_key, agent_meta)
            if not is_available:
                # Deliberate pauses and provider quotas are not offline failures.
                # Keep their work queued instead of fanning it out to other models.
                continue
            is_currently_offline, last_seen_str = is_agent_offline(agent_key)
            if not is_available:
                is_currently_offline = True
                last_seen_str = availability_reason
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
                # Reclaim recently-reassigned-away tasks the substitute hasn't started.
                reclaim_tasks_for_returning_agent(agent_key)
                
        if changed:
            save_offline_agents(offline_data)
    except Exception as e:
        log(f"ERROR in check_agent_health: {e}")

# Repos whose new commits count as evidence that an agent did real work.
# Add more with FLOTILLA_TRACKED_REPOS="/path/one:/path/two".
TRACKED_REPOS = [CODEX_REPO_DIR] + [
    p for p in os.environ.get("FLOTILLA_TRACKED_REPOS", "").split(":") if p
]

def _has_commit_since(start_time):
    """Return True if any tracked repo has at least one new commit since start_time (epoch float)."""
    since = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
    for repo in TRACKED_REPOS:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"--since={since}"],
                cwd=repo, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except Exception:
            pass
    return False


def _collect_finished_agents():
    """Poll running agent processes; handle output and update PB for completed ones."""
    for agent_name in list(_active_agents):
        proc, task, out_path, start_time = _active_agents[agent_name]
        ret = proc.poll()
        if ret is None:
            continue  # still running
        del _active_agents[agent_name]
        try:
            with open(out_path, "r", errors="replace") as f:
                output = (f.read() or "No output")[-5000:]
        except OSError:
            output = "No output"
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass
        if ret == 0:
            post_comment(task["id"], agent_name, output)
            try:
                resp = requests.get(f"{PB_URL}/collections/tasks/records/{task['id']}", timeout=10)
                current_status = resp.json().get("status", "in_progress")
            except Exception:
                current_status = "in_progress"
            if current_status == "in_progress":
                if _has_commit_since(start_time):
                    update_task_status(task["id"], "peer_review", from_status="in_progress", agent=agent_name)
                    log(f"Agent {agent_name} finished '{task['title']}' → peer_review (commit found)")
                else:
                    update_task_status(task["id"], "todo", from_status="in_progress", agent=agent_name)
                    log(f"Agent {agent_name} finished '{task['title']}' → todo (clean exit, no commit)")
            else:
                log(f"Agent {agent_name} finished '{task['title']}' → {current_status} (agent-set)")
        else:
            log(f"ERROR: Agent {agent_name} failed (exit {ret}) on '{task['title']}'")
            post_comment(task["id"], agent_name, f"FAILED exit {ret}:\n{output[:1000]}", "feedback")
            reason, cooldown = classify_agent_failure(output)
            mark_agent_unavailable(agent_name, reason, cooldown)
            update_task_status(task["id"], "todo", from_status="in_progress", agent=agent_name)


AGENT_TIMEOUT_SECONDS = {
    # 2026-11-05: raised to 60 min — LM-G02/G03 game chapters were killed at 20 min
    # twice each mid-build (build + playtest + screenshots + push exceed 20 min).
    "clau":  3600,  # 60 min
    "gem":   3600,  # 60 min
    "misty": 1200,
    "codi":  3600,  # 60 min
    "muse":  3600,  # 60 min
    "qwen":  3600,  # 60 min — local 30b model, thinking mode disabled but codegen is slow
}
_DEFAULT_AGENT_TIMEOUT = 1200

def _kill_timed_out_agents():
    """SIGTERM agents that have been running longer than their per-agent timeout."""
    now = time.time()
    for agent_name, (proc, task, _out_path, start_time) in list(_active_agents.items()):
        limit = AGENT_TIMEOUT_SECONDS.get(agent_name, _DEFAULT_AGENT_TIMEOUT)
        if now - start_time > limit:
            log(f"Agent {agent_name} timed out on '{task['title']}' after {limit}s — killing PG {proc.pid}")
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def _reclaim_stale_tasks():
    """Reset in_progress tasks whose agent process is no longer running.

    An in_progress task with no live agent process means the agent exited
    without setting a final status. After a 2-hour grace period we reset
    to todo so the task gets dispatched again.
    """
    try:
        resp = requests.get(f"{PB_URL}/collections/tasks/records",
                            params={"filter": 'status = "in_progress"', "perPage": 100},
                            timeout=10)
        stale_tasks = resp.json().get("items", [])
    except Exception:
        return
    now = time.time()
    active_task_ids = {task["id"] for _, (_, task, _, _) in _active_agents.items()}
    for task in stale_tasks:
        if task["id"] in active_task_ids:
            continue  # actively running — leave it
        try:
            updated_ts = task.get("updated", "")
            from datetime import datetime, timezone
            updated_dt = datetime.fromisoformat(updated_ts.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 3600
        except Exception:
            continue
        if age_hours >= 2:
            log(f"Reclaiming stale in_progress task '{task['title']}' (no active agent, {age_hours:.1f}h old)")
            update_task_status(task["id"], "todo", from_status="in_progress", agent="dispatcher")


def run_agent(agent_name, task):
    if agent_name not in AGENT_COMMANDS:
        return
    if agent_name in _active_agents:
        log(f"Skipping {agent_name} for '{task['title']}': already running a task")
        return
    is_available, reason = is_agent_available(agent_name)
    if not is_available:
        log(f"Skipping {agent_name} for '{task['title']}': {reason}")
        return

    log(f"Dispatching task '{task['title']}' to {agent_name}")
    update_task_status(task["id"], "in_progress", from_status=task.get("status"), agent=agent_name)

    cmd = list(AGENT_COMMANDS[agent_name])
    if agent_name in ["clau", "gem", "codi", "muse"]:
        task_prompt = f"\n\nYOUR TASK: {task['title']}\nDescription: {task.get('description', '')}"
        cmd[-1] = cmd[-1] + task_prompt
        if agent_name == 'gem':
            cmd[-1] = (
                'This is an explicit dispatcher assignment; availability was already checked. '
                'Do not run heartbeat_check.py or scan unrelated queues. '
                'Read GEMINI.md and the applicable project rules, then perform only the task below. '
                'Update its actual status when finished; retain waiting_human for human-dependent work.'
                + task_prompt
            )

    # For qwen the heartbeat is a self-directed scanner; inject the task via
    # env vars so it skips the PocketBase scan and uses the exact task.
    env = None
    if agent_name == "qwen":
        env = dict(os.environ)
        env["QWEN_TASK_ID"] = task["id"]
        env["QWEN_TASK_TITLE"] = task.get("title", "")
        env["QWEN_TASK_DESC"] = task.get("description", "")

    out_fd, out_path = tempfile.mkstemp(suffix=f"_{agent_name}.log", prefix="dispatcher_agent_")
    os.close(out_fd)
    try:
        out_f = open(out_path, "w")
        proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT,
                                start_new_session=True, env=env)
        out_f.close()
        _active_agents[agent_name] = (proc, task, out_path, time.time())
        log(f"Agent {agent_name} launched PID {proc.pid}")
    except Exception as e:
        log(f"ERROR launching {agent_name}: {e}")
        mark_agent_unavailable(agent_name, "dispatcher exception", FAILURE_COOLDOWN_SECONDS)
        update_task_status(task["id"], "todo", from_status="in_progress", agent=agent_name)
        try:
            os.unlink(out_path)
        except OSError:
            pass

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


def _run_with_group_timeout(cmd, timeout):
    """Run cmd capturing output; on timeout kill the WHOLE process group.

    subprocess.run(timeout=...) only kills the direct child; a grandchild
    (e.g. `git push` -> ssh/credential helper) can keep the pipe open and make
    the post-kill communicate() block forever. Suspected cause of the
    2026-11-10 05:31 dispatcher freeze (40 h silent stall)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        raise subprocess.TimeoutExpired(cmd, timeout, output=out, stderr=err)
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def run_sync_scripts(force_gh=False):
    """Run GitHub and Mission Control sync scripts with error handling."""
    scripts_dir = str(RUNTIME_DIR)
    
    # 1. Mission Control Sync (Every cycle)
    try:
        log("Running Mission Control sync...")
        res = _run_with_group_timeout([sys.executable, os.path.join(scripts_dir, "fleet_sync.py")], 60)
        for line in (res.stdout or "").splitlines():
            if line.startswith("WARN"):
                log(f"fleet_sync: {line}")
        if res.returncode != 0:
            log(f"ERROR: fleet_sync.py failed: {res.stderr}")
            send_telegram(f"❌ Fleet Sync Error: MISSION_CONTROL.md update failed.\n\n{res.stderr[:200]}")
    except Exception as e:
        log(f"ERROR executing fleet_sync.py: {e}")

    # 2. GitHub Sync (Passed force_gh or every 5 mins via main loop)
    if force_gh:
        try:
            log("Running GitHub sync...")
            res = _run_with_group_timeout([sys.executable, os.path.join(scripts_dir, "github_sync.py"), "--once"], 90)
            if res.returncode != 0:
                log(f"ERROR: github_sync.py failed: {res.stderr}")
                send_telegram(f"❌ GitHub Sync Error: bidirectional sync failed.\n\n{res.stderr[:200]}")
        except Exception as e:
            log(f"ERROR executing github_sync.py: {e}")


WATCHDOG_SECONDS = 300  # one cycle should take ~seconds; 5 min means we are stuck
_STDERR_LOG = f"{FLEET_DIR}/logs/dispatcher_err.log"


def _report_previous_gap():
    """On startup, alert if the previous run stopped logging long before now."""
    try:
        with open(LOG_FILE, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4096))
            tail = f.read().decode("utf-8", "replace").strip().splitlines()
        last = next((l for l in reversed(tail) if l.startswith("[")), None)
        if not last:
            return
        last_ts = datetime.strptime(last[1:20], "%Y-%m-%d %H:%M:%S")
        gap_min = (datetime.now() - last_ts).total_seconds() / 60
        if gap_min > 10:
            msg = (f"⚠️ Dispatcher restarted after {gap_min:.0f} min of silence "
                   f"(last log {last[1:20]}). If this was a watchdog exit, the stack "
                   f"trace is in logs/dispatcher_err.log.")
            log(msg)
            send_telegram(msg)
    except Exception as e:
        log(f"WARN gap check failed: {e}")


def main():
    log("Dispatcher v7 started — agent-owned status, stale reclaim after 2h")
    # Stack dumps: on demand (kill -USR1 <pid>) and automatically when a cycle
    # exceeds WATCHDOG_SECONDS, after which the process exits and launchd
    # (KeepAlive) restarts it.
    try:
        _fh_file = open(_STDERR_LOG, "a")
    except Exception:
        _fh_file = sys.stderr
    faulthandler.enable(file=_fh_file)
    faulthandler.register(signal.SIGUSR1, file=_fh_file, all_threads=True)
    _report_previous_gap()
    # In the dispatcher-led model agents only post heartbeats when dispatched,
    # so stale heartbeat timestamps are not a reliable offline signal.
    # Start clean; actual failures will repopulate this file.
    save_offline_agents({})
    cycle_count = 0
    while True:
        faulthandler.dump_traceback_later(WATCHDOG_SECONDS, exit=True, file=_fh_file)
        _collect_finished_agents()
        _kill_timed_out_agents()
        if cycle_count % 10 == 0:
            _reclaim_stale_tasks()
        create_daily_standup()
        check_agent_health()
        log_queue_snapshot()
        
        # Run sync scripts (MC every cycle, GH every 5 cycles)
        run_sync_scripts(force_gh=(cycle_count % 5 == 0))
        
        # Alert on new human issues imported from GitHub
        if cycle_count % 5 == 0:
            try:
                # Find tasks created in the last 6 minutes with no assigned agent or imported description
                r = requests.get(f"{PB_URL}/collections/tasks/records",
                                 params={"filter": 'created > "' + (datetime.utcnow() - timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M:%S") + '" && description ~ "Imported from GitHub issue"', "perPage": 10},
                                 timeout=10)
                new_imported = r.json().get("items", [])
                for task in new_imported:
                    url = task.get('github_issue_url') or f"https://github.com/{GITHUB_REPO}/issues/{task.get('gh_issue_id')}"
                    send_telegram(f"🔔 New GitHub Issue Imported: {task['title']}\nStatus: todo\nReview at: {url}")
            except Exception as e:
                log(f"WARN human issue alert failed: {e}")
        
        # Every 10 cycles (10 minutes), log an idle heartbeat for all agents 
        # if they are skipped by the checksum gate. This keeps the timeline 
        # active without spending any tokens.
        should_log_idle = (cycle_count % 10 == 0)
        
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
                
                if agent:
                    is_available, reason = is_agent_available(agent, _agent_meta_by_key(agent, all_agents_meta))
                    if not is_available:
                        log(f"Skipping task '{task['title']}' for unavailable agent {agent}: {reason}")
                        continue

                if agent and agent not in offline_agents:
                    run_agent(agent, task)
                elif agent and agent in offline_agents:
                    log(f"Skipping task '{task['title']}' — agent {agent} is offline")
            
            check_waiting_human()

            # Run council coordinator every cycle to advance council_open goals
            if _COUNCIL_ENABLED:
                try:
                    _run_council_cycle()
                except Exception as _cc_exc:
                    log(f"WARN council_coordinator cycle failed: {_cc_exc}")
        else:
            if should_log_idle:
                try:
                    meta_path = os.path.join(CODEX_REPO_DIR, "AGENTS/CONFIG/fleet_meta.json")
                    with open(meta_path, "r") as f:
                        fleet_meta = json.load(f)
                    for agent in fleet_meta.get("team", []):
                        log_idle_heartbeat(agent["heartbeatKey"])
                except Exception as e:
                    log(f"WARN idle heartbeat bulk log failed: {e}")
            check_waiting_human()

            # Also run council coordinator on idle cycles to catch timeouts
            if _COUNCIL_ENABLED:
                try:
                    _run_council_cycle()
                except Exception as _cc_exc:
                    log(f"WARN council_coordinator cycle failed: {_cc_exc}")
        
        faulthandler.cancel_dump_traceback_later()
        cycle_count += 1
        time.sleep(60)

if __name__ == "__main__":
    main()
