# WORKLOG — FLOT-105: Session manager — rolling context compression

Task PB ID: 1ooj6p2hpvsvfvj
Branch: task/1ooj6p2hpvsvfvj
Agent: clau

## Plan

Implement `eval/session_manager.py` — a ~150-line module providing two-tier
per-turn context compression for multi-turn Apertus 8B sessions running
beside Ollama.

### Design

**Tier 1 (T1) — citation-ID cache (no LLM)**
- `dict[str, entry]` accumulated across the session; never cleared.
- Rendered as a compact index (`[id] title`) for the context block.
- Ensures facts are always accessible; they never live only in T2 prose.
- Maximum 66 entries (full wiki size) ≈ ~5 KB even at saturation.

**Tier 2 (T2) — rolling intent/state summary (small LLM)**
- After each turn, a capped LLM call rewrites the summary from the last 4
  turns. Hard limit: `num_predict=200`.
- Prompt explicitly excludes facts/numbers/rule IDs so they stay in T1.
- Falls back to the previous summary if the LLM call fails.

**Per-turn assembly order (in the user message):**
1. T2 summary block (empty on turn 0)
2. T1 cache block — compact index of entries from *previous* turns
3. Fresh retrieval block — full bodies of *this* turn's retrieved entries
4. The query itself

**State mutation discipline:**
- `assemble(query, fresh_hits)` is idempotent — reads state, does not mutate.
- `record(query, response, fresh_hits)` is the single mutation point:
  ingests fresh_hits into T1, appends turn to history, refreshes T2.

**Integrates with existing patterns:**
- `retrieve()` from `eval/retrieve.py` (caller's responsibility)
- Same `ollama_chat`-style URL/payload as all existing eval harnesses

### Files to produce
- `eval/session_manager.py` — the module (~150 lines)

### Steps
1. [x] Branch created, WORKLOG committed
2. [ ] Write eval/session_manager.py
3. [ ] Smoke test (import + one-turn assemble, no Ollama required)
4. [ ] Commit + push
5. [ ] Post output comment, set to peer_review
