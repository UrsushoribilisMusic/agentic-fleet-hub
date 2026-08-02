"""
FLOT-118: X (Twitter) composer — hook + link-in-reply pattern.

Voice: sharp single claim; hook before the fold; first person; no em-dashes;
parentheticals fine; image does the visual work. NEVER a truncation of a Reddit
post on the same topic.

Pattern:
    hook post (text + image, NO URL)
    → capture tweet_id
    → reply-to-self with post.link
    → log both ids (handled by executor, not this module)

Importable:
    from x_composer import compose_x
    result = compose_x("my-post-slug", manifest_path=Path("manifest.json"),
                       reddit_texts=["title\\nbody", ...])

CLI:
    python3 x_composer.py --post-id my-post-slug [--manifest path]
                          [--reddit-drafts file.json] [--out draft.json]
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

from lint import lint_x

MANIFEST_PATH = Path.home() / "flotilla/publisher/manifest.json"
VAULT_SCRIPT = Path.home() / "projects/agentic-fleet-hub/vault/agent-fetch.sh"
COMPOSER_MODEL = "claude-sonnet-5"

MAX_RETRIES = 2

_X_SYSTEM_PROMPT = (
    "You are writing tweets for an X (Twitter) account about local AI and indie tech. "
    "X rewards a single sharp claim delivered before the fold. "
    "Write in first person, concretely and specifically. "
    "You never use em-dashes (—). Parenthetical asides are fine. "
    "You never use marketing language "
    "(revolutionary, game-changing, excited to announce, leverage, ecosystem, "
    "disruptive, seamless, scalable, empowering, transformative, next-generation, "
    "supercharging, synergy, pain points). "
    "The tweet is a DISTINCT take — not a truncation of any Reddit post on the same "
    "topic. Different angle, different structure, different opener. "
    "The first line is the hook. Assume an image does the visual work."
)


def _fetch_secret(key: str) -> str:
    result = subprocess.run(
        ["bash", str(VAULT_SCRIPT), key],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"Vault fetch failed for {key!r}: {result.stderr.strip()}")
    return result.stdout.strip()


def _build_prompt(body_seed: str, angle: str, retry_failures: list[str]) -> str:
    failure_block = ""
    if retry_failures:
        failure_block = (
            "\n\n## Previous attempt failed lint -- fix these:\n"
            + "\n".join(f"- {f}" for f in retry_failures)
            + "\n"
        )

    return f"""Write one tweet for X (Twitter).{failure_block}

## Seed content (find the sharpest X angle -- do NOT copy verbatim)
Angle: {angle}
Body seed: {body_seed}

## X editorial rules
- One sharp claim or observation on the first line (the hook, before the fold)
- First person throughout ("I" or "we")
- No em-dashes (—); commas, parentheses, or a new line instead
- Parenthetical asides are fine
- Assume an image accompanies the tweet -- let it carry the visual context
- Do NOT include a URL. The link goes in a reply-to-self (handled separately)
- No hashtags unless they genuinely add meaning
- Must be a DISTINCT take from any Reddit post on the same topic

## Hard constraints
- NO URLs anywhere (http, https, www -- all forbidden in the hook)
- NO em-dashes (—)
- NO marketing language: revolutionary, game-changing, excited to announce,
  leverage, synergy, ecosystem, disruptive, seamless, scalable, empowering,
  transformative, next-generation, supercharging, pain points
- Max 280 characters (count carefully)
- First sentence must work as a standalone hook

## Output format (JSON only, no prose outside the JSON block)
{{
  "hook": "<the tweet text, first-person, <=280 chars, no URL, em-dash-free>"
}}"""


def _parse_response(raw: str) -> Optional[dict]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def compose_x(
    post_id: str,
    *,
    manifest_path: Path = MANIFEST_PATH,
    reddit_texts: Optional[list[str]] = None,
    anthropic_api_key: Optional[str] = None,
) -> dict:
    """
    Generate an X hook+reply pair for one post.

    Args:
        post_id: slug from manifest.json
        manifest_path: path to manifest.json
        reddit_texts: Reddit title+body strings for cross-platform overlap check.
                      Pass compose() output to prevent duplicate n-grams.
        anthropic_api_key: override (default: fetched from Infisical)

    Returns:
        {
            "hook": str,              # tweet body, no URL, ≤280 chars
            "reply_text": str|None,   # post.link goes in the reply-to-self
            "char_count": int,
            "lint_clean": bool,
            "lint_failures": [str],
        }

    Caller owns manifest writes and Twitter API calls.
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    post = next((p for p in manifest.get("posts", []) if p["id"] == post_id), None)
    if post is None:
        raise ValueError(f"Post {post_id!r} not found in manifest")

    body_seed: str = post["body_seed"]
    angle: str = post.get("angle", "")
    reply_text: Optional[str] = post.get("link")

    api_key = anthropic_api_key or _fetch_secret("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    prior_texts: list[str] = list(reddit_texts or [])
    lint_failures: list[str] = []
    data: Optional[dict] = None

    for attempt in range(MAX_RETRIES + 1):
        print(f"  [x] composing attempt {attempt + 1}...", file=sys.stderr)
        prompt = _build_prompt(body_seed, angle, lint_failures if attempt > 0 else [])
        msg = client.messages.create(
            model=COMPOSER_MODEL,
            max_tokens=512,
            system=_X_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        data = _parse_response(msg.content[0].text)

        if data is None:
            print(f"  [x] attempt {attempt + 1}: JSON parse failed", file=sys.stderr)
            lint_failures = ["JSON parse failed"]
            continue

        hook = str(data.get("hook", "")).strip()
        lint_failures = lint_x(hook, prior_texts)

        if not lint_failures:
            break
        print(f"  [x] attempt {attempt + 1}: lint failed: {lint_failures}", file=sys.stderr)

    if data is None:
        return {
            "hook": "",
            "reply_text": reply_text,
            "char_count": 0,
            "lint_clean": False,
            "lint_failures": lint_failures or ["failed to get parseable JSON"],
        }

    hook = str(data.get("hook", "")).strip()
    final_failures = lint_x(hook, prior_texts)
    status = "CLEAN" if not final_failures else f"LINT FAIL: {final_failures}"
    print(f"  [x] {status}", file=sys.stderr)

    return {
        "hook": hook,
        "reply_text": reply_text,
        "char_count": len(hook),
        "lint_clean": len(final_failures) == 0,
        "lint_failures": final_failures,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="FLOT-118: X hook+reply composer")
    ap.add_argument("--post-id", required=True, help="Post slug from manifest.json")
    ap.add_argument("--manifest", default=str(MANIFEST_PATH), help="Path to manifest.json")
    ap.add_argument(
        "--reddit-drafts",
        help="JSON file of Reddit compose() output for cross-platform overlap check",
    )
    ap.add_argument("--out", help="Write draft JSON to file (default: stdout)")
    args = ap.parse_args()

    reddit_texts: list[str] = []
    if args.reddit_drafts:
        with open(args.reddit_drafts) as f:
            drafts = json.load(f)
        for sub_draft in drafts.values():
            title = sub_draft.get("chosen_title", "")
            body = sub_draft.get("body", "")
            if title or body:
                reddit_texts.append(f"{title}\n{body}")

    print(f"FLOT-118 X composer: post='{args.post_id}'", file=sys.stderr)
    try:
        result = compose_x(
            args.post_id,
            manifest_path=Path(args.manifest),
            reddit_texts=reddit_texts,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    out_json = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(out_json)
        print(f"Draft written to {args.out}", file=sys.stderr)
    else:
        print(out_json)

    sys.exit(0 if result.get("lint_clean") else 1)


if __name__ == "__main__":
    main()
