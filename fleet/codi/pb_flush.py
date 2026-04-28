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

Forward-progress guard (added 2026-04-28 against the false-peer_review pattern):
A PATCH on `tasks` that sets status='peer_review' or 'approved' requires a real
git commit referencing the ticket (PC-N or #N) in main on either of the active
repos within the last hour. Otherwise the flip is rejected and logged. Codi can
still stage 'waiting_human', 'todo', or 'in_progress' freely — these are state
markers, not progress claims.
"""
import json, urllib.request, urllib.error, os, sys, re, subprocess, time

PENDING = "/Users/miguelrodriguez/fleet/codi/pb_pending_writes.json"
PB      = "http://127.0.0.1:8090/api/collections"
REPOS   = [
    "/Users/miguelrodriguez/projects/agentic-fleet-hub",
    "/Users/miguelrodriguez/projects/private-core/PrivateCore",
]
PROGRESS_STATES = {"peer_review", "approved", "merged"}


def get_task_title(record_id):
    try:
        with urllib.request.urlopen(f"{PB}/tasks/records/{record_id}", timeout=5) as r:
            return json.loads(r.read()).get("title", "")
    except Exception:
        return ""


def commit_exists_for(ticket_id):
    """Return True if any of the active repos has a commit on main referencing
    `ticket_id` (e.g. 'PC-108' or '#225') in the last hour."""
    for repo in REPOS:
        try:
            out = subprocess.check_output(
                ["git", "-C", repo, "log", "main", "--since=1 hour ago",
                 "--grep", ticket_id, "--oneline"],
                stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            if out.strip():
                return True
        except Exception:
            continue
    return False


def is_forward_progress_flip(op):
    """A tasks PATCH that moves status into peer_review/approved/merged."""
    if op.get("method", "POST").upper() != "PATCH":
        return False
    if op.get("collection") != "tasks":
        return False
    new_status = (op.get("data") or {}).get("status")
    return new_status in PROGRESS_STATES

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
    record_id  = op.get("id", "")

    # Reject forward-progress status flips without a verifying commit.
    if is_forward_progress_flip(op):
        title = get_task_title(record_id)
        m = re.search(r"(PC-\d+|#\d+)", title)
        if not m:
            print(f"[pb_flush] REJECT {record_id} (no PC-N/#N in title to verify against)", file=sys.stderr)
            errors += 1
            continue
        ticket_id = m.group(1)
        if not commit_exists_for(ticket_id):
            print(f"[pb_flush] REJECT {record_id} ({ticket_id} → {op['data'].get('status')}): "
                  f"no recent commit on main mentions {ticket_id}", file=sys.stderr)
            errors += 1
            continue
        print(f"[pb_flush] verified {ticket_id} has a recent commit, allowing {op['data'].get('status')} flip")

    data = json.dumps(op.get("data", {})).encode()

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
