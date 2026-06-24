#!/usr/bin/env python3
"""
EVAL-007: Matched-prompt fair comparison — v1 LoRA vs no-LoRA, identical system prompts.

Two arms (Arm REF dropped — ceiling already known from EVAL-1 Arm 1):
  Arm A (matched floor):  base Apertus + 48-word blurb + RAG (no LoRA)
  Arm B (thesis):         LoRA Apertus + same 48-word blurb + RAG

Critical invariants:
  - System prompt byte-identical for Arm A and Arm B (SHA256 logged at runtime)
  - Retrieval byte-identical (retrieve() called once per question, passed to both)
  - Sampling params explicit and identical: temperature=0.7, top_p=0.9 for all arms
  - Timeout 600s (was 300s → 40 Arm B drops in EVAL-1)

Pre-registered reading (written before seeing numbers):
  Arm B > Arm A composite → thesis supported: LoRA adds value at matched prompts.
  Arm B ≈ Arm A           → v1 baking added little; DPO+r32 (v2) is the real test.
  Arm B < Arm A           → thesis in trouble; investigate before more compute.

Usage:
    python3 eval/run_eval007.py [--eval path] [--k 3] [--out eval/results_eval007.jsonl]
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

ARM_A_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"  # base + blurb
ARM_B_MODEL = "apertus-flotilla"                                  # LoRA + blurb

# Extracted verbatim from `ollama show apertus-flotilla --modelfile` SYSTEM field.
# Arm A and Arm B MUST use this exact string. SHA256 verified at runtime.
BLURB = (
    "You are a capable engineering agent working within a multi-agent fleet. "
    "You follow the heartbeat protocol, respect project scope boundaries, "
    "respond precisely to corrections, verify work before claiming completion, "
    "and never confuse separate project contexts. "
    "When corrected, acknowledge cleanly and act on the new direction without defensiveness."
)
BLURB_SHA256 = hashlib.sha256(BLURB.encode()).hexdigest()

OLLAMA_URL   = "http://localhost:11434/api/chat"
DEFAULT_EVAL = pathlib.Path.home() / "projects/fx/out/datasets/eval.jsonl"
SAMPLING     = {"temperature": 0.7, "top_p": 0.9, "num_ctx": 16384}


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


def is_error(answer: str) -> bool:
    return answer.startswith("[ERROR:")


def trim_context(turns: list, keep_last: int = 4) -> list:
    if len(turns) <= keep_last:
        return turns
    return turns[-keep_last:]


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


def user_turn_sha256(turns: list) -> str:
    last_user = next((t["content"] for t in reversed(turns) if t["role"] == "user"), "")
    return hashlib.sha256(last_user.encode()).hexdigest()


def build_arm(messages: list, hits: list) -> list:
    """Shared builder for Arm A and Arm B — blurb + RAG, no other differences."""
    turns = [m for m in messages if m["role"] != "system"]
    if turns and turns[-1]["role"] == "assistant":
        turns = turns[:-1]
    turns = trim_context(turns)
    turns = inject_wiki(turns, hits)
    return [{"role": "system", "content": BLURB}] + turns


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
    parser.add_argument("--k",    type=int, default=3)
    parser.add_argument("--out",  default="eval/results_eval007.jsonl")
    args = parser.parse_args()

    eval_path = pathlib.Path(args.eval)
    if not eval_path.exists():
        print(f"[ERROR] eval.jsonl not found: {args.eval}", file=sys.stderr); sys.exit(1)

    records  = load_eval(eval_path)
    out_path = pathlib.Path(args.out)
    fail_path = out_path.with_stem(out_path.stem + "_failures")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Verify blurb parity — same object, so always true, but makes the check auditable
    assert hashlib.sha256(BLURB.encode()).hexdigest() == BLURB_SHA256

    print("=== EVAL-007: Matched-prompt fair comparison (2-arm) ===")
    print(f"Blurb SHA256 (Arm A == Arm B): {BLURB_SHA256}  ✓")
    print(f"Sampling: {SAMPLING}")
    print(f"Arm A (matched floor): {ARM_A_MODEL}")
    print(f"Arm B (thesis):        {ARM_B_MODEL}")
    print(f"Eval set: {eval_path}  ({len(records)} questions, k={args.k})")
    print(f"Output:   {out_path}")
    print()
    print("Pre-registered reading:")
    print("  Arm B > Arm A → thesis supported (LoRA adds value at matched prompts)")
    print("  Arm B ≈ Arm A → v1 baking added little; DPO+r32 (v2) is the real test")
    print("  Arm B < Arm A → thesis in trouble; investigate before more compute")
    print()

    total = 0
    errors = {"arm_a": 0, "arm_b": 0}
    intersection = 0
    retrieve_sha_mismatches = 0

    with out_path.open("w") as out_fh, fail_path.open("w") as fail_fh:
        for i, rec in enumerate(records):
            messages = rec["messages"]
            gold     = next((m["content"] for m in reversed(messages) if m["role"] == "assistant"), "")
            question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

            hits   = retrieve(question, k=args.k)
            msgs_a = build_arm(messages, hits)
            msgs_b = build_arm(messages, hits)

            sha_a = user_turn_sha256(msgs_a)
            sha_b = user_turn_sha256(msgs_b)
            if sha_a != sha_b:
                retrieve_sha_mismatches += 1
                print(f"[WARN q{i}] user-turn SHA mismatch: {sha_a} vs {sha_b}")

            t0 = time.time()
            arm_a_answer = ollama_chat(ARM_A_MODEL, msgs_a)
            t1 = time.time()
            arm_b_answer = ollama_chat(ARM_B_MODEL, msgs_b)
            t2 = time.time()

            arm_a_ok = not is_error(arm_a_answer)
            arm_b_ok = not is_error(arm_b_answer)
            all_ok   = arm_a_ok and arm_b_ok

            total += 1
            if not arm_a_ok: errors["arm_a"] += 1
            if not arm_b_ok: errors["arm_b"] += 1
            if all_ok: intersection += 1

            err_flags = "".join(k for k, ok in [("A", arm_a_ok), ("B", arm_b_ok)] if not ok)
            status = "OK" if all_ok else f"ERR({err_flags})"
            print(
                f"[{i+1:03}/{len(records)}] {status}  "
                f"A={round(t1-t0,1)}s B={round(t2-t1,1)}s  "
                f"{question[:60].replace(chr(10),' ')!r}"
            )

            row = {
                "question_id":       i,
                "provenance":        rec.get("provenance", {}),
                "theme":             rec.get("theme", ""),
                "variant_group":     rec.get("variant_group", ""),
                "question":          question[:300],
                "gold":              gold,
                "retrieved_entries": [{"id": h["id"], "title": h["title"], "body": h["body"]} for h in hits],
                "retrieved_k":       args.k,
                "retrieve_sha":      sha_a,
                "blurb_sha":         BLURB_SHA256,
                "arm_a_answer":      arm_a_answer,
                "arm_b_answer":      arm_b_answer,
                "arm_a_ok":          arm_a_ok,
                "arm_b_ok":          arm_b_ok,
            }
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_fh.flush()

            if not all_ok:
                fail_fh.write(json.dumps({
                    "question_id":  i,
                    "question":     question[:300],
                    "arm_a_error":  arm_a_answer if not arm_a_ok else None,
                    "arm_b_error":  arm_b_answer if not arm_b_ok else None,
                }, ensure_ascii=False) + "\n")
                fail_fh.flush()

    print(f"\n=== Run complete ===")
    print(f"Total:                  {total}")
    print(f"Intersection (both OK): {intersection}")
    print(f"Arm A errors:           {errors['arm_a']}")
    print(f"Arm B errors:           {errors['arm_b']}")
    print(f"Retrieve SHA mismatches: {retrieve_sha_mismatches}  (must be 0)")
    print(f"Blurb SHA:              {BLURB_SHA256}")
    print(f"Output:                 {out_path}")


if __name__ == "__main__":
    main()
