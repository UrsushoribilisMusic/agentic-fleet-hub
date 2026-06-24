# WORKLOG — EVAL-007: Matched-prompt fair test (Arm A vs B)

Task ID: 95bdwf1djmrmlo1
Branch: task/95bdwf1djmrmlo1
Agent: clau

## Plan

Run the 2-arm matched-prompt evaluation comparing base Apertus (Arm A) vs LoRA Apertus (Arm B),
both with identical system prompts and RAG context. Then Qwen-grade the results and generate the
blind batch for Opus grading.

### Pipeline steps
1. Complete the inference run (questions 35-49 remain from a partial prior run)
2. Run Qwen grader → results_eval007_graded.jsonl
3. Generate blind batch → blind_batch_eval007.jsonl + blind_reveal_eval007.json
4. Push to branch, post output to PocketBase, move to peer_review

### Pre-registered reading (from run_eval007.py)
- Arm B > Arm A composite → thesis supported: LoRA adds value at matched prompts
- Arm B ≈ Arm A           → v1 baking added little; DPO+r32 (v2) is the real test
- Arm B < Arm A           → thesis in trouble; investigate before more compute

### Models
- Arm A: MichelRosselli/apertus:8b-instruct-2509-q4_k_m (base + blurb)
- Arm B: apertus-flotilla:latest (LoRA + blurb)
- Judge: qwen2.5:7b

### Data
- Eval set: /Users/miguelrodriguez/projects/flotilla-corpus/out/datasets/eval.jsonl (50 questions)
- Note: DEFAULT_EVAL in run_eval007.py points to ~/projects/fx/ which doesn't exist; using flotilla-corpus path directly via continuation script.

## Steps done

1. ✅ Read MISSION_CONTROL.md, heartbeat protocol
2. ✅ git pull, active_context, inbox (all read)
3. ✅ Created branch task/95bdwf1djmrmlo1, pushed
4. ✅ Diagnosed state: 35/50 questions done (q0-34), 6 Arm B errors in existing results
5. ✅ Wrote run_eval007_continue.py — appends only missing questions to existing results
6. [ ] Run continuation (q35-49)
7. [ ] Run grade_eval007.py
8. [ ] Run gen_blind_batch_eval007.py
9. [ ] Commit + push + PocketBase output
