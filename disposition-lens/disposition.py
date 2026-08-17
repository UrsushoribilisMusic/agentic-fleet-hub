"""
Disposition classifier — maps J-space concept tokens to one of 7 dispositions.

Lexicon lookup: each token is matched against per-disposition keyword sets using
prefix matching (handles BPE fragments like "certainly" → confident).
Token weights drive a weighted vote; highest total wins. Falls back to "idle".
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

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


def _score_dispositions(tokens: List[Dict]) -> Dict[str, float]:
    """Weighted lexicon vote → {disposition: summed matched weight}. One disp per token."""
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
    return scores


def classify_disposition(tokens: List[Dict]) -> str:
    """
    Map J-space concept tokens to one of the 7 dispositions via weighted lexicon vote.
    Returns "idle" when no token matches any keyword. (Unchanged raw vote — see
    resolve_disposition for the gated + entropy-aware version used in production.)
    """
    scores = _score_dispositions(tokens)
    if not scores:
        return "idle"
    return max(scores, key=lambda d: scores[d])


# --- Production resolver: weight-gated vote + entropy as the robust axis --------
#
# Why: at the mid layer the top J-space tokens are dominated by generic connectives
# ("Depending", "Generally") that match no lexicon, so a stray low-weight token
# ("Unfortunately" @ 0.11) could hijack the face to "reluctant". Two guards:
#   1. Only tokens with weight >= WEIGHT_FLOOR get a vote, and the winner must clear
#      MIN_WINNING_SCORE — otherwise we stay neutral instead of trusting noise.
#   2. Entropy (the genuinely reliable signal) drives the sure/unsure spectrum:
#      high entropy -> uncertain, low entropy -> confident. Safety-flavoured tokens
#      (concern/reluctant) still win regardless, because a live "danger"/"refuse"
#      concept matters even when the model is otherwise sure.

WEIGHT_FLOOR = 0.30        # ignore concept tokens weaker than this in the vote
MIN_WINNING_SCORE = 0.30   # summed matched weight needed to leave neutral
ENTROPY_HIGH = 0.60        # normalised entropy above this -> uncertain
ENTROPY_LOW = 0.22         # normalised entropy below this -> model is sure
SAFETY_DISPOSITIONS = ("concern", "reluctant")


def resolve_disposition(tokens: List[Dict], entropy: Optional[float] = None) -> str:
    """
    Production disposition decision: weight-gated lexicon vote combined with entropy.

    Args:
        tokens: list of {"t": str, "w": float} from the J-lens readout
        entropy: normalised next-token entropy 0..1 (higher = less sure), or None

    Returns:
        One of: idle | confident | uncertain | curious | concern | reluctant | warm
    """
    gated = [t for t in tokens if float(t.get("w", 0.0)) >= WEIGHT_FLOOR]
    scores = _score_dispositions(gated)

    base = "idle"
    if scores:
        top = max(scores, key=lambda d: scores[d])
        if scores[top] >= MIN_WINNING_SCORE:
            base = top

    # 1) A live safety/refusal concept wins regardless of how sure the model is.
    if base in SAFETY_DISPOSITIONS:
        return base

    # 2) Otherwise entropy governs the sure/unsure axis — the reliable signal.
    if entropy is not None:
        if entropy >= ENTROPY_HIGH:
            return "uncertain"
        if entropy <= ENTROPY_LOW:
            # Model is sure: keep a positive concept if we have one, else "confident".
            return base if base in ("confident", "warm", "curious") else "confident"

    return base
