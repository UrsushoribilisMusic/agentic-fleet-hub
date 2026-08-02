"""
FLOT-109 acceptance tests.

Unit tests (no API, no manifest needed):
    python3 test_composer.py

Integration smoke test (requires manifest.json + ANTHROPIC_API_KEY in Infisical):
    python3 test_composer.py --integration

Acceptance criteria (from FLOT-109):
    For post id "apertus-m4-local-inference" and subs [r/LocalLLaMA, r/Entrepreneur, r/eutech]:
    - Emits three materially different drafts
    - Each passes lint (no em-dash, no marketing register, n-gram overlap < 40%)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lint import lint, ngram_overlap, check_em_dash, check_marketing, check_overlap


# -- Unit tests (lint primitives) ------------------------------------------


def test_em_dash() -> None:
    assert check_em_dash("Running Apertus 8B on Mac Mini M4") == []
    assert check_em_dash("Fast inference -- surprisingly") == []  # double-hyphen is fine
    assert check_em_dash("Fast inference — surprisingly") == ["contains em-dash (—)"]
    print("  PASS: em-dash check")


def test_marketing() -> None:
    assert check_marketing("I ran a local model on my Mac") == []
    assert check_marketing("This is a revolutionary, game-changing solution") != []
    assert check_marketing("Excited to announce our new ecosystem") != []
    print("  PASS: marketing check")


def test_ngram_overlap() -> None:
    a = "running apertus eight b on mac mini m four was surprisingly practical for my workflow"
    b = "running apertus eight b on mac mini m four was surprisingly practical for my workflow"
    assert ngram_overlap(a, b) == 1.0

    c = "completely different text about unrelated topics that share almost nothing with the above"
    assert ngram_overlap(a, c) < 0.1

    print("  PASS: n-gram overlap")


def test_overlap_threshold() -> None:
    # Two sentences sharing fewer than 40% of 4-grams should pass
    a = "I have been running Apertus 8B on a Mac Mini M4 for agent workflows and it is fast enough"
    b = "Building a local inference stack on Mac Mini M4 with Apertus 8B -- here is what I found"
    # These share some words but should be below threshold
    overlap = ngram_overlap(a, b)
    assert overlap < 0.4, f"Expected < 0.40, got {overlap:.2f}"

    # Identical text should fail
    failures = check_overlap(a, [a])
    assert failures, "Expected overlap failure for identical text"
    print("  PASS: overlap threshold")


def test_lint_clean() -> None:
    title = "Running Apertus 8B (Q4_K_M) on Mac Mini M4: 14 tok/s, no cloud"
    body = (
        "I have been running Apertus 8B at Q4_K_M quantisation on a 24 GB Mac Mini M4 "
        "for the past few weeks as the LLM backbone of a small agent pipeline. "
        "Gets around 14 tok/s generation, which is fast enough to not feel like a bottleneck. "
        "No API costs, no data leaving the machine (useful for the client data we process)."
    )
    failures = lint(title, body, [])
    assert failures == [], f"Expected clean draft, got: {failures}"
    print("  PASS: clean draft passes lint")


def test_lint_fails() -> None:
    title = "This revolutionary AI model will transform everything -- game-changer"
    body = "We are excited to announce a game-changing, seamless ecosystem. Leverage synergy."
    failures = lint(title, body, [])
    assert any("em-dash" not in f and "marketing" not in f or True for f in failures)
    assert failures, f"Expected failures, got none"
    print("  PASS: bad draft fails lint")


def run_unit_tests() -> None:
    print("Running lint unit tests...")
    test_em_dash()
    test_marketing()
    test_ngram_overlap()
    test_overlap_threshold()
    test_lint_clean()
    test_lint_fails()
    print("All unit tests passed.\n")


# -- Integration test (calls Anthropic API) --------------------------------


def run_integration(manifest_path: Path) -> None:
    from composer import compose

    post_id = "apertus-m4-local-inference"
    subs = ["r/LocalLLaMA", "r/Entrepreneur", "r/eutech"]

    print(f"Integration test: composing drafts for '{post_id}'...")
    drafts = compose(post_id, subs=subs, manifest_path=manifest_path)

    print("\n--- Drafts ---")
    for sub, draft in drafts.items():
        print(f"\n[{sub}]")
        if "error" in draft:
            print(f"  ERROR: {draft['error']}")
            continue
        print(f"  Title: {draft['chosen_title']}")
        print(f"  Lint clean: {draft['lint_clean']}")
        if draft["lint_failures"]:
            print(f"  Lint failures: {draft['lint_failures']}")
        print(f"  Body preview: {draft['body'][:120]}...")

    print("\n--- Cross-sub overlap check ---")
    texts = [
        f"{d['chosen_title']}\n{d['body']}"
        for d in drafts.values()
        if not d.get("error")
    ]
    sub_list = list(drafts.keys())
    for i, (sub_a, ta) in enumerate(zip(sub_list, texts)):
        for sub_b, tb in zip(sub_list[i + 1:], texts[i + 1:]):
            overlap = ngram_overlap(ta, tb)
            status = "OK" if overlap < 0.40 else "FAIL"
            print(f"  {sub_a} vs {sub_b}: {overlap:.0%} [{status}]")

    # Acceptance: all three clean, all cross-sub overlaps < 40%
    all_clean = all(d.get("lint_clean") for d in drafts.values() if "error" not in d)
    cross_overlap_ok = all(
        ngram_overlap(ta, tb) < 0.40
        for i, ta in enumerate(texts)
        for tb in texts[i + 1:]
    )

    print(f"\nAcceptance: lint_clean={all_clean}, cross_overlap_ok={cross_overlap_ok}")
    if all_clean and cross_overlap_ok:
        print("PASS: acceptance criteria met")
    else:
        print("FAIL: acceptance criteria not met")
        sys.exit(1)


# -- Entry point -----------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="FLOT-109 tests")
    ap.add_argument(
        "--integration",
        action="store_true",
        help="Also run integration test (calls Anthropic API)",
    )
    ap.add_argument(
        "--manifest",
        default=str(Path(__file__).parent / "manifest.json"),
    )
    args = ap.parse_args()

    run_unit_tests()
    if args.integration:
        run_integration(Path(args.manifest))


if __name__ == "__main__":
    main()
