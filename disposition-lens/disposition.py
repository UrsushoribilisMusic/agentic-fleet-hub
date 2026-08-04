"""
Disposition classifier — maps J-space concept tokens to one of 7 dispositions.

Lexicon lookup: each token is matched against per-disposition keyword sets using
prefix matching (handles BPE fragments like "certainly" → confident).
Token weights drive a weighted vote; highest total wins. Falls back to "idle".
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

DISPOSITIONS = ("idle", "confident", "uncertain", "curious", "concern", "reluctant", "warm")

# Keyword sets per disposition (lowercase).  Matched via prefix: token.startswith(keyword).
LEXICON: Dict[str, set] = {
    "concern":   {"danger", "warning", "warn", "alert", "unsafe", "risk", "harm",
                  "critical", "severe", "urgent", "stop", "hazard"},
    "reluctant": {"cannot", "sorry", "unable", "decline", "refuse", "won't", "can't",
                  "regret", "unfortunately", "avoid"},
    "uncertain": {"maybe", "unsure", "perhaps", "possibly", "might", "unclear",
                  "uncertain", "probably", "likely", "approximately"},
    "warm":      {"great", "done", "wonderful", "excellent", "perfect", "happy", "glad",
                  "thanks", "good", "nice", "awesome", "love", "fantastic"},
    "confident": {"certain", "yes", "definitely", "absolutely", "sure", "confirmed",
                  "correct", "indeed", "precisely", "exactly", "clearly"},
    "curious":   {"why", "how", "what", "when", "where", "interesting", "explain",
                  "question", "wonder", "curious", "intriguing"},
}


def _normalise_token(token: str) -> str:
    """Strip BPE prefix characters and whitespace, then lowercase."""
    # Strip BPE prefixes BEFORE lowercasing: Ġ (U+0120) → ġ (U+0121) after lower(),
    # so stripping must happen on the original character first.
    return token.strip().lstrip("▁Ġġ").strip().lower()


def _token_matches(token_norm: str, keyword: str) -> bool:
    """
    True if the normalised token matches this keyword.
    Prefix match: "certainly" matches "certain"; exact match: "yes" matches "yes".
    """
    return token_norm == keyword or token_norm.startswith(keyword)


def classify_disposition(tokens: List[Dict]) -> str:
    """
    Map J-space concept tokens to one of the 7 dispositions via weighted lexicon vote.

    Each token's weight (0..1) is added to its matching disposition score.
    A token counts toward at most one disposition (first match in LEXICON iteration).
    Returns "idle" when no token matches any keyword.

    Args:
        tokens: list of {"t": str, "w": float} from /infer tokens[]

    Returns:
        One of: idle | confident | uncertain | curious | concern | reluctant | warm
    """
    scores: Dict[str, float] = defaultdict(float)

    for tok in tokens:
        t_norm = _normalise_token(tok.get("t", ""))
        w = float(tok.get("w", 0.0))
        if not t_norm:
            continue
        for disp, keywords in LEXICON.items():
            if any(_token_matches(t_norm, kw) for kw in keywords):
                scores[disp] += w
                break  # one disposition per token

    if not scores:
        return "idle"

    return max(scores, key=lambda d: scores[d])
