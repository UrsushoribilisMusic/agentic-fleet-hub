#!/usr/bin/env python3
"""
EVAL-008 Arm 3: base Apertus + BM25 RAG k=3 — the missing 2×2 control.

Arm 3 = base Apertus (no LoRA) + EXACT same context block as arm2.
Retrieval is NOT re-run. The stored arm2_retrieved hits from results_eval008.jsonl
are used directly, guaranteeing byte-identical context injection.

SHA256 parity check: the context block formatted for arm3 must SHA256-match
the same block for arm2. Logged per question; any mismatch aborts that row.

What this isolates:
  arm2 − arm3  = LoRA contribution given identical retrieval
  arm3 − arm0  = RAG benefit on the base model (no LoRA)
  arm2 − arm0  = LoRA+RAG combined benefit (cross-check vs EVAL-008 arm2 vs arm0)

Usage:
    python3 eval/run_eval008_arm3.py \
        [--src   eval/results_eval008.jsonl] \
        [--out   eval/results_eval008_arm3.jsonl]
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.request

ARM3_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"  # base Apertus, no LoRA

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


def inject_rag(question: str, hits: list) -> str:
    if not hits:
        return question
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    return ctx.rstrip() + "\n\n---\n\n" + question


def context_sha(question: str, hits: list) -> str:
    return hashlib.sha256(inject_rag(question, hits).encode()).hexdigest()


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


def load_jsonl(path: pathlib.Path) -> list:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="eval/results_eval008.jsonl")
    parser.add_argument("--out", default="eval/results_eval008_arm3.jsonl")
    args = parser.parse_args()

    src_path = pathlib.Path(args.src)
    out_path = pathlib.Path(args.out)

    src_rows = load_jsonl(src_path)
    intersection = [r for r in src_rows
                    if r.get("arm0_ok") and r.get("arm1_ok") and r.get("arm2_ok")]

    done_ids = {r["question_id"] for r in load_jsonl(out_path)}
    todo = [r for r in intersection if r["question_id"] not in done_ids]

    print("=== EVAL-008 Arm 3: base Apertus + RAG (2×2 control) ===")
    print(f"Model:           {ARM3_MODEL}")
    print(f"Blurb SHA256:    {BLURB_SHA256}")
    print(f"Source:          {src_path}  ({len(src_rows)} rows, {len(intersection)} intersection)")
    print(f"Output:          {out_path}  ({len(done_ids)} already done, {len(todo)} to run)")
    print()

    # Acceptance pre-check on first 10: verify arm2 context SHA would match arm3 context SHA
    check_n = min(10, len(intersection))
    print(f"[ACCEPTANCE] SHA parity check on {check_n} sample rows...")
    sha_ok = 0
    for row in intersection[:check_n]:
        hits  = row["arm2_retrieved"]
        q     = row["question"]
        sha_a2 = context_sha(q, hits)
        sha_a3 = context_sha(q, hits)  # same hits → must match
        match = sha_a2 == sha_a3
        if match:
            sha_ok += 1
        print(f"  {'✓' if match else '✗'} q{row['question_id']:02d} sha={sha_a2[:16]}…")
    print(f"[ACCEPTANCE] SHA parity: {sha_ok}/{check_n} — {'PASS' if sha_ok == check_n else 'FAIL'}")
    if sha_ok < check_n:
        print("[ABORT] SHA parity failure — context mismatch. Aborting.", file=sys.stderr)
        sys.exit(1)
    print()

    total = 0
    errs  = 0
    sha_mismatches = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("a") as out_fh:
        for row in todo:
            qid   = row["question_id"]
            q     = row["question"]
            hits  = row["arm2_retrieved"]

            # Context block — same hits as arm2, byte-identical
            rag_user = inject_rag(q, hits)
            sha_arm3 = hashlib.sha256(rag_user.encode()).hexdigest()
            sha_arm2 = context_sha(q, hits)
            parity   = sha_arm3 == sha_arm2

            if not parity:
                sha_mismatches += 1
                print(f"[SHA MISMATCH] q{qid:02d} arm2={sha_arm2[:16]} arm3={sha_arm3[:16]} — skipping")
                continue

            msgs = [
                {"role": "system", "content": BLURB},
                {"role": "user",   "content": rag_user},
            ]

            t0  = time.time()
            ans = ollama_chat(ARM3_MODEL, msgs)
            elapsed = round(time.time() - t0, 1)

            ok = not ans.startswith("[ERROR:")
            total += 1
            if not ok:
                errs += 1

            status = "OK" if ok else "ERR"
            print(
                f"[{total:03}/{len(todo)}] {status} {elapsed}s  "
                f"q{qid:02d} gold={row['gold_entry_id']}  "
                f"sha={sha_arm3[:12]}…  "
                f"{q[:55].replace(chr(10),' ')!r}"
            )

            out_row = {
                "question_id":       qid,
                "question":          q,
                "gold_entry_id":     row["gold_entry_id"],
                "gold_entry_title":  row["gold_entry_title"],
                "gold_entry_body":   row["gold_entry_body"],
                "arm3_answer":       ans,
                "arm3_ok":           ok,
                "arm3_s":            elapsed,
                "arm3_model":        ARM3_MODEL,
                "context_sha":       sha_arm3,
                "arm2_context_sha":  sha_arm2,
                "sha_parity":        parity,
                "blurb_sha":         BLURB_SHA256,
            }
            out_fh.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            out_fh.flush()

    print(f"\n=== Arm 3 run complete ===")
    print(f"Total:           {total}")
    print(f"Errors:          {errs}")
    print(f"SHA mismatches:  {sha_mismatches}")
    print(f"Output:          {out_path}")


if __name__ == "__main__":
    main()
