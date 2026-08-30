# CANIS Task 1 — Out-of-Distribution test (the artifact gate)

**Question:** does the CE-09 discriminant capture *disposition*, or a *prompt-style artifact*?
5-fold CV shares one generative process; this tests a **fresh, deliberately different** set.

**OOD set:** 420 items (30 pos + 30 matched-neg × 7), authored by separate agents, blind to the
originals — different source, register (casual/formal/technical/narrative vs short trivia),
domain, length, and grammatical person. **CE-09 seeds FROZEN** (no refit); tapped on all 3 models
and scored. `canis_eval001_ood_matrix.jsonl`, `ood_run/`, `ood_results.json`.

## Macro recall / FP: in-distribution CV → OOD (frozen)

| Model | CV recall | **OOD recall** | CV FP | OOD FP | naive seeds on OOD | lexical baseline |
|-------|-----------|----------------|-------|--------|--------------------|------------------|
| Apertus-4B | 89% | **79%** | 7% | 5% | 34% | ~15% |
| Ministral-3B | 95% | **80%** | 9% | 8% | 30% | ~3% |
| Qwen3-4B | 92% | **70%** | 6% | 1% | 32% | ~3% |

**Verdict: it mostly generalizes.** A real ~10–22 pp drop from CV to OOD, but it holds at
**70–80% macro recall — still 2–2.7× the naive seeds on the *same* fresh prompts and far above
the lexical baseline.** The signal is a **disposition axis, not merely a prompt-style artifact.**
The earlier n=6 live failure was misleading (tiny n + ambiguous prompts + the one bad axis below).

## Per-class: which axes are real vs distribution-specific

Holding OOD (real axes): **confident, uncertain, curious, concern, warm** mostly 70–100% across
models; **reluctant** partial (Apertus 94→53%, Qwen 83%).

**mischief does NOT generalize** — Apertus 62→33%, Ministral 94→60%, **Qwen 64→3%**. This axis
behaves like a style/anchor artifact out of distribution and its OOD FP rises. Combined with the
CE-07 caveat (concept-opposite negatives) and its low seed↔OOD-centroid cosine (0.02–0.10, the
lowest of any class), mischief should be **flagged as unresolved / dropped from the headline
claim**, not reported at CV strength.

## Cosine diagnostic

Reported: cosine(frozen seed, OOD positive centroid) — operand **A**. It is modest in absolute
terms everywhere (~0.05–0.40) yet classification holds, because the decision is a **relative
argmax** across classes, not an absolute-cosine threshold. The ordering is diagnostic: **warm**
highest (0.25–0.40, the most robust axis), **mischief** lowest (0.02–0.10, the axis that
collapses). *Operand B (frozen in-dist discriminant ↔ OOD-refit discriminant — the direction-drift
metric) is the sharper artifact test and is still pending; A already tracks the recall story.*

## What this means for the paper

- **Keep the core claim, add the honest OOD gap.** Report both columns: "89–95% in-distribution
  CV, 70–80% on a deliberately out-of-distribution set — degradation, not collapse."
- **Drop/curtail mischief** in the headline; report it as the one axis that does not survive OOD.
- The discriminant is a genuine (supervised) disposition probe that transfers across prompt
  distributions on 6/7 axes — a defensible, honest result.
