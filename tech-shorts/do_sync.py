#!/usr/bin/env python3
"""
TS-10: DO intake API client (Mac-side).

Thin stdlib-only wrapper around the tech-shorts intake REST API running on the
DO droplet.  The Mac Mini is a pure *pull worker*:
  - claim jobs via POST /api/jobs/claim   (atomic — DO writes, Mac never touches DO jobs.json)
  - read job state via GET  /api/jobs/<id>
  - post status back via PATCH /api/jobs/<id>

Connection options (set DO_INTAKE_URL in env or pass base_url explicitly):
  - http://localhost:8766   → via SSH tunnel  (mac_worker.py --tunnel opens it)
  - https://ideas.flotilla.cc  → direct HTTPS once DNS + token auth are live
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_INTAKE_URL = os.environ.get("DO_INTAKE_URL", "http://localhost:8766")

HERE = Path(__file__).resolve().parent
LOCAL_JOBS_FILE = HERE / "jobs.json"
LOCAL_JOBS_LOCK = HERE / "jobs.lock"


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _headers() -> Dict[str, str]:
    """Return request headers, including bearer token if configured."""
    h: Dict[str, str] = {"Content-Type": "application/json"}
    token = os.environ.get("INTAKE_TOKEN", "")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _request(method: str, url: str, body: Any = None, timeout: int = 15) -> Any:
    """Minimal HTTP request; returns parsed JSON or raises on non-2xx."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {raw}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach {url}: {e.reason}") from e


# ── Public API ────────────────────────────────────────────────────────────────

def health_check(base_url: str = DEFAULT_INTAKE_URL) -> bool:
    """Return True if the intake API is reachable."""
    try:
        result = _request("GET", f"{base_url.rstrip('/')}/api/health")
        return bool(result.get("ok"))
    except Exception:
        return False


def claim_queued_job(base_url: str = DEFAULT_INTAKE_URL) -> Optional[Dict]:
    """
    Atomically claim the oldest queued job on DO.

    DO marks it in_progress before returning — only ONE Mac worker can claim it.
    Returns the job dict or None if the queue is empty.
    """
    result = _request("POST", f"{base_url.rstrip('/')}/api/jobs/claim", body={})
    job = result.get("job")
    if job:
        print(f"[do_sync] claimed: {job['id']} — {job['title'][:60]}")
    else:
        print("[do_sync] queue empty — nothing to claim")
    return job


def get_job(job_id: str, base_url: str = DEFAULT_INTAKE_URL) -> Optional[Dict]:
    """Fetch current state of a job from the DO API."""
    try:
        return _request("GET", f"{base_url.rstrip('/')}/api/jobs/{job_id}")
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise


def list_jobs(
    status: Optional[str] = None,
    base_url: str = DEFAULT_INTAKE_URL,
) -> list:
    """List jobs from DO, optionally filtered by status."""
    url = f"{base_url.rstrip('/')}/api/jobs"
    if status:
        url += f"?status={status}"
    result = _request("GET", url)
    return result.get("jobs", [])


def post_status(
    job_id: str,
    status: str,
    base_url: str = DEFAULT_INTAKE_URL,
    **extra_fields: Any,
) -> Dict:
    """
    PATCH the job's status (and optional extra fields) on DO.

    extra_fields: nested-dict fields like assets={...}, youtube={...}, x_post={...}
    """
    payload: Dict[str, Any] = {"status": status}
    payload.update(extra_fields)
    result = _request("PATCH", f"{base_url.rstrip('/')}/api/jobs/{job_id}", body=payload)
    print(f"[do_sync] {job_id} → {status}")
    return result


# ── Local jobs.json sync ──────────────────────────────────────────────────────

def _load_local() -> Dict:
    if not LOCAL_JOBS_FILE.exists():
        return {"version": "1.0", "jobs": []}
    with open(LOCAL_JOBS_FILE) as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return {"version": "1.0", "jobs": raw}
    return raw


def _save_local(data: Dict) -> None:
    import datetime
    data["updated_at"] = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    tmp = LOCAL_JOBS_FILE.with_suffix(".json.tmp")
    with open(LOCAL_JOBS_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            tmp.replace(LOCAL_JOBS_FILE)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def merge_job_local(job: Dict) -> None:
    """
    Upsert a job from DO into the local jobs.json so pipeline.py can work with it.

    This is a one-way write (DO → local cache). pipeline.py continues to operate
    on local files; mac_worker.py is responsible for posting results back to DO.
    """
    data = _load_local()
    existing = {j["id"]: idx for idx, j in enumerate(data["jobs"])}
    if job["id"] in existing:
        data["jobs"][existing[job["id"]]].update(job)
    else:
        data["jobs"].append(job)
    _save_local(data)
    print(f"[do_sync] merged {job['id']} into local jobs.json")


# ── SSH tunnel ────────────────────────────────────────────────────────────────

_TUNNEL_PROC: Optional[subprocess.Popen] = None


def open_tunnel(
    ssh_alias: str = "robotsales",
    remote_port: int = 8766,
    local_port: int = 8766,
    wait_s: float = 2.0,
) -> subprocess.Popen:
    """
    Open an SSH port-forward tunnel in the background.

    Forwards localhost:<local_port> → <ssh_alias>:localhost:<remote_port>.
    Returns the Popen handle; caller is responsible for closing.
    """
    global _TUNNEL_PROC
    if _TUNNEL_PROC and _TUNNEL_PROC.poll() is None:
        print(f"[do_sync] tunnel already open (pid {_TUNNEL_PROC.pid})")
        return _TUNNEL_PROC
    cmd = [
        "ssh", "-N", "-o", "ExitOnForwardFailure=yes",
        "-o", "ServerAliveInterval=30",
        "-L", f"{local_port}:localhost:{remote_port}",
        ssh_alias,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _TUNNEL_PROC = proc
    time.sleep(wait_s)
    if proc.poll() is not None:
        raise RuntimeError(f"SSH tunnel failed to start (exit {proc.returncode})")
    print(f"[do_sync] tunnel open: localhost:{local_port} → {ssh_alias}:{remote_port} (pid {proc.pid})")
    return proc


def close_tunnel() -> None:
    global _TUNNEL_PROC
    if _TUNNEL_PROC and _TUNNEL_PROC.poll() is None:
        _TUNNEL_PROC.terminate()
        _TUNNEL_PROC.wait(timeout=5)
        print("[do_sync] tunnel closed")
    _TUNNEL_PROC = None


# ── CLI (diagnostic use) ──────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="DO intake API client — diagnostic tool")
    parser.add_argument("--base-url", default=DEFAULT_INTAKE_URL)
    parser.add_argument("--tunnel", action="store_true", help="Open SSH tunnel first")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Check API reachability")
    sub.add_parser("list", help="List all DO jobs")

    p_claim = sub.add_parser("claim", help="Claim next queued job")

    p_status = sub.add_parser("status", help="Post status update")
    p_status.add_argument("job_id")
    p_status.add_argument("new_status")

    args = parser.parse_args()
    if args.tunnel:
        open_tunnel()

    try:
        if args.cmd == "health":
            ok = health_check(args.base_url)
            print(f"API reachable: {ok}")
        elif args.cmd == "list":
            jobs = list_jobs(base_url=args.base_url)
            for j in jobs:
                print(f"  {j['status']:16} {j['id']}")
        elif args.cmd == "claim":
            job = claim_queued_job(args.base_url)
            if job:
                print(json.dumps(job, indent=2))
        elif args.cmd == "status":
            result = post_status(args.job_id, args.new_status, args.base_url)
            print(json.dumps(result, indent=2))
    finally:
        if args.tunnel:
            close_tunnel()


if __name__ == "__main__":
    main()
