#!/usr/bin/env python3
"""Assemble the OOD test matrix from the 7 per-class author files into the same schema
run_canis_eval001.py consumes (item_id, split, target_class, prompt, is_fp_test)."""
import json, pathlib

EVAL = pathlib.Path(__file__).parent
SRC = EVAL / "ood_authoring"
CLASSES = ["confident", "uncertain", "curious", "concern", "reluctant", "warm", "mischief"]

rows, missing = [], []
for cl in CLASSES:
    f = SRC / f"class_{cl}.json"
    if not f.exists():
        missing.append(cl); continue
    d = json.loads(f.read_text())
    for i, p in enumerate(d.get("positives", [])):
        rows.append({"item_id": f"OOD_{cl}_p{i:02d}", "split": "positive",
                     "target_class": cl, "prompt": p.strip(), "is_fp_test": False})
    for i, n in enumerate(d.get("negatives", [])):
        rows.append({"item_id": f"OOD_{cl}_n{i:02d}", "split": "negative",
                     "target_class": cl, "prompt": n.strip(), "is_fp_test": True})

if missing:
    print(f"MISSING class files: {missing} — not all authors done yet."); raise SystemExit(1)

out = EVAL / "canis_eval001_ood_matrix.jsonl"
with out.open("w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")

import collections
per = collections.Counter((r["target_class"], r["split"]) for r in rows)
print(f"wrote {out.name}: {len(rows)} items")
for cl in CLASSES:
    print(f"  {cl:10} pos={per[(cl,'positive')]}  neg={per[(cl,'negative')]}")
