# CANIS Task 2 — Inter-rater reliability on the core-matrix labels

**Procedure.** Random 150-item sample of the 540-item core matrix (seed 20260828; 102
positives / 32 matched-negatives / 16 idle). A second **independent rater, blind to the
original labels**, assigned each prompt one of 8 categories (7 dispositions + neutral) by
judging what disposition a model's *response* would exhibit. Cohen's κ computed against the
original labels (positive → target_class; idle & matched-negative → neutral).

**Rater:** a separate Claude instance (LLM rater), blind. *Limitation:* an LLM second rater
may share priors with the prompt author; a human rater would strengthen this and is the
recommended supplement before camera-ready.

## Overall

**Cohen's κ = 0.890** (8-way) — substantial-to-near-perfect agreement. The supervised
labels have a real denominator.

## Per-class (one-vs-rest κ over the whole sample)

| Class | κ | Agreement on its own positives |
|-------|-----|-------------------------------|
| **concern** | **1.000** | 12/12 (100%) |
| **reluctant** | **1.000** | 14/14 (100%) |
| **mischief** | **1.000** | 17/17 (100%) |
| warm | 0.940 | 18/18 (100%) |
| uncertain | 0.926 | 14/15 (93%) |
| curious | 0.821 | 13/13 (100%) |
| confident | 0.791 | 13/13 (100%) |
| neutral | 0.785 | 35/48 (73%) |

## Reading

- **The prediction that concern + mischief would show the most disagreement does NOT hold** —
  they are the *most* reliable (κ = 1.00, perfect agreement on their positives). Their
  difficulty in the readout (§5.3) is therefore **not a labeling artifact**: the ground truth
  is rock-solid, so the entanglement/low-recall lives in the model + probe, not the labels.
- **The disagreement is in the negatives, not the positives.** Every disposition's own
  positives were labeled with ≥93% agreement; the lower one-vs-rest κ for confident / curious /
  neutral comes from the rater occasionally reading a faint disposition into a *matched-negative*
  the original called neutral. This bears on FP measurement, not recall.
- **`confident` is over-applied even by an independent rater** (κ 0.79, own positives 100%),
  echoing the CE-08/CE-09 finding that the confident axis is broad and over-fires — a human/LLM
  rater does the same thing the probe does.

*Source data: irr/irr_sample_blind.json, irr/irr_rater.json, irr/irr_key.json.*
