#!/usr/bin/env python3
"""
Task 1 prep — build blind grading batches for a fresh single-version Opus pass over
ALL FOUR arms (the existing Opus grades are an unpinned manual pass over arms 0-2 only,
so we re-grade everything with one grader).

Reuses the sealed 4-arm blind batch (answer_X/Y/Z/W already shuffled + label-stripped).
Relabels X/Y/Z/W -> A/B/C/D and writes batches that contain ONLY question + gold + the
four candidate answers. The A/B/C/D -> arm map is kept in answer_map.json, which the
graders never see.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE / "grading_opus48"
OUT.mkdir(exist_ok=True)
N_BATCHES = 7

batch = [json.loads(l) for l in (HERE/"blind_batch_eval008_4arm.jsonl").read_text().splitlines() if l.strip()]
reveal = json.loads((HERE/"blind_reveal_eval008_4arm.json").read_text())

REL = {"X": "A", "Y": "B", "Z": "C", "W": "D"}
items, amap = [], {}
for r in batch:
    qid = r["question_id"]
    items.append({
        "qid": qid,
        "question": r["question"],
        "gold_fact": r["gold_entry_body"],
        "candidates": {REL[k]: r[f"answer_{k}"] for k in REL},
    })
    # A/B/C/D -> arm, via the sealed reveal (X/Y/Z/W -> arm)
    amap[str(qid)] = {REL[k]: reveal[str(qid)][k] for k in REL}

(OUT/"answer_map.json").write_text(json.dumps(amap, indent=1))

# split into N contiguous batches
per = -(-len(items)//N_BATCHES)
for b in range(N_BATCHES):
    chunk = items[b*per:(b+1)*per]
    if chunk:
        (OUT/f"batch_{b}.json").write_text(json.dumps(chunk, indent=1))

print(f"{len(items)} items -> {min(N_BATCHES, -(-len(items)//per))} batches in {OUT}")
print("batch files:", sorted(p.name for p in OUT.glob('batch_*.json')))
