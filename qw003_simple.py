#!/usr/bin/env python3
"""
QW-003: Simple version - just generate JSON data
"""

import json
import requests
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import statistics

OUTPUT_DIR = Path("/Users/miguelrodriguez/fleet/analytics/charts")
OUTPUT_JSON = OUTPUT_DIR / "ticket_duration.json"

def parse_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.min
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    return datetime.min

def calc_duration(task: dict) -> float:
    created = parse_date(task.get("created", ""))
    updated = parse_date(task.get("updated", ""))
    status = task.get("status", "").lower()
    if status not in ["approved", "done", "closed"]:
        return None
    if created == datetime.min:
        return None
    if updated != datetime.min:
        return (updated - created).total_seconds() / 86400
    return None

def get_project(tid: str) -> str:
    if tid.startswith("#"):
        return "other"
    for p in ["PC", "SC", "CR", "RT", "fleet", "QW"]:
        if tid.startswith(p):
            return p
    return "other"

def calc_stats(durs: list) -> dict:
    if not durs:
        return {"mean": 0, "median": 0, "std_dev": 0, "p90": 0, "p95": 0, "count": 0}
    ds = sorted(durs)
    return {
        "mean": statistics.mean(ds),
        "median": statistics.median(ds),
        "std_dev": statistics.stdev(ds) if len(ds) > 1 else 0,
        "p90": ds[int(len(ds) * 0.9)] if ds else 0,
        "p95": ds[int(len(ds) * 0.95)] if ds else 0,
        "count": len(ds)
    }

def main():
    print("QW-003: Ticket Duration")
    
    all_tasks = []
    page = 1
    while True:
        resp = requests.get("http://localhost:8090/api/collections/tasks/records",
                           params={"page": page, "perPage": 500}, timeout=30)
        if resp.status_code != 200:
            break
        data = resp.json()
        all_tasks.extend(data.get("items", []))
        if data.get("page") >= data.get("totalPages", 1):
            break
        page += 1
    
    durations = []
    proj_durs = defaultdict(list)
    agent_durs = defaultdict(list)
    resolved = []
    
    for task in all_tasks:
        d = calc_duration(task)
        if d is not None:
            durations.append(d)
            p = get_project(task.get("id", ""))
            proj_durs[p].append(d)
            a = task.get("assigned_agent", "unknown")
            if a != "unknown":
                agent_durs[a].append(d)
            resolved.append({"id": task.get("id",""), "title": task.get("title",""),
                           "duration_days": d, "project": p, "assigned_agent": a})
    
    stats = calc_stats(durations)
    stats['total_tickets'] = len(durations)
    
    histogram = {"0-1 days": 0, "1-3 days": 0, "3-7 days": 0, "7-14 days": 0, "14-30 days": 0, "30+ days": 0}
    for d in durations:
        if d < 1: histogram["0-1 days"] += 1
        elif d < 3: histogram["1-3 days"] += 1
        elif d < 7: histogram["3-7 days"] += 1
        elif d < 14: histogram["7-14 days"] += 1
        elif d < 30: histogram["14-30 days"] += 1
        else: histogram["30+ days"] += 1
    
    top_10 = sorted(resolved, key=lambda x: x['duration_days'], reverse=True)[:10]
    per_project = {p: calc_stats(d) for p, d in proj_durs.items()}
    per_agent = {a: calc_stats(d) for a, d in agent_durs.items()}
    
    output = {
        "statistics": stats,
        "histogram": histogram,
        "top_10": top_10,
        "per_project": per_project,
        "per_agent": per_agent
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"Saved to {OUTPUT_JSON}")
    print(f"Analyzed {len(durations)} tickets")
    print(f"Mean: {stats['mean']:.1f} days, Std Dev: {stats['std_dev']:.1f}")
    print("QW-003 COMPLETE")

if __name__ == "__main__":
    main()
