#!/usr/bin/env python3
"""
Generate a blind grading batch for Opus (EVAL-006).

Reads results_3arm.jsonl (must have arm0_ok/arm1_ok/arm2_ok fields).
Outputs two files:
  blind_batch.jsonl  — one object per question with A/B/C labels (no arm names)
  blind_reveal.json  — the A/B/C → arm mapping per question (open AFTER grading)

The shuffle is seeded per question_id for reproducibility.

Usage:
    python3 eval/gen_blind_batch.py [--in results_3arm.jsonl] [--out-dir eval/]
"""
import argparse
import json
import pathlib
import random
import sys

DEFAULT_IN  = pathlib.Path(__file__).parent / "results_3arm.jsonl"
DEFAULT_DIR = pathlib.Path(__file__).parent


def load_results(path: pathlib.Path) -> list:
    rows = []
    with path.open() as fh:
        for line in fh:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in",      dest="in_path",  default=str(DEFAULT_IN))
    parser.add_argument("--out-dir", dest="out_dir",  default=str(DEFAULT_DIR))
    args = parser.parse_args()

    in_path = pathlib.Path(args.in_path)
    out_dir = pathlib.Path(args.out_dir)

    if not in_path.exists():
        print(f"[ERROR] Input not found: {in_path}", file=sys.stderr); sys.exit(1)

    rows = load_results(in_path)
    eligible = [r for r in rows if r.get("arm0_ok") and r.get("arm1_ok") and r.get("arm2_ok")]
    skipped  = len(rows) - len(eligible)

    print(f"Loaded {len(rows)} rows, {len(eligible)} in intersection ({skipped} skipped)")

    batch_path  = out_dir / "blind_batch.jsonl"
    reveal_path = out_dir / "blind_reveal.json"

    reveals = {}

    with batch_path.open("w") as bf:
        for row in eligible:
            qid = row["question_id"]
            rng = random.Random(qid)  # seeded per question for reproducibility

            arms = ["arm0", "arm1", "arm2"]
            rng.shuffle(arms)
            mapping = {"A": arms[0], "B": arms[1], "C": arms[2]}
            reveals[str(qid)] = mapping

            batch_row = {
                "question_id":       qid,
                "theme":             row.get("theme", ""),
                "variant_group":     row.get("variant_group", ""),
                "question":          row["question"],
                "gold":              row["gold"],
                "retrieved_entries": row.get("retrieved_entries", []),
                "answers": {
                    "A": row[f"{arms[0]}_answer"],
                    "B": row[f"{arms[1]}_answer"],
                    "C": row[f"{arms[2]}_answer"],
                },
            }
            bf.write(json.dumps(batch_row, ensure_ascii=False) + "\n")

    with reveal_path.open("w") as rf:
        json.dump(reveals, rf, indent=2)

    print(f"Blind batch:  {batch_path}  ({len(eligible)} questions)")
    print(f"Reveal file:  {reveal_path}  (open AFTER grading)")
    print("\nReminder: A/B/C labels are randomized per question. Share only blind_batch.jsonl with the judge.")


if __name__ == "__main__":
    main()
