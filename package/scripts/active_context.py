#!/usr/bin/env python3
"""
fleet/active_context.py
-----------------------
Resolves the active project's context paths for the current fleet session.

Run from the repo root after the heartbeat check passes (exit 0).
Prints the files agents should read to orient themselves to the active project(s).

Usage:
    python fleet/active_context.py

Output:
    Prints one or more blocks of project context.
    Always includes the hub as a fallback if no other projects are active.
"""

import json
import os
import sys

FLEET_META = os.path.join("AGENTS", "CONFIG", "fleet_meta.json")
HUB_MC     = "MISSION_CONTROL.md"
HUB_INBOX  = os.path.join("AGENTS", "MESSAGES", "inbox.json")
HUB_LESSONS = os.path.join("AGENTS", "LESSONS", "ledger.json")


def _exists_label(path: str) -> str:
    return "  [exists]" if os.path.exists(path) else "  [NOT FOUND -- hub fallback applies]"


def print_project_block(project: dict):
    repo_path   = project.get("repo_path", ".").strip()
    is_hub      = repo_path in (".", "")
    title       = project.get("title", "Unknown Project")

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
    print(f"--- PROJECT: {title} ---")
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
        print(f"Repo path      : {repo_path}")
        print(f"Action required: cd {repo_path} && git pull origin master")
    
    print()


def main():
    # ── Load fleet_meta ────────────────────────────────────────────────────────
    try:
        with open(FLEET_META) as f:
            meta = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[active_context] ERROR: Could not read {FLEET_META}: {e}", file=sys.stderr)
        # Absolute fallback to hub
        print_project_block({"title": "Agentic Fleet Hub (Flotilla)", "repo_path": "."})
        sys.exit(0)

    projects = meta.get("projects", [])
    active_projects = [p for p in projects if p.get("is_active") and p.get("repo_path") not in (".", "")]

    if not active_projects:
        # Fallback to hub if nothing marked active
        hub = next((p for p in projects if p.get("repo_path") in (".", "")), 
                   {"title": "Agentic Fleet Hub (Flotilla)", "repo_path": "."})
        active_projects = [hub]

    for project in active_projects:
        print_project_block(project)


if __name__ == "__main__":
    main()
