#!/usr/bin/env python3
"""
EVAL-008 4-arm blind batch generator.

Merges arm0/arm1/arm2 answers (from results_eval008.jsonl) with arm3 answers
(from results_eval008_arm3.jsonl) and re-shuffles all four arms into X/Y/Z/W
labels per row. Arm3 answers replace the per-row slot; all four are re-randomised
so no prior label from the 3-arm batch carries over.

Intersection: rows where arm0_ok AND arm1_ok AND arm2_ok AND arm3_ok.

Outputs:
  blind_batch_eval008_4arm.jsonl  — what Opus sees (answers X/Y/Z/W, no arm labels)
  blind_reveal_eval008_4arm.json  — sealed mapping (DO NOT open before grading)

Usage:
    python3 eval/gen_blind_batch_eval008_4arm.py \
        [--src3  eval/results_eval008.jsonl] \
        [--arm3  eval/results_eval008_arm3.jsonl] \
        [--batch eval/blind_batch_eval008_4arm.jsonl] \
        [--reveal eval/blind_reveal_eval008_4arm.json]
"""
import argparse
import json
import pathlib
import random

random.seed(199)
LABELS = ["X", "Y", "Z", "W"]


def load_jsonl(path: pathlib.Path) -> dict:
    rows = {}
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["question_id"]] = r
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src3",   default="eval/results_eval008.jsonl")
    parser.add_argument("--arm3",   default="eval/results_eval008_arm3.jsonl")
    parser.add_argument("--batch",  default="eval/blind_batch_eval008_4arm.jsonl")
    parser.add_argument("--reveal", default="eval/blind_reveal_eval008_4arm.json")
    args = parser.parse_args()

    src3  = load_jsonl(pathlib.Path(args.src3))
    arm3  = load_jsonl(pathlib.Path(args.arm3))

    # Intersection: all 4 arms must be OK
    qids = sorted(
        qid for qid in arm3
        if arm3[qid].get("arm3_ok")
        and qid in src3
        and src3[qid].get("arm0_ok")
        and src3[qid].get("arm1_ok")
        and src3[qid].get("arm2_ok")
        and arm3[qid].get("sha_parity", True)  # only include SHA-verified rows
    )

    print(f"4-arm intersection: {len(qids)} rows")

    reveal = {}
    batch_rows = []

    for qid in qids:
        s = src3[qid]
        a = arm3[qid]

        arms = [
            ("arm0", s["arm0_answer"]),
            ("arm1", s["arm1_answer"]),
            ("arm2", s["arm2_answer"]),
            ("arm3", a["arm3_answer"]),
        ]
        random.shuffle(arms)

        mapping = {label: arm_key for label, (arm_key, _) in zip(LABELS, arms)}
        reveal[str(qid)] = mapping

        batch_row = {
            "question_id":      qid,
            "question":         s["question"],
            "gold_entry_id":    s["gold_entry_id"],
            "gold_entry_title": s["gold_entry_title"],
            "gold_entry_body":  s["gold_entry_body"],
            "arm2_retrieved":   s.get("arm2_retrieved", []),
            "context_sha":      a.get("context_sha", ""),
        }
        for label, (_, answer) in zip(LABELS, arms):
            batch_row[f"answer_{label}"] = answer

        batch_rows.append(batch_row)

    batch_path  = pathlib.Path(args.batch)
    reveal_path = pathlib.Path(args.reveal)

    with batch_path.open("w") as f:
        for r in batch_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with reveal_path.open("w") as f:
        json.dump(reveal, f, indent=2)

    print(f"Blind batch (4-arm): {batch_path}  ({len(batch_rows)} rows)")
    print(f"Reveal (sealed):     {reveal_path}")
    print()
    print("Arm legend (sealed in reveal file):")
    print("  arm0 = base Apertus, no LoRA, no RAG")
    print("  arm1 = apertus-flotilla (LoRA), no RAG")
    print("  arm2 = apertus-flotilla (LoRA) + RAG k=3")
    print("  arm3 = base Apertus, no LoRA + RAG k=3  ← new control")
    print()
    print("Opus prompt hint:")
    print("  For each row: given the gold entry + question + retrieved context,")
    print("  grade answers X/Y/Z/W on: grounded (0-5), correct (0-5), faithful_recall (0-5).")
    print("  Identify best and worst answer.")


if __name__ == "__main__":
    main()
