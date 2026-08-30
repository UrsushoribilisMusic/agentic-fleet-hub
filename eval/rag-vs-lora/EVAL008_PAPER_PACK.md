# EVAL-008 Paper Pack — RAG vs LoRA on a small open model

*Data request for the paper. Sources: `agentic-fleet-hub/eval/` (evaluation) and
`flotilla-corpus/` (LoRA training). Per-question scores are in `eval008_per_question.csv`.
Regenerate: `extract_eval008_paper.py` (Qwen), `aggregate_opus48.py` (Opus), then
`confound_eval008.py` (Task 3) and `contamination_eval008.py` (Task 4).*

---

## Bottom line (now on TWO independent graders)

The claim holds under a paired test on **both** graders — a small open-weight judge
(Qwen 2.5 7B) **and** Claude Opus 4.8 — which agree in direction and rank the arms
identically (**Base+RAG > LoRA+RAG > Base > LoRA**):

- **Retrieval provides the lift.** arm3 − arm0: Qwen **+1.10**, Opus **+2.61**; both p<0.0001.
- **The LoRA adapter does not help — under equal retrieval it hurts.** arm2 − arm3:
  Qwen **−1.02** (CI [−1.38,−0.69]), Opus **−0.92** (CI [−1.29,−0.57]); both p<0.0001;
  base+RAG wins the per-question head-to-head **33/49 on both graders**.

The mechanism is grounding, not length (Task 3): given identical retrieved context, the
base model cites the retrieved facts ~2× as often as the LoRA, which instead spends its
tokens on house-style formatting. Contamination is not detected and would only have helped
the LoRA anyway (Task 4). The training recipe is a standard, reasonable QLoRA config
(Task 2) — the adapter was not obviously "trained badly."

**Honest divergence, stated plainly:** the two graders differ on *arm2 − arm0* (full stack
vs plain base). Qwen calls it a wash (+0.08, n.s.) because it is generous to the no-RAG
base; Opus, which is harsh on no-RAG answers, says the full stack wins (+1.69). This does
**not** touch the core claim, which rests on the clean **equal-retrieval** arm2-vs-arm3
comparison, where both graders agree the LoRA hurts.

---

## Arm map

| Arm | Model | RAG | Role |
|-----|-------|-----|------|
| arm0 | `MichelRosselli/apertus:8b-instruct-2509-q4_k_m` (base) | no | floor |
| arm1 | `apertus-flotilla` (LoRA) | no | LoRA alone |
| arm2 | `apertus-flotilla` (LoRA) | yes (**k=3** BM25) | full stack (production) |
| arm3 | base | yes (**k=3** BM25) | **RAG-only control** |

arm2 and arm3 receive **byte-identical** retrieved context per question (SHA-verified);
the only variable across that pair is the model weights (LoRA vs base).

---

## 1. Per-question graded scores + paired contrasts  (Task 1)

**File: `eval008_per_question.csv`** — 49 rows: `qwen_arm0..3`, `opus_arm0..2` (old manual
pass), `opus48_arm0..3` (**the new pinned blind pass — use these**).

**Grader provenance (why we re-graded).** The pre-existing Opus grades
(`results_eval008_opus_graded.jsonl`) were an **unpinned manual pass**: `"grader":"opus-4"`
(no version/date), hand-written prose notes, and **arms 0–2 only** — arm3 was aggregate-only.
That cannot anchor a paired test. Per the "don't patch mismatched graders" rule, we
**re-graded all four arms in one pass with a single version.**

**New Opus pass.** Grader = **Claude Opus 4.8**, blind: seven independent grading sessions
each saw only *question + gold fact + four unlabelled candidate answers* (relabelled A/B/C/D
from the sealed 4-arm blind batch; the arm map was withheld). Same 3-dimension rubric as the
Qwen grader (grounded / correct / faithful_recall, 0–5). Reproducible pinned-API variant:
`grade_eval008_opus4.py` (set `ANTHROPIC_API_KEY` + a dated model snapshot for camera-ready).

**Paired contrasts** (bootstrap CI + sign-flip perm, seed 42, 10k; scipy Wilcoxon):

| Contrast | grader | Δ | 95% CI | Wilcoxon p | W/L/T |
|---|---|---|---|---|---|
| arm2−arm3 (LoRA vs base, equal RAG) | Qwen | −1.020 | [−1.381,−0.694] | <0.0001 | 5/33/11 |
| | **Opus 4.8** | **−0.918** | **[−1.286,−0.565]** | **<0.0001** | **7/33/9** |
| arm3−arm0 (RAG lift on base) | Qwen | +1.102 | [+0.762,+1.463] | <0.0001 | 31/3/15 |
| | **Opus 4.8** | **+2.605** | **[+2.197,+2.993]** | **<0.0001** | **46/2/1** |
| arm2−arm0 (full stack vs base) | Qwen | +0.082 | [−0.259,+0.429] | 0.64 (n.s.) | 22/18/9 |
| | **Opus 4.8** | **+1.687** | **[+1.279,+2.088]** | **<0.0001** | **41/6/2** |

**Arm means (side by side).** Both graders rank arms identically; Opus is much harsher on
the no-RAG arms.

| arm | Qwen | Opus 4.8 | (old manual Opus) |
|-----|------|----------|-------------------|
| arm0 Base/no-RAG | 3.286 | 1.517 | 1.00 |
| arm1 LoRA/no-RAG | 2.939 | 1.286 | 0.95 |
| arm2 LoRA+RAG | 3.367 | 3.204 | 2.40 |
| arm3 Base+RAG | 4.388 | 4.122 | 2.54 (aggregate-only) |

**Grader agreement.** Per-question Spearman(Qwen, Opus 4.8): pooled **ρ = +0.609** (p<0.0001,
n=196); per arm ρ = 0.42–0.62 — far above the old manual pass (κ ≈ 0.03–0.14).

**DIRECTION CHECK (arm2−arm3):** Qwen −1.020, Opus −0.918 → **graders AGREE** (both say the
LoRA does not help under equal retrieval). No stop condition. The old "2.54 vs 2.40 ≈ tie"
was an artifact of the unreliable manual pass, now resolved.

---

## 2. LoRA hyperparameters  (Task 2)

Recovered from `flotilla-corpus/docs/training.md` — the documented recipe stated to
**match the published `apertus-flotilla` adapter**. Two-stage QLoRA (SFT → DPO), unsloth+trl.

**Base:** `MichelRosselli/apertus:8b-instruct-2509`, loaded 4-bit; `max_seq_length = 4096`.
**LoRA (both stages):** `r = 16`, `lora_alpha = 16`, `lora_dropout = 0`, `bias = none`,
`target_modules = [q,k,v,o,gate,up,down]_proj`, unsloth gradient checkpointing.
**SFT:** 3 epochs, `lr = 2e-4` cosine, warmup 10, batch 2 × grad-accum 4 (eff. 8),
`adamw_8bit`, fp16.
**DPO:** 1 epoch, `lr = 5e-5`, `beta = 0.1`, batch 1 × grad-accum 8 (eff. 8), implicit ref model.
**Export:** merged to GGUF `q4_k_m`; served via Ollama (temp 0.7, top_p 0.9, num_ctx 16384).

**Explicitly UNRECOVERABLE:** actual training/validation **loss curves** — not persisted;
only `output_dir` checkpoints are referenced, and no checkpoints/logs survive on disk (the
adapter was merged+quantised into the GGUF, discarding `adapter_config.json` and trainer state).
**Caveat:** the above is the documented reproduction recipe, not a captured log of the exact
run; values are stated by the authors to match the published adapter. The config itself is
standard and reasonable (r=16, α=16, lr 2e-4 cosine, 3 epochs on 399 examples) — it does not
look under- or mis-trained, which is the relevant point for the "you trained it badly" objection.

---

## 3. Confound checks  (Task 3 — `confound_eval008.py`)

**Length (words = token proxy; tiktoken unavailable).** arm2 (LoRA+RAG) is the **longest**
arm (mean 271 w / 3568 ch), arm3 (Base+RAG) the **shortest** (189 w / 1247 ch); arm0 213 w,
arm1 233 w (median 209; a few very long outliers).

**Length↔grade Spearman.** Qwen has a real length bias (pooled ρ=+0.286, p<0.001; per-arm
arm0 +0.61, arm1 +0.47, arm2 +0.32, arm3 −0.04). Opus is much weaker (pooled ρ=+0.19).
**This does not explain the finding — it runs against it:** arm2 is the *longest* arm yet
scored *lower*, so a length-biased grader would have favoured the LoRA. The adapter lost
in spite of the length bias.

**Citation / grounding format (the mechanism).** Given identical retrieved context:

| arm | cites a fleet ID | cites the *correct* gold ID | mean IDs/answer |
|-----|------------------|-----------------------------|-----------------|
| arm2 LoRA+RAG | 24% | 8% | 0.43 |
| arm3 Base+RAG | **39%** | **16%** | **0.61** |

The base model grounds in the retrieved passages ~2× as often as the LoRA. Structural drift:
arm2 uses markdown headers 92% vs arm3 45%, and tables 37% vs 2%. **The adapter traded
grounding for house-style verbosity** — the candidate mechanism both for the grader-magnitude
gap and for the LoRA damage itself.

---

## 4. Contamination audit  (Task 4 — `contamination_eval008.py`)

Nearest-neighbour cosine (local `nomic-embed-text`, 768-d) between the 450 training items
(399 SFT + 51 DPO) and the 49 eval items:

| view | max top-1 | mean top-1 | items > 0.90 |
|------|-----------|------------|--------------|
| eval **question** vs training | 0.889 | 0.749 | **0** |
| eval **gold fact** vs training | 0.897 | 0.783 | **0** |

No eval item crosses the 0.90 near-duplicate threshold on either view; the nearest neighbours
(commit-ticket-ID, peer-review) are topical, not duplicated. (nomic cosines run high in
absolute terms — mean ≈ 0.75 for same-domain text — so 0.9 is the meaningful "near-identical"
line.) Contamination would bias **toward** the LoRA, which still lost, so this **hardens**
the claim rather than threatening it.

---

## 5. Rubric, questions, grader, retrieval (reference)

- **Rubric (EVAL-008):** 3 dimensions, 0–5 each — grounded / correct / faithful_recall
  (inline in `grade_eval008.py`). Composite = their mean. (`rubric.md` is the richer 4-dim
  EVAL-007 rubric, a different run.)
- **Questions:** 49 graded (50 generated) — for each of the **66 frozen gold wiki entries**
  (`eval/wiki/entries/`, all `created < 2026-06-22`, no FX- IDs), Qwen wrote a paraphrase-varied
  question answerable only from that entry; the entry is the retrieval target. Acceptance-checked
  on 10 samples (`gen_eval008_questions.py`).
- **Graders:** Qwen 2.5 7B (local, blind, grader ≠ any tested model) as the open-weight judge;
  **Claude Opus 4.8** (blind, this pack) as the independent second grader.
- **Retrieval (`retrieve.py`):** BM25, k1=1.5, b=0.75, tokenizer `[a-z0-9]+`, title weighted
  3×, whole-entry (no chunking), **top-k = 3** (runner default; stored `arm2_retrieved_k=3`).
- **Training data:** SFT 399 (409→399 after near-dup dedup; from corrections 233 / lessons 107 /
  tasks 69); DPO 51 (real peer-review chosen/rejected pairs); held-out eval 50 (`sha1 mod 8 == 0`).

---

## Open items (flagged explicitly)

| item | status |
|------|--------|
| Opus arm3 per-question (was the blocker) | **CLOSED** — all 4 arms graded per-question, single blind version |
| LoRA training/validation loss curves | **UNRECOVERABLE** — not persisted; adapter merged to GGUF, no trainer state on disk |
| Reproducible Opus grades vs a *dated API snapshot* | optional camera-ready: run `grade_eval008_opus4.py` with a key; current grades are Opus 4.8 via blind subagent sessions |
| Direct SFT/DPO ↔ eval overlap | **DONE** (Task 4) — no item > 0.90 |

Nothing was re-run to improve the numbers; the LoRA lost on both graders and every confound
check points the same way.

---

## File map (new/changed)

```
eval008_per_question.csv          per-question matrix: qwen_arm0..3, opus_arm0..2 (old), opus48_arm0..3 (new)
extract_eval008_paper.py          Qwen contrasts + CSV
prep_blind_grade.py               builds blind A/B/C/D batches + sealed answer_map.json
grading_opus48/                   batch_*.json (blind inputs) + graded_*.json (Opus 4.8 scores) + answer_map.json
aggregate_opus48.py               maps grades→arms, Opus contrasts, Spearman, direction check
results_eval008_opus48_4arm.jsonl per-question Opus 4.8 scores, all 4 arms
confound_eval008.py               Task 3 (length + citation)
contamination_eval008.py          Task 4 (cosine audit)
grade_eval008_opus4.py            reproducible pinned-API grader (for a dated snapshot re-run)
```
