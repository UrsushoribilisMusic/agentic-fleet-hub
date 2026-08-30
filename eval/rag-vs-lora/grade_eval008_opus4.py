#!/usr/bin/env python3
"""
Reproducible pinned-snapshot Opus grader for EVAL-008 (camera-ready variant of the blind
subagent pass in aggregate_opus48.py).

Grades all four arms blind via the Anthropic API with a PINNED model snapshot at temp 0,
using the identical 3-dimension rubric. Reads the sealed 4-arm blind batch, maps X/Y/Z/W
back to arms via the reveal, and writes per-question scores in the same shape as
results_eval008_opus48_4arm.jsonl.

Usage:
    ANTHROPIC_API_KEY=sk-ant-...  OPUS_MODEL=claude-opus-4-8  python3 grade_eval008_opus4.py

Pin OPUS_MODEL to a dated snapshot for a bit-stable re-run.
"""
import json, os, pathlib, re

HERE = pathlib.Path(__file__).parent
DIMS = ["grounded", "correct", "faithful_recall"]
MODEL = os.environ.get("OPUS_MODEL", "claude-opus-4-8")

RUBRIC = """You are a strict, blind evaluator for a fleet-agent AI system. Grade the answer
against the gold knowledge entry on three dimensions, each an INTEGER 0-5, on its own merits:
- grounded: grounded in fleet knowledge vs hallucinated (5=fully grounded, 0=pure hallucination)
- correct: factually correct relative to the gold fact (5=fully correct, 0=factually wrong)
- faithful_recall: accurately recalls the specific gold content (5=precise, 0=missing/distorted)
If the answer is empty or an obvious error, score all three 0.
Respond with ONLY one line of JSON: {"grounded": n, "correct": n, "faithful_recall": n}"""

def grade(client, question, gold, answer):
    msg = client.messages.create(
        model=MODEL, max_tokens=100, temperature=0,
        system=RUBRIC,
        messages=[{"role": "user", "content":
            f"GOLD FACT:\n{gold}\n\nQUESTION:\n{question}\n\nANSWER:\n{answer}"}],
    )
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{[^}]+\}", txt)
    d = json.loads(m.group()) if m else {}
    return {k: int(d[k]) for k in DIMS if isinstance(d.get(k), (int, float))}

def main():
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    batch = [json.loads(l) for l in (HERE/"blind_batch_eval008_4arm.jsonl").read_text().splitlines() if l.strip()]
    reveal = json.loads((HERE/"blind_reveal_eval008_4arm.json").read_text())
    out = []
    for r in batch:
        qid = r["question_id"]
        rec = {"question_id": qid, "grader": MODEL, "blind": True}
        for lab in ("X", "Y", "Z", "W"):
            arm = reveal[str(qid)][lab]
            rec[f"{arm}_opus48"] = grade(client, r["question"], r["gold_entry_body"], r[f"answer_{lab}"])
        out.append(rec)
        print(f"  graded qid {qid}")
    dest = HERE / "results_eval008_opus4_pinned.jsonl"
    dest.write_text("\n".join(json.dumps(o) for o in out) + "\n")
    print(f"wrote {dest} ({len(out)} questions, model={MODEL})")
    print("Point aggregate_opus48.py at this file to recompute contrasts on the pinned pass.")

if __name__ == "__main__":
    main()
