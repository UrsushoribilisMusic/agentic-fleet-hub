# FX-002 — Stage 0 Filter: Gold-vs-Chaff Criteria

*Authored by Clau, 2026-06-22. This is the rubric every FX extraction ticket applies before classifying or including any candidate. Gem applies this same rubric in FX-010 to achieve ≥8/10 inter-rater agreement. If agreement falls below 8/10 on a 10-event sample, stop — reconcile rubric here, re-run overlap check before splitting work.*

---

## What this document is

A two-part decision system:

1. **Stage 0 Gates** — binary pass/fail checks. Any candidate that fails a gate is dropped immediately; no routing decision needed.
2. **Routing Rules** — for candidates that pass all gates, these determine which bucket(s) they land in: `SFT`, `wiki`, `both`, `SFT+annotation`, or `contested`.

Every downstream extraction ticket (FX-005 through FX-015) runs its candidates through Stage 0 first. No candidate enters a training bucket without passing Stage 0.

---

## Stage 0 Gates (run in order; fail = drop)

### Gate 1 — Exact Duplicate

**Condition:** A (human_turn, assistant_turn) pair is byte-identical to another candidate already in the working set.

**Action:** Drop all duplicates. Keep one. Log: `exact_dup_dropped=N`.

**Note:** Compare after normalizing whitespace (collapse runs of `\s+` to single space, strip leading/trailing whitespace per turn). Two pairs with the same meaning but different formatting are NOT exact duplicates — Gate 2 handles near-duplicates.

---

### Gate 2 — Near-Duplicate Collapse

**Condition:** Cosine similarity between two candidates' concatenated (human_turn + assistant_turn) embeddings exceeds **0.95** after L2 normalization. Use the same embedding model used for semantic search in the facts store (FX-016).

**Action:** Keep the candidate with the longer assistant turn (more context). Drop the shorter. Log: `near_dup_collapsed=N`.

**When to hold off:** If FX-016 embedding model is not available yet, flag candidates as `near_dup_pending` and re-run Gate 2 as a post-processing step before FX-020. Do not skip; do not substitute a different model.

---

### Gate 3 — Empty or Stub Turn

**Condition:** Either the human turn or the assistant turn is:
- Empty string or whitespace only
- A bare file path with no surrounding content (e.g., `/Users/miguelrodriguez/projects/…`)
- A pure metadata blob (JSON with no human-readable content, e.g., `{"status":"in_progress"}` alone)
- A template placeholder that was never filled (e.g., `<insert content here>`)

**Action:** Drop. Log: `empty_turn_dropped=N`.

**Note:** A human turn containing ONLY a task title (e.g., `"PC-087: Allow rename"`) is borderline. Check whether the assistant turn provides enough context to recover the intent — if yes, treat as terse-recoverable (see Routing Rule 5). If the assistant turn is also sparse, drop.

---

### Gate 4 — Boilerplate Drop

**Condition:** The assistant turn is a structural template, session-management prose, or repeating framework output with no unique judgment content. Examples:

- Session sign-off blocks: `"Phase 6 — Sign Off: posted heartbeat idle, git status empty, no commit."`
- Standard protocol confirmations: `"Phase 1 complete. Pulled master. No new inbox messages."`
- Build-verifier boilerplate: `"Running build-tag.sh… BUILD SUCCEEDED."`
- Dispatcher queue snapshots without any decision rationale
- Pure echo responses: assistant restates the human turn verbatim and adds nothing

**Action:** Drop. Log: `boilerplate_dropped=N`.

**Edge case:** If a boilerplate-framed response includes a non-trivial decision (e.g., a sign-off block that explains WHY no commit was made), keep it and route normally.

---

### Gate 5 — Converging-Not-Correction Drop

**Condition:** The human turn directs more work in the same direction the assistant was already going (continuation, iteration, elaboration). It is NOT pushing back on the approach or correcting a mistake. Signals:

- `"Continue"` / `"Keep going"` / `"More"` / `"Do the next ticket"`
- `"Looks good, now do X"` (X is a new subtask, not a correction)
- Human provides new information or context that expands scope (not narrows/corrects it)
- Assistant turn writes more code, more prose, more plan steps — forward progress only

**Action:** Drop. These are not correction signals; they do not carry disposition weight useful for SFT. Log: `converging_dropped=N`.

**Contrast with keep:** `"No, don't do it that way — do it this way instead"` is a correction. `"Stop doing X"` is a correction. `"That's wrong because…"` is a correction. When in doubt about whether a human turn is correcting or continuing, apply the terse-recoverable rule (Gate 5 is about direction of motion, not verbosity).

---

## Routing Rules (applies only to candidates that pass all 5 gates)

Every candidate gets exactly one primary bucket. A candidate can be in two buckets only under the `both` rule.

---

### Rule 1 — Fact → `wiki`

**Signal:** The content is a concrete value, location, count, name, date, or configuration that:
- Is true at a specific point in time
- Could legitimately change as the system evolves
- Would be wrong to bake into model weights as a fixed belief

**Examples:**
- Port numbers, path locations, collection names (`PocketBase on port 8090`, `/Users/miguelrodriguez/fleet/…`)
- Agent roster sizes, lesson counts, ticket counts at a snapshot (`382 lessons as of 2026-06-22`)
- Specific threshold values that appear in configuration (`cooldown = 300s`, `circuit breaker at 3 reassignments`)
- Named agent assignments at a point in time (`FX-001 assigned to Codi`)

**Action:** Route to `wiki` (facts store). Do NOT include in SFT training data. These are citation sources, not weight signals.

---

### Rule 2 — Disposition → `weights` (SFT)

**Signal:** The content is a judgment call, preference, heuristic, or behavioral policy that:
- Is stable across time (doesn't depend on a specific count or configuration value)
- Encodes HOW to decide, prefer, or stop — not WHAT the current state is
- Would improve future behavior if baked into the model

**Examples:**
- `"Don't mock the database in these tests"` (preference with rationale)
- `"Stop summarizing at the end of every response"` (behavioral correction)
- `"Terse responses without trailing summaries"` (disposition)
- `"Prefer integration tests over unit mocks because mock/prod divergence bit us"` (reasoned heuristic)
- Peer-review approval reasoning that explains quality criteria

**Action:** Route to `weights` (SFT). This is a direct training pair.

---

### Rule 3 — Disposition + Named Citable Rule → `both`

**Signal:** The disposition in Rule 2 is additionally tied to a named, citable policy — a specific RULES.md clause, MISSION_CONTROL.md ticket entry, or protocol step (e.g., `"Rule #6 — verify before claiming green"`, `"Phase 2 — Peer Review First"`).

**Action:** Route to `both`:
- The disposition/judgment → `weights` (SFT)
- The rule name + canonical text → `wiki` (citable corpus entry with stable ID, per FX-016)

**How to split:** The SFT pair carries the behavioral signal (`"always run the build verifier before claiming success"`). The wiki entry carries the exact rule text with its canonical reference (`RULES.md §GitHub & Commits, Rule #6`). The SFT pair should NOT include the exact rule text inline — only the behavioral lesson.

---

### Rule 4 — Split Case (Disposition + Embedded Number) → `both`

**Signal:** A disposition that names a specific threshold value. The disposition is stable; the number is a configuration fact.

**Examples:**
- `"Reassign after 3 failures within 10 minutes"` — disposition is `"reassign on repeated failure"`, fact is `N=3, W=10m`
- `"Agents are offline after 30 minutes of heartbeat silence"` — disposition is `"use heartbeat staleness to detect offline"`, fact is `threshold=1800s`

**Action:** Route to `both`:
- Strip the number from the SFT pair; keep the structural judgment (`"reassign after repeated failures within a short window"`)
- Put the exact number into the wiki entry with its source location

**Do not split** if the number is illustrative rather than policy (e.g., `"we had 176 corrections out of 287 raw matches"` — that's a measurement, not a configuration value). Measurements route to `wiki` only.

---

### Rule 5 — Terse-Recoverable → `SFT + inferred_rationale`

**Signal:** The human turn alone carries a judgment but is terse — a single word (`"no"`), a short redirect (`"stop that"`, `"wrong approach"`), or a brief override — with no explicit rationale. The correction intent is clear from the context window (preceding assistant turn makes the subject obvious), and a competent annotator could write the rationale without speculation.

**Action:** Route to `SFT`. Add a mandatory `inferred_rationale` annotation field to the record (see schema below). The SFT training pair uses the original human/assistant turns as-is. The `inferred_rationale` field is metadata for the annotator and for FX-019 scoring — it is NOT injected into the training text.

**inferred_rationale annotation schema:**
```json
{
  "inferred_rationale": "string — one sentence stating what the human was correcting and why, inferred from context. Written by the classifying agent.",
  "rationale_confidence": "high | medium | low"
}
```

Use `rationale_confidence: low` if the intent requires more than one inference step. If `low` and the rationale feels speculative, escalate to `contested` (Rule 6).

---

### Rule 6 — Contested

**Signal:** Either of these conditions:
1. The example would only make sense as training data if the `inferred_rationale` were injected directly into the training text (i.e., the raw human/assistant pair is too ambiguous to train on without adding explanatory text not present in the original).
2. Reasonable annotators could disagree about what behavior the human turn is correcting.
3. The human turn is so terse (e.g., a single emoji, `"hmm"`, a file path with no words) that recovery of intent requires speculation.

**Action:** Route to `contested` bucket. Do NOT place in SFT or weights. Log for Arm 2 human review.

**Note:** Contested ≠ bad. Some contested examples are valuable with a small annotation effort. They go to a separate bucket (FX-010) precisely so they can be reviewed and potentially recovered rather than silently dropped.

---

## Drop Log Requirements

Every extraction ticket must emit a drop log alongside its output. Minimum fields:

| Field | Type | Notes |
|---|---|---|
| `source` | string | Which FX ticket / source file the candidates came from |
| `gate` | string | Which gate caused the drop (`exact_dup`, `near_dup`, `empty_turn`, `boilerplate`, `converging`) |
| `count` | int | Number of candidates dropped at this gate |
| `sample` | list[str] | Up to 3 example human turns from dropped candidates (for audit) |

The log is written to `drops/<source_ticket>.jsonl` in the corpus repo. FX-022 reads all drop logs as part of the final QA checklist.

---

## Inter-Rater Agreement Protocol (FX-010)

Before Gem co-classifies alongside Clau in FX-010:

1. Both agents independently classify the same 10-event sample from FX-009's 176 corrections.
2. Agreement = (number of identical bucket assignments) / 10.
3. **≥8/10 → proceed** with full parallel classification (Clau + Gem split the 176 events).
4. **<8/10 → stop.** Post disagreement breakdown as a comment on FX-002. Reconcile rubric (update this document). Re-run the 10-event sample. Do not begin bulk classification until threshold is met.

The 10-event sample should be drawn from across the spectrum: pick 2–3 explicit-rationale examples, 2–3 terse examples, 2–3 candidates near the converging/contested boundary, and 1–2 boilerplate-adjacent cases.

---

## Quick-Reference Summary Table

| Category | Example Signal | Primary Bucket | Secondary |
|---|---|---|---|
| Fact | Port number, path, count at a date | `wiki` | — |
| Pure disposition | Behavioral preference, heuristic | `weights` (SFT) | — |
| Disposition + rule reference | Judgment tied to named RULES.md clause | `weights` (SFT) | `wiki` |
| Split: disposition + threshold | Policy with embedded config number | `weights` (SFT) | `wiki` |
| Terse-recoverable | `"no"` / `"stop that"` with clear context | `weights` (SFT) | `inferred_rationale` annotation |
| Contested | Ambiguous / requires injected explanation | `contested` | — |
| Exact duplicate | Identical pair already in working set | DROP | — |
| Near-duplicate | Cosine ≥0.95 with another candidate | DROP (keep one) | — |
| Empty/stub | Empty turn or bare path | DROP | — |
| Boilerplate | Protocol confirmation, sign-off block | DROP | — |
| Converging | Continuation, not correction | DROP | — |

---

## Open Questions for Miguel Review

Before any extraction ticket counts as done, Miguel reviews this doc and resolves the following:

1. **Near-dup threshold**: Is 0.95 cosine similarity the right cutoff? Or should it be 0.92 (more aggressive collapse) or 0.97 (more permissive)?
2. **Split-case numbers**: When a rule says "N=3 reassignments", should N be stripped from weights entirely, or is learning the order-of-magnitude (single-digit threshold) useful? Current spec strips the exact number; keeping the approximate range (3–5) in weights may be reasonable.
3. **Contested recovery**: Is there a process planned for Arm 2 (human review of contested bucket)? If yes, does it happen before or after FX-020 final package?
4. **Terse-recoverable confidence floor**: Should `rationale_confidence: low` always escalate to `contested`, or can it stay in SFT with a lower-weight flag?
