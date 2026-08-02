"""
Lint primitives for Flotilla publisher drafts (FLOT-109, FLOT-118).

Shared checks:
  1. No em-dash (—, U+2014)
  2. No marketing register words
  3. N-gram overlap < 40% vs any prior posted text (cross-platform)

X-specific checks (FLOT-118):
  4. No URL in hook (link-in-reply pattern)
  5. Hook ≤ 280 chars
"""

from __future__ import annotations
import re

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
X_CHAR_LIMIT = 280

# Phrases / words that disqualify a draft regardless of context.
# Keep sorted for diffability.
MARKETING_WORDS: frozenset[str] = frozenset({
    "best-in-class",
    "cutting-edge",
    "disruptive",
    "disrupting",
    "ecosystem",
    "empower",
    "empowering",
    "enterprise grade",
    "enterprise-grade",
    "excited to announce",
    "excited to share",
    "game changer",
    "game-changing",
    "groundbreaking",
    "innovative",
    "key takeaways",
    "leverage",
    "next generation",
    "next-generation",
    "pain points",
    "paradigm shift",
    "proud to announce",
    "proud to present",
    "revolutionary",
    "scalable",
    "seamless",
    "solutions",
    "state-of-the-art",
    "supercharge",
    "supercharging",
    "synergies",
    "synergy",
    "thrilled to share",
    "transformative",
    "use case",
    "use cases",
    "utilize",
    "utilise",
    "world-class",
})


def check_em_dash(text: str) -> list[str]:
    if "—" in text:
        return ["contains em-dash (—)"]
    return []


def check_marketing(text: str) -> list[str]:
    lower = text.lower()
    found = sorted(w for w in MARKETING_WORDS if w in lower)
    if found:
        return [f"marketing register: {', '.join(found[:5])}"]
    return []


def _ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    words = re.findall(r"\b\w+\b", text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def ngram_overlap(a: str, b: str, n: int = 4) -> float:
    """Jaccard similarity of 4-grams between two texts."""
    ga, gb = _ngrams(a, n), _ngrams(b, n)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def check_overlap(
    text: str, corpus: list[str], threshold: float = 0.40, n: int = 4
) -> list[str]:
    """Return failure if text overlaps >= threshold with any single corpus entry."""
    if not corpus:
        return []
    worst = max(ngram_overlap(text, c, n) for c in corpus)
    if worst >= threshold:
        return [f"n-gram overlap {worst:.0%} >= {threshold:.0%} limit"]
    return []


def check_x_no_url(text: str) -> list[str]:
    """Hook must never contain a URL (link-in-reply pattern)."""
    if _URL_RE.search(text):
        return ["hook must not contain a URL (use link-in-reply pattern)"]
    return []


def check_x_char_limit(text: str, limit: int = X_CHAR_LIMIT) -> list[str]:
    if len(text) > limit:
        return [f"hook is {len(text)} chars, limit is {limit}"]
    return []


def lint_x(hook: str, prior_texts: list[str]) -> list[str]:
    """
    Run all lint checks against an X hook draft.

    Args:
        hook: tweet text (no URL, first-person, ≤280 chars)
        prior_texts: Reddit and prior X texts for cross-platform overlap check

    Returns:
        List of failure strings. Empty = lint clean.
    """
    failures: list[str] = []
    failures += check_x_no_url(hook)
    failures += check_x_char_limit(hook)
    failures += check_em_dash(hook)
    failures += check_marketing(hook)
    failures += check_overlap(hook, prior_texts)
    return failures


def lint(title: str, body: str, prior_texts: list[str]) -> list[str]:
    """
    Run all lint checks against a draft.

    Args:
        title: chosen post title
        body: post body text
        prior_texts: list of previously-posted strings (titles + bodies) to
                     check for near-duplicate overlap

    Returns:
        List of failure strings. Empty = lint clean.
    """
    full = f"{title}\n{body}"
    failures: list[str] = []
    failures += check_em_dash(full)
    failures += check_marketing(full)
    failures += check_overlap(full, prior_texts)
    return failures
