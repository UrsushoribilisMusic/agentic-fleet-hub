# CANIS Task 2 — Human rater vs original labels (50 items)

**Human rater:** Miguel, blind to original labels, 50 items (~7/class). Compared to the
original labels with Cohen's κ. Contrast with the earlier LLM-rater pass (κ = 0.89).

## Headline

**Human vs original: Cohen's κ = 0.56** — *moderate*, and **far below the LLM rater's 0.89.**
This is exactly the concern that motivated the task: two LLM raters agreeing reflected a
**shared prior**, not label correctness. The human is the real test, and it says the labels
are only moderately reliable overall — with two axes that fail outright.

## Per-class (one-vs-rest κ; agreement on that class's own items)

| Class | κ | agreed | verdict |
|-------|-----|--------|---------|
| confident | **0.92** | 7/7 | robust |
| reluctant | **0.92** | 7/7 | robust |
| concern | 0.70 | 6/8 | ok |
| warm | 0.70 | 4/7 | ok (3 → "neutral") |
| curious | 0.59 | 7/7 | over-applied (absorbs uncertain) |
| **uncertain** | **−0.13** | **0/7** | **FAILS** |
| **mischief** | **0.00** | **0/7** | **FAILS** |

## The two failures

**mischief — human agreed 0/7.** Not one mischief item was read as mischief by the human;
he labeled them uncertain (3), concern (2), reluctant (1), curious (1). This is the **fourth
independent signal** on mischief: perfect LLM agreement (κ=1.00) + total OOD collapse (Qwen
64→3%) + prompt-only *beating* J-space + now **0/7 human**. The "mischief" label encodes a
text/style regularity that models latch onto and a human does not. **It is not a disposition
construct. Drop it.**

**uncertain — human agreed 0/7 (κ = −0.13).** New, and more consequential. The human read
every "uncertain" item as **curious** (mostly) or **confident** — i.e. an open speculative
question reads to a person as curiosity/assurance, not model-uncertainty. This mirrors the
seed-vector collision (confident/uncertain/curious near-collinear) and means the
uncertain-vs-curious distinction **may not be human-valid** either.

## What survives

**confident and reluctant are rock-solid** (κ=0.92, 7/7). **concern, warm, curious** are
usable (κ ≈ 0.6–0.7). The robust, human-validated set is roughly **4–5 axes**, not 7.

## Implication (decision needed before drafting)

The 7-axis framing does not survive human labeling. Honest options:
1. **Drop mischief; merge or drop uncertain** → a paper on the ~5 human-valid axes
   (confident, reluctant, concern, warm, curious).
2. **Make label validity a contribution** — report which disposition axes are human-valid and
   which are model-only artifacts (mischief) or human-inseparable (uncertain/curious). This is
   arguably a *stronger, more honest* paper than "7 axes, 90%."

*n = 7 per class is small; treat single-class κ as indicative. But 0/7 on two classes,
consistent with every other signal, is not noise.*
