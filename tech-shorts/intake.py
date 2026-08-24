#!/usr/bin/env python3
"""
tech-shorts intake & queue management

Lightweight ideation entry point and job manager for the Tech-Shorts pipeline
(NotebookLM -> hook/outro -> YouTube -> X -> stats -> FinOps).

Reuses the music-video-tool / ReelTales job intake pattern.
Zero external dependencies required (Python 3.8+ standard library).

Usage:
    # CLI - Add a new idea
    python3 intake.py add --title "Why Small Models Win On-Device" \
                          --urls "https://example.com/article1, https://example.com/podcast2" \
                          --notes "Why 3B-4B models with MLX outpace cloud APIs for daily tasks." \
                          --tags "on-device,canis,ai-models"

    # CLI - Interactive prompt
    python3 intake.py add

    # CLI - List queue
    python3 intake.py list [--status queued] [--json]

    # CLI - View job details
    python3 intake.py show <job_id> [--json]

    # CLI - Update job status or metadata
    python3 intake.py update <job_id> --status in_progress --notebook-url "https://notebook.google.com/..."

    # CLI - Claim next available job for pipeline workers
    python3 intake.py claim [--json]

    # CLI - Launch local web intake console
    python3 intake.py serve [--port 8766]
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import json
import mimetypes
import os
import re
import shutil
import sys
import urllib.parse
import warnings
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
DEFAULT_JOBS_FILE = HERE / "jobs.json"
_env_uploads = os.environ.get("TS_UPLOADS_DIR")
UPLOADS_DIR = Path(_env_uploads) if _env_uploads else (HERE / "uploads")

MAX_SOURCE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_SOURCE_FILE_EXTS = {".pdf", ".md", ".markdown", ".txt"}

VALID_STATUSES = {
    "queued",
    "in_progress",
    "raw_videos_ready",
    "assembled",
    "published",
    "failed",
}

STATUS_BADGES = {
    "queued": "⏳ QUEUED",
    "in_progress": "⚙️  IN PROGRESS",
    "raw_videos_ready": "🎬 RAW READY",
    "assembled": "✨ ASSEMBLED",
    "published": "🚀 PUBLISHED",
    "failed": "❌ FAILED",
}


def now_iso() -> str:
    """Return UTC timestamp in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    """Convert text to a URL and filesystem safe slug."""
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "untitled"


def clean_urls(urls_input: Any) -> List[str]:
    """Parse and clean URLs from a list, comma-separated string, or newline string."""
    if not urls_input:
        return []
    if isinstance(urls_input, str):
        # Split on newlines, commas, or semicolons
        parts = re.split(r"[\n,;\t]+", urls_input)
    elif isinstance(urls_input, (list, tuple, set)):
        parts = list(urls_input)
    else:
        parts = [str(urls_input)]

    results: List[str] = []
    for p in parts:
        cleaned = p.strip()
        if not cleaned:
            continue
        # Ensure scheme if missing
        if not re.match(r"^https?://", cleaned, re.IGNORECASE):
            if cleaned.startswith("notebook.google.com") or cleaned.startswith("www."):
                cleaned = "https://" + cleaned
        results.append(cleaned)
    # Deduplicate preserving order
    seen = set()
    deduped = []
    for u in results:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def clean_tags(tags_input: Any) -> List[str]:
    """Parse and clean tags list."""
    if not tags_input:
        return []
    if isinstance(tags_input, str):
        parts = re.split(r"[\n,;\t]+", tags_input)
    elif isinstance(tags_input, (list, tuple, set)):
        parts = list(tags_input)
    else:
        parts = [str(tags_input)]
    tags = [p.strip().lower().lstrip("#") for p in parts if p.strip()]
    return list(dict.fromkeys(tags))


def validate_source_file(filename: str, size: int) -> None:
    """Raise ValueError if the filename extension or size is not allowed."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_SOURCE_FILE_EXTS:
        raise ValueError(
            f"File type '{ext}' is not allowed. "
            f"Accepted: {', '.join(sorted(ALLOWED_SOURCE_FILE_EXTS))}"
        )
    if size > MAX_SOURCE_FILE_BYTES:
        mb = size / 1024 / 1024
        raise ValueError(f"File too large ({mb:.1f} MB). Maximum is 50 MB.")


def store_source_file(job_id: str, file_bytes: bytes, original_name: str) -> Dict[str, Any]:
    """
    Persist an uploaded source file and return its metadata dict.

    Stored at: <UPLOADS_DIR>/<job_id>/<original_name>
    Returns: {"path": <absolute path string>, "original_name": ..., "size_bytes": ..., "mime_type": ...}
    """
    dest_dir = UPLOADS_DIR / job_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / original_name
    dest_path.write_bytes(file_bytes)

    mime_type, _ = mimetypes.guess_type(original_name)
    if mime_type is None:
        ext = Path(original_name).suffix.lower()
        mime_type = {"pdf": "application/pdf"}.get(ext.lstrip("."), "text/plain")

    return {
        "path": str(dest_path),
        "original_name": original_name,
        "size_bytes": len(file_bytes),
        "mime_type": mime_type,
    }


@contextlib.contextmanager
def file_lock(lock_path: Path):
    """File-based lock for cross-process concurrency."""
    lock_file = lock_path.with_suffix(".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "w") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass


def load_jobs_data(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the full jobs dictionary from JSON file with lock safety."""
    path = path or DEFAULT_JOBS_FILE
    if not path.exists():
        return {
            "version": "1.0",
            "updated_at": now_iso(),
            "jobs": [],
        }
    with file_lock(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"version": "1.0", "updated_at": now_iso(), "jobs": data}
                if isinstance(data, dict) and "jobs" in data:
                    return data
                return {"version": "1.0", "updated_at": now_iso(), "jobs": []}
        except Exception as e:
            print(f"[intake] Warning: Error reading {path}: {e}", file=sys.stderr)
            return {"version": "1.0", "updated_at": now_iso(), "jobs": []}


def save_jobs_data(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save jobs data atomically using a temporary file and lock."""
    path = path or DEFAULT_JOBS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = now_iso()
    temp_path = path.with_suffix(f".tmp.{os.getpid()}")
    with file_lock(path):
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(temp_path, path)


def generate_job_id(slug: str, date_str: Optional[str] = None) -> str:
    """Create a canonical job ID formatted as ts-YYYYMMDD-slug."""
    date_str = date_str or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    return f"ts-{date_str}-{slug}"


# ── Core Python API ────────────────────────────────────────────────────────────

def create_job(
    title: str,
    source_urls: List[str] | str,
    idea_notes: str = "",
    tags: Optional[List[str] | str] = None,
    notebook_url: str = "",
    status: str = "queued",
    custom_id: Optional[str] = None,
    hook_copy: Optional[Dict[str, Any]] = None,
    outro_copy: Optional[Dict[str, Any]] = None,
    jobs_file: Optional[Path] = None,
    source_file_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create and persist a new tech-short job record."""
    title = (title or "").strip()
    if not title:
        raise ValueError("Job title cannot be empty")

    status = status.lower().strip()
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}")

    urls = clean_urls(source_urls)
    tag_list = clean_tags(tags)
    slug = slugify(title)
    ts = now_iso()

    job_id = custom_id or generate_job_id(slug)

    # Check for existing ID collision
    data = load_jobs_data(jobs_file)
    existing_ids = {j["id"] for j in data["jobs"] if "id" in j}
    if job_id in existing_ids and not custom_id:
        # Append numerical suffix
        count = 2
        while f"{job_id}-{count}" in existing_ids:
            count += 1
        job_id = f"{job_id}-{count}"

    job: Dict[str, Any] = {
        "id": job_id,
        "slug": slug,
        "title": title,
        "source_urls": urls,
        "source_file": source_file_meta or {},
        "idea_notes": (idea_notes or "").strip(),
        "tags": tag_list,
        "status": status,
        "created_at": ts,
        "updated_at": ts,
        "notebook_url": notebook_url.strip() if notebook_url else "",
        "hook_copy": hook_copy or {},
        "outro_copy": outro_copy or {},
        "assets": {
            "raw_short_mp4": "",
            "raw_long_mp4": "",
            "hook_vo_audio": "",
            "final_short_mp4": "",
            "final_long_mp4": "",
        },
        "youtube": {
            "short_id": "",
            "short_url": "",
            "long_id": "",
            "long_url": "",
            "published_at": "",
        },
        "x_post": {
            "post_id": "",
            "post_url": "",
            "caption": "",
        },
        "stats": {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "last_synced_at": "",
        },
    }

    # Pre-populate Notebook URL from source URLs if found
    if not job["notebook_url"]:
        for u in urls:
            if "notebook.google.com" in u:
                job["notebook_url"] = u
                break

    data["jobs"].append(job)
    save_jobs_data(data, jobs_file)
    return job


def get_job(job_id_or_slug: str, jobs_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a job by ID, slug, or unique prefix."""
    target = (job_id_or_slug or "").strip().lower()
    if not target:
        return None
    data = load_jobs_data(jobs_file)
    for j in data["jobs"]:
        jid = str(j.get("id", "")).lower()
        slug = str(j.get("slug", "")).lower()
        if jid == target or slug == target or jid.endswith(f"-{target}"):
            return j
    # Prefix match fallback
    for j in data["jobs"]:
        jid = str(j.get("id", "")).lower()
        if jid.startswith(target):
            return j
    return None


def list_jobs(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    jobs_file: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """List jobs with optional filtering."""
    data = load_jobs_data(jobs_file)
    jobs = data.get("jobs", [])

    if status:
        status_clean = status.lower().strip()
        jobs = [j for j in jobs if j.get("status", "").lower() == status_clean]

    if tag:
        tag_clean = tag.lower().strip().lstrip("#")
        jobs = [j for j in jobs if tag_clean in [t.lower() for t in j.get("tags", [])]]

    if search:
        s = search.lower().strip()
        jobs = [
            j for j in jobs
            if s in j.get("title", "").lower()
            or s in j.get("idea_notes", "").lower()
            or s in j.get("id", "").lower()
            or any(s in u.lower() for u in j.get("source_urls", []))
            or any(s in t.lower() for t in j.get("tags", []))
        ]

    return jobs


def update_job(job_id_or_slug: str, jobs_file: Optional[Path] = None, **updates) -> Optional[Dict[str, Any]]:
    """Update fields on an existing job."""
    target = (job_id_or_slug or "").strip().lower()
    data = load_jobs_data(jobs_file)
    found_idx = None

    for idx, j in enumerate(data["jobs"]):
        jid = str(j.get("id", "")).lower()
        slug = str(j.get("slug", "")).lower()
        if jid == target or slug == target or jid.startswith(target):
            found_idx = idx
            break

    if found_idx is None:
        return None

    job = data["jobs"][found_idx]

    # Validate status if updating
    if "status" in updates:
        new_status = str(updates["status"]).lower().strip()
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {sorted(VALID_STATUSES)}")
        job["status"] = new_status

    if "title" in updates and updates["title"]:
        job["title"] = str(updates["title"]).strip()
        job["slug"] = slugify(job["title"])

    if "source_urls" in updates:
        job["source_urls"] = clean_urls(updates["source_urls"])

    if "idea_notes" in updates:
        job["idea_notes"] = str(updates["idea_notes"] or "").strip()

    if "tags" in updates:
        job["tags"] = clean_tags(updates["tags"])

    if "notebook_url" in updates:
        job["notebook_url"] = str(updates["notebook_url"] or "").strip()

    if "source_file" in updates:
        if isinstance(updates["source_file"], dict):
            job["source_file"] = updates["source_file"]

    # Nested dictionary updates
    for nested_key in ("hook_copy", "outro_copy", "assets", "youtube", "x_post", "stats"):
        if nested_key in updates:
            if isinstance(updates[nested_key], dict):
                job.setdefault(nested_key, {}).update(updates[nested_key])
            else:
                job[nested_key] = updates[nested_key]

    job["updated_at"] = now_iso()
    data["jobs"][found_idx] = job
    save_jobs_data(data, jobs_file)
    return job


def claim_next_job(
    status_from: str = "queued",
    status_to: str = "in_progress",
    jobs_file: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Atomic claim of the oldest job in status_from, advancing it to status_to."""
    data = load_jobs_data(jobs_file)
    for idx, j in enumerate(data["jobs"]):
        if j.get("status", "") == status_from:
            j["status"] = status_to
            j["updated_at"] = now_iso()
            data["jobs"][idx] = j
            save_jobs_data(data, jobs_file)
            return j
    return None


def delete_job(job_id_or_slug: str, jobs_file: Optional[Path] = None) -> bool:
    """Remove a job by ID or slug."""
    target = (job_id_or_slug or "").strip().lower()
    data = load_jobs_data(jobs_file)
    initial_len = len(data["jobs"])
    data["jobs"] = [
        j for j in data["jobs"]
        if str(j.get("id", "")).lower() != target and str(j.get("slug", "")).lower() != target
    ]
    if len(data["jobs"]) < initial_len:
        save_jobs_data(data, jobs_file)
        return True
    return False


# ── Web Intake Server & UI ───────────────────────────────────────────────────

WEB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech-Shorts Intake & Ideation Console</title>
    <style>
        :root {
            --ink: #0B1D26;
            --ink-panel: #112936;
            --ink-card: #183849;
            --ink-border: #234E65;
            --teal: #4FD1C5;
            --teal-dim: #2b7a73;
            --coral: #E8674D;
            --gold: #D4AF6F;
            --mute: #9DB3B8;
            --white: #E7F1EF;
            --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --mono: "SF Mono", Monaco, "Cascadia Code", "Ubuntu Mono", monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--ink);
            color: var(--white);
            font-family: var(--font);
            line-height: 1.5;
            padding: 2rem 1.5rem;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--ink-border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .badge-logo {
            background: linear-gradient(135deg, var(--teal), var(--coral));
            color: var(--ink);
            font-weight: 900;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 1.1rem;
            letter-spacing: 1px;
        }

        h1 {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .subtitle {
            color: var(--mute);
            font-size: 0.9rem;
        }

        .stats-strip {
            display: flex;
            gap: 1.5rem;
            background: var(--ink-panel);
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            border: 1px solid var(--ink-border);
        }

        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .stat-val {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--teal);
        }

        .stat-lbl {
            font-size: 0.7rem;
            color: var(--mute);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .layout {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 2rem;
            align-items: start;
        }

        @media (max-width: 960px) {
            .layout { grid-template-columns: 1fr; }
        }

        .card {
            background: var(--ink-panel);
            border: 1px solid var(--ink-border);
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        .card h2 {
            font-size: 1.2rem;
            margin-bottom: 1rem;
            color: var(--teal);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--white);
            margin-bottom: 0.4rem;
        }

        .hint {
            font-size: 0.75rem;
            color: var(--mute);
            margin-top: 0.2rem;
        }

        input[type="text"], input[type="file"], textarea, select {
            width: 100%;
            background: var(--ink);
            border: 1px solid var(--ink-border);
            border-radius: 6px;
            color: var(--white);
            padding: 0.7rem 0.9rem;
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }

        input[type="file"] {
            padding: 0.5rem 0.7rem;
            cursor: pointer;
        }

        input[type="file"]::file-selector-button {
            background: var(--ink-card);
            border: 1px solid var(--ink-border);
            border-radius: 4px;
            color: var(--white);
            padding: 0.3rem 0.7rem;
            margin-right: 0.75rem;
            font-family: inherit;
            font-size: 0.85rem;
            cursor: pointer;
        }

        input[type="file"]::file-selector-button:hover {
            border-color: var(--teal);
            color: var(--teal);
        }

        .file-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: rgba(79, 209, 197, 0.12);
            border: 1px solid var(--teal-dim);
            border-radius: 4px;
            padding: 0.2rem 0.5rem;
            font-size: 0.75rem;
            color: var(--teal);
            margin-top: 0.3rem;
            font-family: var(--mono);
        }

        input[type="text"]:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--teal);
            box-shadow: 0 0 0 2px rgba(79, 209, 197, 0.2);
        }

        textarea {
            resize: vertical;
            min-height: 90px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: var(--teal);
            color: var(--ink);
            font-weight: 700;
            border: none;
            border-radius: 6px;
            padding: 0.75rem 1.4rem;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
        }

        .btn:hover {
            background: #64e3d7;
            transform: translateY(-1px);
        }

        .btn:active {
            transform: translateY(1px);
        }

        .btn-claim {
            background: var(--coral);
            color: white;
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
            width: auto;
        }
        .btn-claim:hover { background: #f37d65; }

        /* Filter Controls */
        .controls-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .filter-pills {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }

        .pill {
            background: var(--ink-panel);
            border: 1px solid var(--ink-border);
            color: var(--mute);
            padding: 0.35rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }

        .pill.active, .pill:hover {
            background: var(--teal);
            color: var(--ink);
            border-color: var(--teal);
        }

        /* Queue List */
        .queue-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .job-card {
            background: var(--ink-panel);
            border: 1px solid var(--ink-border);
            border-left: 4px solid var(--mute);
            border-radius: 8px;
            padding: 1.2rem;
            transition: all 0.2s ease;
        }

        .job-card:hover {
            border-color: var(--ink-border);
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            transform: translateY(-1px);
        }

        .job-card.status-queued { border-left-color: var(--gold); }
        .job-card.status-in_progress { border-left-color: var(--teal); }
        .job-card.status-raw_videos_ready { border-left-color: #38bdf8; }
        .job-card.status-assembled { border-left-color: #a855f7; }
        .job-card.status-published { border-left-color: #22c55e; }
        .job-card.status-failed { border-left-color: var(--coral); }

        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 0.6rem;
        }

        .job-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--white);
        }

        .status-badge {
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }

        .status-badge.queued { background: rgba(212, 175, 111, 0.2); color: var(--gold); }
        .status-badge.in_progress { background: rgba(79, 209, 197, 0.2); color: var(--teal); }
        .status-badge.raw_videos_ready { background: rgba(56, 189, 248, 0.2); color: #38bdf8; }
        .status-badge.assembled { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
        .status-badge.published { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .status-badge.failed { background: rgba(232, 103, 77, 0.2); color: var(--coral); }

        .job-notes {
            font-size: 0.9rem;
            color: var(--mute);
            margin-bottom: 0.8rem;
            line-height: 1.4;
        }

        .url-pills {
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            margin-bottom: 0.8rem;
        }

        .url-link {
            font-family: var(--mono);
            font-size: 0.8rem;
            color: var(--teal);
            text-decoration: none;
            word-break: break-all;
            background: rgba(79, 209, 197, 0.08);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            display: inline-block;
        }

        .url-link:hover { text-decoration: underline; background: rgba(79, 209, 197, 0.15); }

        .job-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.78rem;
            color: var(--mute);
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 0.6rem;
            margin-top: 0.6rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .tags-row {
            display: flex;
            gap: 0.3rem;
            flex-wrap: wrap;
        }

        .tag {
            background: var(--ink-card);
            border: 1px solid var(--ink-border);
            color: var(--white);
            font-size: 0.7rem;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
        }

        .actions-row {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .btn-action {
            background: var(--ink-card);
            border: 1px solid var(--ink-border);
            color: var(--white);
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            cursor: pointer;
            font-family: inherit;
        }
        .btn-action:hover { border-color: var(--teal); color: var(--teal); }

        /* Pipeline progress bar */
        .pipeline-row {
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .pipeline-row::-webkit-scrollbar { display: none; }

        .pipeline-step {
            font-size: 0.68rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            white-space: nowrap;
            background: var(--ink-card);
            color: var(--mute);
            border: 1px solid var(--ink-border);
        }

        .pipeline-step.done {
            background: rgba(34, 197, 94, 0.12);
            color: #4ade80;
            border-color: rgba(34, 197, 94, 0.3);
        }

        .pipeline-step.active {
            background: rgba(79, 209, 197, 0.15);
            color: var(--teal);
            border-color: var(--teal-dim);
        }

        .pipeline-arrow {
            color: var(--mute);
            font-size: 0.6rem;
            padding: 0 0.25rem;
            flex-shrink: 0;
        }

        /* Asset / published links section */
        .asset-section {
            background: rgba(0, 0, 0, 0.18);
            border: 1px solid var(--ink-border);
            border-radius: 6px;
            padding: 0.55rem 0.75rem;
            margin-bottom: 0.7rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .asset-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .asset-label {
            font-size: 0.68rem;
            color: var(--mute);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            min-width: 3.2rem;
        }

        .asset-link {
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
            font-size: 0.8rem;
            font-weight: 600;
            text-decoration: none;
            padding: 0.28rem 0.6rem;
            border-radius: 4px;
            transition: background 0.15s ease;
            min-height: 32px; /* phone-friendly tap target */
        }

        .asset-link.drive {
            background: rgba(79, 209, 197, 0.1);
            color: var(--teal);
            border: 1px solid var(--teal-dim);
        }
        .asset-link.drive:hover { background: rgba(79, 209, 197, 0.22); }

        .asset-link.youtube {
            background: rgba(255, 80, 80, 0.1);
            color: #ff6b6b;
            border: 1px solid rgba(255, 80, 80, 0.3);
        }
        .asset-link.youtube:hover { background: rgba(255, 80, 80, 0.2); }

        .asset-link.xpost {
            background: rgba(255, 255, 255, 0.06);
            color: var(--white);
            border: 1px solid var(--ink-border);
        }
        .asset-link.xpost:hover { background: rgba(255, 255, 255, 0.12); }

        .asset-pub-date {
            font-size: 0.7rem;
            color: var(--mute);
            margin-left: 0.25rem;
        }

        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--mute);
        }

        /* Toast notification */
        #toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--teal);
            color: var(--ink);
            font-weight: 700;
            padding: 0.8rem 1.4rem;
            border-radius: 6px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <span class="badge-logo">TS</span>
                <div>
                    <h1>Tech-Shorts Intake & Ideation</h1>
                    <p class="subtitle">Step 1 of the NotebookLM &rarr; Hook/Outro &rarr; YouTube Shorts &rarr; X Pipeline</p>
                </div>
            </div>
            <div class="stats-strip">
                <div class="stat-item">
                    <span class="stat-val" id="stat-total">0</span>
                    <span class="stat-lbl">Total</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="stat-queued" style="color: var(--gold);">0</span>
                    <span class="stat-lbl">Queued</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="stat-active" style="color: var(--teal);">0</span>
                    <span class="stat-lbl">Active</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="stat-assembled" style="color: #c084fc;">0</span>
                    <span class="stat-lbl">Assembled</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="stat-published" style="color: #4ade80;">0</span>
                    <span class="stat-lbl">Published</span>
                </div>
            </div>
        </header>

        <div class="layout">
            <!-- Left: Intake Form -->
            <div class="card">
                <h2>💡 Enqueue New Idea</h2>
                <form id="intake-form">
                    <div class="form-group">
                        <label for="title">Topic / Working Title *</label>
                        <input type="text" id="title" required placeholder="e.g. Why AI Agents Spontaneously Lie">
                        <div class="hint">Catchy, thesis-driven title for the short.</div>
                    </div>

                    <div class="form-group">
                        <label for="urls">Source URLs *</label>
                        <textarea id="urls" required placeholder="https://arxiv.org/abs/...&#10;https://notebook.google.com/...&#10;https://x.com/..."></textarea>
                        <div class="hint">Paste one or multiple URLs (articles, podcasts, reports, NotebookLM links).</div>
                    </div>

                    <div class="form-group">
                        <label for="notes">Core Thesis / Hook Angle</label>
                        <textarea id="notes" placeholder="What is the 3-7-21 hook? Why does this matter right now? Key data points or quotes."></textarea>
                    </div>

                    <div class="form-group">
                        <label for="tags">Tags (comma-separated)</label>
                        <input type="text" id="tags" placeholder="safety, agents, aisi, canis, on-device">
                    </div>

                    <div class="form-group">
                        <label for="source-file">Source File <span style="color:var(--mute);font-weight:400;">(optional)</span></label>
                        <input type="file" id="source-file" accept=".pdf,.md,.markdown,.txt">
                        <div class="hint">PDF, Markdown, or TXT — max 50 MB. Uploaded to NotebookLM as a source.</div>
                        <div id="file-preview" style="display:none;margin-top:0.4rem;"></div>
                    </div>

                    <button type="submit" class="btn" id="submit-btn">
                        ⚡ Enqueue Tech-Short Job
                    </button>
                </form>
            </div>

            <!-- Right: Queue & Board -->
            <div>
                <div class="controls-bar">
                    <div class="filter-pills" id="filter-pills">
                        <button class="pill active" data-filter="all">All Jobs</button>
                        <button class="pill" data-filter="queued">Queued</button>
                        <button class="pill" data-filter="in_progress">In Progress</button>
                        <button class="pill" data-filter="assembled">Assembled</button>
                        <button class="pill" data-filter="published">Published</button>
                    </div>

                    <button id="btn-claim-next" class="btn btn-claim">
                        ▶ Claim Next Job
                    </button>
                </div>

                <div class="queue-list" id="queue-container">
                    <div class="empty-state">Loading queue...</div>
                </div>
            </div>
        </div>
    </div>

    <div id="toast"></div>

    <script>
        let allJobs = [];
        let currentFilter = 'all';

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 3000);
        }

        async function fetchJobs() {
            try {
                const res = await fetch('/api/jobs');
                const data = await res.json();
                allJobs = data.jobs || [];
                renderStats();
                renderQueue();
            } catch (err) {
                console.error('Error fetching jobs:', err);
                document.getElementById('queue-container').innerHTML =
                    '<div class="empty-state">Failed to load jobs from backend.</div>';
            }
        }

        function renderStats() {
            document.getElementById('stat-total').textContent = allJobs.length;
            document.getElementById('stat-queued').textContent =
                allJobs.filter(j => j.status === 'queued').length;
            document.getElementById('stat-active').textContent =
                allJobs.filter(j => j.status === 'in_progress' || j.status === 'raw_videos_ready').length;
            document.getElementById('stat-assembled').textContent =
                allJobs.filter(j => j.status === 'assembled').length;
            document.getElementById('stat-published').textContent =
                allJobs.filter(j => j.status === 'published').length;
        }

        function pipelineSteps(status) {
            const ORDER = ['queued', 'in_progress', 'raw_videos_ready', 'assembled', 'published'];
            const LABELS = ['Idea', 'Processing', 'Raw Assets', 'Assembled', 'Published'];
            const cur = ORDER.indexOf(status);
            return LABELS.map((lbl, i) => {
                const cls = i < cur ? 'done' : (i === cur ? 'active' : '');
                return `<span class="pipeline-step ${cls}">${lbl}</span>`;
            }).join('<span class="pipeline-arrow">›</span>');
        }

        function assetLinks(job) {
            const drive = job.drive || {};
            const yt = job.youtube || {};
            const xp = job.x_post || {};

            const hasDrive = drive.folder_url || drive.infographic_url || drive.slidedeck_url;
            const hasYT = yt.short_url || yt.long_url;
            const hasX = xp.post_url;

            if (!hasDrive && !hasYT && !hasX) return '';

            const rows = [];

            if (hasDrive) {
                let links = '';
                if (drive.folder_url)
                    links += `<a href="${escapeHtml(drive.folder_url)}" target="_blank" rel="noopener" class="asset-link drive">📁 Folder</a>`;
                if (drive.infographic_url)
                    links += `<a href="${escapeHtml(drive.infographic_url)}" target="_blank" rel="noopener" class="asset-link drive">🖼 Infographic</a>`;
                if (drive.slidedeck_url)
                    links += `<a href="${escapeHtml(drive.slidedeck_url)}" target="_blank" rel="noopener" class="asset-link drive">📊 Slides</a>`;
                rows.push(`<div class="asset-row"><span class="asset-label">Drive</span>${links}</div>`);
            }

            if (hasYT) {
                const pubDate = yt.published_at ? `<span class="asset-pub-date">${yt.published_at.split('T')[0]}</span>` : '';
                let links = '';
                if (yt.short_url)
                    links += `<a href="${escapeHtml(yt.short_url)}" target="_blank" rel="noopener" class="asset-link youtube">▶ Short</a>`;
                if (yt.long_url)
                    links += `<a href="${escapeHtml(yt.long_url)}" target="_blank" rel="noopener" class="asset-link youtube">▶ Long</a>`;
                rows.push(`<div class="asset-row"><span class="asset-label">YouTube</span>${links}${pubDate}</div>`);
            }

            if (hasX) {
                rows.push(`<div class="asset-row"><span class="asset-label">X Post</span><a href="${escapeHtml(xp.post_url)}" target="_blank" rel="noopener" class="asset-link xpost">✕ View Post</a></div>`);
            }

            return `<div class="asset-section">${rows.join('')}</div>`;
        }

        function renderQueue() {
            const container = document.getElementById('queue-container');
            const filtered = currentFilter === 'all'
                ? allJobs
                : allJobs.filter(j => j.status === currentFilter);

            if (filtered.length === 0) {
                container.innerHTML = `<div class="empty-state">No jobs found in status: ${currentFilter}</div>`;
                return;
            }

            container.innerHTML = filtered.map(job => {
                const statusClass = `status-${job.status}`;
                const urls = job.source_urls || [];
                const tags = job.tags || [];
                const dateStr = job.created_at ? job.created_at.split('T')[0] : '';
                const sf = job.source_file || {};
                const hasFile = !!(sf.original_name);

                return `
                    <div class="job-card ${statusClass}">
                        <div class="job-header">
                            <div>
                                <div class="job-title">${escapeHtml(job.title)}</div>
                                <div style="font-family: var(--mono); font-size: 0.75rem; color: var(--mute);">${escapeHtml(job.id)}</div>
                            </div>
                            <span class="status-badge ${job.status}">${job.status.replace(/_/g, ' ')}</span>
                        </div>

                        <div class="pipeline-row">${pipelineSteps(job.status)}</div>

                        ${assetLinks(job)}

                        ${job.idea_notes ? `<div class="job-notes">${escapeHtml(job.idea_notes)}</div>` : ''}

                        ${urls.length ? `
                            <div class="url-pills">
                                ${urls.map(u => `<a href="${escapeHtml(u)}" target="_blank" rel="noopener" class="url-link">🔗 ${escapeHtml(u)}</a>`).join('')}
                            </div>
                        ` : ''}

                        ${hasFile ? `
                            <div style="margin-bottom:0.8rem;">
                                <a href="/api/jobs/${encodeURIComponent(job.id)}/source-file"
                                   class="file-badge" style="text-decoration:none;" download="${escapeHtml(sf.original_name)}">
                                   📎 ${escapeHtml(sf.original_name)}
                                   ${sf.size_bytes ? ` (${sf.size_bytes < 1048576 ? Math.round(sf.size_bytes/1024) + ' KB' : (sf.size_bytes/1048576).toFixed(1) + ' MB'})` : ''}
                                </a>
                            </div>
                        ` : ''}

                        <div class="job-meta">
                            <div class="tags-row">
                                ${tags.map(t => `<span class="tag">#${escapeHtml(t)}</span>`).join('')}
                                ${dateStr ? `<span style="font-size: 0.72rem; color: var(--mute);">📅 ${dateStr}</span>` : ''}
                            </div>

                            <div class="actions-row">
                                <select onchange="updateStatus('${job.id}', this.value)" style="padding: 0.2rem 0.4rem; font-size: 0.75rem; width: auto;">
                                    <option value="queued" ${job.status === 'queued' ? 'selected' : ''}>queued</option>
                                    <option value="in_progress" ${job.status === 'in_progress' ? 'selected' : ''}>in_progress</option>
                                    <option value="raw_videos_ready" ${job.status === 'raw_videos_ready' ? 'selected' : ''}>raw_videos_ready</option>
                                    <option value="assembled" ${job.status === 'assembled' ? 'selected' : ''}>assembled</option>
                                    <option value="published" ${job.status === 'published' ? 'selected' : ''}>published</option>
                                    <option value="failed" ${job.status === 'failed' ? 'selected' : ''}>failed</option>
                                </select>
                                <button class="btn-action" onclick="deleteJob('${job.id}')" title="Delete job">🗑️</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }

        // File picker preview
        document.getElementById('source-file').addEventListener('change', (e) => {
            const file = e.target.files[0];
            const preview = document.getElementById('file-preview');
            if (!file) {
                preview.style.display = 'none';
                return;
            }
            const allowedExts = ['.pdf', '.md', '.markdown', '.txt'];
            const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
            if (!allowedExts.includes(ext)) {
                preview.innerHTML = `<span style="color:var(--coral);font-size:0.8rem;">✗ ${escapeHtml(file.name)} — unsupported type</span>`;
                preview.style.display = 'block';
                e.target.value = '';
                return;
            }
            if (file.size > 50 * 1024 * 1024) {
                preview.innerHTML = `<span style="color:var(--coral);font-size:0.8rem;">✗ File too large (${(file.size/1024/1024).toFixed(1)} MB). Max 50 MB.</span>`;
                preview.style.display = 'block';
                e.target.value = '';
                return;
            }
            const sizeFmt = file.size < 1024 * 1024
                ? `${(file.size/1024).toFixed(0)} KB`
                : `${(file.size/1024/1024).toFixed(1)} MB`;
            preview.innerHTML = `<span class="file-badge">📎 ${escapeHtml(file.name)} (${sizeFmt})</span>`;
            preview.style.display = 'block';
        });

        // Intake Form Submit
        document.getElementById('intake-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('title').value.trim();
            const urls = document.getElementById('urls').value.trim();
            const notes = document.getElementById('notes').value.trim();
            const tags = document.getElementById('tags').value.trim();
            const fileInput = document.getElementById('source-file');
            const file = fileInput.files[0] || null;

            if (!title) return;

            const submitBtn = document.getElementById('submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enqueueing…';

            try {
                // Step 1: Create job record
                const res = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: title,
                        source_urls: urls,
                        idea_notes: notes,
                        tags: tags
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    alert('Error: ' + (err.error || 'Failed to enqueue job'));
                    return;
                }

                const created = await res.json();

                // Step 2: Upload source file if one was selected
                if (file) {
                    submitBtn.textContent = 'Uploading file…';
                    const fd = new FormData();
                    fd.append('file', file);
                    const uploadRes = await fetch(
                        `/api/jobs/${encodeURIComponent(created.id)}/source-file`,
                        { method: 'POST', body: fd }
                    );
                    if (!uploadRes.ok) {
                        const uploadErr = await uploadRes.json();
                        alert('Job created but file upload failed: ' + (uploadErr.error || 'Unknown error'));
                    } else {
                        showToast(`Enqueued: ${created.title} (+ file attached)`);
                    }
                } else {
                    showToast(`Enqueued: ${created.title}`);
                }

                document.getElementById('intake-form').reset();
                document.getElementById('file-preview').style.display = 'none';
                fetchJobs();
            } catch (err) {
                alert('Failed to connect: ' + err.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '⚡ Enqueue Tech-Short Job';
            }
        });

        // Filter Pills
        document.getElementById('filter-pills').addEventListener('click', (e) => {
            if (e.target.classList.contains('pill')) {
                document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                currentFilter = e.target.dataset.filter;
                renderQueue();
            }
        });

        // Status Update
        async function updateStatus(jobId, newStatus) {
            try {
                const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    showToast(`Updated status &rarr; ${newStatus}`);
                    fetchJobs();
                }
            } catch (err) {
                console.error(err);
            }
        }

        // Claim Next
        document.getElementById('btn-claim-next').addEventListener('click', async () => {
            try {
                const res = await fetch('/api/jobs/claim', { method: 'POST' });
                const data = await res.json();
                if (data.job) {
                    showToast(`Claimed: ${data.job.title}`);
                    fetchJobs();
                } else {
                    showToast('No queued jobs found.');
                }
            } catch (err) {
                console.error(err);
            }
        });

        // Delete Job
        async function deleteJob(jobId) {
            if (!confirm(`Delete job ${jobId}?`)) return;
            try {
                const res = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`, {
                    method: 'DELETE'
                });
                if (res.ok) {
                    showToast('Job removed');
                    fetchJobs();
                }
            } catch (err) {
                console.error(err);
            }
        }

        // Initial fetch
        fetchJobs();
        // Poll for updates every 10 seconds
        setInterval(fetchJobs, 10000);
    </script>
</body>
</html>
"""


class IntakeHTTPHandler(BaseHTTPRequestHandler):
    """Minimal zero-dependency REST and static server."""

    jobs_file: Optional[Path] = None

    def _parse_multipart(self) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Parse multipart/form-data from request body. Returns (fields, files)."""
        import cgi
        content_type = self.headers.get("Content-Type", "")
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ=environ)
        fields: Dict[str, str] = {}
        files: Dict[str, Any] = {}
        for key in form.keys():
            item = form[key]
            if hasattr(item, "filename") and item.filename:
                files[key] = {
                    "filename": item.filename,
                    "data": item.file.read(),
                    "type": item.type or "",
                }
            else:
                fields[key] = item.value if hasattr(item, "value") else str(item)
        return fields, files

    def _send_json(self, data: Any, status: int = HTTPStatus.OK):
        payload = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "" or path == "/index.html":
            payload = WEB_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/api/health":
            self._send_json({"ok": True, "time": now_iso()})
            return

        if path == "/api/jobs":
            query = urllib.parse.parse_qs(parsed.query)
            status = query.get("status", [None])[0]
            tag = query.get("tag", [None])[0]
            search = query.get("search", [None])[0]
            jobs = list_jobs(status=status, tag=tag, search=search, jobs_file=self.jobs_file)
            self._send_json({"jobs": jobs, "total": len(jobs)})
            return

        # Download uploaded source file: GET /api/jobs/<id>/source-file
        if path.endswith("/source-file") and "/api/jobs/" in path:
            job_id = urllib.parse.unquote(
                path[len("/api/jobs/"):path.rfind("/source-file")]
            )
            job = get_job(job_id, jobs_file=self.jobs_file)
            if not job:
                self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
                return
            sf = job.get("source_file") or {}
            if not sf.get("path"):
                self._send_json({"error": "No source file attached"}, status=HTTPStatus.NOT_FOUND)
                return
            file_path = Path(sf["path"])
            if not file_path.exists():
                self._send_json({"error": "File not found on disk"}, status=HTTPStatus.NOT_FOUND)
                return
            data = file_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", sf.get("mime_type", "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{sf.get("original_name", "source")}"',
            )
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith("/api/jobs/"):
            job_id = urllib.parse.unquote(path[len("/api/jobs/"):])
            job = get_job(job_id, jobs_file=self.jobs_file)
            if job:
                self._send_json(job)
            else:
                self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        # File upload is multipart — route it before consuming rfile as JSON
        if path.endswith("/source-file") and path.startswith("/api/jobs/"):
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self._send_json(
                    {"error": "Expected multipart/form-data"},
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            job_id = urllib.parse.unquote(
                path[len("/api/jobs/"):path.rfind("/source-file")]
            )
            job = get_job(job_id, jobs_file=self.jobs_file)
            if not job:
                self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                _fields, files = self._parse_multipart()
            except Exception as e:
                self._send_json({"error": f"Multipart parse error: {e}"}, status=HTTPStatus.BAD_REQUEST)
                return
            if "file" not in files:
                self._send_json({"error": "No 'file' field in upload"}, status=HTTPStatus.BAD_REQUEST)
                return
            upload = files["file"]
            original_name = upload["filename"]
            file_bytes = upload["data"]
            try:
                validate_source_file(original_name, len(file_bytes))
            except ValueError as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
                return
            try:
                meta = store_source_file(job["id"], file_bytes, original_name)
                update_job(job["id"], jobs_file=self.jobs_file, source_file=meta)
                self._send_json({"ok": True, "source_file": meta, "job_id": job["id"]})
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        # All other POST routes expect JSON
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            self._send_json({"error": "Malformed JSON"}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/jobs":
            title = payload.get("title", "")
            urls = payload.get("source_urls", [])
            notes = payload.get("idea_notes", "")
            tags = payload.get("tags", [])
            notebook_url = payload.get("notebook_url", "")
            status = payload.get("status", "queued")

            if not title:
                self._send_json({"error": "Field 'title' is required"}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                job = create_job(
                    title=title,
                    source_urls=urls,
                    idea_notes=notes,
                    tags=tags,
                    notebook_url=notebook_url,
                    status=status,
                    jobs_file=self.jobs_file,
                )
                self._send_json(job, status=HTTPStatus.CREATED)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if path == "/api/jobs/claim":
            status_from = payload.get("from", "queued")
            status_to = payload.get("to", "in_progress")
            job = claim_next_job(status_from=status_from, status_to=status_to, jobs_file=self.jobs_file)
            self._send_json({"job": job, "claimed": bool(job)})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/jobs/"):
            job_id = urllib.parse.unquote(path[len("/api/jobs/"):])
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                updates = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                self._send_json({"error": "Malformed JSON"}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                updated = update_job(job_id, jobs_file=self.jobs_file, **updates)
                if updated:
                    self._send_json(updated)
                else:
                    self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
            except Exception as e:
                self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/jobs/"):
            job_id = urllib.parse.unquote(path[len("/api/jobs/"):])
            deleted = delete_job(job_id, jobs_file=self.jobs_file)
            if deleted:
                self._send_json({"ok": True, "deleted": job_id})
            else:
                self._send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format, *args):
        # Concise console logging
        pass


def serve_web(port: int = 8766, host: str = "127.0.0.1", jobs_file: Optional[Path] = None):
    """Start the lightweight web console server."""
    IntakeHTTPHandler.jobs_file = jobs_file or DEFAULT_JOBS_FILE
    server = HTTPServer((host, port), IntakeHTTPHandler)
    url = f"http://{host}:{port}"
    print(f"┌────────────────────────────────────────────────────────────┐")
    print(f"│  Tech-Shorts Intake & Ideation Console Live               │")
    print(f"│  Open in browser:  {url:<39} │")
    print(f"│  API endpoint:     {url + '/api/jobs':<39} │")
    print(f"│  Press Ctrl+C to stop                                      │")
    print(f"└────────────────────────────────────────────────────────────┘", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[intake] Shutting down web server.")
        server.server_close()


# ── CLI Interface ─────────────────────────────────────────────────────────────

def cli_add(args):
    """Handler for 'intake.py add'."""
    title = args.title
    urls = args.urls
    notes = args.notes
    tags = args.tags
    source_file_path: Optional[Path] = getattr(args, "source_file", None)

    # Interactive mode if title not provided
    if not title:
        print("\n── Tech-Shorts Ideation Intake (Interactive) ──")
        try:
            title = input("1. Topic / Working Title: ").strip()
            if not title:
                print("Error: Title is required.", file=sys.stderr)
                sys.exit(1)
            urls_input = input("2. Source URLs (comma or newline separated): ").strip()
            urls = urls_input
            notes = input("3. Core Thesis / Hook angle (optional): ").strip()
            tags = input("4. Tags (e.g. safety, canis) (optional): ").strip()
            file_input = input("5. Source file path (PDF/MD/TXT, optional — press Enter to skip): ").strip()
            if file_input:
                source_file_path = Path(file_input)
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)

    # Validate and read source file if provided
    source_file_meta: Optional[Dict[str, Any]] = None
    if source_file_path:
        source_file_path = Path(source_file_path)
        if not source_file_path.exists():
            print(f"Error: Source file not found: {source_file_path}", file=sys.stderr)
            sys.exit(1)
        file_bytes = source_file_path.read_bytes()
        try:
            validate_source_file(source_file_path.name, len(file_bytes))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        # File is stored after job creation so we have the job_id
        _pending_file_bytes = file_bytes
        _pending_file_name = source_file_path.name
    else:
        _pending_file_bytes = None
        _pending_file_name = None

    try:
        job = create_job(
            title=title,
            source_urls=urls or [],
            idea_notes=notes or "",
            tags=tags or [],
            notebook_url=args.notebook_url or "",
            status=args.status,
            jobs_file=args.file,
        )

        # Store the source file now that we have a job_id
        if _pending_file_bytes is not None:
            source_file_meta = store_source_file(job["id"], _pending_file_bytes, _pending_file_name)
            update_job(job["id"], jobs_file=args.file, source_file=source_file_meta)
            job["source_file"] = source_file_meta

        if args.json:
            print(json.dumps(job, indent=2))
        else:
            print(f"\n✅ Queued tech-short job:")
            print(f"  ID:          {job['id']}")
            print(f"  Title:       {job['title']}")
            print(f"  Status:      {STATUS_BADGES.get(job['status'], job['status'])}")
            print(f"  URLs ({len(job['source_urls'])}):   {', '.join(job['source_urls']) if job['source_urls'] else '(none)'}")
            if job.get("source_file", {}).get("original_name"):
                sf = job["source_file"]
                size_kb = sf.get("size_bytes", 0) // 1024
                print(f"  File:        {sf['original_name']} ({size_kb} KB) → {sf['path']}")
            if job['idea_notes']:
                print(f"  Notes:       {job['idea_notes']}")
            if job['tags']:
                print(f"  Tags:        {', '.join(job['tags'])}")
            print()
    except Exception as e:
        print(f"Error creating job: {e}", file=sys.stderr)
        sys.exit(1)


def cli_list(args):
    """Handler for 'intake.py list'."""
    jobs = list_jobs(status=args.status, tag=args.tag, search=args.search, jobs_file=args.file)
    if args.json:
        print(json.dumps(jobs, indent=2))
        return

    if not jobs:
        print(f"No jobs found matching criteria.")
        return

    print(f"\n{'ID':<38} {'STATUS':<15} {'TITLE':<36} {'URLS':<5}")
    print("─" * 98)
    for j in jobs:
        badge = STATUS_BADGES.get(j.get("status", ""), j.get("status", ""))
        title = j.get("title", "")
        if len(title) > 34:
            title = title[:31] + "..."
        jid = j.get("id", "")
        n_urls = len(j.get("source_urls", []))
        print(f"{jid:<38} {badge:<15} {title:<36} {n_urls:<5}")
    print(f"\nTotal: {len(jobs)} jobs\n")


def cli_show(args):
    """Handler for 'intake.py show'."""
    job = get_job(args.id, jobs_file=args.file)
    if not job:
        print(f"Error: Job '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(job, indent=2))
        return

    print(f"\n── Tech-Short Job: {job.get('title')} ──")
    print(f"  ID:           {job.get('id')}")
    print(f"  Slug:         {job.get('slug')}")
    print(f"  Status:       {STATUS_BADGES.get(job.get('status'), job.get('status'))}")
    print(f"  Created:      {job.get('created_at')}")
    print(f"  Updated:      {job.get('updated_at')}")
    print(f"  Notebook URL: {job.get('notebook_url') or '(none)'}")
    print(f"  Source URLs:")
    for u in job.get("source_urls", []):
        print(f"    • {u}")
    if not job.get("source_urls"):
        print("    (none)")
    sf = job.get("source_file") or {}
    if sf.get("original_name"):
        size_kb = (sf.get("size_bytes", 0) or 0) // 1024
        print(f"  Source File:  {sf['original_name']} ({size_kb} KB) — {sf.get('path', '?')}")
    else:
        print(f"  Source File:  (none)")
    print(f"  Notes:        {job.get('idea_notes') or '(none)'}")
    print(f"  Tags:         {', '.join(job.get('tags', [])) or '(none)'}")

    assets = job.get("assets", {})
    if any(assets.values()):
        print("  Assets:")
        for k, v in assets.items():
            if v:
                print(f"    • {k}: {v}")

    yt = job.get("youtube", {})
    if any(yt.values()):
        print("  YouTube:")
        for k, v in yt.items():
            if v:
                print(f"    • {k}: {v}")
    print()


def cli_update(args):
    """Handler for 'intake.py update'."""
    updates: Dict[str, Any] = {}
    if args.status:
        updates["status"] = args.status
    if args.title:
        updates["title"] = args.title
    if args.urls:
        updates["source_urls"] = args.urls
    if args.notes:
        updates["idea_notes"] = args.notes
    if args.tags:
        updates["tags"] = args.tags
    if args.notebook_url:
        updates["notebook_url"] = args.notebook_url

    if not updates:
        print("No update arguments specified. Use --status, --title, --urls, etc.", file=sys.stderr)
        sys.exit(1)

    try:
        updated = update_job(args.id, jobs_file=args.file, **updates)
        if not updated:
            print(f"Error: Job '{args.id}' not found.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(updated, indent=2))
        else:
            print(f"✅ Updated job '{updated['id']}' status &rarr; {STATUS_BADGES.get(updated['status'], updated['status'])}")
    except Exception as e:
        print(f"Error updating job: {e}", file=sys.stderr)
        sys.exit(1)


def cli_claim(args):
    """Handler for 'intake.py claim'."""
    job = claim_next_job(status_from=args.status_from, status_to=args.status_to, jobs_file=args.file)
    if not job:
        if args.json:
            print(json.dumps(None))
        else:
            print("No queued jobs available to claim.")
        sys.exit(0)

    if args.json:
        print(json.dumps(job, indent=2))
    else:
        print(f"✅ Claimed job: {job['id']} ('{job['title']}') &rarr; {job['status']}")


def cli_delete(args):
    """Handler for 'intake.py delete'."""
    ok = delete_job(args.id, jobs_file=args.file)
    if ok:
        print(f"✅ Deleted job '{args.id}'")
    else:
        print(f"Error: Job '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)


def cli_serve(args):
    """Handler for 'intake.py serve'."""
    serve_web(port=args.port, host=args.host, jobs_file=args.file)


def main():
    parser = argparse.ArgumentParser(
        description="Tech-Shorts Ideation Intake & Queue Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", type=Path, default=DEFAULT_JOBS_FILE, help="Path to jobs.json file")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # add
    p_add = subparsers.add_parser("add", help="Enqueue a new tech-short idea")
    p_add.add_argument("--title", "-t", type=str, help="Working title of the tech short")
    p_add.add_argument("--urls", "-u", type=str, help="Source URL(s), comma or newline separated")
    p_add.add_argument("--notes", "-n", type=str, help="Idea notes / angle / thesis")
    p_add.add_argument("--tags", type=str, help="Comma-separated tags")
    p_add.add_argument("--notebook-url", type=str, help="Direct NotebookLM URL if already created")
    p_add.add_argument(
        "--source-file",
        type=Path,
        metavar="FILE",
        help="Local PDF, Markdown, or TXT file to attach as source (max 50 MB)",
    )
    p_add.add_argument("--status", type=str, default="queued", choices=sorted(VALID_STATUSES), help="Initial status")
    p_add.add_argument("--json", action="store_true", help="Output created job as JSON")
    p_add.set_defaults(func=cli_add)

    # list
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List tech-short jobs")
    p_list.add_argument("--status", "-s", type=str, choices=sorted(VALID_STATUSES), help="Filter by status")
    p_list.add_argument("--tag", type=str, help="Filter by tag")
    p_list.add_argument("--search", "-q", type=str, help="Search text in title/notes/urls")
    p_list.add_argument("--json", action="store_true", help="Output results as JSON")
    p_list.set_defaults(func=cli_list)

    # show
    p_show = subparsers.add_parser("show", aliases=["get"], help="Show details for a specific job")
    p_show.add_argument("id", type=str, help="Job ID or slug")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=cli_show)

    # update
    p_up = subparsers.add_parser("update", help="Update fields on an existing job")
    p_up.add_argument("id", type=str, help="Job ID or slug to update")
    p_up.add_argument("--status", "-s", type=str, choices=sorted(VALID_STATUSES), help="New status")
    p_up.add_argument("--title", "-t", type=str, help="Update title")
    p_up.add_argument("--urls", "-u", type=str, help="Update source URLs")
    p_up.add_argument("--notes", "-n", type=str, help="Update idea notes")
    p_up.add_argument("--tags", type=str, help="Update tags")
    p_up.add_argument("--notebook-url", type=str, help="Update NotebookLM URL")
    p_up.add_argument("--json", action="store_true", help="Output updated job as JSON")
    p_up.set_defaults(func=cli_update)

    # claim
    p_claim = subparsers.add_parser("claim", help="Claim next available job for pipeline execution")
    p_claim.add_argument("--status-from", default="queued", help="Status to match (default: queued)")
    p_claim.add_argument("--status-to", default="in_progress", help="Status to transition to (default: in_progress)")
    p_claim.add_argument("--json", action="store_true", help="Output claimed job as JSON")
    p_claim.set_defaults(func=cli_claim)

    # delete
    p_del = subparsers.add_parser("delete", aliases=["rm"], help="Delete a job from the queue")
    p_del.add_argument("id", type=str, help="Job ID or slug to delete")
    p_del.set_defaults(func=cli_delete)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start local web intake UI server")
    p_serve.add_argument("--port", "-p", type=int, default=8766, help="Port to listen on (default: 8766)")
    p_serve.add_argument("--host", type=str, default="127.0.0.1", help="Host binding (default: 127.0.0.1)")
    p_serve.set_defaults(func=cli_serve)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        # Default action: list jobs or show help
        cli_list(argparse.Namespace(status=None, tag=None, search=None, file=args.file, json=False))


if __name__ == "__main__":
    main()
