# Which Dispositions Are Real? Three Validity Tests for a Forward-Only Disposition Readout on Small Open Models

*Draft — 29 Aug 2026. All numbers traceable to CANIS-EVAL-001 artifacts. Refs in `references.bib`.*

---

## Abstract

We ask whether a language model's *disposition* — confidence, uncertainty, curiosity,
concern, reluctance, warmth, evasiveness — can be read from its hidden state, forward-only,
on small open models, and whether such a readout measures what it claims. Using a Jacobian
logit-lens ("J-space") scored against per-disposition **discriminant directions**
(μ_pos − μ_neg), a light supervised calibration lifts macro recall from 27–55% (authored seed
phrases) to **89–95% five-fold cross-validated** at 6–9% false-positive rate, across Apertus-4B,
Ministral-3B, and Qwen3-4B. But a high supervised score is not evidence that the probe reads
the *model*, or that the axis is a real construct. We therefore subject seven candidate axes to
**three orthogonal validity tests**: (i) out-of-distribution generalization with frozen seeds on
a deliberately different-style test set; (ii) a **prompt-only control** (a text classifier with
no model access); and (iii) **human** inter-rater reliability against the labels. The three tests
partition the axes into three kinds: **real** (confident, reluctant, concern — generalize,
beat text-only, human-valid), **subjective** (uncertain/curious — the model represents them
stably but human raters cannot agree on the label), and **artifact** (mischief — high
in-distribution recall and perfect model-to-model agreement, yet exposed as prompt-surface
leakage by all three controls). We argue the contribution is not "seven axes at 90%" but a
reusable method for telling a real internal signal from an apparent one, and an honest map of
where small-model disposition readout does and does not hold.

---

## 1. Introduction

There is growing interest in surfacing a model's internal "character" or state to users — is it
sure, is it hedging, is it evading. On small open models one would like this **on-device and
forward-only**, without training a sparse autoencoder per model. A supervised probe makes this
easy to *appear* to solve: fit reference directions from labelled activations and report high
recall. The trap is that such a number can be high for the wrong reasons — the probe may be
reading **prompt style** rather than the model's state, or the **label** it is scored against may
not name a construct humans agree on.

We take the readout seriously enough to try to break it. We build the probe, calibrate it, and
then run three tests that a genuine disposition axis must survive: it should **generalize** to a
differently-worded test set with the calibration frozen; it should **beat a prompt-only baseline**
that never sees the model; and its labels should be **reproducible by a human**. Applied to seven
axes on three models, the tests do not uniformly pass — and the pattern of failures is the result.

**Contributions.** (1) A forward-only discriminant J-space readout that reaches 89–95% CV recall
on three small open models. (2) A three-test validity protocol (OOD-frozen, prompt-only, human
IRR) that separates a real internal signal from an apparent one. (3) The resulting taxonomy —
**real / subjective / artifact** — including a fully worked artifact case (mischief) that looks
real on every in-distribution metric and fails every control.

## 2. Related work

The readout builds on the **logit lens** (nostalgebraist, 2020) and **tuned lens** (Belrose et
al., 2023, arXiv:2303.08112), and on the observation that verbalizable content forms a small
"global workspace" readable via a Jacobian lens (Gurnee et al., 2026, arXiv:2607.15495). The
discriminant-direction construction is a cousin of **concept/refusal directions** (Arditi et al.,
NeurIPS 2024, arXiv:2406.11717; concept cones, Wollschläger et al., 2025, arXiv:2502.17420).
Where "character" is exposed today it is via **sparse autoencoders** (JumpReLU SAEs,
Rajamanoharan et al., 2024, arXiv:2407.14435; Karvonen's Qwen3 SAEs and Qwen-Scope on
Neuronpedia) — which require per-model training and exist only for a few models. The
certainty-vs-uncertainty asymmetry we observe echoes a transcoder study on Qwen3-4B (Mazzaccara
et al., 2026, arXiv:2608.18106).

## 3. Method

**J-space.** Tap the residual stream at ~3/4 depth; project through the model's own unembedding
(the Jacobian lens) to a vocab-space vector z = J·h. Forward-only: no autodiff, no auxiliary
model, runs on-device.

**Reference directions.** Score z by cosine against one unit reference vector per disposition;
predict argmax. We compare two constructions: *authored seed phrases* (zero-shot) and a
**discriminant direction**, seed = unit(μ_pos − μ_neg), estimated from labelled positives and
concept-matched negatives. The discriminant requires a one-time offline calibration
(~50 pos + 50 matched-neg per class per model); inference stays forward-only.

**Three validity tests.** (i) **OOD-frozen:** freeze the calibrated seeds; score a fresh,
deliberately different-style test set. (ii) **Prompt-only control:** a TF-IDF + logistic-
regression classifier on the prompt text alone (no activations); if it matches the probe, the
"signal" is in the prompt. (iii) **Human IRR:** a person, blind to the labels, re-rates a sample;
Cohen's κ against the original labels measures whether the label names a human-reproducible
construct.

## 4. Evaluation design

**Core matrix (CANIS-EVAL-001):** 540 items — 7 axes × (50 positives + 20 controls) + 50 idle —
plus **350 concept-matched negatives** (50/class) for a hard false-positive test. Three models:
Apertus-4B, Ministral-3B, Qwen3-4B (all 4-bit, on-device).

**OOD set:** 420 items, **30 positives + 30 matched-negatives per class (balanced; none thinner)**,
authored by a separate process blind to the originals, with an explicit mandate to differ in
**register** (casual/formal/technical/narrative vs the originals' short factual style),
**domain** (medicine, law, software, cooking, finance, relationships, …), **length** (1–4
sentences vs short), and **grammatical person**, and *not* to lean on disposition keywords so the
signal comes from the situation, not the wording. Independence is a limitation we state
plainly (§7): the authors were LLM agents, not a wholly separate human corpus.

**Human rating:** 50 items sampled ~7/class, rated blind by a human.

**Prompt-only control:** trained on the core-matrix positives, tested on the same 420 OOD items,
scored identically to the probe.

## 5. Results

### 5.1 The discriminant readout (in-distribution)

Building reference directions as discriminants rather than authored phrases raises macro recall
from **27–55% → 89–95% (5-fold CV)** at 6–9% FP, on all three models. Notably the earlier
impression that "Ministral is weak for this readout" (27% naive) was a **seed-construction
artifact**: with discriminant seeds Ministral reaches 95%. The signal is present in all three.

### 5.2 The three tests, per axis

Full per-class results (CV recall/FP; OOD recall/FP with frozen seeds; **B** = cosine between the
frozen in-distribution discriminant and an OOD-refit discriminant — direction stability):

| Model | axis | CV rec | CV FP | OOD rec | OOD FP | B |
|-------|------|-------:|------:|--------:|-------:|---:|
| Apertus | confident | 98% | 26% | 100% | 0% | 0.59 |
| | uncertain | 88% | 6% | 90% | 3% | 0.65 |
| | curious | 100% | 10% | 87% | 10% | 0.58 |
| | concern | 90% | 0% | 93% | 3% | 0.49 |
| | reluctant | 94% | 0% | 53% | 0% | 0.86 |
| | warm | 94% | 0% | 93% | 0% | 0.77 |
| | **mischief** | 62% | 10% | **33%** | 17% | **0.22** |
| Ministral | confident | 100% | 38% | 83% | 0% | 0.49 |
| | uncertain | 100% | 12% | 77% | 7% | 0.64 |
| | curious | 98% | 6% | 80% | 7% | 0.69 |
| | concern | 96% | 0% | 87% | 27% | 0.42 |
| | reluctant | 92% | 0% | 73% | 0% | 0.73 |
| | warm | 84% | 0% | 100% | 0% | 0.68 |
| | **mischief** | 94% | 4% | **60%** | 13% | **0.17** |
| Qwen | confident | 100% | 20% | 87% | 3% | 0.60 |
| | uncertain | 94% | 2% | 70% | 0% | 0.69 |
| | curious | 96% | 16% | 100% | 7% | 0.60 |
| | concern | 100% | 0% | 80% | 0% | 0.28 |
| | reluctant | 100% | 0% | 83% | 0% | 0.63 |
| | warm | 92% | 0% | 67% | 0% | 0.59 |
| | **mischief** | 64% | 2% | **3%** | 0% | **0.12** |

Macro OOD recall is 79/80/70% (Apertus/Ministral/Qwen) vs **45% for the prompt-only control** and
~3–15% for a lexical baseline — so *in aggregate* the probe reads the model, not the prompt.

**Prompt-only gap** (J-space − prompt-only recall, avg over models): concern **+83**, curious
+52, uncertain +46, reluctant +30, confident +23, warm ≈ 0, **mischief −14**.

**Human IRR:** overall Cohen's κ = **0.56** (vs an LLM-rater's 0.89 — the LLM agreement was an
inflated shared prior). Per class: confident **0.92**, reluctant **0.92**, concern 0.70, warm
0.70, curious 0.59, **uncertain −0.13 (0/7)**, **mischief 0.00 (0/7)**.

### 5.3 Qualitative agreement with SAE feature analysis (one model)

**This is not a controlled head-to-head.** On Qwen3-4B — the one model with published SAE
features — a reader (an LLM assistant) compared the probe's per-axis *behaviour* to the
published *descriptions* of Karvonen's Qwen3-4B JumpReLU SAE features and the Mazzaccara et al.
transcoder study; no SAE activations were computed and no feature-to-axis alignment was measured.
On that qualitative basis the probe's behaviour is *consistent with* the descriptions on 5/7
axes (e.g. certainty as a broad coalition → our high-recall/high-FP confident; uncertainty as a
sparse override → our harder uncertain). We report this as corroboration, not validation, and
we explicitly removed layer/neuron figures an earlier draft had attributed to these papers but
that do not appear in them.

## 6. The taxonomy

The three tests partition the seven axes:

**Real** — generalize OOD, beat prompt-only, human-reproducible:
- **reluctant** (human κ 0.92; highest direction stability B≈0.6–0.86; +30 over text) and
  **confident** (κ 0.92; +23) are the clearest.
- **concern** is real and the *most model-dependent* axis: it beats prompt-only by **+83**
  (a person cannot read it from the text, the model can), human κ 0.70. Its direction is
  less stable on Qwen (B 0.28) — a caveat, not a disqualifier.
- **warm** generalizes and is human-valid (κ 0.70) but has ~0 prompt-only gap — its signal is
  partly **lexical** (gratitude words). Real, with a surface confound worth flagging.

**Subjective** — the model represents them, humans don't agree on the label:
- **uncertain / curious.** Both generalize OOD and beat prompt-only, and uncertain's direction is
  *stable* (B 0.64–0.69). But the human labelled **0/7** "uncertain" items as uncertain (reading
  them as curious or confident), and κ = −0.13. The distinction between "the model is unsure" and
  "the model is exploring" is **rater-dependent** — a curious rater and an anxious rater label the
  same open question differently. The axis is real in the model's geometry; its *ground truth* is
  subjective. This is itself a finding: disposition perception depends on the perceiver.

**Artifact** — looks real in-distribution, fails every control:
- **mischief.** In-distribution it is unremarkable-to-strong (CV 62–94%) and shows *perfect*
  model-to-model agreement (κ=1.00 between two LLM raters). Yet it **collapses OOD** (Qwen 64→3%),
  a **prompt-only classifier beats it** (−14), its **direction does not transfer** (B 0.12–0.22,
  lowest by far), and a **human labels 0/7** of its items as mischief. Four independent controls
  agree: the "signal" is **prompt-surface phrasing**, not an internal state. Importantly, what was
  tested is *evasive wording*, not a model's *intent* to act without authorization; the latter is
  a distinct, unsolved problem we do not claim to touch. Mischief is the paper's cautionary case —
  the axis that proves the controls are load-bearing.

## 7. Limitations

- **Supervised calibration.** The discriminant needs labelled data per model; it demonstrates
  linear decodability, not a zero-shot capability. (Authored seed phrases, which need no labels,
  reach only 27–55%.)
- **OOD independence.** The OOD authors were LLM agents with a documented differ-in-style mandate,
  not a wholly independent human corpus. A human-authored OOD set would be stronger.
- **Human rating: one rater, n=7/class.** κ is indicative, not tight; a multi-rater human study is
  the obvious next step — and would let us *measure* the uncertain/curious subjectivity rather
  than assert it.
- **Production check.** When the discriminant seeds were briefly deployed to a live server, a
  quick sanity test on fresh casual prompts showed **mischief over-firing** — plain confident,
  uncertain, and reluctant prompts were classified as mischief — and the change was **rolled back
  within minutes**. This operational failure is consistent with, and corroborates, the offline
  finding that mischief keys on prompt surface; we report it as evidence, not an ops footnote.
- **`confident` over-fires** in-distribution (FP 20–38%) — consistent with a broad-coalition
  representation; it tightens out-of-distribution but is the readout's noisiest axis.

## 8. Conclusion

Disposition is linearly and cheaply decodable, forward-only, from small open models — but "90%
recall" is not the claim that matters. Subjecting seven axes to OOD, prompt-only, and human
tests yields a map: some axes are real internal signals (confident, reluctant, concern), one pair
is real-but-subjectively-labelled (uncertain/curious), and one is a prompt-style artifact that
looks real until the controls expose it (mischief). The reusable result is the **method** for
drawing that map — and the discipline of trusting the controls over the headline number.

---

*Artifacts: `ce09_results.json` (CV), `ood_results.json` (OOD), `ood_cosine_B.json` (direction
stability), `promptonly_results.json`, `irr/kappa_table.md` (LLM IRR), `irr_human/human_kappa.md`
(human IRR), `canis_eval001_ood_matrix.jsonl` (OOD set), `references.bib` (verified).*
