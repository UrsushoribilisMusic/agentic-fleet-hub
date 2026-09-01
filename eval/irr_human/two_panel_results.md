# CANIS-EVAL-001 — Model-judge vs human panel (§6.3)

*Computed 2026-09-01 via `compute_two_panel.py`. Same 50 items, same 8-label protocol as the human
panel. Model judges labelled blind via the fleet (one PocketBase ticket each). Data:
`model_ratings/{gem,clau,codi,misty}.json` + `canis_ratings.jsonl` (humans).*

## Headline

| panel | raters | **inter-rater Fleiss κ** |
|-------|--------|:---:|
| **Large-model judges** | gem, misty, clau, codi (cross-family: Gemini / Mistral / Claude / Codex) | **0.89** |
| **Humans** | R1, R2, R3 | **0.42** |

**Four cross-family models agree at κ = 0.89; three humans at κ = 0.42 — on identical items.** The
disposition labels are a *model-native* regularity: models converge on them, individual humans do
not. This is the paper's central claim in its strongest, most symmetric form.

## Per-rater agreement with the labels (Cohen's κ)

| model | κ | | human | κ |
|-------|---:|---|-------|---:|
| gem | 0.98 | | R1 | 0.86 |
| misty | 0.98 | | R2 | 0.56 |
| clau | 0.84 | | R3 | 0.42 |
| codi | 0.84 | | | |

The four judges rated with **distinct patterns** (clau/codi over-apply *confident*, 11–12; gem/misty
balanced) and none copied the key (43/43/49/49 of 50) — genuine independent judgments.

## The nuance (belongs in the paper, not hidden)

The **majority vote of each panel** lands near the labels — model-consensus vs key κ = 0.86,
human-consensus vs key κ = 0.84 — so the labels are **not wrong**; a crowd of humans recovers them.
What collapses is **individual human reliability** (Fleiss 0.42) against **model reliability** (0.89).
Precise claim: *the disposition signal is far more stable across models than across individual
humans.* (With only 3 human raters, per-class majority is fragile to tie-breaking — lead with the
Fleiss numbers.)

## Per-axis (each panel's majority on that class's own items — indicative only)

| axis | MODEL | HUMAN |
|------|:-----:|:-----:|
| confident | 7/7 | 7/7 |
| reluctant | 7/7 | 7/7 |
| concern | 8/8 | 8/8 |
| warm | 7/7 | 7/7 |
| uncertain | 5/7 | 4/7 |
| curious | 3/7 | 4/7 |
| **mischief** | **7/7** | split 0/7 · 3/7 · 7/7 per rater |

**mischief** is the sharpest: all four models label it; the three humans span the full range. Models
see a category individual humans do not converge on.

## Caveat

The answer key sits in the repo; judges were instructed not to open it and their distinct,
non-ceiling patterns (esp. clau/codi at 43/50) are consistent with genuine blind rating, but this is
an instruction, not an enforced wall.
