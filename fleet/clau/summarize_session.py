#!/usr/bin/env python3
"""
fleet/clau/summarize_session.py
--------------------------------
Post-session lesson summarizer for Clau (Claude Code).

Modes:
  --pre           Pre-session: fetch top lessons from PB, write active_lessons.txt.
  --post          Post-session: scrape log for new lessons, post to PB, refresh active_lessons.txt.
  --lesson JSON   Submit a single JSON-structured lesson to PB and ledger.

When called with no args, defaults to --post.

Active lessons file: ~/fleet/clau/active_lessons.txt
This file is read by heartbeat_wrapper.sh and prepended to the Claude prompt.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────────
FLEET        = Path("/Users/miguelrodriguez/fleet")
CLAU_DIR     = FLEET / "clau"
LOG_FILE     = FLEET / "logs" / "clau.log"
PROGRESS_MD  = CLAU_DIR / "PROGRESS.md"
LEDGER_FILE  = FLEET / "lessons" / "ledger.json"
ACTIVE_FILE  = CLAU_DIR / "active_lessons.txt"

PB_BASE      = "http://127.0.0.1:8090/api/collections"
AGENT        = "clau"
TOP_N        = 5          # lessons to inject into active_lessons.txt
MAX_LOG_LINES = 500       # lines to scan from end of log


# ── PocketBase helpers ─────────────────────────────────────────────────────────

def pb_get(path: str) -> dict:
    url = f"{PB_BASE}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[summarize] WARN GET {path}: {e}", file=sys.stderr)
        return {"items": []}


def pb_post(collection: str, data: dict) -> Optional[dict]:
    url = f"{PB_BASE}/{collection}/records"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[summarize] WARN POST {collection}: {e}", file=sys.stderr)
        return None


# ── Ledger helpers ─────────────────────────────────────────────────────────────

def load_ledger() -> list:
    if LEDGER_FILE.exists():
        try:
            return json.loads(LEDGER_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def save_ledger(ledger: list):
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_FILE.write_text(json.dumps(ledger, indent=2))


def ledger_has(title: str, ledger: list) -> bool:
    t = title.strip().lower()
    return any(e.get("title", "").strip().lower() == t for e in ledger)


# ── Lesson extraction from log ─────────────────────────────────────────────────

# Markers that signal an agent-stated lesson in the log output
LESSON_PATTERNS = [
    re.compile(r"(?i)^lesson[:\-]\s*(.+)$"),
    re.compile(r"(?i)^key insight[:\-]\s*(.+)$"),
    re.compile(r"(?i)^NOTE[:\-]\s*(.+)$"),
    re.compile(r"(?i)^\[lesson\]\s*(.+)$"),
]


def extract_lessons_from_log(since_ts: Optional[datetime.datetime] = None) -> list[dict]:
    """Scan the end of clau.log for lines matching lesson patterns."""
    if not LOG_FILE.exists():
        return []

    raw_lines = LOG_FILE.read_text(errors="replace").splitlines()
    lines = raw_lines[-MAX_LOG_LINES:]

    lessons = []
    for line in lines:
        for pat in LESSON_PATTERNS:
            m = pat.match(line.strip())
            if m:
                text = m.group(1).strip()
                if len(text) > 20:   # skip very short fragments
                    lessons.append({
                        "title": text[:80],
                        "content": text,
                        "category": "workflow",
                        "confidence": "medium",
                        "agent": AGENT,
                    })
                break

    return lessons


def extract_lessons_from_progress() -> list[dict]:
    """Pull structured lessons from PROGRESS.md (## Lessons section)."""
    if not PROGRESS_MD.exists():
        return []

    text = PROGRESS_MD.read_text()
    # Find a ## Lessons section
    m = re.search(r"(?m)^##\s+Lessons?\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if not m:
        return []

    block = m.group(1)
    lessons = []
    for item in re.findall(r"(?m)^[-*]\s+(.+)$", block):
        item = item.strip()
        if len(item) > 20:
            lessons.append({
                "title": item[:80],
                "content": item,
                "category": "workflow",
                "confidence": "medium",
                "agent": AGENT,
            })
    return lessons


# ── Active lessons file ────────────────────────────────────────────────────────

CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}


def fetch_top_lessons(n: int = TOP_N) -> list[dict]:
    """Fetch the most relevant active lessons from PocketBase."""
    data = pb_get(f"lessons/records?filter=status%3D'active'&perPage=100&sort=-updated")
    items = data.get("items", [])

    # Sort by confidence, then recency
    items.sort(key=lambda x: (
        CONFIDENCE_ORDER.get(x.get("confidence", ""), 3),
        x.get("updated", "")
    ), reverse=False)

    return items[:n]


def write_active_lessons(lessons: list[dict]):
    """Write active_lessons.txt for prompt injection."""
    if not lessons:
        ACTIVE_FILE.write_text("")
        return

    lines = ["## Top Active Lessons (auto-generated — do not edit)\n"]
    for i, l in enumerate(lessons, 1):
        title = l.get("title", "").strip()
        content = l.get("content", l.get("lesson", "")).strip()
        confidence = l.get("confidence", "").strip()
        category = l.get("category", "").strip()
        tag = f"[{confidence}]" if confidence else ""
        lines.append(f"{i}. **{title}** {tag}")
        if content and content != title:
            lines.append(f"   {content}")
        lines.append("")

    ACTIVE_FILE.write_text("\n".join(lines))
    print(f"[summarize] active_lessons.txt updated ({len(lessons)} lessons)")


# ── Submit a single structured lesson ─────────────────────────────────────────

def submit_lesson(lesson_json: str):
    try:
        lesson = json.loads(lesson_json)
    except json.JSONDecodeError as e:
        print(f"[summarize] ERROR: invalid lesson JSON: {e}", file=sys.stderr)
        sys.exit(1)

    required = ("title", "content")
    for f in required:
        if f not in lesson:
            print(f"[summarize] ERROR: lesson missing field '{f}'", file=sys.stderr)
            sys.exit(1)

    lesson.setdefault("agent", AGENT)
    lesson.setdefault("category", "workflow")
    lesson.setdefault("confidence", "medium")
    lesson.setdefault("status", "pending_review")

    # Post to PocketBase
    result = pb_post("lessons", lesson)
    if result:
        print(f"[summarize] lesson posted to PB: {result.get('id')} — {lesson['title']}")
    else:
        print(f"[summarize] WARN: PB post failed, writing to ledger only")

    # Update local ledger
    ledger = load_ledger()
    if not ledger_has(lesson["title"], ledger):
        entry = {
            "id": result["id"] if result else f"local-{datetime.datetime.utcnow().isoformat()}",
            "title": lesson["title"],
            "category": lesson.get("category", ""),
            "project": lesson.get("project", ""),
            "lesson": lesson["content"],
            "agent": lesson["agent"],
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "pending_review",
        }
        ledger.append(entry)
        save_ledger(ledger)
        print(f"[summarize] lesson appended to ledger.json")


# ── Post mode ─────────────────────────────────────────────────────────────────

def run_post():
    """Post-session: extract new lessons, post to PB, refresh active_lessons."""
    print(f"[summarize] post-session run at {datetime.datetime.utcnow().isoformat()}")

    candidates = extract_lessons_from_log() + extract_lessons_from_progress()
    ledger = load_ledger()
    posted = 0

    for lesson in candidates:
        if ledger_has(lesson["title"], ledger):
            continue   # already recorded
        lesson["status"] = "pending_review"
        result = pb_post("lessons", lesson)
        entry = {
            "id": result["id"] if result else f"local-{datetime.datetime.utcnow().isoformat()}",
            "title": lesson["title"],
            "category": lesson.get("category", ""),
            "project": lesson.get("project", ""),
            "lesson": lesson["content"],
            "agent": lesson["agent"],
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "pending_review",
        }
        ledger.append(entry)
        posted += 1
        print(f"[summarize] new lesson: {lesson['title']}")

    if posted:
        save_ledger(ledger)
        print(f"[summarize] {posted} new lesson(s) written to ledger.json")
    else:
        print(f"[summarize] no new lessons found in log/PROGRESS.md")

    # Refresh active_lessons.txt regardless
    top = fetch_top_lessons()
    write_active_lessons(top)


# ── Pre mode ──────────────────────────────────────────────────────────────────

def run_pre():
    """Pre-session: refresh active_lessons.txt from PocketBase."""
    print(f"[summarize] pre-session run at {datetime.datetime.utcnow().isoformat()}")
    top = fetch_top_lessons()
    write_active_lessons(top)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Clau session lesson summarizer")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pre", action="store_true",
                       help="Pre-session: refresh active_lessons.txt only")
    group.add_argument("--post", action="store_true",
                       help="Post-session: extract lessons + refresh active_lessons.txt")
    group.add_argument("--lesson", metavar="JSON",
                       help="Submit a single JSON-structured lesson")
    args = parser.parse_args()

    if args.lesson:
        submit_lesson(args.lesson)
        top = fetch_top_lessons()
        write_active_lessons(top)
    elif args.pre:
        run_pre()
    else:
        # Default to post mode
        run_post()


if __name__ == "__main__":
    main()
