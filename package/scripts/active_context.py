#!/usr/bin/env python3
"""
fleet/active_context.py
-----------------------
Resolves the active project's context paths for the current fleet session.

Run from the repo root after the heartbeat check passes (exit 0).
Prints the files agents should read to orient themselves to the active project.

Usage:
    python fleet/active_context.py

Output example (hub is active):
    Active project : Agentic Fleet Hub (Flotilla)
    Mission Control: MISSION_CONTROL.md
    Inbox          : AGENTS/MESSAGES/inbox.json
    Lessons (global): AGENTS/LESSONS/ledger.json

Output example (external project is active):
    Active project : Music Video Tool
    Mission Control: ../music-video-tool/MISSION_CONTROL.md  [exists]
    Inbox          : AGENTS/MESSAGES/inbox.json  (hub IAP -- always)
    Lessons (global): AGENTS/LESSONS/ledger.json
    Lessons (project): ../music-video-tool/AGENTS/LESSONS/ledger.json  [exists]
"""

import json
import os
import sys
from pathlib import Path

FLEET_META = os.path.join("AGENTS", "CONFIG", "fleet_meta.json")
HUB_MC     = "MISSION_CONTROL.md"
HUB_INBOX  = os.path.join("AGENTS", "MESSAGES", "inbox.json")
HUB_LESSONS = os.path.join("AGENTS", "LESSONS", "ledger.json")


def _exists_label(path: str) -> str:
    return "  [exists]" if os.path.exists(path) else "  [NOT FOUND -- hub fallback applies]"


def main():
    # ── Load fleet_meta ────────────────────────────────────────────────────────
    try:
        with open(FLEET_META) as f:
            meta = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[active_context] ERROR: Could not read {FLEET_META}: {e}", file=sys.stderr)
        print(f"Mission Control: {HUB_MC}")
        print(f"Inbox          : {HUB_INBOX}")
        print(f"Lessons (global): {HUB_LESSONS}")
        sys.exit(0)

    projects = meta.get("projects", [])

    # ── Find active project ────────────────────────────────────────────────────
    # Prefer first active non-hub project; fall back to hub if only hub is active
    hub_project  = None
    work_project = None

    for p in projects:
        if not p.get("is_active"):
            continue
        repo_path = p.get("repo_path", ".")
        if repo_path.strip() in (".", ""):
            hub_project = p
        else:
            if work_project is None:
                work_project = p  # first non-hub active project wins

    active = work_project or hub_project

    if not active:
        # Nothing marked active — fall back to hub
        print("[active_context] WARNING: No active project found in fleet_meta.json. Using hub defaults.")
        print(f"Active project : Agentic Fleet Hub (Flotilla) [default]")
        print(f"Mission Control: {HUB_MC}")
        print(f"Inbox          : {HUB_INBOX}")
        print(f"Lessons (global): {HUB_LESSONS}")
        sys.exit(0)

    repo_path   = active.get("repo_path", ".").strip()
    is_hub      = repo_path in (".", "")
    title       = active.get("title", "Unknown Project")

    # ── Resolve paths ──────────────────────────────────────────────────────────
    if is_hub:
        mc_path     = HUB_MC
        lessons_project = None
    else:
        mc_path     = os.path.join(repo_path, "MISSION_CONTROL.md")
        proj_lessons = os.path.join(repo_path, "AGENTS", "LESSONS", "ledger.json")
        lessons_project = proj_lessons

    # Inbox is always hub-level (IAP is fleet-wide coordination)
    inbox_path = HUB_INBOX

    # ── Print context ──────────────────────────────────────────────────────────
    print(f"Active project : {title}")
    if is_hub:
        print(f"Mission Control: {mc_path}")
    else:
        print(f"Mission Control: {mc_path}{_exists_label(mc_path)}")
        if not os.path.exists(mc_path):
            print(f"  --> Fallback  : {HUB_MC}  (use hub MC -- project has none)")

    print(f"Inbox          : {inbox_path}  (hub IAP -- always)")
    print(f"Lessons (global): {HUB_LESSONS}{_exists_label(HUB_LESSONS)}")

    if lessons_project:
        print(f"Lessons (project): {lessons_project}{_exists_label(lessons_project)}")

    if not is_hub:
        print()
        print(f"NOTE: Active project is '{title}'. Before picking up tickets:")
        print(f"  1. cd {repo_path} && git pull origin master  (pull project repo)")
        print(f"  2. Read the Mission Control at the path above.")
        print(f"  3. Write lessons to the project lessons ledger, not just the global one.")


if __name__ == "__main__":
    main()
