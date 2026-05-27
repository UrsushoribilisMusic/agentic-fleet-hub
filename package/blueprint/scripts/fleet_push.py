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
from datetime import datetime, timezone


POCKETBASE_URL = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090/api")
FLEET_SYNC_URL = os.environ.get("FLEET_SYNC_URL", "https://api.robotross.art/fleet/snapshot")
FLEET_SYNC_TOKEN = os.environ.get("FLEET_SYNC_TOKEN", "")
FLEET_SYNC_INTERVAL_SEC = int(os.environ.get("FLEET_SYNC_INTERVAL_SEC", "60"))
FLEET_SYNC_SOURCE = os.environ.get("FLEET_SYNC_SOURCE", "mac-mini")
FLEET_DIR = os.environ.get("FLEET_DIR", "/Users/miguelrodriguez/fleet")
LOG_FILE = os.path.join(FLEET_DIR, "logs", "fleet_push.log")

CORE_COLLECTION_QUERIES = {
    "heartbeats": {"sort": "-updated", "perPage": 50},
    "tasks": {"sort": "-updated", "perPage": 100},
    "comments": {"sort": "-created", "perPage": 50},
}

FINANCIAL_COLLECTION_QUERIES = {
    "watch_hours_ledger": {"sort": "-audit_date", "perPage": 200},
    "cost_ledger": {"sort": "-date", "perPage": 500},
    "income_ledger": {"sort": "-date", "perPage": 500},
    "campaigns_snapshot": {"sort": "-snapshot_date", "perPage": 200},
}


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
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.load(response)
    if isinstance(payload, list):
        return payload
    return payload.get("items", [])


def fetch_optional_collection(name, query):
    try:
        return fetch_collection(name, query)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            log(f"optional collection missing: {name}")
            return []
        raise


def build_snapshot():
    collections = {
        name: fetch_collection(name, query)
        for name, query in CORE_COLLECTION_QUERIES.items()
    }
    collections.update({
        name: fetch_optional_collection(name, query)
        for name, query in FINANCIAL_COLLECTION_QUERIES.items()
    })
    return {
        "source": FLEET_SYNC_SOURCE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collections": collections,
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
