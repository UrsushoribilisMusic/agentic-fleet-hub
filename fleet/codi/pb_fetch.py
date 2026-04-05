#!/usr/bin/env python3
"""Pre-fetch PocketBase snapshot for Codi's sandboxed heartbeat session."""
import json, urllib.request, datetime, sys

PB = "http://127.0.0.1:8090/api/collections"
OUT = "/Users/miguelrodriguez/fleet/codi/pb_snapshot.json"

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[pb_fetch] WARN: {url} -> {e}", file=sys.stderr)
        return {"items": []}

lessons   = fetch(f"{PB}/lessons/records?filter=status%3D'active'&perPage=50")
tasks     = fetch(f"{PB}/tasks/records?perPage=50&sort=-updated")
heartbeat = fetch(f"{PB}/heartbeats/records?sort=-created&perPage=10")

snapshot = {
    "fetched_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "lessons":    lessons.get("items", []),
    "tasks":      tasks.get("items", []),
    "heartbeats": heartbeat.get("items", []),
}

with open(OUT, "w") as f:
    json.dump(snapshot, f, indent=2)

print(f"[pb_fetch] snapshot written: {len(snapshot['tasks'])} tasks, "
      f"{len(snapshot['lessons'])} lessons, {len(snapshot['heartbeats'])} heartbeats")
