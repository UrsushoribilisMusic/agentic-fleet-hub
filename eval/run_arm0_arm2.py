#!/usr/bin/env python3
"""
Arm 0 vs Arm 2 (with retrieval) evaluation runner.

Arm 0: base Apertus, no system prompt, no retrieval — the floor.
Arm 2: LoRA-merged Apertus, no rules in prompt, WITH wiki retrieval injected.

Usage:
    python3 eval/run_arm0_arm2.py [--eval path/to/eval.jsonl] [--k 3] [--out results_arm0_arm2.jsonl]
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.request

# Adjust path so we can import retrieve from the same package
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve

ARM0_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM2_MODEL = "apertus-flotilla"
OLLAMA_URL = "http://localhost:11434/api/chat"

DEFAULT_EVAL = pathlib.Path(__file__).parent.parent / "projects/fx/out/datasets/eval.jsonl"


def ollama_chat(model: str, messages: list, timeout: int = 300) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def trim_context(turns: list, keep_last: int = 4) -> list:
    """Keep only the last N turns to avoid prompt bloat on multi-turn eval questions."""
    if len(turns) <= keep_last:
        return turns
    return turns[-keep_last:]


def build_arm0_messages(messages: list) -> list:
    """Strip system turn; keep last 4 user/assistant turns except gold assistant."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    return trim_context(turns)


def build_arm2_messages(messages: list, k: int) -> list:
    """No system prompt (baked in weights); inject retrieved wiki into last user turn."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)

    # Find last user turn to retrieve on
    last_user_idx = None
    for i in range(len(turns) - 1, -1, -1):
        if turns[i]["role"] == "user":
            last_user_idx = i
            break

    if last_user_idx is None:
        return turns

    query = turns[last_user_idx]["content"]
    hits = retrieve(query, k=k)

    if hits:
        context_block = "Relevant fleet knowledge:\n"
        for h in hits:
            context_block += f"[{h['id']}] {h['title']}\n{h['body']}\n\n"
        augmented_content = context_block.rstrip() + "\n\n---\n\n" + query
        turns = list(turns)
        turns[last_user_idx] = {"role": "user", "content": augmented_content}

    return turns


def load_eval(path: pathlib.Path) -> list:
    records = []
    with path.open() as fh:
        for line in fh:
            s = line.strip()
            if s:
                records.append(json.loads(s))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", default=str(DEFAULT_EVAL))
    parser.add_argument("--k", type=int, default=3, help="wiki entries to retrieve")
    parser.add_argument("--out", default="eval/results_arm0_arm2.jsonl")
    args = parser.parse_args()

    eval_path = pathlib.Path(args.eval)
    if not eval_path.exists():
        # Try relative to repo root
        eval_path = pathlib.Path(__file__).parent.parent / "out/datasets/eval.jsonl"
    if not eval_path.exists():
        print(f"[ERROR] eval.jsonl not found at {args.eval}", file=sys.stderr)
        sys.exit(1)

    records = load_eval(eval_path)
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loaded {len(records)} eval questions from {eval_path}")
    print(f"Arm 0: {ARM0_MODEL}")
    print(f"Arm 2: {ARM2_MODEL}  (retrieval k={args.k})")
    print(f"Output: {out_path}")
    print()

    results = []
    with out_path.open("w") as out_fh:
        for i, rec in enumerate(records):
            messages = rec["messages"]

            # Gold answer = last assistant turn
            gold = next(
                (m["content"] for m in reversed(messages) if m["role"] == "assistant"),
                ""
            )

            # Last user turn = the "question"
            question = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                ""
            )

            # --- Arm 0 ---
            t0 = time.time()
            arm0_msgs = build_arm0_messages(messages)
            arm0_answer = ollama_chat(ARM0_MODEL, arm0_msgs)
            t0_elapsed = round(time.time() - t0, 1)
            print(f"[{i+1:02}/{len(records)}] arm0 {t0_elapsed}s  {question[:60].replace(chr(10),' ')!r}")

            # --- Arm 2 ---
            t2 = time.time()
            arm2_msgs = build_arm2_messages(messages, k=args.k)
            arm2_answer = ollama_chat(ARM2_MODEL, arm2_msgs)
            t2_elapsed = round(time.time() - t2, 1)
            print(f"[{i+1:02}/{len(records)}] arm2 {t2_elapsed}s")

            row = {
                "question_id":  i,
                "provenance":   rec.get("provenance", {}),
                "question":     question[:300],
                "gold":         gold,
                "arm0_answer":  arm0_answer,
                "arm2_answer":  arm2_answer,
                "retrieved_k":  args.k,
            }
            results.append(row)
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_fh.flush()

    print(f"\nDone. {len(results)} rows written to {out_path}")


if __name__ == "__main__":
    main()
