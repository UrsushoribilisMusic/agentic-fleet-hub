#!/usr/bin/env python3
"""
EVAL-008: Generate blind batch for Opus morning grading + human validation.

For each graded row, shuffles the three arm answers into a randomised order
and strips arm labels. Writes:
  blind_batch_eval008.jsonl  — what Opus sees (no labels)
  blind_reveal_eval008.json  — sealed mapping (DO NOT open before grading)

Usage:
    python3 eval/gen_blind_batch_eval008.py \
        [--in    eval/results_eval008_graded.jsonl] \
        [--batch eval/blind_batch_eval008.jsonl] \
        [--reveal eval/blind_reveal_eval008.json]
"""
import argparse
import json
import pathlib
import random

random.seed(99)
LABELS = ["X", "Y", "Z"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in",     dest="inp", default="eval/results_eval008_graded.jsonl")
    parser.add_argument("--batch",  default="eval/blind_batch_eval008.jsonl")
    parser.add_argument("--reveal", default="eval/blind_reveal_eval008.json")
    args = parser.parse_args()

    rows = [json.loads(l) for l in pathlib.Path(args.inp).read_text().splitlines() if l.strip()]
    batch_path  = pathlib.Path(args.batch)
    reveal_path = pathlib.Path(args.reveal)

    reveal = {}
    batch_rows = []

    for row in rows:
        qid = row["question_id"]
        arms = [
            ("arm0", row["arm0_answer"]),
            ("arm1", row["arm1_answer"]),
            ("arm2", row["arm2_answer"]),
        ]
        random.shuffle(arms)

        mapping = {label: arm_key for label, (arm_key, _) in zip(LABELS, arms)}
        reveal[str(qid)] = mapping

        batch_row = {
            "question_id":     qid,
            "question":        row["question"],
            "gold_entry_id":   row["gold_entry_id"],
            "gold_entry_title":row["gold_entry_title"],
            "gold_entry_body": row["gold_entry_body"],
            "arm2_retrieved":  row.get("arm2_retrieved", []),
        }
        for label, (_, answer) in zip(LABELS, arms):
            batch_row[f"answer_{label}"] = answer

        batch_rows.append(batch_row)

    with batch_path.open("w") as f:
        for r in batch_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with reveal_path.open("w") as f:
        json.dump(reveal, f, indent=2)

    print(f"Blind batch: {batch_path}  ({len(batch_rows)} rows)")
    print(f"Reveal:      {reveal_path}  (sealed — do NOT open before grading)")
    print()
    print("Opus prompt hint:")
    print("  For each row: given the gold entry + question, grade answers X/Y/Z on:")
    print("  grounded (0–5), correct (0–5), faithful_recall (0–5).")
    print("  Identify which is best and whether any answer is clearly worse.")


if __name__ == "__main__":
    main()
