#!/usr/bin/env python3
"""
FLOT-106: Generate multi_turn_threads.json for EVAL-010.

5 threads × 10 turns.  Structure per thread:
  - Turn 1:   Question targeting the anchor fact (gold = anchor entry)
  - Turn 2-9: Noise questions on unrelated entries (context pressure)
  - Turn 10:  Recall question requiring anchor fact stated at turn 1

The same 8 noise entries are used across all 5 threads (turns 2-9) so that
the window-pressure is identical between conditions; only the anchor differs.

Run:
    python3 eval/gen_eval010_multiturn.py
Output: eval/multi_turn_threads.json
"""
import json, pathlib

OUT = pathlib.Path(__file__).parent / "multi_turn_threads.json"

# ── noise entries used for turns 2–9 (same across all threads) ───────────────
NOISE_TURNS = [
    {
        "turn": 2,
        "gold_entry_id": "F002",
        "question": (
            "How many total tasks exist in the PocketBase collection, and what is "
            "their approval status breakdown?"
        ),
        "check_phrase": "760",
    },
    {
        "turn": 3,
        "gold_entry_id": "R10",
        "question": (
            "What must be included in every peer review output comment according to "
            "the documented rule, and why?"
        ),
        "check_phrase": "commit hash",
    },
    {
        "turn": 4,
        "gold_entry_id": "F007",
        "question": (
            "How many lessons are in the lessons corpus and how are they distributed "
            "across categories?"
        ),
        "check_phrase": "382",
    },
    {
        "turn": 5,
        "gold_entry_id": "P003",
        "question": (
            "Describe the inter-agent handoff protocol — how do agents send and "
            "receive messages between sessions?"
        ),
        "check_phrase": "inbox.json",
    },
    {
        "turn": 6,
        "gold_entry_id": "I001",
        "question": (
            "What happened during the TCR-15 reassignment death spiral incident, "
            "and how was it resolved?"
        ),
        "check_phrase": "circuit breaker",
    },
    {
        "turn": 7,
        "gold_entry_id": "F017",
        "question": (
            "Which agent logged the most active days in standup data, and which "
            "agent had the fewest?"
        ),
        "check_phrase": "tcr_scout",
    },
    {
        "turn": 8,
        "gold_entry_id": "R27",
        "question": (
            "Why is self-approval of tasks prohibited in the fleet protocol, and "
            "what status should an agent set instead?"
        ),
        "check_phrase": "peer_review",
    },
    {
        "turn": 9,
        "gold_entry_id": "F004",
        "question": (
            "How many task events are in the task_events collection, and what is "
            "the most common event type?"
        ),
        "check_phrase": "143,936",
    },
]

# ── 5 anchor threads ──────────────────────────────────────────────────────────
ANCHORS = [
    {
        "thread_id": 0,
        "anchor_entry_id": "F003",
        "anchor_title": "Agent workload distribution across all tasks",
        "turn_1_question": (
            "What is the task assignment distribution across all agents in the fleet? "
            "Provide the count for each agent."
        ),
        "turn_10_question": (
            "Earlier in our conversation you described the task assignment counts for "
            "each fleet agent. Can you recall those exact numbers — specifically how "
            "many tasks clau handled and what percentage that represented?"
        ),
        "turn_1_check_phrase": "290",        # clau=290
        "turn_10_check_phrase": "290",        # must recall clau=290
    },
    {
        "thread_id": 1,
        "anchor_entry_id": "F012",
        "anchor_title": "SFT dataset: 409 records from corrections, lessons, and tasks",
        "turn_1_question": (
            "What does the SFT training dataset contain, and how many records does it "
            "have in total? Where did the records come from?"
        ),
        "turn_10_question": (
            "Going back to what you told me at the start of our conversation — what "
            "was the total record count in the SFT dataset, and how was it broken down "
            "by source?"
        ),
        "turn_1_check_phrase": "409",
        "turn_10_check_phrase": "409",
    },
    {
        "thread_id": 2,
        "anchor_entry_id": "F006",
        "anchor_title": "Git repository stats: 4,964 commits, 1.94M insertions (pre-cutoff)",
        "turn_1_question": (
            "What are the combined git repository statistics for the agentic-fleet-hub "
            "and silicon-oracle repos — how many commits and how many insertions?"
        ),
        "turn_10_question": (
            "At the beginning of our conversation you described the combined git "
            "repository stats. Can you recall the commit count and total insertions "
            "you mentioned?"
        ),
        "turn_1_check_phrase": "4,964",
        "turn_10_check_phrase": "4,964",
    },
    {
        "thread_id": 3,
        "anchor_entry_id": "F008",
        "anchor_title": "Circuit breaker threshold: 3 reassignments in 10 minutes triggers block",
        "turn_1_question": (
            "What is the exact threshold that triggers the dispatcher circuit breaker, "
            "and what action does it take when triggered?"
        ),
        "turn_10_question": (
            "Earlier you explained the circuit breaker trigger condition. What were the "
            "exact numbers — how many reassignments in what time window?"
        ),
        "turn_1_check_phrase": "3",           # 3 reassignments
        "turn_10_check_phrase": "3",
    },
    {
        "thread_id": 4,
        "anchor_entry_id": "F016",
        "anchor_title": "Fleet active period: 2026-03-10 to 2026-06-22 (105 calendar days)",
        "turn_1_question": (
            "What is the fleet's active period in terms of date range, number of "
            "calendar days, and total sessions recorded in standups?"
        ),
        "turn_10_question": (
            "Recall what you told me at the start of our conversation about the fleet's "
            "active period — what were the start and end dates and how many sessions "
            "were recorded?"
        ),
        "turn_1_check_phrase": "105",         # 105 calendar days
        "turn_10_check_phrase": "105",
    },
]


def build_thread(anchor: dict) -> dict:
    turns = []
    # Turn 1 — anchor
    turns.append({
        "turn": 1,
        "gold_entry_id": anchor["anchor_entry_id"],
        "question": anchor["turn_1_question"],
        "is_anchor": True,
        "is_recall": False,
        "check_phrase": anchor["turn_1_check_phrase"],
    })
    # Turns 2–9 — noise
    for nt in NOISE_TURNS:
        turns.append({**nt, "is_anchor": False, "is_recall": False})
    # Turn 10 — recall
    turns.append({
        "turn": 10,
        "gold_entry_id": anchor["anchor_entry_id"],
        "question": anchor["turn_10_question"],
        "is_anchor": False,
        "is_recall": True,
        "check_phrase": anchor["turn_10_check_phrase"],
    })
    return {
        "thread_id": anchor["thread_id"],
        "anchor_entry_id": anchor["anchor_entry_id"],
        "anchor_title": anchor["anchor_title"],
        "turns": turns,
    }


def main() -> None:
    threads = [build_thread(a) for a in ANCHORS]
    OUT.write_text(json.dumps(threads, indent=2))
    print(f"Written {len(threads)} threads ({sum(len(t['turns']) for t in threads)} turns) → {OUT}")


if __name__ == "__main__":
    main()
