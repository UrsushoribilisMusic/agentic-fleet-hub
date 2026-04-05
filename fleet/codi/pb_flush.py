#!/usr/bin/env python3
"""Execute PB write operations staged by Codi during her sandboxed session.

Codi writes intended PocketBase operations to:
  ~/fleet/codi/pb_pending_writes.json

Format:
  [
    {"method": "POST", "collection": "heartbeats", "data": {...}},
    {"method": "PATCH", "collection": "tasks", "id": "recordid", "data": {...}}
  ]

This script runs after Codex exits and flushes those operations.
"""
import json, urllib.request, urllib.error, os, sys

PENDING = "/Users/miguelrodriguez/fleet/codi/pb_pending_writes.json"
PB      = "http://127.0.0.1:8090/api/collections"

if not os.path.exists(PENDING):
    print("[pb_flush] no pending writes file, nothing to do")
    sys.exit(0)

with open(PENDING) as f:
    ops = json.load(f)

if not ops:
    print("[pb_flush] pending writes file is empty")
    os.remove(PENDING)
    sys.exit(0)

print(f"[pb_flush] executing {len(ops)} staged operation(s)")
errors = 0

for op in ops:
    method     = op.get("method", "POST").upper()
    collection = op["collection"]
    data       = json.dumps(op.get("data", {})).encode()
    record_id  = op.get("id", "")

    if method == "PATCH" and record_id:
        url = f"{PB}/{collection}/records/{record_id}"
    else:
        url = f"{PB}/{collection}/records"

    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            result = json.loads(r.read())
            print(f"[pb_flush] {method} {collection}/{record_id or ''} -> {result.get('id','ok')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[pb_flush] ERROR {method} {collection}: {e.code} {body}", file=sys.stderr)
        errors += 1
    except Exception as e:
        print(f"[pb_flush] ERROR {method} {collection}: {e}", file=sys.stderr)
        errors += 1

os.remove(PENDING)
print(f"[pb_flush] done, {errors} error(s)")
sys.exit(1 if errors else 0)
