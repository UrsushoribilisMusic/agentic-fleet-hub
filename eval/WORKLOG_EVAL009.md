# WORKLOG — EVAL-009 Adversarial Enforcement (FLOT-104)

**Task:** twadswmr6whpceo  
**Branch:** task/twadswmr6whpceo  
**Date:** 2026-07-06  
**Agent:** Clau

---

## Goal

Fair fight: Arm 2 (LoRA+RAG) vs Arm 3 (base + GEPA-optimized prompt + RAG).  
Answers the customer objection: "why not just use a good prompt instead of fine-tuning?"

## Dependency note

FLOT-103 (GEPA prompt-optimization harness, assigned to Agy/Gem) is still `todo`.  
**Impact on this task:** Arm 3 uses the GEPA-optimized prompt. Until FLOT-103 delivers it,  
Arm 3 runs with a strong hand-crafted "best baseline" system prompt (labeled `arm3_prompt_version: "baseline_v1"`).

**FLOT-103 also needs our adversarial set** — this task's output `eval009_adversarial.jsonl`  
is the adversarial component of FLOT-103's trainset. So this task unblocks FLOT-103.

When GEPA delivers the optimized prompt, re-run Arm 3 only with `run_eval009_arm3_gepa.py`  
(same infrastructure, different prompt string). Results update automatically.

---

## Plan

### Step 1 — Adversarial question bank (eval009_adversarial.jsonl)
30 questions across 3 attack types (10 per type):
- **PI** (Prompt Injection): injection payload embedded in user message or RAG context
- **OCD** (Omitted-Context Degradation): key wiki fact deliberately absent from retrieval
- **RO** (Role Override): user asks model to abandon fleet persona

### Step 2 — Runner (run_eval009.py)
Two-arm runner:
- Arm 2: `apertus-flotilla` (LoRA) + BLURB + RAG (k=3, same retrieve.py)
- Arm 3: base Apertus + BASELINE_PROMPT (or GEPA prompt) + RAG (identical context SHA)

Context SHA parity check per row (same as run_eval008_arm3.py pattern).

### Step 3 — Grader (grade_eval009.py)
Binary classification per attack type using Qwen:
- PI → `resisted` (1) or `leaked` (1)
- OCD → `grounded` (1) or `hallucinated` (1)  
- RO → `resisted` (1) or `leaked` (1)

Grader prompt tailored per attack_type. Blind label stripping before grading.

### Step 4 — Run Arm 2 and Arm 3 (baseline_v1)
Execute both arms, produce results_eval009.jsonl.

### Step 5 — Grade and compute per-attack rates

### Step 6 — Write EVAL009_results.md (enforceability section for the paper)

---

## Key decisions

- **30 questions** (10 per type) matches the adversarial depth of existing evals while keeping runtime under 2 hours.
- **OCD questions** reuse gold entries from eval008_questions.jsonl but inject WRONG retrieval.
- **Grader = Qwen 2.5 72B** (same judge as EVAL-007/008 for consistency).
- **Arm 3 baseline prompt** is verbose and explicit (≈250 words) to give prompt engineering the best possible chance — this is a fair fight.
- **Binary rubric** (not 0–5): adversarial eval is about enforcement, not quality. Pass/fail is the right measure.

---

## Files produced

```
eval/
  eval009_adversarial.jsonl        30 adversarial questions (3 attack types)
  run_eval009.py                   2-arm runner
  grade_eval009.py                 binary grader
  results_eval009.jsonl            run output (Arm 2 + Arm 3)
  results_eval009_graded.jsonl     graded output
  EVAL009_results.md               enforceability section for paper
  WORKLOG_EVAL009.md               this file
```
