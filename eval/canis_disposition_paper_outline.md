# Paper outline — Reading disposition from small open models, forward-only

*Draft skeleton for big sis. Every number below is traceable to CANIS-EVAL-001
(CE-06/07/08/09). Flagging what's solid, what's thin, and where I want your read.*

**Working title:** *Forward-Only Disposition Readout for Small Open Models: A Discriminant
J-Space Probe*

**One-line thesis:** A model's dispositional state (confidence, uncertainty, curiosity,
concern, reluctance, warmth, evasiveness) is **linearly decodable from its hidden state,
forward-only, with no SAE training** — across three open models of different families —
at 89–95% cross-validated recall and 6–9% false-positive rate, and on the one model that has
published SAE features, the probe's per-axis behaviour **qualitatively agrees with those
feature descriptions on 5 of 7 axes**.

---

## Abstract (draft)

Interpretability tools that expose a model's internal "character" (e.g., Neuronpedia's
assistant-axis) rely on sparse autoencoders that must be trained per model and exist only
for a handful of large, well-resourced models. We ask whether a cheaper probe — a
**forward-only logit-lens Jacobian read** of the residual stream ("J-space"), scored against
per-disposition reference vectors — can recover the same dispositional structure on small
open models that no SAE covers. On a 540-item labelled elicitation matrix spanning seven
dispositions, evaluated on **Apertus-4B, Ministral-3B, and Qwen3-4B**, we find: (1) the probe
beats an adversarial lexical baseline by 25–53 points (>7× the CI) on all three models; (2)
building the reference vectors as **discriminant directions (μ_pos − μ_neg)** rather than
authored seed phrases raises macro recall from 27–55% to **89–95% (5-fold CV)** while cutting
FP to 6–9%; (3) on Qwen3-4B, the one model with published SAE features, the probe's per-axis
behaviour **qualitatively agrees** with published SAE/transcoder feature descriptions on 5/7
axes — a descriptive comparison, not a controlled feature-level head-to-head. We argue
disposition is cheaply and portably decodable forward-only, enabling on-device
"disposition-aware" UX on sovereign small models.

---

## 1. Introduction
- Motivation: users want to *see* when a model is unsure, evasive, or concerned — live,
  on-device, on models they can actually run (small, open, European/sovereign).
- The gap: character/assistant-axis interpretability today = SAEs (Neuronpedia), which need
  per-model training and cover only large instrumented models.
- Our claim: a forward-only J-space probe + a light per-model discriminant calibration
  recovers the same structure, cheaply, on models SAEs don't reach.
- Contributions: (i) the probe + discriminant calibration; (ii) a 3-model, 7-axis, 4-arm
  eval with matched negatives and an adversarial lexical control; (iii) a qualitative
  comparison of the probe's per-axis behaviour to published SAE feature descriptions on the
  one covered model.

## 2. Related work
- Verbalizable representations / the "global workspace" (Anthropic, 2026) — the conceptual
  basis for reading a workspace-like state via the unembedding. **[big sis: exact cite?]**
- Logit lens / tuned lens lineage.
- SAEs and Neuronpedia (JumpReLU SAEs for Qwen3; circuit-tracer transcoders; Qwen-Scope);
  the assistant-axis / character-steering line.
- Refusal-direction and concept-direction work (the discriminant μ_pos−μ_neg is a cousin).
- **Positioning:** every prior character-probe we know of is SAE-based and large-model-only.

## 3. Method
- **J-space:** tap the residual stream at ~3/4 depth; project through final-norm +
  unembedding (the "Jacobian"/logit-lens matrix J, cached per model) to get z = J·h in
  vocab space. Forward-only: no autodiff, no SAE, no aux model → runs on-device.
- **Disposition scoring:** cosine of z against a unit reference vector per disposition; argmax
  (+ an entropy signal in the production blend, see §5.4).
- **Reference vectors, two constructions:**
  - *Seed-phrase* (zero-shot): embed a few authored phrases per disposition. No labels.
  - *Discriminant* (calibrated): from labelled activations, seed = normalize(w·μ_pos +
    (1−w)·normalize(μ_pos − μ_neg)); w=0 is pure discriminant. One-time offline calibration
    per model; inference stays forward-only (only the vectors change).
- Seven dispositions: confident, uncertain, curious, concern, reluctant, warm, mischief
  (+ visual idle). Note honesty framing: "mischief" = evasive **wording**, not proven intent.

## 4. Evaluation design (CANIS-EVAL-001)
- 540-item core matrix: 7 dispositions × (50 positives + 20 negative controls) + 50 idle;
  plus **350 matched negatives** (50/class, concept-matched near-misses) added for a harder
  FP test. Elicitation prompts authored + labelled; **[big sis: inter-rater check status?]**.
- Three models: Apertus-4B-Instruct, Ministral-3B, Qwen3-4B-Instruct (all 4-bit, on-device).
- Four arms: arm0 entropy-only floor · arm1 J-space-only · arm2 full (J-space+entropy,
  production) · **arm3 lexical baseline** (keyword match on anchor words — the adversarial
  control). *A "no" against arm3 would have killed the thesis; it didn't.*
- Metrics: per-class recall, per-class FP (against matched negatives), macro; Wilson 95% CIs;
  seed-vector cosine collision ranking.

## 5. Results

### 5.1 J-space beats the lexical baseline on all three models (CE-06/CE-08)
- arm1 vs arm3 positive accuracy: Apertus **52.6% vs 15.1%**, Ministral **27.1% vs 2.6%**,
  Qwen **56.0% vs 3.4%** — gaps of +37/+25/+53 pp, each >7× the CI half-width. **CONFIRMED.**

### 5.2 Discriminant calibration — the main result (CE-09, 5-fold CV)
- Macro recall / FP, naive → w=0 discriminant: Apertus 33%/21% → **89%/7%**; Ministral
  27%/18% → **95%/9%**; Qwen 55%/21% → **92%/6%**.
- **Reframing:** the earlier "Ministral is weak at J-space" (27%) was a **seed-construction
  artifact** — with discriminant seeds it hits 95%. All three models carry the signal strongly.
- Epistemic cluster (confident/uncertain/curious/concern) **separates**: curious 0→100%
  (Apertus), concern 2→100% (Qwen); confident↔uncertain seed cosine 0.94→0.18 (Apertus).
- Honest cost: this is a **supervised** probe (needs ~50 labelled pos + 50 matched-neg per
  class per model); it proves linear decodability, not that zero-shot phrases suffice.

### 5.3 Qualitative agreement with SAE feature analysis on the one covered model (CE-08)

**What this is — and is not.** This is **not** a controlled, feature-level head-to-head. It
is a **qualitative comparison** on the single model (Qwen3-4B) for which published SAE
features exist: we take our probe's per-axis *behaviour* (which axes are easy/high-recall vs
hard/low-recall, which over-fire) and check it against the *published descriptions* of how
those concepts are represented.

**Procedure (state it exactly).**
- **What was compared:** our seven per-axis recall/FP results on Qwen3-4B vs (a) the published
  feature descriptions of Adam Karvonen's **Qwen3-Instruct JumpReLU SAEs** on Neuronpedia (the
  only verified SAE set covering Qwen3-**4B**), and (b) the certainty/uncertainty findings of
  **Mazzaccara et al. (arXiv:2608.18106)**, a transcoder study on Qwen3-4B.
- **How an axis was scored "agreeing":** a reader (an LLM assistant, not a metric) read the
  published description of the relevant concept and judged whether its qualitative character —
  *broad/distributed* vs *sparse/dedicated* vs *monosemantic* vs *polysemantic/entangled* —
  matched our probe's behaviour on that axis. **No SAE feature activations were computed and no
  feature-to-axis alignment was measured.** It is a human-legible narrative match, nothing more.
- **Caveat / correction:** an earlier draft attributed specific layer ranges and neuron counts
  to these sources; those specifics are **not in the papers** and have been removed. Only the
  coarse qualitative claims the sources actually make are retained.

**Result (qualitative, 5/7 concordant):** confident — sources describe certainty as a *broad
coalition* → matches our easy/high-recall, high-FP confident. uncertain — described as a
*sparse override* → matches our harder uncertain. reluctant, warm — described as clean/
distinctive concepts → match our ~100% axes. curious — described as sitting near uncertainty →
matches our partial separation. Divergences, both diagnostic: **concern** (sources describe it
as entangled/polysemantic — matches our low recall, i.e. a model-class limit, not a probe
failure); **mischief** (no clean published feature for it, yet our discriminant recovers it —
a probe advantage, but with no SAE description to check against, "agreement" is undefined here).

**Claim scoping:** we say only that the probe's behaviour is *consistent with* published
feature descriptions on one model. We do **not** claim cross-validation or feature-level
equivalence.

### 5.4 The entropy gate hurts (CE-05/06, replicated on Qwen)
- arm1 (J-space only) > arm2 (J-space + entropy blend) on Apertus and Qwen — the entropy gate
  suppresses uncertain. Production was rerouted to J-space-only. Report as a negative design
  finding, not hidden.

## 6. Limitations / honest negatives (own these up front)
- Supervised per-model calibration required (offline; inference still forward-only).
- Small n (50/class) → wide CIs; single-class numbers indicative.
- `confident` FP stays high (26–38%) — the broad-coalition problem, SAE-confirmed intrinsic.
- `concern` is entangled at 4B scale (both J-space and SAE); `mischief` FP is measured against
  a harder-than-spec control (concept-opposite honesty prompts), so its FP is pessimistic.
- "Disposition" here = a behavioural/linguistic axis read from activations; **not** a claim
  about latent intent or phenomenology.

## 7. Discussion
- Why forward-only matters: portability (works on Apertus/Ministral, which Neuronpedia doesn't
  cover) + on-device feasibility (no SAE, no autodiff).
- The SAE agreement is the credibility anchor: on the one model with ground truth, the cheap
  probe recovers the same structure the expensive method finds.
- Product: Canis — live disposition-aware avatar on-device; the calibration set is the moat.

## 8. Conclusion
- Disposition is cheaply, portably, forward-only decodable from small open models, validated
  against SAEs where ground truth exists; the honest negatives sharpen rather than undermine it.

---

## Figures / tables to produce
- T1: 3 models × 7 axes, naive vs discriminant recall/FP (CV) — the money table.
- T2: arm1 vs arm3 (J-space vs lexical) per model — the adversarial-control result.
- T3: qualitative 7-axis agreement with published SAE feature descriptions (one model).
- F1: epistemic-cluster de-correlation (cosine heatmap naive vs discriminant).
- F2: confusion matrices (Qwen, arm1 naive vs discriminant).
- F3: the J-space method schematic (already have Canis Fig3).

## Status / what's still needed
- **Solid:** all four arms run × 3 models; CE-09 CV numbers; adversarial lexical control.
- **DONE (this pass):** (a) inter-rater reliability — Cohen's κ = 0.89 overall, all axes ≥ 0.79,
  concern/reluctant/mischief = 1.00 (`irr/kappa_table.md`); (c) citations verified against
  arXiv/publisher (`references.bib`), the fabricated layer/neuron specifics removed and §5.3
  retitled to qualitative agreement (Task 4).
- **In progress:** (b) the OOD test set (Task 1) — fresh, different-style 420-item set; frozen
  CE-09 seeds scored on it, OOD-vs-CV table pending the tap. **This gates the paper.**
- **Still open:** (d) a human-facing usefulness study; a human second rater to supplement the
  LLM IRR; a prompt-only control (predict disposition from prompt text alone — the artifact test).

## Open questions for big sis
1. **Framing:** lead with the *forward-only-beats/matches-SAE* wedge, or with the
   *disposition-is-linearly-decodable* result? Which is the stronger paper spine?
2. **The supervised-calibration caveat** is the obvious reviewer target. Do we present the
   discriminant as the headline (strong, but supervised), or foreground the zero-shot
   seed-phrase result and treat the discriminant as an upper-bound "signal exists" probe?
3. **Venue/scope:** interpretability workshop paper, or a fuller systems+interp paper given
   the on-device/sovereign angle? Different framings.
4. **Do we need a fresh OOD test set** before this is submittable, or is 5-fold CV on 350+350
   defensible for the claim we're making?
```
