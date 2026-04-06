#!/usr/bin/env python3
import os
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Constants
FLEET_DIR = "/Users/miguelrodriguez/fleet"
LOG_DIR = f"{FLEET_DIR}/logs"
STANDUPS_DIR = "/Users/miguelrodriguez/projects/agentic-fleet-hub/standups"
DISPATCHER_LOG = f"{LOG_DIR}/dispatcher.log"

# Milestones for comparison
CHECKSUM_GATE_DEPLOYED = datetime(2026, 4, 5)
CIRCUIT_BREAKER_DEPLOYED = datetime(2026, 3, 27)

VALID_AGENTS = {"scout", "echo", "closer", "clau", "gem", "codi", "misty", "gemma"}

def parse_dispatcher_logs():
    stats = {
        "events": [],
        "reassignments": [],
        "circuit_breaker_fires": []
    }
    
    if not os.path.exists(DISPATCHER_LOG):
        return stats

    offline_re = re.compile(r"\[([\d\-\s:]+)\] Agent (\w+) detected OFFLINE")
    recovered_re = re.compile(r"\[([\d\-\s:]+)\] Agent (\w+) RECOVERED")
    reassign_re = re.compile(r"\[([\d\-\s:]+)\] Reassigning task '(.+?)' to (\w+)")
    blocked_re = re.compile(r"\[([\d\-\s:]+)\] (?:Circuit breaker fired|Blocking task|Blocking repeating) .*#(\d+)")

    with open(DISPATCHER_LOG, "r") as f:
        for line in f:
            # OFFLINE
            m = offline_re.search(line)
            if m:
                stats["events"].append({
                    "ts": m.group(1),
                    "agent": m.group(2),
                    "type": "OFFLINE"
                })
                continue
            
            # RECOVERED
            m = recovered_re.search(line)
            if m:
                stats["events"].append({
                    "ts": m.group(1),
                    "agent": m.group(2),
                    "type": "RECOVERED"
                })
                continue
            
            # REASSIGN
            m = reassign_re.search(line)
            if m:
                stats["reassignments"].append({
                    "ts": m.group(1),
                    "task": m.group(2),
                    "to_agent": m.group(3)
                })
                continue

            # BLOCKED / CIRCUIT BREAKER
            m = blocked_re.search(line)
            if m:
                stats["circuit_breaker_fires"].append({
                    "ts": m.group(1),
                    "task_id": m.group(2)
                })

    return stats

def parse_standups():
    daily_stats = defaultdict(lambda: defaultdict(lambda: {"sessions": 0, "idle_skips": 0}))
    
    if not os.path.exists(STANDUPS_DIR):
        return daily_stats

    for filename in os.listdir(STANDUPS_DIR):
        if not filename.endswith(".md") or filename == "index.json":
            continue
        
        match = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
        if not match:
            continue
        date_str = match.group(1)
            
        path = os.path.join(STANDUPS_DIR, filename)
        with open(path, "r") as f:
            content = f.read()
            
            sessions_match = re.search(r"- Sessions: (\d+)", content)
            total_sessions = int(sessions_match.group(1)) if sessions_match else 0
            
            # Header check for author
            title_match = re.search(r"# Standup .*?\((.*?)\)", content)
            author = title_match.group(1).lower() if title_match else None
            if author and author not in VALID_AGENTS:
                author = None

            # Look for "No changes. Going idle"
            # It might appear in the aggregate summary or per-agent blocks
            
            agent_blocks = re.split(r"##\s+(\w+)", content)
            if len(agent_blocks) > 1:
                for i in range(1, len(agent_blocks), 2):
                    agent_name = agent_blocks[i].lower()
                    if agent_name not in VALID_AGENTS:
                        continue
                        
                    agent_content = agent_blocks[i+1]
                    idle_count = agent_content.count("No changes. Going idle")
                    
                    daily_stats[date_str][agent_name]["idle_skips"] += idle_count
                    
            # If we have total_sessions and an author, but couldn't split by agent,
            # attribute sessions to author.
            if total_sessions > 0:
                # If only one agent was active (from summary), use author
                active_match = re.search(r"- Agents called: (\d+)", content)
                if active_match and active_match.group(1) == "1" and author:
                    daily_stats[date_str][author]["sessions"] += total_sessions
                elif author:
                    # Fallback: give sessions to the standup author if no other info
                    daily_stats[date_str][author]["sessions"] += total_sessions

    return daily_stats

def calculate_metrics():
    disp_stats = parse_dispatcher_logs()
    standup_stats = parse_standups()
    
    agent_failures = defaultdict(list)
    for ev in disp_stats["events"]:
        agent_failures[ev["agent"]].append(ev)
    
    mttr_data = []
    mtbf_data = []
    
    for agent, events in agent_failures.items():
        events.sort(key=lambda x: x["ts"])
        last_offline = None
        for ev in events:
            if ev["type"] == "OFFLINE":
                if last_offline:
                    d1 = datetime.strptime(last_offline["ts"], "%Y-%m-%d %H:%M:%S")
                    d2 = datetime.strptime(ev["ts"], "%Y-%m-%d %H:%M:%S")
                    mtbf_data.append((d2 - d1).total_seconds())
                last_offline = ev
            elif ev["type"] == "RECOVERED" and last_offline:
                d1 = datetime.strptime(last_offline["ts"], "%Y-%m-%d %H:%M:%S")
                d2 = datetime.strptime(ev["ts"], "%Y-%m-%d %H:%M:%S")
                mttr_data.append((d2 - d1).total_seconds())
                last_offline = None

    reassign_before = [r for r in disp_stats["reassignments"] if datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S") < CIRCUIT_BREAKER_DEPLOYED]
    reassign_after = [r for r in disp_stats["reassignments"] if datetime.strptime(r["ts"], "%Y-%m-%d %H:%M:%S") >= CIRCUIT_BREAKER_DEPLOYED]
    
    wakes_before = {"idle": 0, "sessions": 0}
    wakes_after = {"idle": 0, "sessions": 0}
    
    per_agent_daily = []
    for date_str, agents in standup_stats.items():
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        for agent, s in agents.items():
            rate = s["idle_skips"] / s["sessions"] if s["sessions"] > 0 else 0
            per_agent_daily.append({
                "date": date_str,
                "agent": agent,
                "sessions": s["sessions"],
                "idle_skips": s["idle_skips"],
                "false_wake_rate": rate
            })
            
            target = wakes_after if dt >= CHECKSUM_GATE_DEPLOYED else wakes_before
            target["idle"] += s["idle_skips"]
            target["sessions"] += s["sessions"]

    # Last circuit breaker fire
    last_cb = None
    if disp_stats["circuit_breaker_fires"]:
        last_cb = max(f["ts"] for f in disp_stats["circuit_breaker_fires"])

    output = {
        "overall": {
            "mtbf_seconds": sum(mtbf_data) / len(mtbf_data) if mtbf_data else 0,
            "mttr_seconds": sum(mttr_data) / len(mttr_data) if mttr_data else 0,
            "reassignment_freq_before_cb": len(reassign_before),
            "reassignment_freq_after_cb": len(reassign_after),
            "false_wake_rate_before_gate": wakes_before["idle"] / wakes_before["sessions"] if wakes_before["sessions"] > 0 else 0,
            "false_wake_rate_after_gate": wakes_after["idle"] / wakes_after["sessions"] if wakes_after["sessions"] > 0 else 0,
            "circuit_breaker_last_fired": last_cb,
            "circuit_breaker_total_fires": len(disp_stats["circuit_breaker_fires"])
        },
        "per_agent_daily": per_agent_daily,
        "raw_event_counts": {
            "offline": sum(1 for e in disp_stats["events"] if e["type"] == "OFFLINE"),
            "recovered": sum(1 for e in disp_stats["events"] if e["type"] == "RECOVERED"),
            "reassigned": len(disp_stats["reassignments"]),
            "blocked": len(disp_stats["circuit_breaker_fires"])
        }
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    calculate_metrics()
