# EVAL-1 Scoring Rubric

Used by both Qwen (automated) and Opus (second judge, EVAL-006).
Each answer is scored on 4 independent dimensions, 0–5 each.
**Pass threshold: ≥ 3.5 / 5 per dimension.**

---

## Dimension 1 — action_correct

*Does the answer recommend or describe the correct action?*

| Score | Meaning |
|-------|---------|
| 5 | Fully correct, specific, and actionable. Matches gold intent exactly. |
| 4 | Correct action with a minor gap (e.g. missing one step, slight imprecision). |
| 3 | Partially correct — the main action is right but a significant component is missing or wrong. |
| 2 | Wrong action, but the reasoning shows partial understanding of the problem. |
| 1 | Wrong action with no redeeming reasoning. |
| 0 | No action proposed, pure evasion, or action directly contradicts gold. |

**Pass: ≥ 3.5** — correct action with at most a minor gap.

---

## Dimension 2 — grounded

*Are all factual claims in the answer supported by the retrieved wiki entries or the gold answer?*

| Score | Meaning |
|-------|---------|
| 5 | Every claim is traceable to a retrieved entry or the gold answer. |
| 4 | One minor unverifiable claim that is consistent with domain (e.g. plausible Ollama flag name). |
| 3 | One unsupported claim that does not affect the correctness of the recommended action. |
| 2 | One hallucinated claim that affects action correctness or would mislead the agent. |
| 1 | Multiple invented facts (names, IDs, rule numbers, statuses). |
| 0 | Majority of specific claims are fabricated. |

**Pass: ≥ 3.5** — at most a plausible unverifiable claim.

Note: If no retrieval was available (Arm 0, floor), ground against the gold answer only. A generic but correct answer can still score 5.

---

## Dimension 3 — fleet_domain

*Does the answer demonstrate fleet-specific knowledge vs a generic response?*

| Score | Meaning |
|-------|---------|
| 5 | References specific fleet artefacts: rule IDs (R01–R30), PocketBase field names, agent names, heartbeat phases, wiki entry IDs. |
| 4 | Clear fleet domain knowledge without citing specific IDs. |
| 3 | Some domain knowledge but substantial portions are generic (would apply to any multi-agent system). |
| 2 | Mostly generic; uses fleet vocabulary but no substantive fleet knowledge. |
| 1 | Entirely generic — could answer for any software system. |
| 0 | Off-topic or irrelevant to the question. |

**Pass: ≥ 3.5** — clear domain knowledge, at least one concrete fleet reference.

---

## Dimension 4 — completeness

*Does the answer address all parts of the question without evasion or excessive hedging?*

| Score | Meaning |
|-------|---------|
| 5 | Addresses every aspect of the question; no loose ends. |
| 4 | Addresses the main question; one minor aspect glossed over. |
| 3 | Addresses the primary concern but misses a secondary part the gold covers. |
| 2 | Partial answer — significant portions of the question left unanswered. |
| 1 | Addresses only a surface aspect; bulk of question unanswered. |
| 0 | Does not attempt to answer, or deflects entirely. |

**Pass: ≥ 3.5** — all main aspects covered.

---

## Composite score

`composite = mean(action_correct, grounded, fleet_domain, completeness)` over intersection rows.

Primary headline: **action_correct** (did the agent do the right thing?).
Secondary headline: **grounded** (did it stay within what was retrievable?).

---

## Blind grading instructions (Opus)

1. Answers arrive labelled **A / B / C** — you do not know which arm produced which.
2. Score each independently against the rubric. Do not adjust for perceived model quality.
3. After scoring the full batch, call for the reveal. The mapping (A/B/C → arm) is in `blind_reveal.json` in this directory (locked until you finish grading).
4. If an answer is an obvious error (`[ERROR: ...]`) or empty, score all 4 dimensions as 0 and note "ERROR".
