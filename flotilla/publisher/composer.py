"""
FLOT-109: Post composer -- per-sub Reddit drafts.

Importable:
    from composer import compose
    drafts = compose("my-post-slug", manifest_path=Path("manifest.json"))

CLI:
    python3 composer.py --post-id my-post-slug [--subs r/LocalLLaMA r/eutech] [--manifest path] [--out drafts.json]

Input: manifest.json (FLOT-108 schema). Required fields per post:
    id, angle, body_seed, primary_sub, fallback_subs[], attempts[]

Output: {sub_name: {title_variants, chosen_title, body, lint_clean, lint_failures}}
Caller (FLOT-110 executor) owns all manifest writes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import anthropic

from lint import lint

# -- Paths -----------------------------------------------------------------

MANIFEST_PATH = Path.home() / "flotilla/publisher/manifest.json"
VAULT_SCRIPT = Path.home() / "projects/agentic-fleet-hub/vault/agent-fetch.sh"
COMPOSER_MODEL = "claude-sonnet-5"

# -- Per-sub editorial conventions -----------------------------------------

# Keys match the sub name without r/ prefix.
# "other" is the fallback for unknown subs.
SUB_CONVENTIONS: dict[str, dict[str, str]] = {
    "LocalLLaMA": {
        "title_angle": "model name, quantisation level, hardware context",
        "lead": (
            "Lead with the model (name + parameter count + quant). "
            "Include the hardware setup (Mac Mini M4, unified memory amount, "
            "context length used). Give concrete numbers: tok/s, RAM footprint, "
            "context length. Readers here are ML practitioners who will catch "
            "hand-wavy claims."
        ),
        "body_style": (
            "Technical but readable. Mention what prompted the test, "
            "what surprised you (positive or negative), and what the numbers actually were. "
            "Avoid adjectives when a number will do."
        ),
        "avoid": "hype, adjectives where numbers work, marketing",
    },
    "Entrepreneur": {
        "title_angle": "the story arc: problem you hit, what you tried, what happened",
        "lead": (
            "Open with the problem or the moment something shifted. "
            "Reader wants a before/after narrative with specific details "
            "(timeline, rough cost, how many users, what broke). "
            "Not a product announcement -- a lived experience."
        ),
        "body_style": (
            "Personal, reflective, first-person. Can end with a lesson, "
            "open question, or 'here is what I would do differently'. "
            "Medium-length paragraphs, not a listicle."
        ),
        "avoid": "technical jargon, model names unless integral to the story",
    },
    "eutech": {
        "title_angle": "EU digital sovereignty: on-device, no US cloud, GDPR-clean",
        "lead": (
            "Frame around what the setup avoids: data never leaving the device, "
            "open weights, no US-vendor lock-in, EU hosting if applicable. "
            "Mention specific architecture (on-device inference, quantised open model). "
            "Don't oversell -- concrete architecture beats buzzwords."
        ),
        "body_style": (
            "Matter-of-fact, slightly policy-aware. Reference GDPR or EU AI Act "
            "only if genuinely relevant; do not force it. One paragraph of technical "
            "architecture, one of practical implications."
        ),
        "avoid": "US-centric framing, buzzwords, anything that sounds promotional",
    },
    "other": {
        "title_angle": "the most relevant angle for the community",
        "lead": "First person, concrete, specific to what this community cares about.",
        "body_style": "Readable, no hype, specific details.",
        "avoid": "marketing language, em-dashes",
    },
}

SYSTEM_PROMPT = (
    "You are a technical writer drafting Reddit posts. "
    "You write in first person, concretely and specifically. "
    "You never use em-dashes (—). "
    "You never use marketing language "
    "(revolutionary, game-changing, excited to announce, leverage, ecosystem, "
    "disruptive, seamless, scalable, empowering, transformative, next-generation, "
    "supercharging, synergy, pain points). "
    "You prefer parenthetical asides over em-dashes. "
    "Your titles do real work: a reader skimming should understand the post "
    "without reading the body."
)

MAX_RETRIES = 2  # attempts after first try = 3 total


# -- Helpers ---------------------------------------------------------------


def _fetch_secret(key: str) -> str:
    result = subprocess.run(
        ["bash", str(VAULT_SCRIPT), key],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(
            f"Vault fetch failed for {key!r}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _prior_texts_from_manifest(manifest: dict) -> list[str]:
    """Collect titles and bodies from all previous posting attempts."""
    texts: list[str] = []
    for post in manifest.get("posts", []):
        for attempt in post.get("attempts", []):
            if t := attempt.get("draft_title"):
                texts.append(t)
            if b := attempt.get("draft_body"):
                texts.append(b)
    return texts


def _build_prompt(body_seed: str, angle: str, sub: str, retry_failures: list[str]) -> str:
    sub_key = sub.lstrip("r/")
    conv = SUB_CONVENTIONS.get(sub_key, SUB_CONVENTIONS["other"])

    failure_block = ""
    if retry_failures:
        failure_block = (
            "\n\n## Previous attempt failed lint -- fix these:\n"
            + "\n".join(f"- {f}" for f in retry_failures)
            + "\n"
        )

    return f"""Draft a Reddit post for r/{sub_key}.{failure_block}

## Seed content (do NOT copy verbatim -- reframe for this sub)
Angle: {angle}
Body seed: {body_seed}

## Sub convention for r/{sub_key}
Title angle: {conv["title_angle"]}
Lead instruction: {conv["lead"]}
Body style: {conv["body_style"]}
Avoid: {conv["avoid"]}

## Hard constraints (non-negotiable)
- NO em-dashes (—). Use commas, parentheses, or a new sentence instead.
- NO marketing language: revolutionary, game-changing, excited to announce,
  leverage, synergy, ecosystem, disruptive, seamless, scalable, empowering,
  transformative, next-generation, supercharging, solutions, pain points.
- First person throughout ("I", "we").
- Parenthetical asides are preferred over em-dashes.
- Title carries the whole load. Reader skims the title -- it must stand alone.
- Body must be materially different from other subs (different opening line,
  different framing, different paragraph structure).

## Output format (JSON only, no prose outside the JSON block)
{{
  "title_variants": [
    "<variant 0: direct statement of the main fact/event>",
    "<variant 1: question or observation angle>",
    "<variant 2: outcome or result angle>"
  ],
  "title_pick": <0, 1, or 2 -- index of variant that best fits r/{sub_key}>,
  "body": "<2-4 paragraphs, first person, no em-dashes, no marketing register>"
}}"""


def _parse_response(raw: str) -> Optional[dict]:
    text = raw.strip()
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Last resort: find first {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _pick_title(data: dict) -> str:
    variants = data.get("title_variants") or []
    if not variants:
        return ""
    pick = data.get("title_pick")
    if isinstance(pick, int) and 0 <= pick < len(variants):
        return variants[pick]
    # Fallback: first variant
    return variants[0]


# -- Public API ------------------------------------------------------------


def compose(
    post_id: str,
    *,
    subs: Optional[list[str]] = None,
    manifest_path: Path = MANIFEST_PATH,
    anthropic_api_key: Optional[str] = None,
) -> dict[str, dict]:
    """
    Generate per-sub drafts for one post.

    Returns:
        {sub_name: {"title_variants": [...], "chosen_title": str, "body": str,
                    "lint_clean": bool, "lint_failures": [str]}}

    Caller (FLOT-110) owns manifest writes. This function is read-only on the manifest.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    post = next((p for p in manifest.get("posts", []) if p["id"] == post_id), None)
    if post is None:
        raise ValueError(f"Post {post_id!r} not found in manifest")

    body_seed: str = post["body_seed"]
    angle: str = post.get("angle", "")
    target_subs: list[str] = subs or ([post["primary_sub"]] + post.get("fallback_subs", []))

    api_key = anthropic_api_key or _fetch_secret("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    # Corpus of prior posted text for overlap detection.
    # We extend this with each sub's output as we go, preventing
    # near-duplicate posts within the same run.
    prior_texts: list[str] = _prior_texts_from_manifest(manifest)

    results: dict[str, dict] = {}

    for sub in target_subs:
        print(f"  [{sub}] composing...", file=sys.stderr)
        data: Optional[dict] = None
        lint_failures: list[str] = []

        for attempt in range(MAX_RETRIES + 1):
            prompt = _build_prompt(body_seed, angle, sub, lint_failures if attempt > 0 else [])
            msg = client.messages.create(
                model=COMPOSER_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            data = _parse_response(msg.content[0].text)

            if data is None:
                print(f"  [{sub}] attempt {attempt+1}: JSON parse failed", file=sys.stderr)
                lint_failures = ["JSON parse failed"]
                continue

            title = _pick_title(data)
            body = data.get("body", "")
            lint_failures = lint(title, body, prior_texts)

            if not lint_failures:
                break
            print(
                f"  [{sub}] attempt {attempt+1}: lint failed: {lint_failures}",
                file=sys.stderr,
            )

        if data is None:
            results[sub] = {
                "sub": sub,
                "error": "failed to get parseable JSON after all attempts",
                "lint_clean": False,
                "lint_failures": lint_failures,
            }
            continue

        title = _pick_title(data)
        body = data.get("body", "")
        # Final lint uses only original prior_texts (not cross-sub additions),
        # because that's what the FLOT-109 spec checks against.
        final_failures = lint(title, body, prior_texts)

        results[sub] = {
            "sub": sub,
            "title_variants": data.get("title_variants", []),
            "chosen_title": title,
            "body": body,
            "lint_clean": len(final_failures) == 0,
            "lint_failures": final_failures,
        }

        # Cross-sub guard: add this draft to prior_texts so the NEXT sub
        # in this run cannot produce near-identical text.
        prior_texts.append(f"{title}\n{body}")

        status = "CLEAN" if not final_failures else f"LINT FAIL: {final_failures}"
        print(f"  [{sub}] {status}", file=sys.stderr)

    return results


# -- CLI -------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description="FLOT-109: Reddit post composer (per-sub drafts)"
    )
    ap.add_argument("--post-id", required=True, help="Post slug from manifest.json")
    ap.add_argument("--subs", nargs="*", help="Override subreddits (default: primary + fallbacks)")
    ap.add_argument("--manifest", default=str(MANIFEST_PATH), help="Path to manifest.json")
    ap.add_argument("--out", help="Write drafts JSON to file (default: stdout)")
    args = ap.parse_args()

    print(f"FLOT-109 composer: post='{args.post_id}'", file=sys.stderr)
    try:
        drafts = compose(
            args.post_id,
            subs=args.subs or None,
            manifest_path=Path(args.manifest),
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    out_json = json.dumps(drafts, indent=2)
    if args.out:
        Path(args.out).write_text(out_json)
        print(f"Drafts written to {args.out}", file=sys.stderr)
    else:
        print(out_json)

    clean = sum(1 for d in drafts.values() if d.get("lint_clean"))
    total = len(drafts)
    print(f"\n{clean}/{total} drafts passed lint", file=sys.stderr)
    sys.exit(0 if clean == total else 1)


if __name__ == "__main__":
    main()
