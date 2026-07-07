#!/usr/bin/env python3
"""
EVAL-008: In-corpus recall — 3-arm, N=50.

Arms (all Q4_K_M, matched precision):
  Arm 0 — Apertus base, no LoRA, no RAG
  Arm 1 — Apertus + LoRA, NO RAG  (baked know-how alone)
  Arm 2 — Apertus + LoRA + RAG wiki  (full product)

Design invariants:
  - All three arms receive the same system prompt (BLURB)
  - Only Arm 2 gets RAG context injected into the user turn
  - Retrieval called once per question, reused by Arm 2 only
  - 180s timeout + 1 retry; log per-arm timeouts
  - Write incrementally — safe to restart (skips already-done question_ids)
  - Score on intersection (all 3 OK); report intersection N + full N

What this measures:
  Arm 0 → 1 : effect of LoRA baking (same prompt, no RAG)
  Arm 1 → 2 : what RAG adds on top of baked weights
  vs EVAL-007 (out-of-corpus): in-corpus >> out-of-corpus = faithful ingestion

Usage:
    python3 eval/run_eval008.py [--questions eval/eval008_questions.jsonl]
                                [--out eval/results_eval008.jsonl] [--k 3]
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

ARM0_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"  # base, no LoRA
ARM1_MODEL = "apertus-flotilla"                                   # LoRA, no RAG
ARM2_MODEL = "apertus-flotilla"                                   # LoRA + RAG

# Identical system prompt for all three arms — only variable is LoRA + RAG
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


def ollama_chat(model: str, messages: list, timeout: int = 180) -> str:
    payload = json.dumps({"model": model, "messages": messages,
                          "stream": False, "options": SAMPLING}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:
            if attempt == 0:
                time.sleep(10)
            else:
                return f"[ERROR: {e}]"
    return "[ERROR: timed out]"


def is_error(s: str) -> bool:
    return s.startswith("[ERROR:")


def inject_rag(question: str, hits: list) -> str:
    """Prepend RAG context to the user question (Arm 2 only)."""
    if not hits:
        return question
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    return ctx.rstrip() + "\n\n---\n\n" + question


def build_messages(question: str, rag_context: bool = False, hits: list = None) -> list:
    user_content = inject_rag(question, hits or []) if rag_context else question
    return [
        {"role": "system", "content": BLURB},
        {"role": "user",   "content": user_content},
    ]


def load_jsonl(path: pathlib.Path) -> list:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="eval/eval008_questions.jsonl")
    parser.add_argument("--out",       default="eval/results_eval008.jsonl")
    parser.add_argument("--k",         type=int, default=3)
    args = parser.parse_args()

    q_path  = pathlib.Path(args.questions)
    out_path = pathlib.Path(args.out)

    if not q_path.exists():
        print(f"[ERROR] questions file not found: {q_path}", file=sys.stderr); sys.exit(1)

    questions = load_jsonl(q_path)

    # Resume support: skip already-completed question_ids
    done_ids = {r["question_id"] for r in load_jsonl(out_path)}
    if done_ids:
        print(f"[RESUME] {len(done_ids)} questions already done, skipping.")

    print("=== EVAL-008: In-corpus recall — 3-arm ===")
    print(f"Blurb SHA256 (all arms): {BLURB_SHA256}")
    print(f"Arm 0 (base, no LoRA, no RAG): {ARM0_MODEL}")
    print(f"Arm 1 (LoRA, no RAG):          {ARM1_MODEL}")
    print(f"Arm 2 (LoRA + RAG, k={args.k}): {ARM2_MODEL}")
    print(f"Questions: {q_path}  ({len(questions)} total, {len(questions)-len(done_ids)} to run)")
    print(f"Output:    {out_path}")
    print()

    total = 0
    errs = {"arm0": 0, "arm1": 0, "arm2": 0}
    intersection = 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as out_fh:
        for q in questions:
            qid = q["question_id"]
            if qid in done_ids:
                continue

            question_text = q["question"]
            gold_id       = q["gold_entry_id"]
            gold_body     = q["gold_entry_body"]

            # RAG retrieval — Arm 2 only, called once
            hits = retrieve(question_text, k=args.k)

            msgs0 = build_messages(question_text, rag_context=False)
            msgs1 = build_messages(question_text, rag_context=False)
            msgs2 = build_messages(question_text, rag_context=True, hits=hits)

            t0 = time.time()
            ans0 = ollama_chat(ARM0_MODEL, msgs0)
            t1 = time.time()
            ans1 = ollama_chat(ARM1_MODEL, msgs1)
            t2 = time.time()
            ans2 = ollama_chat(ARM2_MODEL, msgs2)
            t3 = time.time()

            ok0, ok1, ok2 = not is_error(ans0), not is_error(ans1), not is_error(ans2)
            all_ok = ok0 and ok1 and ok2
            total += 1
            if not ok0: errs["arm0"] += 1
            if not ok1: errs["arm1"] += 1
            if not ok2: errs["arm2"] += 1
            if all_ok:  intersection += 1

            flags = "".join(k for k, ok in [("0", ok0), ("1", ok1), ("2", ok2)] if not ok)
            status = "OK" if all_ok else f"ERR({flags})"
            print(
                f"[{qid+1:03}/{len(questions)}] {status}  "
                f"0={round(t1-t0,1)}s 1={round(t2-t1,1)}s 2={round(t3-t2,1)}s  "
                f"gold={gold_id}  {question_text[:55].replace(chr(10),' ')!r}"
            )

            row = {
                "question_id":     qid,
                "question":        question_text,
                "gold_entry_id":   gold_id,
                "gold_entry_title":q["gold_entry_title"],
                "gold_entry_body": gold_body,
                "arm2_retrieved":  [{"id": h["id"], "title": h["title"], "body": h["body"],
                                     "score": h["score"]} for h in hits],
                "arm2_retrieved_k":args.k,
                "blurb_sha":       BLURB_SHA256,
                "arm0_answer":     ans0,
                "arm1_answer":     ans1,
                "arm2_answer":     ans2,
                "arm0_ok":         ok0,
                "arm1_ok":         ok1,
                "arm2_ok":         ok2,
                "arm0_s":          round(t1 - t0, 1),
                "arm1_s":          round(t2 - t1, 1),
                "arm2_s":          round(t3 - t2, 1),
            }
            out_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_fh.flush()

    print(f"\n=== Run complete ===")
    print(f"Total:                    {total}")
    print(f"Intersection (all 3 OK):  {intersection}")
    print(f"Arm 0 errors:             {errs['arm0']}")
    print(f"Arm 1 errors:             {errs['arm1']}")
    print(f"Arm 2 errors:             {errs['arm2']}")
    print(f"Blurb SHA256:             {BLURB_SHA256}")
    print(f"Output:                   {out_path}")


if __name__ == "__main__":
    main()
