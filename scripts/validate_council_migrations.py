#!/usr/bin/env python3
"""Static smoke validation for the Council Protocol PocketBase migration.

This does not connect to PocketBase and does not create live records. It checks
that the migration file contains the expected collections, fields, enums, and
relations needed by FCP-3/FCP-4/FCP-5.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "fleet" / "1782094000_created_council_collections.js"

EXPECTED_COLLECTIONS = [
    "goals",
    "deliberations",
    "decision_briefs",
]

EXPECTED_FIELDS = {
    "goals": [
        "title",
        "status",
        "goal",
        "why_now",
        "constraints",
        "success_criteria",
        "deadline",
        "output_type",
        "allow_internet_research",
        "owner",
    ],
    "deliberations": [
        "goal_id",
        "agent",
        "round",
        "role",
        "recommendation",
        "risks",
        "rejected_options",
        "open_questions",
        "evidence_needed",
        "confidence",
    ],
    "decision_briefs": [
        "goal_id",
        "status",
        "summary",
        "recommended_approach",
        "agreement",
        "disagreement",
        "rejected_alternatives",
        "known_risks",
        "open_questions_for_miguel",
        "ticket_plan",
        "definition_of_done",
        "review_assignments",
        "created_by",
        "approved_by",
    ],
}

GOAL_STATUSES = [
    "draft",
    "council_open",
    "synthesis_ready",
    "waiting_human",
    "approved",
    "rejected",
    "ticketed",
    "closed",
]

BRIEF_STATUSES = [
    "draft",
    "waiting_human",
    "approved",
    "rejected",
    "ticketed",
]

CONFIDENCE_TIERS = [
    "high",
    "moderate",
    "low",
    "speculative",
]


def fail(message: str) -> None:
    print(f"[council-migration] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def assert_literal(text: str, literal: str, context: str) -> None:
    if literal not in text:
        fail(f"missing {context}: {literal}")


def main() -> None:
    if not MIGRATION.exists():
        fail(f"missing migration: {MIGRATION.relative_to(ROOT)}")

    text = MIGRATION.read_text(encoding="utf-8")

    assert_literal(text, "migrate((db) =>", "PocketBase up migration")
    assert_literal(text, "}, (db) =>", "PocketBase down migration")

    for collection in EXPECTED_COLLECTIONS:
        assert_literal(text, f'name: "{collection}"', f"{collection} collection")

    for collection, fields in EXPECTED_FIELDS.items():
        for field in fields:
            assert_literal(text, f'"{field}"', f"{collection}.{field} field")

    for status in GOAL_STATUSES:
        assert_literal(text, f'"{status}"', f"goals.status value {status}")

    for status in BRIEF_STATUSES:
        assert_literal(text, f'"{status}"', f"decision_briefs.status value {status}")

    for tier in CONFIDENCE_TIERS:
        assert_literal(text, f'"{tier}"', f"confidence tier {tier}")

    relation_count = len(re.findall(r'relationField\("[^"]+", "goal_id", goalsCollection\.id, true\)', text))
    if relation_count != 2:
        fail(f"expected 2 required goal_id relations, found {relation_count}")

    print("[council-migration] OK: Council PocketBase schema migration contains expected collections, fields, enums, and relations.")


if __name__ == "__main__":
    main()
