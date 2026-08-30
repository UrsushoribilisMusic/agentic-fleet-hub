#!/usr/bin/env python3
"""
FLOT-105: Session manager — rolling context compression.

Tier 1 (T1): Deterministic citation-ID cache — wiki entries retrieved in prior
    turns, stored id→entry, rendered as a compact index. No LLM. Never cleared.
    Facts always live here, never only in the T2 prose summary.

Tier 2 (T2): Capped ~200-token rolling intent/state summary — rewritten each
    turn by a small LLM call over the last 4 turns. Facts and rule IDs are
    explicitly excluded from the summarisation prompt. Falls back on error.

Per-turn assembly: [system: role+grounding] [user: T2|T1-cache|fresh|query]

Usage:
    sm = SessionManager(role_prompt=BLURB)
    for query in conversation:
        fresh = retrieve(query, k=3)
        messages = sm.assemble(query, fresh)   # idempotent
        response = ollama_chat(model, messages)
        sm.record(query, response, fresh)      # mutates: ingest T1, refresh T2
"""
import json
import urllib.request

OLLAMA_URL         = "http://localhost:11434/api/chat"
SUMMARY_MAX_TOKENS = 200   # hard cap on T2 LLM output (Ollama num_predict)
_HISTORY_WINDOW    = 4     # max recent turns fed to the summariser


def _compact_ollama(model: str, prompt: str, max_tokens: int) -> str:
    """Minimal Ollama call: low-temperature, capped output, 60 s timeout."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": max_tokens},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as exc:
        return f"[summary unavailable: {exc}]"


class SessionManager:
    """
    Two-tier per-turn context compressor for multi-turn Apertus 8B sessions.

    Parameters
    ----------
    role_prompt         System message content (role + grounding / BLURB).
    summary_model       Ollama model tag used for T2 summarisation.
    max_summary_tokens  Hard output cap passed to Ollama as num_predict.
    """

    def __init__(
        self,
        role_prompt: str,
        summary_model: str = "apertus-flotilla",
        max_summary_tokens: int = SUMMARY_MAX_TOKENS,
    ) -> None:
        self.role_prompt        = role_prompt
        self.summary_model      = summary_model
        self.max_summary_tokens = max_summary_tokens

        self._cache:   dict[str, dict]        = {}   # T1: id → entry (prior turns)
        self._summary: str                    = ""   # T2: behavioural / intent prose
        self._history: list[tuple[str, str]]  = []   # (query, response) per turn

    # ── T1 renderers ─────────────────────────────────────────────────────────

    def _render_t1_cache(self) -> str:
        """Compact index of all T1 entries retrieved in prior turns."""
        if not self._cache:
            return ""
        lines = [f"[{eid}] {e['title']}" for eid, e in sorted(self._cache.items())]
        return "[CITATION CACHE — entries consulted in earlier turns]\n" + "\n".join(lines)

    @staticmethod
    def _render_fresh(hits: list[dict]) -> str:
        """Full body for this turn's retrieved entries."""
        if not hits:
            return ""
        parts = [f"[{h['id']}] {h['title']}\n{h['body']}" for h in hits]
        return "[FRESH RETRIEVAL]\n" + "\n\n".join(parts)

    # ── T2 renderer & refresh ─────────────────────────────────────────────────

    def _render_t2_summary(self) -> str:
        if not self._summary:
            return ""
        return (
            "[SESSION SUMMARY — intent and state only; "
            "facts are in the citation blocks above]\n"
            + self._summary
        )

    def _refresh_summary(self) -> None:
        """Rewrite T2 from the last _HISTORY_WINDOW turns via a capped LLM call."""
        if not self._history:
            self._summary = ""
            return
        recent     = self._history[-_HISTORY_WINDOW:]
        turns_text = "\n".join(f"Q: {q[:300]}\nA: {a[:300]}" for q, a in recent)
        prompt     = (
            f"Summarise the intent and state of this conversation in "
            f"≤{self.max_summary_tokens} tokens. "
            "Exclude specific facts, numbers, rule names, or citation IDs — "
            "those are stored separately. Focus only on what the user is "
            "trying to accomplish and what has been resolved so far.\n\n"
            f"{turns_text}\n\nSummary:"
        )
        result = _compact_ollama(self.summary_model, prompt, self.max_summary_tokens)
        if not result.startswith("[summary unavailable:"):
            self._summary = result
        # else: keep prior summary — stale is better than blank

    # ── public API ────────────────────────────────────────────────────────────

    def assemble(self, query: str, fresh_hits: list[dict]) -> list[dict]:
        """
        Build the per-turn ChatML message list.

        Idempotent: does NOT mutate session state.  Call record() after the
        model responds to ingest fresh_hits into T1 and refresh T2.

        T1 cache is rendered from *prior* turns; fresh_hits appear in the
        FRESH RETRIEVAL block with full bodies.  After record() they move
        to the compact cache index for subsequent turns.
        """
        blocks = [
            self._render_t2_summary(),
            self._render_t1_cache(),
            self._render_fresh(fresh_hits),
            query,
        ]
        user_content = "\n\n".join(b for b in blocks if b)
        return [
            {"role": "system", "content": self.role_prompt},
            {"role": "user",   "content": user_content},
        ]

    def record(self, query: str, response: str, fresh_hits: list[dict]) -> None:
        """
        Record a completed turn.

        Ingests fresh_hits into T1 (new ids only; setdefault preserves
        determinism), appends the turn to history, and refreshes T2.
        Call this exactly once per turn, after the model has responded.
        """
        for h in fresh_hits:
            self._cache.setdefault(h["id"], h)
        self._history.append((query, response))
        self._refresh_summary()

    @property
    def cache_size(self) -> int:
        """Number of distinct wiki entries in T1 cache."""
        return len(self._cache)

    @property
    def turn_count(self) -> int:
        """Number of completed turns recorded this session."""
        return len(self._history)
