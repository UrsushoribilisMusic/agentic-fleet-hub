#!/usr/bin/env python3
"""FCP-4 verification test for Goal Intake UI and API.

Verifies:
1. Navigation entry for "Goals" in dashboard.html.
2. Goal intake form in dashboard.html containing all required fields:
   - title
   - goal
   - why now
   - deadline
   - constraints
   - success criteria
   - output type
   - allow internet research
3. Goal registry list with status badges in dashboard.html & style.css.
4. Validation rules: title, goal, and success criteria are required.
   Missing success criteria cannot be submitted silently (returns 400).
5. Goal record creation in the `goals` collection.
6. Guardrail verification: creating a goal MUST NOT create execution tasks in `tasks`.
7. Created goal is visible in list query.

Usage:
    python3 scripts/test_goal_intake_ui.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
SALESMAN_DIR = ROOT.parent / "salesman-cloud-infra" / "opt" / "salesman-api"
PB_URL = os.environ.get("POCKETBASE_URL", "http://127.0.0.1:8090/api")
SERVER_PORT = 8789
API_BASE = f"http://127.0.0.1:{SERVER_PORT}/fleet/api/council"

created_goal_ids = []


def check(condition: bool, message: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    if not condition:
        cleanup()
        sys.exit(1)


def cleanup() -> None:
    print("\n[Cleanup] Cleaning test entities...")
    for gid in created_goal_ids:
        try:
            requests.delete(f"{PB_URL}/collections/goals/records/{gid}", timeout=5)
        except Exception:
            pass
    print("  Cleanup complete.")


def test_frontend_markup() -> None:
    print("\n[1] Verifying frontend markup and assets...")
    dash_html = (SALESMAN_DIR / "fleet" / "dashboard.html").read_text(encoding="utf-8")
    style_css = (SALESMAN_DIR / "fleet" / "assets" / "style.css").read_text(encoding="utf-8")
    main_js = (SALESMAN_DIR / "fleet" / "assets" / "main.js").read_text(encoding="utf-8")

    # 1. Navigation entry
    check('data-section-button="section-goals"' in dash_html, "Goals nav button present in dashboard.html")
    check('id="section-goals"' in dash_html, "#section-goals view container present")

    # 2. Intake form and fields
    check('id="standalone-goal-intake-form"' in dash_html, "Goal intake form present")
    check('id="intake-goal-title"' in dash_html, "Title input present")
    check('id="intake-goal-body"' in dash_html, "Goal description textarea present")
    check('id="intake-goal-whynow"' in dash_html, "Why now input present")
    check('id="intake-goal-deadline"' in dash_html, "Deadline input present")
    check('id="intake-goal-constraints"' in dash_html, "Constraints textarea present")
    check('id="intake-goal-criteria"' in dash_html, "Success criteria textarea present")
    check('id="intake-goal-output-type"' in dash_html, "Output type select present")
    check('id="intake-goal-research"' in dash_html, "Allow internet research checkbox present")
    check('id="goal-intake-alert"' in dash_html, "Validation alert container present")

    # 3. Existing goals registry
    check('id="goals-registry-table"' in dash_html, "Goals registry table present")
    check('id="goals-registry-tbody"' in dash_html, "Goals registry tbody present")
    check('id="goals-status-filter"' in dash_html, "Goals status filter present")

    # 4. CSS styling
    check('.council-goals-grid' in style_css, ".council-goals-grid styling defined")
    check('.goal-status-badge' in style_css, ".goal-status-badge styling defined")
    check('.goal-status-council_open' in style_css, ".goal-status-council_open styling defined")
    check('.goal-status-waiting_human' in style_css, ".goal-status-waiting_human styling defined")
    check('.goal-status-approved' in style_css, ".goal-status-approved styling defined")

    # 5. JS application wiring
    check("targetId === 'section-goals'" in main_js, "activateSection handles section-goals")
    check("loadGoalsRegistry" in main_js, "loadGoalsRegistry function defined")
    check("submitStandaloneGoalIntake" in main_js, "submitStandaloneGoalIntake function defined")
    check("openGoalInCouncil" in main_js, "openGoalInCouncil function defined")


def test_api_server() -> None:
    print(f"\n[2] Starting server.mjs on test port {SERVER_PORT}...")
    env = os.environ.copy()
    env["SALESMAN_API_PORT"] = str(SERVER_PORT)
    env["POCKETBASE_URL"] = "http://127.0.0.1:8090"
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"

    proc = subprocess.Popen(
        ["/opt/homebrew/bin/node", str(SALESMAN_DIR / "server.mjs")],
        cwd=str(SALESMAN_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    started = False
    for _ in range(30):
        time.sleep(0.3)
        try:
            r = requests.get(f"http://127.0.0.1:{SERVER_PORT}/fleet/api/agent-stats", timeout=2)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            pass

    check(started, f"server.mjs responding on port {SERVER_PORT}")

    try:
        # 3. Validation: title, goal, and success criteria required
        print("\n[3] Testing Goal Intake validation...")
        r = requests.post(f"{API_BASE}/goals", json={"goal": "G", "success_criteria": "S"}, timeout=5)
        check(r.status_code == 400 and "title" in r.json().get("error", ""), "Rejects missing title")

        r = requests.post(f"{API_BASE}/goals", json={"title": "T", "success_criteria": "S"}, timeout=5)
        check(r.status_code == 400 and "goal" in r.json().get("error", ""), "Rejects missing goal")

        r = requests.post(f"{API_BASE}/goals", json={"title": "T", "goal": "G"}, timeout=5)
        check(r.status_code == 400 and "success_criteria" in r.json().get("error", ""), "Rejects missing success_criteria (cannot submit silently)")

        # 4. Create real goal
        print("\n[4] Creating real goal via Intake API...")
        # Get count of tasks in PocketBase before goal creation
        tasks_before = requests.get(f"{PB_URL}/collections/tasks/records", timeout=5).json().get("totalItems", 0)

        payload = {
            "title": "FCP-4 Test: Knowledge Index Intake",
            "goal": "Build dense indexing view for product intent.",
            "why_now": "Unblock multi-agent council protocol.",
            "deadline": "2026-10-15T18:00:00.000Z",
            "constraints": "No mock data; dense layout.",
            "success_criteria": "Miguel can create a real goal from dashboard and see it in goal list.",
            "output_type": "code",
            "allow_internet_research": True,
            "status": "council_open",
            "owner": "miguel",
        }
        r = requests.post(f"{API_BASE}/goals", json=payload, timeout=5)
        check(r.status_code == 201, f"Goal creation succeeded (HTTP 201), got {r.status_code}")
        data = r.json()
        rec = data.get("record", {})
        gid = rec.get("id")
        check(bool(gid), f"Received record id: {gid}")
        created_goal_ids.append(gid)
        check(rec.get("title") == payload["title"], "Goal title persisted correctly")
        check(rec.get("allow_internet_research") is True, "allow_internet_research persisted as True")
        check(rec.get("output_type") == "code", "output_type persisted as code")

        # 5. Guardrail: creating a goal must NOT create execution tasks!
        tasks_after = requests.get(f"{PB_URL}/collections/tasks/records", timeout=5).json().get("totalItems", 0)
        check(tasks_after == tasks_before, f"No execution tasks were created (before: {tasks_before}, after: {tasks_after})")

        # 6. Retrieve list and verify newly created goal is visible
        print("\n[5] Verifying created goal appears in goals list...")
        list_res = requests.get(f"{API_BASE}/goals?sort=-created", timeout=5)
        check(list_res.status_code == 200, "GET /goals returns 200")
        items = list_res.json().get("items", [])
        found = any(item.get("id") == gid for item in items)
        check(found, f"Created goal {gid} is visible in goal list")

    finally:
        print("\n[Teardown] Terminating test server...")
        proc.terminate()
        proc.wait(timeout=5)


def main() -> None:
    print("=== FCP-4: Fleet Hub Goal Intake UI & API Verification ===")
    test_frontend_markup()
    test_api_server()
    cleanup()
    print("\n=== All FCP-4 Verification Checks PASSED! ===")


if __name__ == "__main__":
    main()
