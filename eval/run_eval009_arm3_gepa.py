#!/usr/bin/env python3
"""
FLOT-103 follow-up: Re-run EVAL-009 Arm 3 with the GEPA-optimized prompt.

This replaces the baseline_v1 hand-crafted prompt with the GEPA output.
Results update the Arm 3 column in EVAL009_results.md.

Usage:
    python3 eval/run_eval009_arm3_gepa.py \
        [--gepa-prompt eval/gepa_out/optimized_prompt.json] \
        [--questions eval/eval009_adversarial.jsonl] \
        [--out eval/results_eval009_gepa.jsonl] \
        [--k 3]
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve  # noqa: E402

DEFAULT_GEPA_PROMPT = "eval/gepa_out/optimized_prompt.json"
ARM3_MODEL = "MichelRosselli/apertus:8b-instruct-2509-q4_k_m"
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


def inject_rag(question: str, hits: list) -> str:
    if not hits:
        return question
    ctx = "Relevant fleet knowledge:\n" + "".join(
        f"[{h['id']}] {h['title']}\n{h['body']}\n\n" for h in hits
    )
    return ctx.rstrip() + "\n\n---\n\n" + question


def load_jsonl(path: pathlib.Path) -> list:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gepa-prompt", default=DEFAULT_GEPA_PROMPT)
    ap.add_argument("--questions",   default="eval/eval009_adversarial.jsonl")
    ap.add_argument("--out",         default="eval/results_eval009_gepa.jsonl")
    ap.add_argument("--k",           type=int, default=3)
    args = ap.parse_args()

    gepa_path = pathlib.Path(args.gepa_prompt)
    if not gepa_path.exists():
        sys.exit(f"[ERROR] GEPA prompt not found: {gepa_path}. Run gepa_harness.py first.")

    with gepa_path.open() as f:
        gepa = json.load(f)

    prompt_text = gepa["optimized_prompt"]
    prompt_sha  = hashlib.sha256(prompt_text.encode()).hexdigest()
    coop_score  = gepa.get("coop_score", "?")
    adv_score   = gepa.get("adv_score", "?")
    composite   = gepa.get("composite_score", "?")
    beats       = gepa.get("beats_baseline", "?")

    print("=== EVAL-009 Arm 3 — GEPA-optimized prompt ===")
    print(f"Prompt ({gepa.get('prompt_words','?')} words):  {prompt_text[:100]}…")
    print(f"GEPA scores: coop={coop_score}  adv={adv_score}  composite={composite}  beats_baseline={beats}")
    print(f"Model: {ARM3_MODEL}")
    print()

    q_path   = pathlib.Path(args.questions)
    out_path = pathlib.Path(args.out)

    questions = load_jsonl(q_path)
    done_ids  = {r["question_id"] for r in load_jsonl(out_path)}
    if done_ids:
        print(f"[RESUME] {len(done_ids)} questions already done.")

    by_type = {"PI": 0, "OCD": 0, "RO": 0}
    total = errs = 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for q in questions:
            qid = q["question_id"]
            if qid in done_ids:
                continue

            attack_type   = q["attack_type"]
            question_text = q["question"]
            predef_ctx    = q.get("rag_context", [])

            if attack_type == "OCD":
                hits = predef_ctx
                retrieval_mode = "predef_wrong"
            elif predef_ctx:
                hits = predef_ctx
                retrieval_mode = "predef_poisoned"
            else:
                hits = retrieve(question_text, k=args.k)
                retrieval_mode = "live_bm25"

            user = inject_rag(question_text, hits)
            msgs = [
                {"role": "system", "content": prompt_text},
                {"role": "user",   "content": user},
            ]

            t0  = time.time()
            ans = ollama_chat(ARM3_MODEL, msgs)
            elapsed = time.time() - t0

            ok = not ans.startswith("[ERROR:")
            total += 1
            if not ok:
                errs += 1
            by_type[attack_type] += 1

            status = "OK" if ok else "ERR"
            print(
                f"[{qid+1:02d}/{len(questions)}] {attack_type} {status}  {elapsed:.1f}s  "
                f"ctx={retrieval_mode}  {question_text[:60].replace(chr(10),' ')!r}"
            )

            row = {
                "question_id":        qid,
                "attack_type":        attack_type,
                "question":           question_text,
                "gold_correct":       q["gold_correct"],
                "gold_wrong":         q["gold_wrong"],
                "scoring_hint":       q["scoring_hint"],
                "retrieval_mode":     retrieval_mode,
                "rag_hits":           hits,
                "arm3_model":         ARM3_MODEL,
                "arm3_prompt_version": "gepa_v1",
                "arm3_prompt_sha":    prompt_sha,
                "arm3_answer":        ans,
                "arm3_ok":            ok,
                "arm3_s":             round(elapsed, 1),
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()

    print(f"\n=== Run complete ===")
    print(f"Total: {total}  (PI={by_type['PI']} OCD={by_type['OCD']} RO={by_type['RO']})")
    print(f"Errors: {errs}")
    print(f"Output: {out_path}")
    print(f"Grade with: python3 eval/grade_eval009.py --results {out_path}")


if __name__ == "__main__":
    main()
