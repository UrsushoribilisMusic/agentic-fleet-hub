#!/usr/bin/env python3
"""
fleet/summarize_session.py
--------------------------
Post-session lesson extractor. Run at the end of each major heartbeat loop
(Phase 5 in the heartbeat protocol).

What it does:
  1. Reads today's agent log (~/fleet/logs/<agent>.log) and finds task IDs
     that were touched this session.
  2. Pulls PocketBase comments for those tasks (type: "output", "approval").
  3. Extracts structured lessons: decision, rationale, outcome, confidence.
  4. POSTs each lesson to PocketBase (status: pending_review) — avoids dupes
     by title.
  5. Writes ~/fleet/<agent>/TOP_LESSONS.md with the top 8 active lessons for
     prompt injection at next startup.

Usage:
    python ~/fleet/summarize_session.py [--agent clau] [--dry-run]
    python ~/fleet/summarize_session.py --agent gem --dry-run
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

PB_BASE = "http://localhost:8090/api/collections"
FLEET_ROOT = Path(__file__).parent
LOGS_DIR = FLEET_ROOT / "logs"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Confidence heuristics: keyword -> (confidence_label, score)
CONFIDENCE_MAP = [
    (["verified", "tested", "confirmed", "approved"], ("high", 85)),
    (["fixed", "resolved", "corrected", "working"], ("high", 80)),
    (["implemented", "added", "completed", "shipped"], ("medium", 65)),
    (["noted", "observed", "likely", "probably"], ("low", 40)),
]

# Categories: only values accepted by PocketBase lessons collection.
# Valid values: "tooling", "workflow", "architecture", ""
CATEGORY_MAP = [
    (["deploy", "push", "publish", "npm", "git", "release", "package"], "tooling"),
    (["pocketbase", "pb", "database", "schema", "collection", "sql"], "tooling"),
    (["api", "endpoint", "route", "server", "script", "bug", "fix", "error"], "tooling"),
    (["heartbeat", "launchd", "plist", "cron", "schedule", "dispatcher"], "workflow"),
    (["telegram", "message", "bot", "bridge", "notification", "standup"], "workflow"),
    (["review", "peer", "approval", "policy", "mandate", "protocol"], "workflow"),
    (["design", "pattern", "structure", "architecture", "schema", "contract"], "architecture"),
    (["refactor", "module", "interface", "abstraction", "system"], "architecture"),
]


# ── PocketBase helpers ────────────────────────────────────────────────────────

def pb_get(path: str) -> dict:
    url = f"{PB_BASE}/{path}"
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "items": [], "totalItems": 0}


def pb_post(collection: str, data: dict) -> dict:
    url = f"{PB_BASE}/{collection}/records"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


def lesson_exists(title: str) -> bool:
    """Check if a lesson with this title already exists in PocketBase."""
    encoded = urllib.request.quote(f'title="{title}"')
    result = pb_get(f"lessons/records?filter={encoded}&perPage=1")
    return result.get("totalItems", 0) > 0


# ── Log parsing ───────────────────────────────────────────────────────────────

def extract_task_ids_from_log(log_path: Path) -> list[str]:
    """
    Scan today's log for PocketBase task IDs (15-char alphanumeric) and
    ticket numbers like #87.
    """
    if not log_path.exists():
        return []

    task_ids = set()
    pb_id_re = re.compile(r'\b([a-z0-9]{15})\b')
    ticket_re = re.compile(r'#(\d{2,4})\b')

    try:
        text = log_path.read_text(errors="replace")
    except Exception:
        return []

    # Only scan lines that look like they belong to today
    today_lines = []
    in_today = False
    for line in text.splitlines():
        if TODAY in line:
            in_today = True
        if in_today:
            today_lines.append(line)

    # If we couldn't isolate today, scan the last 300 lines
    if not today_lines:
        today_lines = text.splitlines()[-300:]

    scan_text = "\n".join(today_lines)

    for m in pb_id_re.finditer(scan_text):
        task_ids.add(m.group(1))
    for m in ticket_re.finditer(scan_text):
        task_ids.add(m.group(0))  # keep as "#87" for label matching

    return list(task_ids)


def get_today_tasks_for_agent(agent: str) -> list[dict]:
    """
    Get tasks touched today: either assigned to the agent or updated today
    with approved/peer_review/in_progress status.
    """
    filter_q = urllib.request.quote(
        f'assigned_agent="{agent}"&&(status="approved"||status="peer_review"||status="in_progress")'
    )
    result = pb_get(f"tasks/records?filter={filter_q}&perPage=50&sort=-updated")
    items = result.get("items", [])

    # Filter to only tasks updated today
    today_tasks = []
    for task in items:
        updated = task.get("updated", "")
        if TODAY in updated:
            today_tasks.append(task)

    return today_tasks


def get_comments_for_task(task_id: str) -> list[dict]:
    """Fetch output and approval comments for a task."""
    filter_q = urllib.request.quote(
        f'task_id="{task_id}"&&(type="output"||type="approval"||type="question")'
    )
    result = pb_get(f"comments/records?filter={filter_q}&perPage=20&sort=created")
    return result.get("items", [])


# ── Lesson extraction ─────────────────────────────────────────────────────────

def infer_confidence(text: str) -> tuple[str, int]:
    lower = text.lower()
    for keywords, (label, score) in CONFIDENCE_MAP:
        if any(kw in lower for kw in keywords):
            return label, score
    return "medium", 60


def infer_category(text: str) -> str:
    lower = text.lower()
    for keywords, category in CATEGORY_MAP:
        if any(kw in lower for kw in keywords):
            return category
    return ""


def extract_lessons_from_task(task: dict, comments: list[dict]) -> list[dict]:
    """
    Turn a completed task + its comments into zero or more lesson candidates.
    Returns a list of lesson dicts ready for PocketBase insertion.
    """
    lessons = []
    title_raw = task.get("title", "").strip()
    description = task.get("description", "").strip()

    # Build a combined content blob from output comments
    output_parts = []
    approval_parts = []
    for c in comments:
        ctype = c.get("type", "")
        content = c.get("content", "").strip()
        if not content:
            continue
        if ctype == "output":
            output_parts.append(content)
        elif ctype == "approval":
            approval_parts.append(content)

    if not output_parts and not approval_parts:
        # No substantive comments — generate a minimal lesson from task metadata
        if not description:
            return []
        output_parts = [description]

    combined = "\n\n".join(output_parts)
    approval_text = "\n\n".join(approval_parts)

    # Decision: first meaningful sentence from combined output
    sentences = re.split(r'(?<=[.!?])\s+', combined.replace("\n", " "))
    decision = next(
        (s.strip() for s in sentences if len(s.strip()) > 20),
        title_raw[:120]
    )

    # Rationale: pull from description or first bullet if available
    rationale = description[:200] if description else "Derived from session output."

    # Outcome: pull from approval comment if present, else last sentence of output
    if approval_text:
        outcome_sentences = re.split(r'(?<=[.!?])\s+', approval_text.replace("\n", " "))
        outcome = next(
            (s.strip() for s in outcome_sentences if len(s.strip()) > 15),
            "Approved by peer reviewer."
        )
    else:
        outcome = sentences[-1].strip() if sentences else "Completed."

    # Content: trimmed combined text
    content = combined[:800] if combined else description[:400]

    confidence_label, confidence_score = infer_confidence(combined + " " + approval_text)
    category = infer_category(title_raw + " " + combined)
    lesson_title = re.sub(r'^#\d+:\s*', '', title_raw)[:100]

    lessons.append({
        "agent": task.get("assigned_agent", "clau"),
        "title": lesson_title,
        "category": category,
        "content": content,
        "decision": decision[:300],
        "rationale": rationale[:300],
        "outcome": outcome[:300],
        "confidence": confidence_label,
        "confidence_score": confidence_score,
        "status": "pending_review",
        "project": "",
    })

    return lessons


# ── Top lessons prompt injection ──────────────────────────────────────────────

def write_top_lessons_file(agent: str, dry_run: bool = False):
    """
    Fetch the top 8 active lessons and write them to ~/fleet/<agent>/TOP_LESSONS.md
    so they can be prepended to the system prompt at next startup.
    """
    result = pb_get(
        'lessons/records?filter=status%3D"active"&perPage=8&sort=-confidence_score'
    )
    lessons = result.get("items", [])

    if not lessons:
        print("[summarize] No active lessons found for injection file.")
        return

    lines = [
        f"# Top Lessons — injected {TODAY}",
        "",
        "These are the highest-confidence active lessons from past sessions.",
        "Use them to avoid repeating known mistakes.",
        "",
    ]
    for i, lesson in enumerate(lessons, 1):
        lines.append(f"## {i}. {lesson.get('title', 'Untitled')}")
        lines.append(f"**Category**: {lesson.get('category', '?')}  |  "
                     f"**Confidence**: {lesson.get('confidence', '?')} "
                     f"({lesson.get('confidence_score', 0)})")
        lines.append("")
        content = lesson.get("content", "").strip()
        if content:
            lines.append(content[:400])
        decision = lesson.get("decision", "").strip()
        if decision:
            lines.append(f"\n**Decision**: {decision[:200]}")
        outcome = lesson.get("outcome", "").strip()
        if outcome:
            lines.append(f"**Outcome**: {outcome[:200]}")
        lines.append("")

    output_path = FLEET_ROOT / agent / "TOP_LESSONS.md"
    if dry_run:
        print(f"[DRY RUN] Would write {len(lessons)} lessons to {output_path}")
        print("\n".join(lines[:30]))
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines))
        print(f"[summarize] Wrote {len(lessons)} active lessons to {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Post-session lesson extractor")
    parser.add_argument("--agent", default="clau", help="Agent name (default: clau)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be posted without writing to PocketBase")
    args = parser.parse_args()

    agent = args.agent.lower()
    dry_run = args.dry_run
    log_path = LOGS_DIR / f"{agent}.log"

    print(f"[summarize] Agent: {agent} | Date: {TODAY} | Dry-run: {dry_run}")

    # Phase A: Discover today's tasks from PocketBase
    tasks = get_today_tasks_for_agent(agent)
    print(f"[summarize] Found {len(tasks)} tasks updated today for {agent}")

    # Phase B: Also scan log for any IDs we might have missed
    log_ids = extract_task_ids_from_log(log_path)
    print(f"[summarize] Extracted {len(log_ids)} potential IDs from log")

    # Phase C: Extract and post lessons
    total_new = 0
    total_skipped = 0

    for task in tasks:
        task_id = task.get("id", "")
        task_title = task.get("title", "?")
        comments = get_comments_for_task(task_id)
        lesson_candidates = extract_lessons_from_task(task, comments)

        for lesson in lesson_candidates:
            lesson_title = lesson["title"]

            if dry_run:
                print(f"\n[DRY RUN] Lesson: {lesson_title}")
                print(f"  Category: {lesson['category']} | Confidence: {lesson['confidence']} ({lesson['confidence_score']})")
                print(f"  Decision: {lesson['decision'][:80]}...")
                continue

            if lesson_exists(lesson_title):
                print(f"[summarize] SKIP (exists): {lesson_title}")
                total_skipped += 1
                continue

            result = pb_post("lessons", lesson)
            if "error" in result:
                print(f"[summarize] ERROR posting lesson '{lesson_title}': {result['error']}")
            else:
                print(f"[summarize] NEW lesson posted: {lesson_title} [{result.get('id', '?')}]")
                total_new += 1

    # Phase D: Write TOP_LESSONS.md for prompt injection
    write_top_lessons_file(agent, dry_run=dry_run)

    print(f"\n[summarize] Done. New lessons: {total_new} | Skipped (dupes): {total_skipped}")


if __name__ == "__main__":
    main()
