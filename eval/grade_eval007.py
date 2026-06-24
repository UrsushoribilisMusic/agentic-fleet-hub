#!/usr/bin/env python3
"""
EVAL-007: Qwen2.5:7b blind grader — strict grounded check.

Changes vs grade_3arm.py (EVAL-1):
  - Arm names: arm_a / arm_b only (Arm REF dropped)
  - Grounded scoring explicitly penalises fabricated artifact IDs
    (ticket IDs, agent names, PB record IDs not in retrieved_entries or gold).
    A single invented ID → ≤ 2; multiple → ≤ 1.

Usage:
    python3 eval/grade_eval007.py [--in eval/results_eval007.jsonl] [--out eval/results_eval007_graded.jsonl]
"""
import argparse
import json
import pathlib
import re
import sys
import time
import urllib.request

OLLAMA_URL    = "http://localhost:11434/api/chat"
DEFAULT_IN    = pathlib.Path(__file__).parent / "results_eval007.jsonl"
DEFAULT_OUT   = pathlib.Path(__file__).parent / "results_eval007_graded.jsonl"
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

## Retrieved knowledge (facts the agent had access to at answer time)
{retrieved}

## Answer to evaluate
{answer}

Score this answer on 4 dimensions (each 0–5). Reply with JSON in exactly this shape:
{{"action_correct": <0-5>, "grounded": <0-5>, "fleet_domain": <0-5>, "completeness": <0-5>, "rationale": "<one sentence>"}}

Scoring guide (pass threshold = 3.5/5 per dimension):

action_correct:
  5 = fully correct + actionable, matches gold exactly
  4 = correct with minor gap or omission
  3 = partially correct — right direction, wrong detail
  2 = wrong action but shows partial understanding
  1 = wrong
  0 = evasion, refusal, or directly contradicts gold

grounded (STRICT — fabricated IDs are an automatic penalty):
  RULE: Any artifact ID (ticket ID, PB record ID, agent name, rule ID) cited in the answer
        that does NOT appear in retrieved knowledge or gold is FABRICATED.
        One fabricated ID → score ≤ 2. Two or more fabricated IDs → score ≤ 1.
        This overrides all other grounded considerations.
  5 = all factual claims traceable to retrieved entries or gold; no fabricated IDs
  4 = one minor unverifiable but plausible claim; no fabricated IDs
  3 = one unsupported claim not affecting the action; no fabricated IDs
  2 = one hallucination affecting the action OR one fabricated artifact ID
  1 = multiple invented facts OR two or more fabricated artifact IDs
  0 = majority fabricated

  If retrieved knowledge is empty (arm had no retrieval), grade grounded vs gold only.

fleet_domain:
  5 = cites specific fleet rule IDs / agent names / PB fields that appear in retrieved entries
  4 = clear fleet knowledge without specific IDs
  3 = some domain knowledge but mostly generic
  2 = mostly generic fleet vocabulary
  1 = entirely generic
  0 = off-topic

completeness:
  5 = addresses all parts of the question
  4 = main question covered, minor secondary gap
  3 = primary concern answered, secondary concern missed
  2 = partial answer
  1 = surface only
  0 = no attempt\
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

    rows     = load_results(in_path)
    eligible = [r for r in rows if r.get("arm_a_ok") and r.get("arm_b_ok")]
    skipped  = len(rows) - len(eligible)

    print(f"Loaded {len(rows)} rows, {len(eligible)} in intersection ({skipped} skipped)")
    print(f"Judge: {args.judge} (strict grounded — fabricated IDs penalised)")
    print(f"Output: {out_path}\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as fh:
        for i, row in enumerate(eligible):
            question = row["question"]
            gold     = row["gold"]
            entries  = row.get("retrieved_entries", [])

            t0 = time.time()
            ga = grade_answer(question, gold, entries, row["arm_a_answer"], args.judge)
            gb = grade_answer(question, gold, entries, row["arm_b_answer"], args.judge)
            elapsed = time.time() - t0

            print(
                f"[{i+1:03}/{len(eligible)}] {elapsed:.1f}s  "
                f"A={ga['action_correct']}/{ga['grounded']}  "
                f"B={gb['action_correct']}/{gb['grounded']}  "
                f"{question[:60].replace(chr(10),' ')!r}"
            )

            out_row = dict(row)
            out_row["arm_a_grade"] = ga
            out_row["arm_b_grade"] = gb
            fh.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            fh.flush()

    # Summary
    graded_rows = load_results(out_path)
    DIMS     = ["action_correct", "grounded", "fleet_domain", "completeness"]
    ARM_KEYS = [("arm_a", "Arm A (floor)"), ("arm_b", "Arm B (LoRA)")]

    def avg(key, arm_key):
        vals = [r[f"{arm_key}_grade"][key] for r in graded_rows
                if isinstance(r[f"{arm_key}_grade"].get(key), (int, float))
                and 0 <= r[f"{arm_key}_grade"][key] <= 5]
        return sum(vals) / len(vals) if vals else float("nan")

    def composite(arm_key):
        vals = [r[f"{arm_key}_grade"][d] for r in graded_rows for d in DIMS
                if isinstance(r[f"{arm_key}_grade"].get(d), (int, float))
                and 0 <= r[f"{arm_key}_grade"][d] <= 5]
        return sum(vals) / len(vals) if vals else float("nan")

    print(f"\n=== EVAL-007 Qwen Grading ({len(graded_rows)} questions) ===")
    print(f"{'Metric':<22} {'Arm A (floor)':>15} {'Arm B (LoRA)':>14}  pass≥3.5")
    print("-" * 60)
    for dim in DIMS:
        vals = [avg(dim, ak) for ak, _ in ARM_KEYS]
        marks = ["✓" if v >= 3.5 else "✗" for v in vals]
        print(f"{dim:<22} {vals[0]:>14.3f}{marks[0]}  {vals[1]:>12.3f}{marks[1]}")
    print("-" * 60)
    cvals  = [composite(ak) for ak, _ in ARM_KEYS]
    cmarks = ["✓" if v >= 3.5 else "✗" for v in cvals]
    print(f"{'composite (mean)':<22} {cvals[0]:>14.3f}{cmarks[0]}  {cvals[1]:>12.3f}{cmarks[1]}")

    # Pre-registered reading
    delta = cvals[1] - cvals[0]
    print()
    if delta > 0.1:
        print(f"Pre-registered verdict: Arm B > Arm A (+{delta:.3f}) → THESIS SUPPORTED")
    elif delta < -0.1:
        print(f"Pre-registered verdict: Arm B < Arm A ({delta:.3f}) → THESIS IN TROUBLE")
    else:
        print(f"Pre-registered verdict: Arm B ≈ Arm A (Δ={delta:+.3f}) → v1 baking added little; DPO+r32 (v2) is the real test")
    print(f"\nEVAL-1 Arm 1 reference (full rules, Qwen): 3.922  gap to close: {3.922 - cvals[1]:+.3f}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
