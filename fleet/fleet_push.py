#!/usr/bin/env python3
"""
Hybrid fleet snapshot push connector.

Pulls selected PocketBase collections from the local Mac Mini and pushes them to
the remote Fleet Hub so a public dashboard can show current heartbeats/task
counts even when PocketBase is not exposed publicly.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


POCKETBASE_URL = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090/api")
FLEET_SYNC_URL = os.environ.get("FLEET_SYNC_URL", "https://api.robotross.art/fleet/snapshot")
FLEET_SYNC_TOKEN = os.environ.get("FLEET_SYNC_TOKEN", "")
FLEET_SYNC_INTERVAL_SEC = int(os.environ.get("FLEET_SYNC_INTERVAL_SEC", "60"))
FLEET_SYNC_SOURCE = os.environ.get("FLEET_SYNC_SOURCE", "mac-mini")
FLEET_DIR = os.environ.get("FLEET_DIR", "/Users/miguelrodriguez/fleet")
LOG_FILE = os.path.join(FLEET_DIR, "logs", "fleet_push.log")
POCKETBASE_TIMEOUT = int(os.environ.get("POCKETBASE_TIMEOUT", "12"))


def ensure_logs():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def log(message):
    ensure_logs()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line)


def fetch_collection(name, query):
    url = f"{POCKETBASE_URL}/collections/{name}/records?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(url, timeout=POCKETBASE_TIMEOUT) as response:
        payload = json.load(response)
    if isinstance(payload, list):
        return payload
    return payload.get("items", [])


def fetch_collection_safe(name, query, default=None, context=""):
    try:
        return fetch_collection(name, query)
    except Exception as exc:
        log(f"pb fetch failed {name}{' (' + context + ')' if context else ''}: {exc}")
        return [] if default is None else default


def fetch_collection_paged(name: str, base_query: dict, max_pages: int = 10) -> list:
    """Fetch all pages of a collection up to max_pages."""
    all_items = []
    for page in range(1, max_pages + 1):
        query = {**base_query, "page": page}
        items = fetch_collection_safe(name, query, default=[], context=f"page {page}")
        all_items.extend(items)
        if len(items) < int(base_query.get("perPage", 30)):
            break
    return all_items


def parse_timestamp(value: str):
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def fetch_archived_heartbeats(days: int = 30) -> list:
    archive_path = os.path.join(FLEET_DIR, "heartbeat_archive.jsonl")
    if not os.path.exists(archive_path):
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    records = []
    with open(archive_path, "r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue

            ts = parse_timestamp(rec.get("timestamp") or rec.get("created"))
            if not ts or ts < cutoff:
                continue

            created_iso = ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.000Z")
            records.append({
                "id": rec.get("pb_record_id") or f"archive_{rec.get('agent', 'unknown')}_{int(ts.timestamp() * 1000)}",
                "agent": rec.get("agent", "unknown"),
                "status": rec.get("status", "idle"),
                "created": created_iso,
                "updated": created_iso,
                "task_id": rec.get("task_id", ""),
                "note": rec.get("note", ""),
                "source": "archive",
            })
    return records


def fetch_offline_agents() -> dict:
    offline_path = os.path.join(FLEET_DIR, "logs", "offline_agents.json")
    if not os.path.exists(offline_path):
        return {}
    try:
        with open(offline_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def should_ignore_activity_comment(comment: dict) -> bool:
    content = str(comment.get("content", "")).strip().lower()
    comment_type = str(comment.get("type", "")).strip().lower()

    # Ignore obvious non-work artifacts that were polluting the timeline.
    if "<think>" in content:
        return True
    if "you're out of extra usage" in content:
        return True
    if content.startswith("failed with return code"):
        return True
    if "resets 7pm" in content or "resets apr" in content:
        return True

    # Feedback spam from failed quota retries should not count as working time.
    if comment_type == "feedback" and "failed with return code" in content:
        return True

    return False


def build_activity_heartbeats(task_events: list, comments: list) -> list:
    """
    Derive synthetic working heartbeats from task lifecycle and output activity.

    Some agents mutate tasks/comments without reliably emitting a matching
    `working` heartbeat, so the Shift Timeline needs a secondary signal.
    """
    records = []

    for event in task_events:
        agent = str(event.get("agent", "")).strip().lower()
        if not agent or agent == "dispatcher":
            continue
        if str(event.get("event_type", "")).strip().lower() != "status_transition":
            continue
        from_status = str(event.get("from_status", "")).strip().lower()
        to_status = str(event.get("to_status", "")).strip().lower()
        if to_status not in {"in_progress", "peer_review", "approved"} and from_status != "in_progress":
            continue
        created = event.get("timestamp") or event.get("created")
        if not created:
            continue
        records.append({
            "id": f"task_event_{event.get('id') or event.get('task_id')}_{agent}_{created}",
            "agent": agent,
            "status": "working",
            "created": created,
            "updated": created,
            "task_id": event.get("task_id", ""),
            "note": "Derived from task_events.status_transition",
            "source": "task_events",
        })

    for comment in comments:
        agent = str(comment.get("agent", "")).strip().lower()
        if not agent or agent == "dispatcher":
            continue
        comment_type = str(comment.get("type", "")).strip().lower()
        if comment_type not in {"output", "approval", "feedback", "question", "comment"}:
            continue
        if should_ignore_activity_comment(comment):
            continue
        created = comment.get("created") or comment.get("updated")
        if not created:
            continue
        records.append({
            "id": f"comment_{comment.get('id')}_{agent}_{created}",
            "agent": agent,
            "status": "working",
            "created": created,
            "updated": created,
            "task_id": comment.get("task_id", ""),
            "note": f"Derived from comments.{comment_type}",
            "source": "comments",
        })

    return records


def build_offline_heartbeats(offline_agents: dict) -> list:
    """
    Surface dispatcher-detected stale agents into the timeline as explicit
    `offline` status. This keeps the timeline from inheriting a stale `idle`.
    """
    records = []
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.000Z")
    for agent, payload in offline_agents.items():
        if not agent:
            continue
        note = "Dispatcher marked agent offline"
        if isinstance(payload, dict) and payload.get("offline_since"):
            note += f" since {payload['offline_since']}"
        records.append({
            "id": f"offline_{agent}_{created}",
            "agent": str(agent).strip().lower(),
            "status": "offline",
            "created": created,
            "updated": created,
            "note": note,
            "source": "offline_agents",
        })
    return records


def merge_timeline_heartbeats(archived: list, pocketbase_records: list) -> list:
    merged = {}

    def add(record):
        created = record.get("created") or record.get("timestamp") or ""
        key = record.get("id") or record.get("pb_record_id") or (
            f"{record.get('agent', '')}|{record.get('status', '')}|{created}"
        )
        normalized = dict(record)
        normalized["created"] = created
        normalized["updated"] = normalized.get("updated") or created
        merged[key] = normalized

    for rec in archived:
        add(rec)
    for rec in pocketbase_records:
        add(rec)

    return sorted(merged.values(), key=lambda item: item.get("created", ""))


def build_timeline_segments(heartbeats: list) -> dict:
    """
    Pre-aggregate raw heartbeat records into 15-minute timeline segments per agent.

    For each 15-min bucket, the dominant (most-recent) heartbeat status wins.
    Returns a dict mapping agent_name -> list of synthetic heartbeat-shaped
    dicts [{agent, status, created, updated}] one per bucket, sorted by created.

    This compresses potentially thousands of raw heartbeats into a manageable
    snapshot payload while preserving enough resolution for the Schichtplan UI.
    """
    BUCKET_MS = 15 * 60 * 1000  # 15 minutes in milliseconds

    # Group raw records by agent
    by_agent: dict[str, list] = {}
    for hb in heartbeats:
        agent = hb.get("agent", "unknown")
        by_agent.setdefault(agent, []).append(hb)

    segments: dict[str, list] = {}
    for agent, records in by_agent.items():
        # Sort chronologically
        records.sort(key=lambda h: h.get("created", ""))
        if not records:
            continue
        buckets: dict[int, str] = {}
        for hb in records:
            ts_str = hb.get("created", "")
            if not ts_str:
                continue
            try:
                ts_ms = int(datetime.fromisoformat(
                    ts_str.replace("Z", "+00:00")
                ).timestamp() * 1000)
            except ValueError:
                continue
            bucket_key = (ts_ms // BUCKET_MS) * BUCKET_MS
            # Last record in the bucket wins (most recent status)
            buckets[bucket_key] = hb.get("status", "idle")

        agent_segs = []
        for bucket_ms, status in sorted(buckets.items()):
            created_iso = datetime.fromtimestamp(
                bucket_ms / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S.000Z")
            agent_segs.append({
                "agent": agent,
                "status": status,
                "created": created_iso,
                "updated": created_iso,
                # Synthetic id so the client can deduplicate safely
                "id": f"seg_{agent}_{bucket_ms}",
            })
        segments[agent] = agent_segs

    return segments


CODEX_REPO_DIR = "/Users/miguelrodriguez/projects/agentic-fleet-hub"

def fetch_inbox():
    """Read inter-agent inbox from disk."""
    inbox_path = os.path.join(CODEX_REPO_DIR, "AGENTS/MESSAGES/inbox.json")
    if os.path.exists(inbox_path):
        try:
            with open(inbox_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def fetch_lessons():
    """Read lessons ledger from disk."""
    lessons_path = os.path.join(CODEX_REPO_DIR, "AGENTS/LESSONS/ledger.json")
    if os.path.exists(lessons_path):
        try:
            with open(lessons_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def fetch_standups():
    """Read standup index and recent files from disk."""
    standups_dir = os.path.join(CODEX_REPO_DIR, "standups")
    index_path = os.path.join(standups_dir, "index.json")
    
    result = {
        "index": [],
        "files": {}
    }
    
    if os.path.exists(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                result["index"] = json.load(f)
        except:
            pass
            
    # Load last 5 standup files
    if result["index"]:
        for entry in result["index"][:5]:
            date = entry.get("date")
            file_name = entry.get("file")
            if date and file_name:
                file_path = os.path.join(standups_dir, file_name)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            result["files"][date] = f.read()
                    except:
                        pass
    return result

def fetch_kanban():
    """Fetch parsed kanban state from the local server."""
    try:
        # The local fleet-server.mjs parses MISSION_CONTROL.md and today's standup
        url = f"http://localhost:8787/fleet/api/kanban"
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except:
        return None

def build_snapshot():
    # Fetch last 30 days of heartbeats (paged) for the timeline.
    # We sort by -created to get the MOST RECENT ones first, then reverse for the aggregator.
    cutoff_30d = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S.000Z"
    )
    filter_30d = f'created >= "{cutoff_30d}"'
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
        "%Y-%m-%d %H:%M:%S.000Z"
    )
    filter_7d = f'created >= "{cutoff_7d}"'
    timeline_heartbeats = fetch_collection_paged(
        "heartbeats",
        {"sort": "-created", "perPage": 200, "filter": filter_30d},
        max_pages=20,
    )
    # Reverse so timeline builder gets chronological order
    timeline_heartbeats.reverse()
    archived_heartbeats = fetch_archived_heartbeats(days=30)
    task_events = fetch_collection_paged(
        "task_events",
        {"sort": "-timestamp", "perPage": 200, "filter": filter_7d},
        max_pages=5,
    )
    task_events.reverse()
    comments = fetch_collection_paged(
        "comments",
        {"sort": "-created", "perPage": 200, "filter": filter_7d},
        max_pages=5,
    )
    comments.reverse()
    activity_heartbeats = build_activity_heartbeats(task_events, comments)
    offline_heartbeats = build_offline_heartbeats(fetch_offline_agents())
    merged_timeline_heartbeats = merge_timeline_heartbeats(
        archived_heartbeats + activity_heartbeats + offline_heartbeats,
        timeline_heartbeats,
    )

    # Fetch tasks: all non-approved + last 20 approved
    active_tasks = fetch_collection_safe("tasks", {"filter": 'status != "approved"', "perPage": 100}, context="active_tasks")
    recent_approved = fetch_collection_safe("tasks", {"filter": 'status = "approved"', "sort": "-updated", "perPage": 20}, context="recent_approved")
    tasks = active_tasks + recent_approved

    return {
        "source": FLEET_SYNC_SOURCE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collections": {
            "heartbeats": fetch_collection_safe("heartbeats", {"sort": "-updated", "perPage": 50}, context="dashboard heartbeats"),
            "tasks": tasks,
            "comments": fetch_collection_safe("comments", {"sort": "-created", "perPage": 100}, context="dashboard comments"),
            "lessons": fetch_lessons(),
            "messages": fetch_inbox(),
            "standups": fetch_standups(),
            "songs": fetch_collection_safe("songs", {"sort": "-combined_views", "perPage": 200}, context="songs"),
            "kanban": fetch_kanban(),
            "watch_hours_ledger": fetch_collection_safe(
                "watch_hours_ledger",
                {"sort": "-audit_date", "perPage": 200},
                context="watch_hours_ledger",
            ),
            "cost_ledger": fetch_collection_safe(
                "cost_ledger",
                {"sort": "-date", "perPage": 500},
                context="cost_ledger",
            ),
            "income_ledger": fetch_collection_safe(
                "income_ledger",
                {"sort": "-date", "perPage": 500},
                context="income_ledger",
            ),
            "campaigns_snapshot": fetch_collection_safe(
                "campaigns_snapshot",
                {"sort": "-snapshot_date", "perPage": 200},
                context="campaigns_snapshot",
            ),
            "classical_reels_assets": fetch_collection_safe(
                "classical_reels_assets",
                {"sort": "-date", "perPage": 500},
                context="classical_reels_assets",
            ),
            "shopify_orders": fetch_collection_safe(
                "shopify_orders",
                {"sort": "-created_at", "perPage": 500},
                context="shopify_orders",
            ),
        },
        "timeline_segments": build_timeline_segments(merged_timeline_heartbeats),
    }


def push_snapshot(snapshot):
    if not FLEET_SYNC_TOKEN:
        raise RuntimeError("FLEET_SYNC_TOKEN missing")

    body = json.dumps(snapshot).encode("utf-8")
    request = urllib.request.Request(
        FLEET_SYNC_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FLEET_SYNC_TOKEN}",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def run_once():
    snapshot = build_snapshot()
    result = push_snapshot(snapshot)
    counts = snapshot["collections"]
    log(
        "sync ok "
        f"hb={len(counts['heartbeats'])} "
        f"tasks={len(counts['tasks'])} "
        f"comments={len(counts['comments'])} "
        f"watch_hours={len(counts['watch_hours_ledger'])} "
        f"costs={len(counts['cost_ledger'])} "
        f"income={len(counts['income_ledger'])} "
        f"campaigns={len(counts['campaigns_snapshot'])} "
        f"reels_assets={len(counts['classical_reels_assets'])} "
        f"shopify_orders={len(counts['shopify_orders'])} "
        f"remote={result.get('received_at', 'unknown')}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Push one snapshot and exit")
    args = parser.parse_args()

    if args.once:
        run_once()
        return

    log("fleet_push started")
    while True:
        try:
            run_once()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            log(f"sync http error {exc.code}: {detail[:300]}")
        except Exception as exc:
            log(f"sync failed: {exc}")
        time.sleep(max(10, FLEET_SYNC_INTERVAL_SEC))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
