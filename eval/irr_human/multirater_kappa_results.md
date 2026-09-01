# CANIS-EVAL-001 — Three-rater human IRR (final)

*Computed 2026-09-01 via `compute_multirater_kappa.py`. Raters blind to the original labels,
50 items (~7/class). Data: `canis_ratings.jsonl` (R1 + R3, web app) + R2
(recovered from `human_sheet.numbers`). Original labels: `human_key.json`.*

## Headline

**Fleiss' κ across the 3 raters = 0.42** (moderate) — vs the two-LLM-rater κ = 0.89. Three humans
agree only *moderately* on disposition labels, while two LLMs agreed almost perfectly. This is the
core finding the task was built to test: **the high LLM agreement reflected a shared prior, not
label validity.** Human disposition perception is genuinely rater-dependent.

## Per-rater vs the original labels (Cohen's κ)

| rater | agree | Cohen's κ |
|-------|------:|----------:|
| R1 | 44/50 | **0.86** |
| R2 | 31/50 | **0.56** |
| R3 | 25/50 | **0.42** |

## Pairwise agreement (Cohen's κ)

| pair | κ |
|------|---:|
| R2 ↔ R1 | 0.56 |
| R1 ↔ R3 | 0.48 |
| R2 ↔ R3 | 0.26 |

Even human-to-human agreement is only fair-to-moderate — and one pair (R2↔R3) is *fair* (0.26).

## Per-class agreement with the original label (rater labels its own-class item correctly)

| axis | R2 | R1 | R3 | verdict (3-rater) |
|------|:------:|:-----:|:----:|-------------------|
| **confident** | 7/7 | 7/7 | 7/7 | **unanimous — the one truly robust axis** |
| reluctant | 7/7 | 7/7 | **1/7** | 2 of 3 agree; **R3 breaks it** — not unanimous |
| concern | 6/8 | 8/8 | 5/8 | moderate, holds |
| warm | 4/7 | 7/7 | 7/7 | moderate, rater-variable |
| curious | 7/7 | 4/7 | **0/7** | strongly rater-dependent |
| uncertain | 0/7 | 4/7 | 2/7 | **subjective** (low across all) |
| mischief | 0/7 | 7/7 | 3/7 | **maximal spread (0 / 7 / 3)** — radically rater-dependent |

## Reading

1. **`confident` is the only unanimous axis** — 7/7 for all three humans *and* the model. Genuinely real.
2. **`reluctant` does not survive the third rater.** R2 and R1 map it perfectly (7/7), but R3
   almost never does (1/7). The two-rater view called it "rock-solid"; with three raters it is
   *mostly agreed but not unanimous* — a caveat §6 must now carry.
3. **`mischief`, `curious`, `uncertain` are strongly rater-dependent.** mischief in particular spans
   the whole range (0 / 7 / 3): it is not "invisible to humans," it is **read completely differently
   by different humans** — a sharper artifact story than the single-rater pass gave. curious swings
   7→0 across raters; uncertain is low for everyone.
4. **`warm`, `concern`** sit in the moderate middle.
5. R3's disagreement concentrates on **reluctant (1/7)** and **curious (0/7)**, dragging both his
   per-rater κ (0.42) and the overall Fleiss down.

## Implication for §6.3

The taxonomy survives but tightens:
- **Real (human-robust): `confident`** unambiguously; `concern`/`warm` moderate.
- **`reluctant`**: real for 2 of 3 raters — demote from "rock-solid" to "agreed-but-not-unanimous."
- **Subjective: `uncertain`/`curious`** confirmed (and curious's 7→0 swing is stronger evidence than before).
- **Artifact/rater-dependent: `mischief`** confirmed, now framed as *humans radically disagree* (0/7/3),
  not *humans can't see it*.
- Overall **Fleiss κ = 0.42 vs LLM 0.89** is the number that carries the paper's central claim.
