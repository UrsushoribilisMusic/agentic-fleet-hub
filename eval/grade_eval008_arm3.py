#!/usr/bin/env python3
"""
EVAL-008 arm3 Qwen grader — grades arm3 (base+RAG) answers using same
rubric as grade_eval008.py.

Output: eval/results_eval008_arm3_graded.jsonl
  One record per question with keys: question_id, arm3_grade {grounded, correct, faithful_recall}

Usage:
    python3 eval/grade_eval008_arm3.py
"""
import json
import pathlib
import textwrap
import time
import urllib.request
import re

GRADE_MODEL = "qwen2.5:7b"
OLLAMA_URL  = "http://localhost:11434/api/chat"
DIMS = ["grounded", "correct", "faithful_recall"]

IN_PATH  = pathlib.Path("eval/results_eval008_arm3.jsonl")
OUT_PATH = pathlib.Path("eval/results_eval008_arm3_graded.jsonl")


def ollama_chat(model, messages, timeout=240):
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


def grade_answer(question, gold_body, answer):
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
          faithful_recall— Does the answer accurately recall the specific content of the gold entry?
                           5=precisely recalls key facts, 0=misses or distorts them

        Respond with ONLY valid JSON on a single line, no explanation:
        {{"grounded": N, "correct": N, "faithful_recall": N}}
    """).strip()

    raw = ollama_chat(GRADE_MODEL, [{"role": "user", "content": prompt}])
    try:
        m = re.search(r'\{[^}]+\}', raw)
        if not m:
            return {"grounded": None, "correct": None, "faithful_recall": None, "_raw": raw[:200]}
        d = json.loads(m.group())
        return {k: int(d[k]) if isinstance(d.get(k), (int, float)) else None for k in DIMS}
    except Exception:
        return {"grounded": None, "correct": None, "faithful_recall": None, "_raw": raw[:200]}


def main():
    rows = [json.loads(l) for l in IN_PATH.read_text().splitlines() if l.strip()]
    to_grade = [r for r in rows if r.get("arm3_ok")]

    print(f"Grading arm3 with {GRADE_MODEL}: {len(to_grade)} questions")

    with OUT_PATH.open("w") as out_fh:
        for i, row in enumerate(to_grade):
            qid = row["question_id"]
            g3 = grade_answer(row["question"], row["gold_entry_body"], row["arm3_answer"])
            out = {"question_id": qid, "arm3_grade": g3}
            out_fh.write(json.dumps(out) + "\n")
            out_fh.flush()
            vals = "/".join(str(g3.get(d, "?")) for d in DIMS)
            print(f"  [{i+1:02}/{len(to_grade)}] q{qid:02d} arm3={vals}")

    print(f"Done → {OUT_PATH}")


if __name__ == "__main__":
    main()
