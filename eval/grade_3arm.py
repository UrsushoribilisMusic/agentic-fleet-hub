#!/usr/bin/env python3
"""
EVAL-005: Blind Qwen grader for 3-arm results.

- Loads results_3arm.jsonl
- Filters to intersection (all 3 arms non-error)
- Grades each arm's answer independently with Qwen (blind — no arm labels shown to judge)
- Scores: action_correct (0/1) and grounded (0/1, semantic hallucination check vs retrieved entries)
- Outputs results_3arm_graded.jsonl with per-arm scores

Usage:
    python3 eval/grade_3arm.py [--in results_3arm.jsonl] [--out results_3arm_graded.jsonl]
                               [--judge qwen2.5:7b]
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.request

OLLAMA_URL   = "http://localhost:11434/api/chat"
DEFAULT_IN   = pathlib.Path(__file__).parent / "results_3arm.jsonl"
DEFAULT_OUT  = pathlib.Path(__file__).parent / "results_3arm_graded.jsonl"
DEFAULT_JUDGE = "qwen2.5:7b"

JUDGE_SYSTEM = (
    "You are a strict, impartial evaluation judge for a fleet agent system. "
    "Your only job is to score an agent answer against a gold standard and retrieved knowledge. "
    "Reply with valid JSON only — no prose, no markdown fences."
)

JUDGE_TEMPLATE = """\
## Question
{question}

## Gold answer (verified correct)
{gold}

## Retrieved knowledge (facts available to the agent at answer time)
{retrieved}

## Answer to evaluate
{answer}

Score this answer on 4 dimensions (each 0–5). Reply with JSON in exactly this shape:
{{"action_correct": <0-5>, "grounded": <0-5>, "fleet_domain": <0-5>, "completeness": <0-5>, "rationale": "<one sentence>"}}

Scoring guide (pass threshold = 3.5/5 per dimension):
- action_correct: 5=fully correct+actionable matches gold, 4=correct with minor gap, 3=partially correct, 2=wrong but partial understanding, 1=wrong, 0=evasion or contradicts gold.
- grounded: 5=all claims traceable to retrieved entries or gold, 4=one minor unverifiable but plausible claim, 3=one unsupported claim not affecting action, 2=one hallucination affecting action, 1=multiple invented facts, 0=majority fabricated. If no retrieval, grade vs gold only.
- fleet_domain: 5=cites specific fleet rule IDs/agent names/PB fields, 4=clear fleet knowledge without IDs, 3=some domain knowledge but mostly generic, 2=mostly generic fleet vocabulary, 1=entirely generic, 0=off-topic.
- completeness: 5=addresses all parts of question, 4=main question covered minor gap, 3=primary concern answered secondary missed, 2=partial answer, 1=surface only, 0=no attempt.\
"""


def ollama_chat(model: str, messages: list, timeout: int = 120) -> str:
    payload = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"num_ctx": 8192, "temperature": 0},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def parse_grade(raw: str) -> dict:
    """Extract JSON grade from judge response; return defaults on parse failure."""
    raw = raw.strip()
    m = re.search(r'\{[^{}]*"action_correct"[^{}]*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return {
        "action_correct": -1, "grounded": -1, "fleet_domain": -1, "completeness": -1,
        "rationale": f"[PARSE ERROR] {raw[:120]}",
    }


def format_retrieved(entries: list) -> str:
    if not entries:
        return "(no retrieval — arm had no wiki context)"
    return "\n\n".join(f"[{e['id']}] {e['title']}\n{e['body']}" for e in entries)


def grade_answer(question: str, gold: str, retrieved_entries: list, answer: str, judge: str) -> dict:
    """Grade a single answer. Retrieved entries may be empty (Arm 0)."""
    prompt = JUDGE_TEMPLATE.format(
        question=question,
        gold=gold,
        retrieved=format_retrieved(retrieved_entries),
        answer=answer,
    )
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user",   "content": prompt},
    ]
    raw = ollama_chat(judge, messages)
    return parse_grade(raw)


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
    parser.add_argument("--in",    dest="in_path",  default=str(DEFAULT_IN))
    parser.add_argument("--out",   dest="out_path", default=str(DEFAULT_OUT))
    parser.add_argument("--judge", default=DEFAULT_JUDGE)
    args = parser.parse_args()

    in_path  = pathlib.Path(args.in_path)
    out_path = pathlib.Path(args.out_path)

    if not in_path.exists():
        print(f"[ERROR] Input not found: {in_path}", file=sys.stderr); sys.exit(1)

    rows = load_results(in_path)
    total    = len(rows)
    eligible = [r for r in rows if r.get("arm0_ok") and r.get("arm1_ok") and r.get("arm2_ok")]
    skipped  = total - len(eligible)

    print(f"Loaded {total} rows, {len(eligible)} in intersection ({skipped} skipped — one or more arm errors)")
    print(f"Judge: {args.judge}")
    print(f"Output: {out_path}\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    graded = 0
    with out_path.open("w") as fh:
        for i, row in enumerate(eligible):
            question = row["question"]
            gold     = row["gold"]
            entries  = row.get("retrieved_entries", [])

            t0 = time.time()
            g0 = grade_answer(question, gold, [],      row["arm0_answer"], args.judge)  # Arm 0: no retrieval
            g1 = grade_answer(question, gold, entries, row["arm1_answer"], args.judge)
            g2 = grade_answer(question, gold, entries, row["arm2_answer"], args.judge)
            elapsed = time.time() - t0

            graded += 1
            print(
                f"[{i+1:03}/{len(eligible)}] {elapsed:.1f}s  "
                f"arm0={g0['action_correct']}/{g0['grounded']}  "
                f"arm1={g1['action_correct']}/{g1['grounded']}  "
                f"arm2={g2['action_correct']}/{g2['grounded']}  "
                f"{question[:50].replace(chr(10),' ')!r}"
            )

            out_row = dict(row)
            out_row["arm0_grade"] = g0
            out_row["arm1_grade"] = g1
            out_row["arm2_grade"] = g2
            fh.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            fh.flush()

    # Summary stats
    with out_path.open() as fh:
        graded_rows = [json.loads(l) for l in fh if l.strip()]

    def avg(key, arm):
        vals = [r[f"arm{arm}_grade"][key] for r in graded_rows if r[f"arm{arm}_grade"][key] in (0, 1)]
        return sum(vals) / len(vals) if vals else float("nan")

    print(f"\n--- Grading complete ({graded} questions) ---")
    print(f"{'Metric':<22} {'Arm0 (floor)':>14} {'Arm1 (rules+RAG)':>18} {'Arm2 (LoRA+RAG)':>17}")
    print("-" * 75)
    for dim in ["action_correct", "grounded", "fleet_domain", "completeness"]:
        print(f"{dim:<22} {avg(dim,0):>14.3f} {avg(dim,1):>18.3f} {avg(dim,2):>17.3f}")

    def composite(arm):
        vals = [
            r[f"arm{arm}_grade"][d]
            for r in graded_rows
            for d in ["action_correct", "grounded", "fleet_domain", "completeness"]
            if r[f"arm{arm}_grade"][d] in range(6)
        ]
        return sum(vals) / len(vals) if vals else float("nan")

    print("-" * 75)
    print(f"{'composite (mean)':<22} {composite(0):>14.3f} {composite(1):>18.3f} {composite(2):>17.3f}")
    print(f"\nOutput: {out_path}")


if __name__ == "__main__":
    main()
