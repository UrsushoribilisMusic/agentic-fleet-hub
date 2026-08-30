#!/usr/bin/env python3
"""
FLOT-106 / EVAL-010: Grade multi-turn grounding decay results.

Two grading signals per turn:
  1. keyword_hit (fast, deterministic):
     checks if check_phrase appears in the response (case-insensitive).
  2. llm_hit (judge, blind):
     asks qwen2.5:7b whether the response correctly uses the gold fact.
     judge sees: gold_entry body + question + response; strips condition label.

Final grounding_score per record = keyword_hit (0/1).
llm_hit recorded separately for cross-validation.

Usage:
    python3 eval/grade_eval010.py [--in eval/results_eval010.jsonl]
                                  [--out eval/results_eval010_graded.jsonl]
                                  [--judge qwen2.5:7b]
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from eval.retrieve import retrieve

OLLAMA_URL = "http://localhost:11434/api/chat"
JUDGE_SAMPLING = {"temperature": 0.1, "num_predict": 50, "num_ctx": 4096}

WIKI_DIR = pathlib.Path(__file__).parent / "wiki" / "entries"
_entry_cache: dict = {}


def load_entry(entry_id: str) -> dict | None:
    if entry_id in _entry_cache:
        return _entry_cache[entry_id]
    path = WIKI_DIR / f"{entry_id}.json"
    if not path.exists():
        return None
    e = json.loads(path.read_text())
    _entry_cache[entry_id] = e
    return e


def ollama_judge(judge_model: str, prompt: str, timeout: int = 60) -> str:
    payload = json.dumps({
        "model": judge_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": JUDGE_SAMPLING,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip().lower()
    except Exception as e:
        return f"[judge_error: {e}]"


def keyword_score(record: dict) -> int:
    phrase = record.get("check_phrase", "").lower()
    response = record.get("response", "").lower()
    if not phrase or record.get("error"):
        return 0
    return 1 if phrase in response else 0


def llm_score(record: dict, judge_model: str) -> int:
    entry = load_entry(record.get("gold_entry_id", ""))
    if entry is None or record.get("error"):
        return 0
    prompt = (
        f"Gold fact:\n{entry['body']}\n\n"
        f"Question: {record['question']}\n\n"
        f"Response: {record['response']}\n\n"
        "Does the response correctly use or cite the key facts from the gold fact above? "
        "Answer only 'yes' or 'no'."
    )
    raw = ollama_judge(judge_model, prompt)
    return 1 if raw.startswith("yes") else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="eval/results_eval010.jsonl")
    ap.add_argument("--out", default="eval/results_eval010_graded.jsonl")
    ap.add_argument("--judge", default="qwen2.5:7b")
    ap.add_argument("--no-llm", action="store_true",
                    help="Skip LLM judge (keyword only)")
    args = ap.parse_args()

    in_path = pathlib.Path(args.inp)
    out_path = pathlib.Path(args.out)

    # Load already-graded keys
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            try:
                r = json.loads(line)
                done.add((r["thread_id"], r["condition"], r["turn"]))
            except Exception:
                pass

    records = []
    for line in in_path.read_text().splitlines():
        if line.strip():
            records.append(json.loads(line))

    print(f"Grading {len(records)} records ({len(done)} already done)...")

    fh = out_path.open("a")
    for r in records:
        key = (r["thread_id"], r["condition"], r["turn"])
        if key in done:
            continue

        kw = keyword_score(r)
        llm = 0
        if not args.no_llm:
            llm = llm_score(r, args.judge)
            time.sleep(0.3)

        r["keyword_hit"] = kw
        r["llm_hit"] = llm
        r["grounding_score"] = kw   # primary signal
        r["judge_model"] = args.judge if not args.no_llm else "keyword_only"

        label = "ANCHOR" if r["is_anchor"] else ("RECALL" if r["is_recall"] else f"noise")
        print(f"  T{r['thread_id']} {r['condition'][:8]} turn{r['turn']:02d} "
              f"[{label:6}] kw={kw} llm={llm}  phrase={r['check_phrase']!r}")
        fh.write(json.dumps(r) + "\n")
        fh.flush()
        done.add(key)

    fh.close()
    total = sum(1 for _ in out_path.read_text().splitlines() if _.strip())
    print(f"\nDone. {total} graded records written to {out_path}")


if __name__ == "__main__":
    main()
