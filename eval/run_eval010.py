#!/usr/bin/env python3
"""
FLOT-106 / EVAL-010: Multi-turn grounding decay.

Two conditions run against the same 5 threads × 10 turns:

  Condition A — Naive  (no session manager)
    Messages grow each turn: accumulated [user+assistant] history.
    With num_ctx=4096 this saturates by turn 5-6, pushing early facts out.

  Condition B — Session manager (FLOT-105)
    Bounded context: [system][user: T2|T1-cache|fresh-rag|q] per turn.
    T1 keeps all seen fact IDs; window never grows unboundedly.

Both conditions use the same model (apertus-flotilla) and same RAG calls.

Usage:
    python3 eval/run_eval010.py [--threads eval/multi_turn_threads.json]
                                [--out eval/results_eval010.jsonl]
                                [--model apertus-flotilla] [--k 3]

Output columns per JSONL record:
    thread_id, condition, turn, gold_entry_id, question,
    is_anchor, is_recall, check_phrase, response, elapsed_s, error
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve
from eval.session_manager import SessionManager

OLLAMA_URL = "http://localhost:11434/api/chat"

# Small num_ctx to make saturation visible within 10 turns.
# 3 full RAG entries (~200 tok each) + rag metadata + Q + A ≈ 900 tokens/turn.
# 4096 / 900 ≈ 4.5 turns before the naive window overflows turn-1 context.
SAMPLING = {"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096}

BLURB = (
    "You are a capable engineering agent working within a multi-agent fleet. "
    "You follow the heartbeat protocol, respect project scope boundaries, "
    "respond precisely to corrections, verify work before claiming completion, "
    "and never confuse separate project contexts. "
    "When corrected, acknowledge cleanly and act on the new direction without defensiveness."
)


def ollama_chat(model: str, messages: list, timeout: int = 120) -> str:
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": SAMPLING,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:
            if attempt == 0:
                time.sleep(5)
            else:
                return f"[ERROR: {e}]"
    return "[ERROR: timed out]"


def run_naive(thread: dict, model: str, k: int) -> list[dict]:
    """Condition A: accumulate full history, no session manager."""
    records = []
    messages = [{"role": "system", "content": BLURB}]

    for turn_info in thread["turns"]:
        q = turn_info["question"]
        hits = retrieve(q, k=k)
        # Build user content: RAG block + question
        rag_block = ""
        if hits:
            parts = [f"[{h['id']}] {h['title']}\n{h['body']}" for h in hits]
            rag_block = "[RETRIEVED CONTEXT]\n" + "\n\n".join(parts) + "\n\n"
        user_content = rag_block + q
        messages.append({"role": "user", "content": user_content})

        t0 = time.time()
        response = ollama_chat(model, messages)
        elapsed = round(time.time() - t0, 2)

        records.append({
            "thread_id": thread["thread_id"],
            "condition": "naive",
            "turn": turn_info["turn"],
            "gold_entry_id": turn_info["gold_entry_id"],
            "question": q,
            "is_anchor": turn_info["is_anchor"],
            "is_recall": turn_info["is_recall"],
            "check_phrase": turn_info["check_phrase"],
            "response": response,
            "elapsed_s": elapsed,
            "error": response.startswith("[ERROR:"),
            "rag_ids": [h["id"] for h in hits],
        })

        # Accumulate history — this is what fills the context window
        messages.append({"role": "assistant", "content": response})
        label = "ANCHOR" if turn_info["is_anchor"] else ("RECALL" if turn_info["is_recall"] else f"noise-t{turn_info['turn']}")
        print(f"  [naive  T{turn_info['turn']:02d} {label}] {elapsed}s → {response[:60]!r}")

    return records


def run_session_manager(thread: dict, model: str, k: int) -> list[dict]:
    """Condition B: session manager compresses context each turn."""
    records = []
    sm = SessionManager(role_prompt=BLURB, summary_model=model)

    for turn_info in thread["turns"]:
        q = turn_info["question"]
        hits = retrieve(q, k=k)
        messages = sm.assemble(q, hits)

        t0 = time.time()
        response = ollama_chat(model, messages)
        elapsed = round(time.time() - t0, 2)

        records.append({
            "thread_id": thread["thread_id"],
            "condition": "session_mgr",
            "turn": turn_info["turn"],
            "gold_entry_id": turn_info["gold_entry_id"],
            "question": q,
            "is_anchor": turn_info["is_anchor"],
            "is_recall": turn_info["is_recall"],
            "check_phrase": turn_info["check_phrase"],
            "response": response,
            "elapsed_s": elapsed,
            "error": response.startswith("[ERROR:"),
            "rag_ids": [h["id"] for h in hits],
            "t1_cache_size": sm.cache_size,
            "turn_count": sm.turn_count,
        })

        sm.record(q, response, hits)
        label = "ANCHOR" if turn_info["is_anchor"] else ("RECALL" if turn_info["is_recall"] else f"noise-t{turn_info['turn']}")
        print(f"  [sess   T{turn_info['turn']:02d} {label}] {elapsed}s T1={sm.cache_size} → {response[:60]!r}")

    return records


def load_done(out_path: pathlib.Path) -> set:
    """Keys of already-completed records (for incremental restarts)."""
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            try:
                r = json.loads(line)
                done.add((r["thread_id"], r["condition"], r["turn"]))
            except Exception:
                pass
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", default="eval/multi_turn_threads.json")
    ap.add_argument("--out", default="eval/results_eval010.jsonl")
    ap.add_argument("--model", default="apertus-flotilla")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    threads_path = pathlib.Path(args.threads)
    out_path = pathlib.Path(args.out)
    threads = json.loads(threads_path.read_text())

    done = load_done(out_path)
    print(f"Loaded {len(threads)} threads. Already done: {len(done)} records.")

    fh = out_path.open("a")

    for thread in threads:
        tid = thread["thread_id"]
        print(f"\n=== Thread {tid}: {thread['anchor_title']!r} ===")

        # Condition A: naive
        if not all((tid, "naive", t["turn"]) in done for t in thread["turns"]):
            print(f"  Running naive condition...")
            naive_records = run_naive(thread, args.model, args.k)
            for r in naive_records:
                if (r["thread_id"], r["condition"], r["turn"]) not in done:
                    fh.write(json.dumps(r) + "\n")
            fh.flush()
        else:
            print(f"  Naive condition already done, skipping.")

        # Condition B: session manager
        if not all((tid, "session_mgr", t["turn"]) in done for t in thread["turns"]):
            print(f"  Running session manager condition...")
            sm_records = run_session_manager(thread, args.model, args.k)
            for r in sm_records:
                if (r["thread_id"], r["condition"], r["turn"]) not in done:
                    fh.write(json.dumps(r) + "\n")
            fh.flush()
        else:
            print(f"  Session manager condition already done, skipping.")

    fh.close()
    total = sum(1 for _ in out_path.read_text().splitlines() if _.strip())
    print(f"\nDone. {total} records written to {out_path}")


if __name__ == "__main__":
    main()
