#!/usr/bin/env python3
"""
EVAL-008 grader — Qwen blind preview (3 dimensions).

Grades each answer on:
  grounded       (0–5): answer is grounded in the fleet corpus, not hallucinated
  correct        (0–5): answer is factually correct relative to the gold entry
  faithful_recall(0–5): accurately recalls the specific content of the gold entry

IMPORTANT: This is a PREVIEW only. Arm labels are stripped before grading (blind).
Final verdict comes from Opus + Miguel's ~15-sample human validation.

Only grades rows where all 3 arms completed (intersection set).

Usage:
    python3 eval/grade_eval008.py \
        [--in  eval/results_eval008.jsonl] \
        [--out eval/results_eval008_graded.jsonl]
"""
import argparse
import json
import pathlib
import sys
import textwrap
import time
import urllib.request

GRADE_MODEL = "qwen2.5:7b"
OLLAMA_URL  = "http://localhost:11434/api/chat"
DIMS = ["grounded", "correct", "faithful_recall"]


def ollama_chat(model: str, messages: list, timeout: int = 240) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False,
                          "options": {"temperature": 0.1, "top_p": 0.9}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:
            if attempt == 0: time.sleep(10)
            else: return f"[ERROR: {e}]"
    return "[ERROR]"


def grade_answer(question: str, gold_body: str, answer: str) -> dict:
    """Grade one answer blind (no arm label). Returns dict with 3 scores."""
    prompt = textwrap.dedent(f"""
        You are a strict evaluator for a fleet-agent AI system.

        GOLD KNOWLEDGE ENTRY (the correct answer source):
        {gold_body}

        QUESTION asked to the agent:
        {question}

        AGENT ANSWER:
        {answer}

        Score the answer on three dimensions, each 0–5:
          grounded       — Is the answer grounded in fleet knowledge, or does it hallucinate?
                           5=fully grounded, 0=pure hallucination
          correct        — Is the answer factually correct relative to the gold entry?
                           5=fully correct, 0=factually wrong
          faithful_recall— Does the answer accurately recall the specific content from the gold entry?
                           5=precisely recalls key facts, 0=misses or distorts them

        Respond with ONLY valid JSON on a single line, no explanation:
        {{"grounded": N, "correct": N, "faithful_recall": N}}
    """).strip()

    raw = ollama_chat(GRADE_MODEL, [{"role": "user", "content": prompt}])
    try:
        # Extract JSON — strip any markdown fences
        import re
        m = re.search(r'\{[^}]+\}', raw)
        if not m:
            return {"grounded": None, "correct": None, "faithful_recall": None, "_raw": raw[:200]}
        d = json.loads(m.group())
        return {k: int(d[k]) if isinstance(d.get(k), (int, float)) else None for k in DIMS}
    except Exception:
        return {"grounded": None, "correct": None, "faithful_recall": None, "_raw": raw[:200]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in",  dest="inp", default="eval/results_eval008.jsonl")
    parser.add_argument("--out",             default="eval/results_eval008_graded.jsonl")
    args = parser.parse_args()

    in_path  = pathlib.Path(args.inp)
    out_path = pathlib.Path(args.out)

    rows = [json.loads(l) for l in in_path.read_text().splitlines() if l.strip()]
    to_grade = [r for r in rows if r.get("arm0_ok") and r.get("arm1_ok") and r.get("arm2_ok")]

    print(f"=== EVAL-008 Qwen Grading (PREVIEW — blind, {len(to_grade)} intersection rows) ===")
    print(f"Grader: {GRADE_MODEL}  |  Grading model != tested models  |  Blind (no arm labels)")
    print(f"Input:  {in_path}  ({len(rows)} total, {len(to_grade)} in intersection)")
    print()
    print("NOTE: This is a PREVIEW. Opus blind grading + Miguel ~15-sample validation to follow.")
    print()

    graded = []
    with out_path.open("w") as out_fh:
        for i, row in enumerate(to_grade):
            qid = row["question_id"]
            q   = row["question"]
            gold = row["gold_entry_body"]
            print(f"[{i+1:03}/{len(to_grade)}] q{qid:02d} gold={row['gold_entry_id']}", end="", flush=True)

            g0 = grade_answer(q, gold, row["arm0_answer"])
            g1 = grade_answer(q, gold, row["arm1_answer"])
            g2 = grade_answer(q, gold, row["arm2_answer"])

            row_out = dict(row)
            row_out["arm0_grade"] = g0
            row_out["arm1_grade"] = g1
            row_out["arm2_grade"] = g2
            graded.append(row_out)
            out_fh.write(json.dumps(row_out, ensure_ascii=False) + "\n")
            out_fh.flush()

            def fmt(g):
                vals = [g.get(d) for d in DIMS]
                return "/".join(str(v) if v is not None else "?" for v in vals)
            print(f"  0={fmt(g0)}  1={fmt(g1)}  2={fmt(g2)}")

    # Preview summary
    print(f"\n=== EVAL-008 Qwen Grading (171 questions) ===")
    arm_keys = ["arm0", "arm1", "arm2"]
    header = f"{'Metric':<22}"
    for ak in arm_keys:
        header += f"  {ak:>14}"
    print(header)
    print("-" * (22 + 3 * 16))

    for dim in DIMS:
        line = f"{dim:<22}"
        for ak in arm_keys:
            vals = [r[f"{ak}_grade"].get(dim) for r in graded
                    if r.get(f"{ak}_grade") and r[f"{ak}_grade"].get(dim) is not None]
            avg = sum(vals) / len(vals) if vals else float("nan")
            mark = "✓" if avg >= 3.5 else "✗"
            line += f"  {avg:>12.3f}{mark}"
        print(line)

    print("-" * (22 + 3 * 16))
    line = f"{'composite (mean)':<22}"
    composites = {}
    for ak in arm_keys:
        all_vals = []
        for r in graded:
            g = r.get(f"{ak}_grade", {})
            for dim in DIMS:
                v = g.get(dim)
                if isinstance(v, (int, float)) and 0 <= v <= 5:
                    all_vals.append(v)
        avg = sum(all_vals) / len(all_vals) if all_vals else float("nan")
        composites[ak] = avg
        mark = "✓" if avg >= 3.5 else "✗"
        line += f"  {avg:>12.3f}{mark}"
    print(line)

    print()
    d01 = composites["arm1"] - composites["arm0"]
    d12 = composites["arm2"] - composites["arm1"]
    print(f"Arm 0→1 (LoRA baking alone): {d01:+.3f}")
    print(f"Arm 1→2 (RAG on top of LoRA): {d12:+.3f}")
    print()
    print("⚠  PREVIEW ONLY — do not report these as final. Opus blind + human validation to follow.")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
