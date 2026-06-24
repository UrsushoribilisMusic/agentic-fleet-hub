#!/usr/bin/env python3
"""
EVAL-007: Generate blind batch for Opus grading.

Reads results_eval007_graded.jsonl (intersection rows), shuffles arm_a/arm_b/arm_ref
→ X/Y/Z per question (seeded on question_id for reproducibility), and emits:

  blind_batch_eval007.jsonl  — question, gold, retrieved_entries, answers {X, Y, Z}
  blind_reveal_eval007.json  — sealed: {question_id: {X: "arm_a", Y: "arm_b", Z: "arm_ref"}}

The reveal file must be sealed (not passed to Opus) until all grading is done.

Usage:
    python3 eval/gen_blind_batch_eval007.py [--in eval/results_eval007_graded.jsonl]
                                            [--batch eval/blind_batch_eval007.jsonl]
                                            [--reveal eval/blind_reveal_eval007.json]
"""
import argparse
import json
import pathlib
import random
import sys

DEFAULT_IN     = pathlib.Path(__file__).parent / "results_eval007_graded.jsonl"
DEFAULT_BATCH  = pathlib.Path(__file__).parent / "blind_batch_eval007.jsonl"
DEFAULT_REVEAL = pathlib.Path(__file__).parent / "blind_reveal_eval007.json"

LABELS = ["X", "Y", "Z"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in",     dest="in_path",     default=str(DEFAULT_IN))
    parser.add_argument("--batch",  dest="batch_path",  default=str(DEFAULT_BATCH))
    parser.add_argument("--reveal", dest="reveal_path", default=str(DEFAULT_REVEAL))
    args = parser.parse_args()

    in_path     = pathlib.Path(args.in_path)
    batch_path  = pathlib.Path(args.batch_path)
    reveal_path = pathlib.Path(args.reveal_path)

    if not in_path.exists():
        print(f"[ERROR] Input not found: {in_path}", file=sys.stderr); sys.exit(1)

    rows = [json.loads(l) for l in in_path.read_text().splitlines() if l.strip()]
    eligible = [r for r in rows if r.get("arm_a_ok") and r.get("arm_b_ok") and r.get("arm_ref_ok")]
    print(f"Loaded {len(rows)} rows, {len(eligible)} in intersection")

    reveal = {}
    batch_path.parent.mkdir(parents=True, exist_ok=True)

    with batch_path.open("w") as bf:
        for row in eligible:
            qid = row["question_id"]
            rng = random.Random(qid)
            arms = ["arm_a", "arm_b", "arm_ref"]
            rng.shuffle(arms)
            mapping = {LABELS[i]: arms[i] for i in range(3)}
            reveal[str(qid)] = mapping

            batch_row = {
                "question_id":       qid,
                "theme":             row.get("theme", ""),
                "variant_group":     row.get("variant_group", ""),
                "question":          row["question"],
                "gold":              row["gold"],
                "retrieved_entries": row.get("retrieved_entries", []),
                "answers": {
                    label: row[f"{arm}_answer"]
                    for label, arm in mapping.items()
                },
            }
            bf.write(json.dumps(batch_row, ensure_ascii=False) + "\n")

    reveal_path.write_text(json.dumps(reveal, indent=2, ensure_ascii=False) + "\n")

    print(f"Blind batch:  {batch_path}  ({len(eligible)} questions, labels X/Y/Z)")
    print(f"Reveal (SEALED — do not pass to Opus): {reveal_path}")
    print()
    print("Pass to Opus: blind_batch_eval007.jsonl + rubric.md")
    print("Do NOT pass:  blind_reveal_eval007.json (sealed until grading complete)")


if __name__ == "__main__":
    main()
