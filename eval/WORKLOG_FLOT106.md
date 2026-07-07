# WORKLOG — FLOT-106: EVAL-010 multi-turn grounding decay

Task PB ID: hr00jlznntwcp57
Branch: task/hr00jlznntwcp57
Agent: clau

## Plan

Verify that the FLOT-105 session manager holds grounding over a 10-turn
conversation compared to a naive baseline that accumulates full history until
window saturation.

### Design

Two conditions on the same 5 multi-turn conversation threads (10 turns each):

**Condition A — Naive (no session manager)**
  Messages grow each turn: [system] [u:rag+q1] [a:a1] [u:rag+q2] ... [u:rag+qN]
  By turn 10, full history is in context. At small num_ctx settings this
  saturates the window, pushing early-turn facts out.

**Condition B — Session manager (FLOT-105)**
  Bounded context each turn: [system] [u: T2_summary | T1_cache | fresh_rag | q]
  T1 cache keeps fact IDs from all prior turns; T2 summarises intent.
  Window never grows unboundedly.

### Conversation thread design

Each 5-thread conversation is structured to test recall across the window:
  - Turn 1: Question targeting a specific fact F (wiki entry, verifiable)
  - Turns 2–8: Questions on unrelated facts (context noise / window pressure)
  - Turn 9: Noise + bridging
  - Turn 10: "Recall" question requiring the fact from turn 1

### Grounding score

After each turn, judge model (qwen2.5:7b) assigns grounding 0/1:
  1 = response correctly cites / uses the gold fact for that turn
  0 = response misses, hallucinates, or ignores the gold fact

Decay curve: mean grounding per turn (1–10) × condition.

### Files to produce
- eval/gen_eval010_multiturn.py    — builds multi_turn_threads.json
- eval/run_eval010.py              — runs both conditions, writes results_eval010.jsonl
- eval/grade_eval010.py            — judges grounding 0/1, writes results_eval010_graded.jsonl
- eval/report_eval010.py           — prints decay table + EVAL-010 verdict
- eval/multi_turn_threads.json     — static question set (committed)
- eval/results_eval010.jsonl       — run output (committed after run)
- eval/results_eval010_graded.jsonl — graded output (committed after grade)
- eval/EVAL010_report.md           — human-readable results

### Steps
1. [x] Branch + WORKLOG
2. [ ] Write multi_turn_threads.json (5 threads × 10 turns, with gold facts)
3. [ ] Write gen_eval010_multiturn.py (script that produced the json, for audit)
4. [ ] Write run_eval010.py
5. [ ] Write grade_eval010.py
6. [ ] Run harness
7. [ ] Write report_eval010.py + EVAL010_report.md
8. [ ] Commit + push; post output; set peer_review
