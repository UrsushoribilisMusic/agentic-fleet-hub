# CE-06 WORKLOG — Analysis & Outputs

**Task**: WP2 CE-06: Analysis & outputs (confusion + FP + arm comparison + writeup)
**PB ID**: e8nrog087hprlfa
**Agent**: Clau
**Date**: 2026-08-26

## Plan

1. Read CE-05 results (`eval/results_canis_eval001_apertus.jsonl` — 539/540 items, Apertus only)
2. Generate full 4-arm × 1-model confusion matrices (8×8)
3. Compute per-class precision/recall/F1 with 95% Wilson CI
4. Compute FP rate per axis (on the 20 negatives per class)
5. Generate arm0/1/2/3 comparison table on same items
6. Compute pairwise seed-vector cosine separations for collision ranking
7. Write the statistical verdict on J-space vs lexical baseline
8. Deliver: `eval/canis_eval001_ce06_report.md`

## Key decisions

- Only Apertus results available (CE-05 ran Apertus only; Ministral server had DL-8 bug).
  Report scoped to Apertus-4B. Flag Ministral as pending.
- Mischief missing from `seed_vectors_apertus_3q4.npz` (added in CANIS-G, after npz was built).
  This explains 0% recall for mischief — structural gap, not a collision.
- curious→uncertain is the primary collision confirmed by data (39/50 curious → uncertain in arm1)
  and by seed vector cosine (0.9145).

## Status: complete — report written to eval/canis_eval001_ce06_report.md
