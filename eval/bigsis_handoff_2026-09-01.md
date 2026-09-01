# CANIS paper — response to Big Sis review (1 Sep 2026)

Clau processed everything actionable without the human raters. One item (multi-rater IRR) is
genuinely blocked on the evaluators and is now running in the background. Summary below; all
changes are in `canis_disposition_paper_DRAFT.md` (rev. 1 Sep 2026).

---

## 1. Cross-axis B baseline — DONE (this is the one that moved §6)

Computed the full **7×7 frozen×OOD-refit cosine matrix per model**, plus the in-distribution
off-diagonal. Script: `compute_cross_axis_B.py`; data: `cross_axis_B.json`.

**Headline: B carries an argument *in aggregate*, but not for every axis.**

| model | diag mean | cross off-diag mean (max) | in-dist off-diag mean (max) |
|-------|----------:|--------------------------:|----------------------------:|
| Apertus  | 0.59 | 0.08 (0.60) | 0.13 (0.53) |
| Ministral| 0.55 | 0.08 (0.63) | 0.16 (0.57) |
| Qwen     | 0.50 | 0.03 (0.60) | 0.12 (0.59) |

So the diagonal is well clear of the *mean* off-diagonal, and the in-distribution discriminants
are mostly distinct — the stability column is not vacuous. **But the per-axis margin**
(diag − best competing off-diagonal refit) is where §6 is decided:

| axis | Apertus | Ministral | Qwen | read |
|------|--------:|----------:|-----:|------|
| confident | +0.55 | +0.20 | +0.53 | cleanly separable |
| reluctant | +0.35 | +0.24 | +0.32 | cleanly separable |
| warm | +0.53 | +0.43 | +0.36 | cleanly separable |
| curious | +0.44 | +0.26 | +0.08 | separable (thin on Qwen) |
| uncertain | +0.04 | +0.01 | +0.19 | **near-collinear with curious** |
| concern | +0.02 | **−0.09** | **−0.12** | **not separable from uncertain-OOD** |
| mischief | **−0.32** | **−0.37** | **−0.48** | **anti-separable** (closer to warm/curious) |

**What changed in the paper (your prediction was right — §6 changes substantially, but the
verdicts hold):**
- **concern**: the direction is *not* separable from the uncertain OOD-refit (margin ≤ +0.02,
  negative on 2/3 models). Its "real" verdict now rests **only on prompt-only (+83) and human
  (κ 0.70)** — the stability column can no longer be cited for it. §6 + §5.2 updated.
- **uncertain/curious**: added the geometric confirmation — each is the other's closest
  competitor, so they are barely two axes. Strengthens the "subjective" grouping with geometry,
  not just human disagreement.
- **mischief**: added anti-separability as a further independent signal (frozen mischief is
  closer to warm/curious refits than to its own). Reinforces the artifact verdict.
- **confident/reluctant/warm**: cleanly separable — B stands for these.

## 2. Three-rater human IRR — DONE

50 items (Miguel's call, not 100). Three blind raters via the web app + Numbers recovery.
Artifacts: `irr_human/multirater_kappa_results.md`, `compute_multirater_kappa.py`,
`canis_ratings.jsonl`.

- **Fleiss' κ = 0.42** across the three raters — vs the two-LLM-rater **0.89**. That contrast is
  now the paper's central number (folded into abstract + §5.2 + §6).
- Per-rater Cohen's κ vs original: **0.86 / 0.56 / 0.42**; human–human pairwise 0.26–0.56.
- Per-class agreement rewrites §6: **confident is the only unanimous axis** (7/7 × 3 + model);
  **reluctant breaks on the 3rd rater** (7/7, 7/7, **1/7**) → demoted from "rock-solid" to
  "agreed by 2 of 3"; **mischief spans 0/7, 7/7, 3/7** (humans read it completely differently —
  a sharper artifact story than "invisible to humans"); curious swings 7/7→0/7; uncertain low for all.

## 2b. Model-judge panel — the symmetric control (NEW, Miguel's idea)

Ran the *same* 50 items, blind, through a **four-model cross-family panel** (Gemini / Claude /
Codex / Mistral) — one PocketBase ticket per judge. Artifacts: `irr_human/two_panel_results.md`,
`compute_two_panel.py`, `model_ratings/*.json`.

- **Model-panel Fleiss κ = 0.89** vs **human-panel 0.42** — identical items, identical scale. The
  labels are a **model-native regularity**: four cross-family models converge, three humans don't.
  This is the paper's thesis in its strongest symmetric form (now in abstract + §5.2).
- Per-model κ vs labels 0.84–0.98; distinct patterns, none a key copy (43/43/49/49).
- **Honest nuance:** the *majority vote* of each panel recovers the labels (model 0.86, human 0.84)
  — labels aren't wrong; it's **individual human reliability** that collapses vs model reliability.
- **mischief**: all four models label it; humans span 0/7·3/7·7/7 — the sharpest artifact demo.
- Caveat (in §7): judges rated blind but the key lives in the repo; a sandboxed rerun would harden it.

## 3. The three smaller items — all DONE

**(a) Apertus reluctant drop & Ministral concern FP — retracted (per your Wilson note).**
Recomputed Wilson 95% CIs: Apertus reluctant OOD **53% [36–70]** (n=30); Ministral concern OOD FP
**27% [14–44]** (n=30). The Apertus CV→OOD reluctant drop is statistically real (CV [84–98] vs OOD
[36–70], non-overlapping) but the OOD magnitude is imprecise. §7 now states explicitly that **no
axis-level conclusion is drawn from either cell** — verdicts rest on the convergent
human/prompt-only/cross-axis evidence.

**(b) arXiv citations — verified against the live abstract pages.**
- `arXiv:2607.15495` = Gurnee, Sofroniew, Pearce, Piotrowski, Kauvar, *"Verbalizable Representations
  Form a Global Workspace in Language Models"* — J-space / Jacobian lens. ✔ matches.
- `arXiv:2608.18106` = Mazzaccara, Bertolazzi, Bernardi, *"Different Facets of Verbalised
  Overconfidence: an Interpretability Study"* — Qwen3-4B transcoder, certainty broad-coalition /
  uncertainty sparse-override asymmetry. ✔ matches.
Artifacts line updated to record the verification date.

**(c) SAE qualitative comparison — moved to Appendix A.** §5.3 is now a one-line pointer in the
body; the full text lives in Appendix A, flagged as corroboration (no SAE activations computed).

---

## Net effect on the paper
The taxonomy verdicts (**real** confident/reluctant/concern; **subjective** uncertain/curious;
**artifact** mischief) survive — but the *evidence basis* is now cleaner and more honest:
- concern is "real" on 2 of 3 tests, explicitly **not** on direction stability;
- uncertain/curious get geometric backing for "subjective";
- mischief gets a further nail;
- two noisy OOD cells are demoted to "no interpretation."

**Open / waiting on you & the evaluators:** the 3-rater IRR (50 items) is the only thing left to
close §6.3. Everything else in your review is applied.
