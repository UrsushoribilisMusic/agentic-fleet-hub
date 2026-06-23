#!/usr/bin/env python3
"""
3-arm evaluation runner: Arm 0 vs Arm 1 vs Arm 2.

Arm 0: base Apertus, no system prompt, no retrieval — the floor.
Arm 1: base Apertus, RULES.md as system prompt + wiki retrieval — honest RAG baseline.
Arm 2: LoRA-merged Apertus, no rules in prompt, WITH wiki retrieval — judgment baked in.

Retrieval is identical for Arms 1 and 2 (same retrieve() call, same k).

Usage:
    python3 eval/run_arm0_arm2.py [--eval path] [--rules path] [--k 3] [--out results.jsonl]
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

ARM0_MODEL  = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM1_MODEL  = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM2_MODEL  = "apertus-flotilla"
OLLAMA_URL  = "http://localhost:11434/api/chat"

DEFAULT_EVAL  = pathlib.Path(__file__).parent.parent / "projects/fx/out/datasets/eval.jsonl"
DEFAULT_RULES = pathlib.Path(__file__).parent.parent / "projects/fx/rules.md"


def ollama_chat(model: str, messages: list, timeout: int = 300) -> str:
    payload = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"num_ctx": 16384},
    }).encode()
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
    """Arm 0: no system prompt, no retrieval — pure floor."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    return trim_context(turns)


def inject_wiki(turns: list, k: int) -> list:
    """Inject top-k wiki entries into the last user turn."""
    last_user_idx = next(
        (i for i in range(len(turns) - 1, -1, -1) if turns[i]["role"] == "user"), None
    )
    if last_user_idx is None:
        return turns
    query = turns[last_user_idx]["content"]
    hits = retrieve(query, k=k)
    if not hits:
        return turns
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    turns = list(turns)
    turns[last_user_idx] = {"role": "user", "content": ctx.rstrip() + "\n\n---\n\n" + query}
    return turns


def build_arm1_messages(messages: list, rules_text: str, k: int) -> list:
    """Arm 1: RULES.md as system prompt + wiki retrieval. No LoRA."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    turns = inject_wiki(turns, k)
    return [{"role": "system", "content": rules_text}] + turns


def build_arm2_messages(messages: list, k: int) -> list:
    """Arm 2: LoRA weights (system prompt baked in), wiki retrieval, no rules in prompt."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    return inject_wiki(turns, k)


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
    parser.add_argument("--eval",  default=str(DEFAULT_EVAL))
    parser.add_argument("--rules", default=str(DEFAULT_RULES))
    parser.add_argument("--k",     type=int, default=3)
    parser.add_argument("--out",   default="eval/results_3arm.jsonl")
    args = parser.parse_args()

    eval_path  = pathlib.Path(args.eval)
    rules_path = pathlib.Path(args.rules)

    if not eval_path.exists():
        print(f"[ERROR] eval.jsonl not found at {args.eval}", file=sys.stderr); sys.exit(1)
    if not rules_path.exists():
        print(f"[ERROR] rules.md not found at {args.rules}", file=sys.stderr); sys.exit(1)

    records    = load_eval(eval_path)
    rules_text = rules_path.read_text()
    out_path   = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loaded {len(records)} eval questions")
    print(f"Arm 0: {ARM0_MODEL} (no rules, no retrieval)")
    print(f"Arm 1: {ARM1_MODEL} (rules.md + retrieval k={args.k})")
    print(f"Arm 2: {ARM2_MODEL} (LoRA + retrieval k={args.k}, no rules in prompt)")
    print(f"Output: {out_path}\n")

    with out_path.open("w") as out_fh:
        for i, rec in enumerate(records):
            messages = rec["messages"]
            gold     = next((m["content"] for m in reversed(messages) if m["role"] == "assistant"), "")
            question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

            t0 = time.time()
            arm0_answer = ollama_chat(ARM0_MODEL, build_arm0_messages(messages))
            t1 = time.time()
            arm1_answer = ollama_chat(ARM1_MODEL, build_arm1_messages(messages, rules_text, args.k))
            t2 = time.time()
            arm2_answer = ollama_chat(ARM2_MODEL, build_arm2_messages(messages, args.k))
            t3 = time.time()

            print(f"[{i+1:03}/{len(records)}] arm0={round(t1-t0,1)}s arm1={round(t2-t1,1)}s arm2={round(t3-t2,1)}s  {question[:50].replace(chr(10),' ')!r}")

            row = {
                "question_id": i,
                "provenance":  rec.get("provenance", {}),
                "theme":       rec.get("theme", ""),
                "variant_group": rec.get("variant_group", ""),
                "question":    question[:300],
                "gold":        gold,
                "arm0_answer": arm0_answer,
                "arm1_answer": arm1_answer,
                "arm2_answer": arm2_answer,
                "retrieved_k": args.k,
            }
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_fh.flush()

    print(f"\nDone. {i+1} rows → {out_path}")


if __name__ == "__main__":
    main()
