#!/usr/bin/env python3
"""FCP-5 verification test for Council Room UI and API endpoints.

Tests:
1. Server.mjs startup and availability on test port (8788).
2. Council goals API (validation, creation, retrieval, filtering).
3. Deliberation rounds API (Round 1 & 2 across agents, confidence tiers).
4. Decision brief API (synthesized brief with agreements, disagreements, risks, questions).
5. Human approval workflow API (actions: request_changes, reject, approve).
6. Frontend static asset inspection (dashboard.html, style.css, main.js).
7. PocketBase comment logging verification.
8. Full cleanup of test entities.

Usage:
    python3 scripts/test_council_ui_api.py
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
SERVER_PORT = 8788
API_BASE = f"http://127.0.0.1:{SERVER_PORT}/fleet/api/council"

created_goal_ids = []
created_brief_ids = []
created_delib_ids = []
created_task_ids = []


def check(condition: bool, message: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    if not condition:
        cleanup()
        sys.exit(1)


def cleanup() -> None:
    print("\n[Cleanup] Removing test entities...")
    for tid in created_task_ids:
        try:
            # Delete comments for task first
            r = requests.get(f"{PB_URL}/collections/comments/records", params={"filter": f'task_id="{tid}"'}, timeout=5)
            for c in r.json().get("items", []):
                requests.delete(f"{PB_URL}/collections/comments/records/{c['id']}", timeout=5)
            requests.delete(f"{PB_URL}/collections/tasks/records/{tid}", timeout=5)
        except Exception:
            pass
    for did in created_delib_ids:
        try:
            requests.delete(f"{PB_URL}/collections/deliberations/records/{did}", timeout=5)
        except Exception:
            pass
    for bid in created_brief_ids:
        try:
            requests.delete(f"{PB_URL}/collections/decision_briefs/records/{bid}", timeout=5)
        except Exception:
            pass
    for gid in created_goal_ids:
        try:
            requests.delete(f"{PB_URL}/collections/goals/records/{gid}", timeout=5)
        except Exception:
            pass
    print("  Cleanup complete.")


def test_frontend_assets() -> None:
    print("\n[1] Verifying frontend static assets...")
    dash_html = (SALESMAN_DIR / "fleet" / "dashboard.html").read_text(encoding="utf-8")
    style_css = (SALESMAN_DIR / "fleet" / "assets" / "style.css").read_text(encoding="utf-8")
    main_js = (SALESMAN_DIR / "fleet" / "assets" / "main.js").read_text(encoding="utf-8")

    # 1. Dashboard HTML
    check('data-section-button="section-council"' in dash_html, "Council Room nav button in dashboard.html")
    check('id="section-council"' in dash_html, "#section-council present in dashboard.html")
    check('id="council-view-container"' in dash_html, "#council-view-container present")
    check('id="goal-intake-modal"' in dash_html, "#goal-intake-modal present")
    check('id="council-action-modal"' in dash_html, "#council-action-modal present")

    # 2. Styles
    check('.council-agent-card' in style_css, ".council-agent-card styling defined")
    check('.highlight-agreement' in style_css, ".highlight-agreement styling defined")
    check('.highlight-disagreement' in style_css, ".highlight-disagreement styling defined (never averaged away)")
    check('.highlight-questions' in style_css, ".highlight-questions styling defined")
    check('.highlight-risks' in style_css, ".highlight-risks styling defined")
    check('.highlight-verification' in style_css, ".highlight-verification styling defined")
    check('.btn-approve' in style_css, ".btn-approve styling defined")
    check('.btn-reject' in style_css, ".btn-reject styling defined")
    check('.btn-request-changes' in style_css, ".btn-request-changes styling defined")

    # 3. Main JS
    check('loadCouncilRoom' in main_js, "loadCouncilRoom function defined in main.js")
    check('renderCouncilGoal' in main_js, "renderCouncilGoal function defined in main.js")
    check('submitCouncilAction' in main_js, "submitCouncilAction function defined in main.js")
    check('openGoalIntakeModal' in main_js, "openGoalIntakeModal function defined in main.js")
    check('btn-approve' in main_js, "Approval button wiring in main.js")


def test_api_server() -> None:
    print("\n[2] Starting server.mjs on test port...")
    env = os.environ.copy()
    env["SALESMAN_API_PORT"] = str(SERVER_PORT)
    env["POCKETBASE_URL"] = "http://127.0.0.1:8090"

    server_proc = subprocess.Popen(
        ["/opt/homebrew/bin/node", str(SALESMAN_DIR / "server.mjs")],
        cwd=str(SALESMAN_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to listen
    time.sleep(1.5)

    try:
        # Check health/reachability
        r = requests.get(f"http://127.0.0.1:{SERVER_PORT}/fleet/api/agent-stats", timeout=5)
        check(r.status_code == 200, f"server.mjs responding on port {SERVER_PORT}")

        print("\n[3] Testing Goal API validation...")
        # Missing title
        r = requests.post(f"{API_BASE}/goals", json={"goal": "x", "success_criteria": "y"}, timeout=5)
        check(r.status_code == 400 and "title" in r.text, "Goal creation rejects missing title")

        # Missing goal description
        r = requests.post(f"{API_BASE}/goals", json={"title": "x", "success_criteria": "y"}, timeout=5)
        check(r.status_code == 400 and "goal description" in r.text, "Goal creation rejects missing goal")

        # Missing success criteria
        r = requests.post(f"{API_BASE}/goals", json={"title": "x", "goal": "y"}, timeout=5)
        check(r.status_code == 400 and "success_criteria" in r.text, "Goal creation rejects missing success_criteria")

        print("\n[4] Creating test goal...")
        goal_payload = {
            "title": "[FCP-5 Test] Autonomous Knowledge Graph Indexing",
            "status": "council_open",
            "goal": "Build an incremental knowledge graph indexer across all fleet documentation.",
            "why_now": "Rapid fleet expansion requires cross-repo context retrieval.",
            "constraints": "Zero cloud LLM API cost for extraction; must run on Mac Mini M4.",
            "success_criteria": "Indexes 500 documents under 60 seconds with <500MB RAM.",
            "output_type": "code",
            "allow_internet_research": True,
            "owner": "miguel",
        }
        r = requests.post(f"{API_BASE}/goals", json=goal_payload, timeout=5)
        if r.status_code != 201:
            print(f"DEBUG: Goal creation failed with status {r.status_code}, response: {r.text}")
        check(r.status_code == 201, f"Goal created successfully (status {r.status_code})")
        goal_res = r.json()
        goal_id = goal_res["record"]["id"]
        created_goal_ids.append(goal_id)
        check(goal_res["record"]["title"] == goal_payload["title"], "Goal record title matches")

        # Test GET /goals/:id
        r = requests.get(f"{API_BASE}/goals/{goal_id}", timeout=5)
        check(r.status_code == 200 and r.json()["goal"]["id"] == goal_id, "GET /goals/:id returns goal")

        # Test GET /goals list
        r = requests.get(f"{API_BASE}/goals?status=council_open", timeout=5)
        check(r.status_code == 200, "GET /goals?status=council_open returns 200")
        items = r.json().get("items", [])
        check(any(it["id"] == goal_id for it in items), "New goal present in list query")

        print("\n[5] Testing Deliberations API (Rounds 1 & 2)...")
        # Round 1 - Clau (architecture proposal)
        r1_clau = {
            "goal_id": goal_id,
            "agent": "clau",
            "round": 1,
            "role": "architect",
            "recommendation": "Use SQLite FTS5 + BM25 ranking paired with local MLX mini-embeddings.",
            "risks": "Index corruption if parallel writes occur during ingest.",
            "rejected_options": "Graph database like Neo4j (too heavy for Mac Mini memory budget).",
            "open_questions": "Will documents contain binary PDFs or only Markdown?",
            "evidence_needed": "Benchmark SQLite FTS5 on 10,000 Markdown files.",
            "confidence": "high",
        }
        r = requests.post(f"{API_BASE}/deliberations", json=r1_clau, timeout=5)
        check(r.status_code == 201, "Round 1 Clau deliberation posted")
        created_delib_ids.append(r.json()["record"]["id"])

        # Round 1 - Codi (implementation proposal)
        r1_codi = {
            "goal_id": goal_id,
            "agent": "codi",
            "round": 1,
            "role": "executor",
            "recommendation": "Pure Python pipeline with LanceDB and uv for lightning fast initialization.",
            "risks": "LanceDB C-bindings may cause installation friction on Apple Silicon.",
            "rejected_options": "ChromaDB (heavy footprint).",
            "open_questions": "Should incremental watch use fsevents or watchdog?",
            "evidence_needed": "Measure cold start import time.",
            "confidence": "moderate",
        }
        r = requests.post(f"{API_BASE}/deliberations", json=r1_codi, timeout=5)
        if r.status_code != 201:
            print(f"DEBUG: Codi deliberation failed: {r.status_code} {r.text}")
        check(r.status_code == 201, "Round 1 Codi deliberation posted")
        created_delib_ids.append(r.json()["record"]["id"])

        # Round 2 - Critiques and Revisions
        r2_gem = {
            "goal_id": goal_id,
            "agent": "gem",
            "round": 2,
            "role": "skeptic",
            "recommendation": "Agree with SQLite FTS5 baseline; critique LanceDB dependency as non-standard in fleet.",
            "risks": "Watchdog polling cpu usage if large directories are scanned.",
            "rejected_options": "LanceDB.",
            "open_questions": "Confirm with Miguel if PDF extraction is required in v1.",
            "evidence_needed": "Validate against existing documentation corpus.",
            "confidence": "high",
        }
        r = requests.post(f"{API_BASE}/deliberations", json=r2_gem, timeout=5)
        check(r.status_code == 201, "Round 2 Gem deliberation posted")
        created_delib_ids.append(r.json()["record"]["id"])

        # Query deliberations for goal
        r = requests.get(f"{API_BASE}/deliberations?goal_id={goal_id}", timeout=5)
        check(r.status_code == 200, "GET /deliberations returns 200")
        delibs = r.json().get("items", [])
        check(len(delibs) == 3, f"Expected 3 deliberations, got {len(delibs)}")

        print("\n[6] Testing Synthesized Decision Brief API...")
        brief_payload = {
            "goal_id": goal_id,
            "status": "waiting_human",
            "summary": "Implement incremental documentation indexer using SQLite FTS5.",
            "recommended_approach": "Build lightweight Python tool under fleet/indexer.py using SQLite FTS5.",
            "agreement": "All agents agree on zero cloud LLM cost and Mac Mini M4 local execution.",
            "disagreement": "Clau advocated pure FTS5; Codi proposed LanceDB vector store. Synthesizer selected FTS5 for v1.",
            "rejected_alternatives": "LanceDB, Neo4j, ChromaDB.",
            "known_risks": "File locks on simultaneous writes from multiple agent sessions.",
            "open_questions_for_miguel": "Should we include ~/Downloads PDF files or strictly git Markdown docs?",
            "ticket_plan": [
                {"title": "FTS-1: SQLite schema and FTS5 virtual table", "assigned_agent": "codi", "estimate_hours": 3},
                {"title": "FTS-2: Markdown parser and incremental tokenizer", "assigned_agent": "clau", "estimate_hours": 4},
                {"title": "FTS-3: Fleet Hub search integration and CLI", "assigned_agent": "gem", "estimate_hours": 3}
            ],
            "definition_of_done": "500 docs indexed in <60s with full test coverage.",
            "review_assignments": [
                {"ticket": "FTS-1", "reviewer": "clau"},
                {"ticket": "FTS-2", "reviewer": "gem"},
                {"ticket": "FTS-3", "reviewer": "codi"}
            ],
            "created_by": "clau",
        }
        r = requests.post(f"{API_BASE}/decision-briefs", json=brief_payload, timeout=5)
        check(r.status_code == 201, "Decision brief created successfully")
        brief_id = r.json()["record"]["id"]
        created_brief_ids.append(brief_id)

        # Retrieve decision brief
        r = requests.get(f"{API_BASE}/decision-briefs?goal_id={goal_id}", timeout=5)
        check(r.status_code == 200, "GET /decision-briefs returns 200")
        briefs = r.json().get("items", [])
        check(len(briefs) >= 1 and briefs[0]["id"] == brief_id, "Brief retrieved successfully")

        # Create a council synthesis task linked to this goal (simulating coordinator task)
        task_r = requests.post(f"{PB_URL}/collections/tasks/records", json={
            "title": f"[Council Synthesis] {goal_payload['title']}",
            "status": "peer_review",
            "goal_id": goal_id,
            "assigned_agent": "clau",
            "description": "Council synthesis task for FCP-5 test.",
        }, timeout=5)
        check(task_r.status_code == 200, "Council synthesis task created in PocketBase")
        council_task_id = task_r.json()["id"]
        created_task_ids.append(council_task_id)

        print("\n[7] Testing Human Approval Workflow Actions...")
        # Action 1: request_changes
        r = requests.post(f"{API_BASE}/decision-briefs/{brief_id}/action", json={
            "action": "request_changes",
            "note": "Please ensure Markdown frontmatter tags are indexed separately."
        }, timeout=5)
        check(r.status_code == 200, "Action request_changes returns 200")
        action_res = r.json()
        check(action_res["brief"]["status"] == "waiting_human", "Brief remains waiting_human after request_changes")
        check("Markdown frontmatter tags" in action_res["brief"]["open_questions_for_miguel"],
              "Note appended to open_questions_for_miguel")

        # Action 2: reject
        r = requests.post(f"{API_BASE}/decision-briefs/{brief_id}/action", json={
            "action": "reject",
            "note": "Testing rejection flow."
        }, timeout=5)
        check(r.status_code == 200, "Action reject returns 200")
        check(r.json()["brief"]["status"] == "rejected", "Brief status is rejected")
        check(r.json()["goal"]["status"] == "rejected", "Goal status is rejected")

        # Action 3: approve
        r = requests.post(f"{API_BASE}/decision-briefs/{brief_id}/action", json={
            "action": "approve",
            "note": "Approved for ticket breakdown in FCP-6."
        }, timeout=5)
        check(r.status_code == 200, "Action approve returns 200")
        check(r.json()["brief"]["status"] == "approved", "Brief status is approved")
        check(r.json()["brief"]["approved_by"] == "miguel", "Brief approved_by is miguel")
        check(r.json()["goal"]["status"] == "approved", "Goal status is approved")

        # Verify comment logged in PocketBase comments collection
        comm_r = requests.get(f"{PB_URL}/collections/comments/records", params={
            "filter": f'task_id="{council_task_id}"',
            "sort": "-created",
            "perPage": 5
        }, timeout=5)
        check(comm_r.status_code == 200, "Comments query succeeded")
        comments = comm_r.json().get("items", [])
        check(len(comments) >= 1, "Approval comment was logged to PocketBase comments collection")
        check("FCP-6" in comments[0]["content"], "Comment content contains approval note")

        print("\n=== ALL Council UI and API verification tests PASSED! ===")

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()
        cleanup()


def main() -> None:
    print("=== Council Room UI & API (FCP-5) Verification ===")
    test_frontend_assets()
    test_api_server()


if __name__ == "__main__":
    main()
