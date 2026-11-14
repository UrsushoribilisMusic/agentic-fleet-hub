#!/usr/bin/env python3
"""
Compliance Archive Writer — EU AI Act tamper-evident logging.

Maintains two append-only JSONL files:
  <fleet_dir>/heartbeat_archive.jsonl — one entry per heartbeat event
  <fleet_dir>/task_archive.jsonl      — lifecycle events per task

Each entry carries a prev_entry_hash (SHA-256 of the preceding raw JSON line)
creating a tamper-evidence chain. Files are never pruned; they should be
periodically committed to a private fleet-audit-log git branch.

Usage (standalone sync from PocketBase):
    python3 archive_writer.py --sync-heartbeats
    python3 archive_writer.py --sync-tasks
    python3 archive_writer.py --sync-all

Usage (as a module):
    from archive_writer import append_heartbeat, append_task_event
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from flotilla_config import FLEET_DIR as _FLEET_DIR
FLEET_DIR = os.environ.get("FLEET_DIR", str(_FLEET_DIR))
from flotilla_config import PB_URL as _PB_URL
POCKETBASE_URL = os.environ.get("POCKETBASE_URL", _PB_URL)

HB_ARCHIVE = os.path.join(FLEET_DIR, "heartbeat_archive.jsonl")
TASK_ARCHIVE = os.path.join(FLEET_DIR, "task_archive.jsonl")

# Sentinel used as prev_entry_hash for the very first record in a file.
GENESIS_HASH = "0" * 64


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _last_line_hash(filepath: str) -> str:
    """Return SHA-256 hex digest of the last non-empty line, or GENESIS_HASH."""
    if not os.path.exists(filepath):
        return GENESIS_HASH
    last = b""
    with open(filepath, "rb") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped:
                last = stripped
    if not last:
        return GENESIS_HASH
    return hashlib.sha256(last).hexdigest()


def _append_record(filepath: str, record: dict) -> None:
    """Append a single JSON record (with tamper-evidence hash) to a JSONL file."""
    record["prev_entry_hash"] = _last_line_hash(filepath)
    record["archived_at"] = datetime.now(timezone.utc).isoformat()
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def append_heartbeat(agent: str, status: str, task_id: str = "",
                     note: str = "", pb_record_id: str = "") -> None:
    """Append one heartbeat event to heartbeat_archive.jsonl."""
    _append_record(HB_ARCHIVE, {
        "agent": agent,
        "status": status,
        "task_id": task_id,
        "note": note,
        "pb_record_id": pb_record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def append_task_event(task_id: str, event_type: str, agent: str,
                      details: dict = None, pb_record_id: str = "") -> None:
    """
    Append one task lifecycle event to task_archive.jsonl.

    event_type should be one of: created, picked_up, completed,
    reassigned, blocked, peer_review, approved.

    At pick-up, pass details={"title": ..., "description": ...} to attach
    the agent intent document.
    """
    _append_record(TASK_ARCHIVE, {
        "task_id": task_id,
        "event_type": event_type,
        "agent": agent,
        "details": details or {},
        "pb_record_id": pb_record_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ---------------------------------------------------------------------------
# Integrity check
# ---------------------------------------------------------------------------

def verify_archive(filepath: str) -> bool:
    """
    Walk the chain in filepath, verifying each prev_entry_hash matches the
    SHA-256 of the preceding line.  Returns True if intact, False otherwise.
    """
    if not os.path.exists(filepath):
        print(f"[verify] {filepath} does not exist — nothing to check.")
        return True
    prev_hash = GENESIS_HASH
    errors = 0
    lineno = 0
    with open(filepath, "rb") as fh:
        for raw_bytes in fh:
            stripped = raw_bytes.strip()
            if not stripped:
                continue
            lineno += 1
            try:
                record = json.loads(stripped.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                print(f"[verify] line {lineno}: parse error: {exc}")
                errors += 1
                # Still advance the chain so subsequent lines can be checked
                prev_hash = hashlib.sha256(stripped).hexdigest()
                continue
            claimed = record.get("prev_entry_hash", "")
            if claimed != prev_hash:
                print(
                    f"[verify] line {lineno}: hash mismatch "
                    f"(expected {prev_hash[:12]}…, got {claimed[:12]}…)"
                )
                errors += 1
            # Next record's prev_entry_hash must equal SHA256 of this raw line
            prev_hash = hashlib.sha256(stripped).hexdigest()
    if lineno == 0:
        print(f"[verify] {filepath}: empty file — nothing to check.")
        return True
    if errors == 0:
        print(f"[verify] {filepath}: OK ({lineno} records, chain intact)")
    else:
        print(f"[verify] {filepath}: {errors} error(s) detected")
    return errors == 0


# ---------------------------------------------------------------------------
# PocketBase sync helpers
# ---------------------------------------------------------------------------

def _pb_fetch(collection: str, params: dict) -> list:
    url = (f"{POCKETBASE_URL}/collections/{collection}/records?"
           + urllib.parse.urlencode(params))
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    return data.get("items", [])


def _already_archived(filepath: str, pb_id_field: str) -> set:
    """Return set of pb_record_id values already present in archive."""
    seen = set()
    if not os.path.exists(filepath):
        return seen
    with open(filepath, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
                val = rec.get(pb_id_field, "")
                if val:
                    seen.add(val)
            except json.JSONDecodeError:
                pass
    return seen


def sync_heartbeats_from_pb(max_pages: int = 20) -> int:
    """
    Pull heartbeat records from PocketBase (oldest first) and append any not
    yet in heartbeat_archive.jsonl.  Returns number of new records written.
    """
    seen = _already_archived(HB_ARCHIVE, "pb_record_id")
    written = 0
    page = 1
    while page <= max_pages:
        items = _pb_fetch("heartbeats", {
            "sort": "created",
            "perPage": 200,
            "page": page,
        })
        if not items:
            break
        for hb in items:
            if hb["id"] in seen:
                continue
            _append_record(HB_ARCHIVE, {
                "agent": hb.get("agent", ""),
                "status": hb.get("status", ""),
                "task_id": hb.get("task_id", ""),
                "note": hb.get("note", ""),
                "pb_record_id": hb["id"],
                "timestamp": hb.get("created", ""),
            })
            seen.add(hb["id"])
            written += 1
        if len(items) < 200:
            break
        page += 1
    return written


def sync_tasks_from_pb(max_pages: int = 20) -> int:
    """
    Pull task records from PocketBase and append a 'created' lifecycle event
    for any task not yet in task_archive.jsonl.  Returns new records written.
    """
    seen = _already_archived(TASK_ARCHIVE, "pb_record_id")
    written = 0
    page = 1
    while page <= max_pages:
        items = _pb_fetch("tasks", {
            "sort": "created",
            "perPage": 200,
            "page": page,
        })
        if not items:
            break
        for task in items:
            synthetic_id = f"created:{task['id']}"
            if synthetic_id in seen:
                continue
            _append_record(TASK_ARCHIVE, {
                "task_id": task["id"],
                "event_type": "created",
                "agent": task.get("assigned_agent", ""),
                "details": {
                    "title": task.get("title", ""),
                    "status": task.get("status", ""),
                },
                "pb_record_id": synthetic_id,
                "timestamp": task.get("created", ""),
            })
            seen.add(synthetic_id)
            written += 1
        if len(items) < 200:
            break
        page += 1
    return written


def prune_old_heartbeats(days: int = 14) -> int:
    """
    Delete PocketBase heartbeat records older than `days` days.
    Returns number of records deleted.
    """
    cutoff_ts = int(time.time()) - days * 86400
    cutoff_iso = (
        datetime.fromtimestamp(cutoff_ts, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", ".000Z")
        .replace("T", " ")
    )
    filter_str = f'created < "{cutoff_iso}"'
    params = {
        "filter": filter_str,
        "perPage": 200,
        "sort": "created",
    }
    deleted = 0
    while True:
        items = _pb_fetch("heartbeats", params)
        if not items:
            break
        for hb in items:
            url = f"{POCKETBASE_URL}/collections/heartbeats/records/{hb['id']}"
            req = urllib.request.Request(url, method="DELETE")
            try:
                with urllib.request.urlopen(req, timeout=10):
                    pass
                deleted += 1
            except Exception as exc:
                print(f"[prune] failed to delete {hb['id']}: {exc}")
                # Forbidden/unauthorized deletes are structural, not transient.
                # Stop immediately instead of hammering PocketBase with the rest.
                if "403" in str(exc) or "Forbidden" in str(exc):
                    return deleted
        if len(items) < 200:
            break
    return deleted


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compliance archive writer / sync tool"
    )
    parser.add_argument("--sync-heartbeats", action="store_true",
                        help="Sync heartbeats from PocketBase to archive")
    parser.add_argument("--sync-tasks", action="store_true",
                        help="Sync task lifecycle events from PocketBase")
    parser.add_argument("--sync-all", action="store_true",
                        help="Sync both heartbeats and tasks")
    parser.add_argument("--verify", action="store_true",
                        help="Verify hash chain integrity of both archives")
    parser.add_argument("--prune-heartbeats", action="store_true",
                        help="Delete PocketBase heartbeats older than 14 days")
    parser.add_argument("--prune-days", type=int, default=14,
                        help="Retention window in days (default: 14)")
    args = parser.parse_args()

    if args.verify:
        ok1 = verify_archive(HB_ARCHIVE)
        ok2 = verify_archive(TASK_ARCHIVE)
        sys.exit(0 if (ok1 and ok2) else 1)

    if args.sync_all or args.sync_heartbeats:
        n = sync_heartbeats_from_pb()
        print(f"[sync] heartbeats: {n} new records written to {HB_ARCHIVE}")

    if args.sync_all or args.sync_tasks:
        n = sync_tasks_from_pb()
        print(f"[sync] tasks: {n} new records written to {TASK_ARCHIVE}")

    if args.prune_heartbeats:
        n = prune_old_heartbeats(days=args.prune_days)
        print(f"[prune] deleted {n} PocketBase heartbeats older than {args.prune_days}d")


if __name__ == "__main__":
    main()
