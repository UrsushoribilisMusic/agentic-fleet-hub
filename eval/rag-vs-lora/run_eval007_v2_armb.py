#!/usr/bin/env python3
"""
EVAL-007 v2 — Arm B only rerun.

Reuses Arm A answers from a previous run (results_eval007_v2.jsonl where
arm_a_ok=True for all 50 rows) and re-generates only Arm B with apertus-v2.
Writes merged output to the same results file.

Usage:
    python3 eval/run_eval007_v2_armb.py \
        [--prev eval/results_eval007_v2.jsonl] \
        [--eval ~/projects/flotilla-corpus/out/datasets/eval.jsonl] \
        [--out  eval/results_eval007_v2.jsonl] \
        [--arm-b apertus-v2] \
        [--timeout 600]
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve

ARM_A_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM_B_MODEL = "apertus-v2"

BLURB = (
    "You are a capable engineering agent working within a multi-agent fleet. "
    "You follow the heartbeat protocol, respect project scope boundaries, "
    "respond precisely to corrections, verify work before claiming completion, "
    "and never confuse separate project contexts. "
    "When corrected, acknowledge cleanly and act on the new direction without defensiveness."
)
BLURB_SHA256 = hashlib.sha256(BLURB.encode()).hexdigest()

OLLAMA_URL = "http://localhost:11434/api/chat"
SAMPLING   = {"temperature": 0.7, "top_p": 0.9, "num_ctx": 16384}


def ollama_chat(model: str, messages: list, timeout: int = 600) -> str:
    payload = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": SAMPLING,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def is_error(s: str) -> bool:
    return s.startswith("[ERROR:")


def trim_context(turns: list, keep_last: int = 4) -> list:
    return turns[-keep_last:] if len(turns) > keep_last else turns


def inject_wiki(turns: list, hits: list) -> list:
    last_user_idx = next(
        (i for i in range(len(turns) - 1, -1, -1) if turns[i]["role"] == "user"), None
    )
    if last_user_idx is None or not hits:
        return turns
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    turns = list(turns)
    turns[last_user_idx] = {
        "role": "user",
        "content": ctx.rstrip() + "\n\n---\n\n" + turns[last_user_idx]["content"],
    }
    return turns


def build_arm(messages: list, hits: list) -> list:
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    turns = inject_wiki(turns, hits)
    return [{"role": "system", "content": BLURB}] + turns


def load_jsonl(path: pathlib.Path) -> list:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev",    default="eval/results_eval007.jsonl",
                        help="Previous run file supplying Arm A answers (default: v1 full 200-row run)")
    parser.add_argument("--eval",    default="eval/eval007_full.jsonl",
                        help="Eval set (default: 200-question set reconstructed from v1 results)")
    parser.add_argument("--out",     default="eval/results_eval007_v2_full.jsonl",
                        help="Output file (default: v2 full 200-row results)")
    parser.add_argument("--arm-b",   default=ARM_B_MODEL)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--k",       type=int, default=3)
    args = parser.parse_args()

    prev_path = pathlib.Path(args.prev)
    eval_path = pathlib.Path(args.eval)
    out_path  = pathlib.Path(args.out)
    arm_b     = args.arm_b

    if not prev_path.exists():
        print(f"[ERROR] prev results not found: {prev_path}", file=sys.stderr); sys.exit(1)
    if not eval_path.exists():
        print(f"[ERROR] eval.jsonl not found: {eval_path}", file=sys.stderr); sys.exit(1)

    prev_rows  = load_jsonl(prev_path)
    eval_recs  = load_jsonl(eval_path)

    assert len(prev_rows) == len(eval_recs), \
        f"Row count mismatch: prev={len(prev_rows)} eval={len(eval_recs)}"

    print("=== EVAL-007 v2 — Arm B rerun ===")
    print(f"Arm A answers: reused from {prev_path}")
    print(f"Arm B model:   {arm_b}")
    print(f"Timeout:       {args.timeout}s (no retry — give the model its time)")
    print(f"Blurb SHA256:  {BLURB_SHA256}")
    print(f"Eval set:      {eval_path}  ({len(eval_recs)} questions)")
    print(f"Output:        {out_path}")
    print()

    total = 0
    arm_b_errors = 0
    arm_b_ok_count = 0

    merged_rows = []
    for i, (prev, rec) in enumerate(zip(prev_rows, eval_recs)):
        assert prev["question_id"] == i, f"question_id mismatch at row {i}"

        messages = rec["messages"]
        question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

        hits   = retrieve(question, k=args.k)
        msgs_b = build_arm(messages, hits)

        t0 = time.time()
        arm_b_answer = ollama_chat(arm_b, msgs_b, timeout=args.timeout)
        elapsed = round(time.time() - t0, 1)

        arm_b_ok = not is_error(arm_b_answer)
        total += 1
        if arm_b_ok:
            arm_b_ok_count += 1
        else:
            arm_b_errors += 1

        status = "OK" if arm_b_ok else f"ERR"
        print(
            f"[{i+1:03}/{len(eval_recs)}] B={status} {elapsed}s  "
            f"{question[:60].replace(chr(10),' ')!r}"
        )

        row = dict(prev)
        row["arm_b_answer"] = arm_b_answer
        row["arm_b_ok"]     = arm_b_ok
        merged_rows.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for row in merged_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\n=== Arm B rerun complete ===")
    print(f"Total:     {total}")
    print(f"Arm B OK:  {arm_b_ok_count}")
    print(f"Arm B ERR: {arm_b_errors}")
    print(f"Output:    {out_path}")


if __name__ == "__main__":
    main()
