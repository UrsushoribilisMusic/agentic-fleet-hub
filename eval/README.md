# EVAL-007: Apertus LoRA Evaluation

**Research question:** Does LoRA fine-tuning on the Flotilla correction corpus improve Apertus's fleet-agent behaviour?

**Pre-registered reading (written before seeing any numbers):**
- Arm B > Arm A composite → thesis supported
- Arm B ≈ Arm A → v1 bake added little; DPO+r32 (v2) is the real test
- Arm B < Arm A → thesis in trouble; investigate before more compute

---

## Experiment design

Two-arm matched-prompt comparison. Both arms receive byte-identical system prompts and byte-identical RAG context per question. The only variable is the model weights.

| Arm | Model | Description |
|-----|-------|-------------|
| A (floor) | `MichelRosselli/apertus:8b-instruct-2509-q4_k_m` | Base Apertus, no LoRA |
| B (thesis) | `apertus-flotilla` (v1) / `apertus-v2` (v2) | LoRA fine-tuned on Flotilla corpus |

**Eval set:** 200 questions drawn from 4 sources:
- EVAL-003 (150 q): held-out questions generated from the Flotilla rules corpus
- corpus_corrections (32 q): real corrections from live agent sessions
- lessons (13 q): lessons-learned Q&A pairs
- tasks (5 q): task-tracking Q&A pairs

File: `eval/eval007_full.jsonl` (reconstructed from v1 results; 22 of 200 questions truncated at 300 chars in the results file — minor limitation).

---

## Scoring (Qwen grader)

Each Arm A and Arm B answer is graded on 4 dimensions by `qwen2.5:72b` (local, blind):

| Dimension | Description | Scale |
|-----------|-------------|-------|
| `action_correct` | Does the response take the right action? | 1–5 |
| `grounded` | Is the answer grounded in the retrieved wiki? | 1–5 |
| `fleet_domain` | Does it respect fleet scope / project boundaries? | 1–5 |
| `completeness` | Is the response complete relative to the question? | 1–5 |

Composite = mean of all four dimensions across all rows.

---

## File map

```
eval/
  eval007_full.jsonl            200-question eval set (reconstructed from v1 results)
  run_eval007.py                Full 2-arm runner (Arm A + Arm B, both fresh)
  run_eval007_v2_armb.py        Arm-B-only rerun — reuses Arm A from a previous run
  run_eval007_continue.py       Resume interrupted run from checkpoint
  grade_eval007.py              Qwen grader
  gen_blind_batch_eval007.py    Produces blind batch for Opus/human grading
  chain_eval007.py              Autonomous chain: runner → grader → blind batch → Telegram
  retrieve.py                   RAG retrieval from the wiki corpus

  results_eval007.jsonl         v1 run: 200 questions, Arm B = apertus-flotilla (v1 LoRA)
  results_eval007_graded.jsonl  v1 graded (171 rows where both arms OK)
  blind_batch_eval007.jsonl     v1 blind batch for Opus grading
  blind_reveal_eval007.json     v1 arm identity reveal (do NOT open before grading)

  results_eval007_v2_full.jsonl v2 run: 200 questions, Arm B = apertus-v2 (SFT+DPO LoRA)
  results_eval007_v2_full_graded.jsonl  v2 graded (generated after run)
```

---

## v1 results (apertus-flotilla, 200 questions, 171 graded)

| Metric | Arm A | Arm B | Delta |
|--------|-------|-------|-------|
| Composite | ~4.0 | ~3.5 | −0.54 |
| action_correct | — | — | — |
| grounded | — | — | −0.80 |
| fleet_domain | — | — | −0.12 |
| completeness | — | — | — |

**Verdict: THESIS IN TROUBLE** — Arm B (v1 LoRA) underperformed Arm A across all dimensions. Grounding was worst.

---

## v2 results (apertus-v2 SFT+DPO, 200 questions, 171 graded)

| Metric | Arm A | Arm B | Delta |
|--------|-------|-------|-------|
| **Composite** | **4.044** | **3.022** | **−1.022** |
| action_correct | 3.789 | 2.632 | −1.157 |
| grounded | 4.140 | 2.977 | −1.163 |
| fleet_domain | 4.018 | 3.439 | −0.579 |
| completeness | 4.228 | 3.041 | −1.187 |

29/200 Arm B timeouts (600 s). Same count as v1 (29 dropped).

**Verdict: THESIS IN TROUBLE** — v2 LoRA (SFT+DPO) is worse than v1 LoRA on all dimensions. Delta widened from −0.54 (v1) to −1.022 (v2). Fleet domain closest to parity (−0.58). Grounding and completeness worst.

### apertus-v2 GGUF fix (2026-06-25)

The apertus-v2 GGUF (`sha256-1fef6862…`) had a broken embedded Jinja2 chat template (TypeScript tool-calling macros), causing every Ollama request to crash llama-server with "Automatic parser generation failed". Fixed by in-place byte patch at offset 7,860,109 — replaced broken 14,601-byte template with the working flotilla template (exact same length, no file copy or manifest change needed).

---

## How to restart a run

```bash
# Arm B only (reuses Arm A from v1):
nohup python3 -u eval/run_eval007_v2_armb.py \
  --prev eval/results_eval007.jsonl \
  --eval eval/eval007_full.jsonl \
  --out  eval/results_eval007_v2_full.jsonl \
  --arm-b apertus-v2 --timeout 600 >> /tmp/eval007_v2.log 2>&1 &

# Then grade:
python3 eval/grade_eval007.py \
  --in  eval/results_eval007_v2_full.jsonl \
  --out eval/results_eval007_v2_full_graded.jsonl

# Then blind batch:
python3 eval/gen_blind_batch_eval007.py \
  --in    eval/results_eval007_v2_full_graded.jsonl \
  --batch eval/blind_batch_eval007_v2.jsonl \
  --reveal eval/blind_reveal_eval007_v2.json
```

---

## Model notes

- Base: `MichelRosselli/apertus:8b-instruct-2509-q4_k_m` — 8.1B custom architecture (`general.architecture: apertus`), uses `xielu` activations, Tekken tokenizer, 65536 context, RoPE freq 12M. Swiss open model.
- v1 LoRA: `apertus-flotilla` — SFT fine-tune on Flotilla correction corpus
- v2 LoRA: `apertus-v2` — SFT + DPO pass on same corpus

Both LoRA models are fully merged (no adapter files — the weights are baked in). GGUF blob: `sha256-1fef6862...` (5.1 GB, patched template).

The apertus architecture is NOT standard Mistral/LLaMA. It requires Ollama's Go-layer template rendering — running llama-server directly produces garbage output for this architecture.
