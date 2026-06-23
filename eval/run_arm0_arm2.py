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

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve

ARM0_MODEL  = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM1_MODEL  = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
ARM2_MODEL  = "apertus-flotilla"
OLLAMA_URL  = "http://localhost:11434/api/chat"

DEFAULT_EVAL  = pathlib.Path.home() / "projects/fx/out/datasets/eval.jsonl"
DEFAULT_RULES = pathlib.Path.home() / "projects/fx/rules.md"


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


def is_error(answer: str) -> bool:
    return answer.startswith("[ERROR:")


def trim_context(turns: list, keep_last: int = 4) -> list:
    """Keep only the last N turns to avoid prompt bloat on multi-turn eval questions."""
    if len(turns) <= keep_last:
        return turns
    return turns[-keep_last:]


def inject_wiki(turns: list, hits: list) -> list:
    """Inject pre-retrieved wiki entries into the last user turn."""
    last_user_idx = next(
        (i for i in range(len(turns) - 1, -1, -1) if turns[i]["role"] == "user"), None
    )
    if last_user_idx is None or not hits:
        return turns
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    turns = list(turns)
    turns[last_user_idx] = {"role": "user", "content": ctx.rstrip() + "\n\n---\n\n" + turns[last_user_idx]["content"]}
    return turns


def build_arm0_messages(messages: list) -> list:
    """Arm 0: no system prompt, no retrieval — pure floor."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    return trim_context(turns)


def build_arm1_messages(messages: list, rules_text: str, hits: list) -> list:
    """Arm 1: RULES.md as system prompt + wiki retrieval. No LoRA."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    turns = inject_wiki(turns, hits)
    return [{"role": "system", "content": rules_text}] + turns


def build_arm2_messages(messages: list, hits: list) -> list:
    """Arm 2: LoRA weights (system prompt baked in), wiki retrieval, no rules in prompt."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    return inject_wiki(turns, hits)


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
    fail_path  = out_path.with_stem(out_path.stem + "_failures")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loaded {len(records)} eval questions")
    print(f"Arm 0: {ARM0_MODEL} (no rules, no retrieval)")
    print(f"Arm 1: {ARM1_MODEL} (rules.md + retrieval k={args.k})")
    print(f"Arm 2: {ARM2_MODEL} (LoRA + retrieval k={args.k}, no rules in prompt)")
    print(f"Output:   {out_path}")
    print(f"Failures: {fail_path}\n")

    total = 0
    errors = {"arm0": 0, "arm1": 0, "arm2": 0}
    intersection = 0

    with out_path.open("w") as out_fh, fail_path.open("w") as fail_fh:
        for i, rec in enumerate(records):
            messages = rec["messages"]
            gold     = next((m["content"] for m in reversed(messages) if m["role"] == "assistant"), "")
            question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

            # Retrieve once — identical for Arms 1 & 2 (deterministic BM25)
            hits = retrieve(question, k=args.k)

            t0 = time.time()
            arm0_answer = ollama_chat(ARM0_MODEL, build_arm0_messages(messages))
            t1 = time.time()
            arm1_answer = ollama_chat(ARM1_MODEL, build_arm1_messages(messages, rules_text, hits))
            t2 = time.time()
            arm2_answer = ollama_chat(ARM2_MODEL, build_arm2_messages(messages, hits))
            t3 = time.time()

            arm0_ok = not is_error(arm0_answer)
            arm1_ok = not is_error(arm1_answer)
            arm2_ok = not is_error(arm2_answer)
            all_ok  = arm0_ok and arm1_ok and arm2_ok

            total += 1
            if not arm0_ok: errors["arm0"] += 1
            if not arm1_ok: errors["arm1"] += 1
            if not arm2_ok: errors["arm2"] += 1
            if all_ok: intersection += 1

            status = "OK" if all_ok else f"ERR({''.join(a[3] for a, ok in [('arm0',arm0_ok),('arm1',arm1_ok),('arm2',arm2_ok)] if not ok)})"
            print(f"[{i+1:03}/{len(records)}] {status} arm0={round(t1-t0,1)}s arm1={round(t2-t1,1)}s arm2={round(t3-t2,1)}s  {question[:50].replace(chr(10),' ')!r}")

            row = {
                "question_id":    i,
                "provenance":     rec.get("provenance", {}),
                "theme":          rec.get("theme", ""),
                "variant_group":  rec.get("variant_group", ""),
                "question":       question[:300],
                "gold":           gold,
                "retrieved_entries": [{"id": h["id"], "title": h["title"], "body": h["body"]} for h in hits],
                "retrieved_k":    args.k,
                "arm0_answer":    arm0_answer,
                "arm1_answer":    arm1_answer,
                "arm2_answer":    arm2_answer,
                "arm0_ok":        arm0_ok,
                "arm1_ok":        arm1_ok,
                "arm2_ok":        arm2_ok,
            }
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_fh.flush()

            if not all_ok:
                fail_row = {
                    "question_id": i,
                    "question":    question[:300],
                    "arm0_error":  arm0_answer if not arm0_ok else None,
                    "arm1_error":  arm1_answer if not arm1_ok else None,
                    "arm2_error":  arm2_answer if not arm2_ok else None,
                }
                fail_fh.write(json.dumps(fail_row, ensure_ascii=False) + "\n")
                fail_fh.flush()

    print(f"\n--- Run complete ---")
    print(f"Total:        {total}")
    print(f"Intersection: {intersection}  (all 3 arms non-error — use these for comparison)")
    print(f"arm0 errors:  {errors['arm0']}")
    print(f"arm1 errors:  {errors['arm1']}")
    print(f"arm2 errors:  {errors['arm2']}")
    print(f"Output:       {out_path}")
    print(f"Failures:     {fail_path}")


if __name__ == "__main__":
    main()
