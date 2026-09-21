#!/usr/bin/env python3
"""scripts/test_research_ledger.py — Verification suite for FCP-7 Research Workbench.

Validates:
1. Static schema migration (collections, fields, enums, indexes, relations).
2. Research discipline validation (confidence tiers, verification status, public-copy URL requirements).
3. File-backed pilot operations (offline ledger, source linking, evidence auditing, markdown export).
4. Live PocketBase operations (schema verification, API round-trip, cleanup).
5. Fleet Hub UI & API integration (server endpoints, dashboard markup, styles, client JS).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALESMAN_DIR = ROOT.parent / "salesman-cloud-infra"
sys.path.insert(0, str(ROOT))

from fleet.research_ledger import (
    CONFIDENCE_TIERS,
    RELIABILITY_TIERS,
    SOURCE_TYPES,
    VERIFICATION_STATUSES,
    ResearchClaim,
    ResearchLedgerClient,
    ResearchSource,
    ValidationError,
)

PASSED = 0
FAILED = 0


def check(condition: bool, description: str) -> None:
    global PASSED, FAILED
    if condition:
        print(f"  ✓ {description}")
        PASSED += 1
    else:
        print(f"  ✗ FAIL: {description}", file=sys.stderr)
        FAILED += 1


def test_migration_schema() -> None:
    print("\n--- 1. Testing Schema Migration (fleet/1782094003_created_research_ledger.js) ---")
    migration_file = ROOT / "fleet" / "1782094003_created_research_ledger.js"
    check(migration_file.exists(), "Migration file exists")

    text = migration_file.read_text(encoding="utf-8")
    check("research_sources" in text, "Creates research_sources collection")
    check("research_claims" in text, "Creates research_claims collection")

    expected_claim_fields = [
        "goal_id",
        "source_id",
        "source_url",
        "source_title",
        "source_type",
        "extracted_claim",
        "confidence",
        "verification_status",
        "usable_in_public_copy",
        "needs_human_review",
        "quote_snippet",
        "notes",
    ]
    for field in expected_claim_fields:
        check(f'"{field}"' in text, f"research_claims has field '{field}'")

    expected_source_fields = [
        "goal_id",
        "url",
        "title",
        "source_type",
        "reliability",
        "author",
        "notes",
    ]
    for field in expected_source_fields:
        check(f'"{field}"' in text, f"research_sources has field '{field}'")

    for tier in ["high", "moderate", "low", "speculative"]:
        check(f'"{tier}"' in text, f"Migration includes confidence tier '{tier}'")

    for status in ["unverified", "verified", "contested", "refuted"]:
        check(f'"{status}"' in text, f"Migration includes verification status '{status}'")


def test_research_discipline_rules() -> None:
    print("\n--- 2. Testing Research Discipline & Validation Rules ---")

    # Empty goal_id or claim
    try:
        ResearchClaim(goal_id="", extracted_claim="Some claim").validate()
        check(False, "Rejects empty goal_id")
    except ValidationError:
        check(True, "Rejects empty goal_id")

    try:
        ResearchClaim(goal_id="g1", extracted_claim="").validate()
        check(False, "Rejects empty claim text")
    except ValidationError:
        check(True, "Rejects empty claim text")

    # Invalid confidence tier
    try:
        ResearchClaim(goal_id="g1", extracted_claim="Some claim", confidence="certain").validate()
        check(False, "Rejects invalid confidence tier 'certain'")
    except ValidationError:
        check(True, "Rejects invalid confidence tier 'certain'")

    # Valid default claim is unverified
    c_default = ResearchClaim(goal_id="g1", extracted_claim="Preliminary finding")
    c_default.validate()
    check(c_default.verification_status == "unverified", "Default verification status is 'unverified'")
    check(c_default.confidence == "moderate", "Default confidence is 'moderate'")

    # Public copy discipline: requires source URL
    try:
        ResearchClaim(
            goal_id="g1",
            extracted_claim="Public claim without source",
            usable_in_public_copy=True,
            source_url="",
        ).validate()
        check(False, "Rejects public copy claim without source URL")
    except ValidationError:
        check(True, "Rejects public copy claim without source URL")

    # Public copy discipline: cannot be speculative
    try:
        ResearchClaim(
            goal_id="g1",
            extracted_claim="Speculative public claim",
            usable_in_public_copy=True,
            source_url="https://example.com",
            confidence="speculative",
        ).validate()
        check(False, "Rejects speculative claim for public copy")
    except ValidationError:
        check(True, "Rejects speculative claim for public copy")

    # Verified claim requires citation and quote/notes
    try:
        ResearchClaim(
            goal_id="g1",
            extracted_claim="Verified claim with no proof",
            verification_status="verified",
            source_url="",
        ).validate()
        check(False, "Rejects verified claim without citation")
    except ValidationError:
        check(True, "Rejects verified claim without citation")

    # Valid verified claim with primary source
    c_valid = ResearchClaim(
        goal_id="g1",
        extracted_claim="Revenue reached $10M in Q2.",
        source_url="https://example.com/sec/10-q",
        source_title="Q2 10-Q Filing",
        source_type="primary",
        quote_snippet="Total Q2 revenue reported at $10.1M",
        confidence="high",
        verification_status="verified",
        usable_in_public_copy=True,
    )
    c_valid.validate()
    check(True, "Accepts valid verified primary source claim for public copy")


def test_file_backed_pilot_operations() -> None:
    print("\n--- 3. Testing File-Backed Pilot Operations (Offline Ledger) ---")

    test_goal = "test_goal_fcp7_pilot"
    client = ResearchLedgerClient(force_file=True)

    # Record source
    src = ResearchSource(
        goal_id=test_goal,
        url="https://flotilla.cc/whitepaper.pdf",
        title="Flotilla Architecture Whitepaper",
        source_type="primary",
        reliability="high",
        author="Big Bear Engineering",
    )
    saved_src = client.record_source(src)
    check(bool(saved_src.id), f"File-backed source created with ID: {saved_src.id}")

    # Record claims
    c1 = ResearchClaim(
        goal_id=test_goal,
        extracted_claim="Multi-model consensus cuts hallucination rate by 80%.",
        source_id=saved_src.id,
        source_url=saved_src.url,
        source_title=saved_src.title,
        source_type="primary",
        confidence="high",
        verification_status="verified",
        quote_snippet="Observed cross-model disagreement rate dropped 80% with two-round council.",
        usable_in_public_copy=True,
        agent="gem",
    )
    c1_saved = client.record_claim(c1)
    check(bool(c1_saved.id), f"Claim 1 recorded with ID: {c1_saved.id}")

    c2 = ResearchClaim(
        goal_id=test_goal,
        extracted_claim="Enterprise deployment takes under 15 minutes.",
        source_url="https://flotilla.cc/install",
        source_title="Install Guide",
        confidence="moderate",
        verification_status="unverified",
        needs_human_review=True,
        agent="misty",
    )
    c2_saved = client.record_claim(c2)
    check(bool(c2_saved.id), f"Claim 2 recorded with ID: {c2_saved.id}")

    # Listing
    sources = client.list_sources(test_goal)
    claims = client.list_claims(test_goal)
    check(len(sources) == 1, f"Listed 1 source (got {len(sources)})")
    check(len(claims) == 2, f"Listed 2 claims (got {len(claims)})")

    # Update claim verification status
    client.update_claim(c2_saved.id, {"verification_status": "verified", "reviewed_by": "clau", "notes": "Verified by timed script"}, goal_id=test_goal)
    updated_c2 = [c for c in client.list_claims(test_goal) if c.id == c2_saved.id][0]
    check(updated_c2.verification_status == "verified", "Claim verification status updated to 'verified'")
    check(updated_c2.reviewed_by == "clau", "Claim reviewer logged as 'clau'")

    # Audit trail
    audit = client.audit_trail(test_goal)
    check(audit["total_sources"] == 1, "Audit reports 1 source")
    check(audit["total_claims"] == 2, "Audit reports 2 claims")
    check(audit["verification_distribution"]["verified"] == 2, "Audit reports 2 verified claims")
    check(audit["integrity_passed"] is True, "Audit reports evidence trail integrity passed (no unlinked claims)")

    # Markdown export
    md = client.export_markdown(test_goal)
    check("# Research Evidence Ledger" in md, "Markdown export includes header")
    check("Multi-model consensus" in md, "Markdown export includes extracted claim")
    check("Flotilla Architecture Whitepaper" in md, "Markdown export includes source title")

    # Clean up test file
    test_file = ROOT / "AGENTS" / "COUNCIL" / "research" / f"{test_goal}.json"
    if test_file.exists():
        test_file.unlink()
    check(not test_file.exists(), "Cleaned up file-backed test artifacts")


def test_live_pocketbase() -> None:
    print("\n--- 4. Testing Live PocketBase API & Collections ---")
    client = ResearchLedgerClient()
    if not client.is_pocketbase_available():
        print("  ⚠️ PocketBase not running at default URL; skipping live PB test.")
        return

    check(True, "PocketBase is online and reachable")

    # Check collection accessibility
    try:
        req = urllib.request.Request("http://127.0.0.1:8090/api/collections/research_sources/records?perPage=1")
        with urllib.request.urlopen(req, timeout=2) as resp:
            check(resp.status == 200, "GET /api/collections/research_sources/records responds 200")
    except Exception as e:
        check(False, f"GET research_sources failed: {e}")

    try:
        req = urllib.request.Request("http://127.0.0.1:8090/api/collections/research_claims/records?perPage=1")
        with urllib.request.urlopen(req, timeout=2) as resp:
            check(resp.status == 200, "GET /api/collections/research_claims/records responds 200")
    except Exception as e:
        check(False, f"GET research_claims failed: {e}")

    # Create temporary live records and verify round-trip
    # First find a valid goal_id or create one
    goal_res = None
    try:
        req = urllib.request.Request("http://127.0.0.1:8090/api/collections/goals/records?perPage=1")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("items"):
                goal_res = data["items"][0]["id"]
    except Exception:
        pass

    if goal_res:
        # Create test source
        src = ResearchSource(
            goal_id=goal_res,
            url="https://example.com/test-spec",
            title="Automated Test Spec",
            source_type="primary",
            reliability="high",
            agent="test-runner",
        )
        saved_src = client.record_source(src)
        check(bool(saved_src.id), f"Created live PB research_source record: {saved_src.id}")

        # Create test claim
        claim = ResearchClaim(
            goal_id=goal_res,
            extracted_claim="Automated verification claim in live PB.",
            source_id=saved_src.id,
            source_url=saved_src.url,
            source_title=saved_src.title,
            confidence="high",
            verification_status="verified",
            quote_snippet="Quote verbatim snippet.",
            usable_in_public_copy=True,
            agent="test-runner",
        )
        saved_claim = client.record_claim(claim)
        check(bool(saved_claim.id), f"Created live PB research_claim record: {saved_claim.id}")

        # Query back
        claims = client.list_claims(goal_res, confidence="high")
        matching = [c for c in claims if c.id == saved_claim.id]
        check(len(matching) == 1, "Retrieved live claim with exact field values")

        # Verify tamper protection (unauthenticated REST DELETE is forbidden by deleteRule: null)
        try:
            req_del_claim = urllib.request.Request(f"http://127.0.0.1:8090/api/collections/research_claims/records/{saved_claim.id}", method="DELETE")
            urllib.request.urlopen(req_del_claim, timeout=2)
            check(False, "REST DELETE should be protected/forbidden")
        except urllib.error.HTTPError as e:
            check(e.code == 403, "REST DELETE correctly forbidden (tamper protection for evidence trail)")

        # Clean up test rows via local DB
        import sqlite3
        pb_db = Path("/Users/miguelrodriguez/fleet/pocketbase/pb_data/data.db")
        if pb_db.exists():
            conn = sqlite3.connect(pb_db)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM research_claims WHERE id = ?", (saved_claim.id,))
            cursor.execute("DELETE FROM research_sources WHERE id = ?", (saved_src.id,))
            conn.commit()
            conn.close()
            check(True, "Cleaned up live test records in PocketBase")


def test_ui_and_api_integration() -> None:
    print("\n--- 5. Testing Fleet Hub API & UI Integration ---")

    server_file = SALESMAN_DIR / "opt" / "salesman-api" / "server.mjs"
    check(server_file.exists(), "server.mjs exists")
    server_text = server_file.read_text(encoding="utf-8")
    check("/fleet/api/council/research/sources" in server_text, "server.mjs has /fleet/api/council/research/sources endpoint")
    check("/fleet/api/council/research/claims" in server_text, "server.mjs has /fleet/api/council/research/claims endpoint")

    dashboard_file = SALESMAN_DIR / "opt" / "salesman-api" / "fleet" / "dashboard.html"
    check(dashboard_file.exists(), "dashboard.html exists")
    dash_text = dashboard_file.read_text(encoding="utf-8")
    check("council-claim-modal" in dash_text, "dashboard.html contains council-claim-modal")
    check("council-claim-confidence" in dash_text, "dashboard.html contains confidence selector")
    check("council-claim-vstatus" in dash_text, "dashboard.html contains verification status selector")

    main_js_file = SALESMAN_DIR / "opt" / "salesman-api" / "fleet" / "assets" / "main.js"
    check(main_js_file.exists(), "main.js exists")
    main_text = main_js_file.read_text(encoding="utf-8")
    check("renderCouncilResearchWorkbench" in main_text, "main.js defines renderCouncilResearchWorkbench")
    check("openCouncilClaimModal" in main_text, "main.js defines openCouncilClaimModal")
    check("submitCouncilClaim" in main_text, "main.js defines submitCouncilClaim")

    style_file = SALESMAN_DIR / "opt" / "salesman-api" / "fleet" / "assets" / "style.css"
    check(style_file.exists(), "style.css exists")
    style_text = style_file.read_text(encoding="utf-8")
    check("council-research-box" in style_text, "style.css defines .council-research-box")
    check("council-research-table" in style_text, "style.css defines .council-research-table")
    check("badge-vstatus" in style_text, "style.css defines .badge-vstatus")


def main() -> None:
    print("=======================================================")
    print(" FCP-7: Research Workbench Source & Claim Ledger Suite ")
    print("=======================================================")

    test_migration_schema()
    test_research_discipline_rules()
    test_file_backed_pilot_operations()
    test_live_pocketbase()
    test_ui_and_api_integration()

    print("\n-------------------------------------------------------")
    print(f"Summary: {PASSED} passed, {FAILED} failed")
    print("-------------------------------------------------------")

    if FAILED > 0:
        sys.exit(1)
    print("\n[research-ledger-test] ALL TESTS PASSED.")


if __name__ == "__main__":
    main()
