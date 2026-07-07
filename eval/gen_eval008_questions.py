#!/usr/bin/env python3
"""
EVAL-008: Generate 50 in-corpus recall questions from the wiki entries.

For each wiki entry, asks Qwen to write a paraphrase-varied question that is
only answerable if you know that entry's specific content. Selects 50 with
good type coverage, then runs an acceptance check on 10 random samples.

Usage:
    python3 eval/gen_eval008_questions.py [--n 50] [--out eval/eval008_questions.jsonl]
"""
import argparse
import json
import pathlib
import random
import sys
import textwrap
import urllib.request

OLLAMA_URL   = "http://localhost:11434/api/chat"
GRADE_MODEL  = "qwen2.5:7b"    # local Qwen
WIKI_DIR     = pathlib.Path(__file__).parent / "wiki" / "entries"
random.seed(42)


def ollama_chat(model: str, messages: list, timeout: int = 180) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False,
                          "options": {"temperature": 0.7, "top_p": 0.9}}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["message"]["content"].strip()
        except Exception as e:
            if attempt == 0:
                import time; time.sleep(5)
            else:
                return f"[ERROR: {e}]"
    return "[ERROR]"


def load_entries() -> list[dict]:
    entries = []
    for p in sorted(WIKI_DIR.glob("*.json")):
        entries.append(json.load(p.open()))
    return entries


def generate_question(entry: dict) -> str:
    """Ask Qwen to write one paraphrase-varied recall question for this entry."""
    prompt = textwrap.dedent(f"""
        You are writing test questions for an AI agent evaluation.

        Below is one entry from a fleet knowledge base:

        Entry ID: {entry['id']}
        Title: {entry['title']}
        Content: {entry['body']}

        Write ONE question that:
        - Can only be answered correctly by someone who knows this specific entry
        - Tests practical application or consequence, not just literal recall
        - Uses different phrasing from the source text (paraphrase)
        - Is answerable in 2–5 sentences
        - Does NOT mention the entry ID or title in the question itself

        Output ONLY the question text, nothing else.
    """).strip()

    return ollama_chat(GRADE_MODEL, [{"role": "user", "content": prompt}], timeout=180)


def acceptance_check(samples: list[dict]) -> list[dict]:
    """Verify each sample is genuinely answerable from its gold entry. Returns results."""
    print(f"\n[ACCEPTANCE] Checking {len(samples)} samples...")
    results = []
    for s in samples:
        prompt = textwrap.dedent(f"""
            A question was written to be answerable from a specific knowledge base entry.

            Entry ID: {s['gold_entry_id']}
            Entry content: {s['gold_entry_body']}

            Question: {s['question']}

            Is this question GENUINELY answerable from the entry content above?
            Answer YES or NO on the first line, then explain in one sentence.
        """).strip()

        verdict = ollama_chat(GRADE_MODEL, [{"role": "user", "content": prompt}], timeout=120)
        passed = verdict.upper().startswith("YES")
        results.append({"q_id": s["question_id"], "gold": s["gold_entry_id"],
                        "passed": passed, "verdict": verdict[:200]})
        mark = "✓" if passed else "✗"
        print(f"  [{mark}] q{s['question_id']:02d} ({s['gold_entry_id']}): {verdict[:80]}")
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n",   type=int, default=50)
    parser.add_argument("--out", default="eval/eval008_questions.jsonl")
    args = parser.parse_args()

    entries = load_entries()
    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[GEN] {len(entries)} wiki entries → generating questions with {GRADE_MODEL}")
    print(f"[GEN] Target: {args.n} questions  Output: {out_path}\n")

    # Generate one question per entry
    candidates = []
    for i, entry in enumerate(entries):
        print(f"  [{i+1:02d}/{len(entries)}] {entry['id']}  {entry['title'][:55]}", end="", flush=True)
        q = generate_question(entry)
        if q.startswith("[ERROR"):
            print(f" → SKIP ({q[:40]})")
            continue
        candidates.append({
            "gold_entry_id":   entry["id"],
            "gold_entry_type": entry["type"],
            "gold_entry_title":entry["title"],
            "gold_entry_body": entry["body"],
            "question":        q,
        })
        print(f" → OK  {q[:60]!r}")

    print(f"\n[GEN] {len(candidates)} candidates generated. Selecting {args.n}...")

    # Stratified sample: proportional to entry type counts
    by_type: dict[str, list] = {}
    for c in candidates:
        by_type.setdefault(c["gold_entry_type"], []).append(c)
    for t in by_type:
        random.shuffle(by_type[t])

    # Allocate slots proportionally
    total_cands = len(candidates)
    selected = []
    type_alloc = {}
    for t, items in by_type.items():
        alloc = round(args.n * len(items) / total_cands)
        type_alloc[t] = alloc
        selected.extend(items[:alloc])

    # Fill to exactly n
    remaining = [c for c in candidates if c not in selected]
    random.shuffle(remaining)
    while len(selected) < args.n and remaining:
        selected.append(remaining.pop(0))
    selected = selected[:args.n]
    random.shuffle(selected)  # shuffle final order

    # Assign IDs
    for i, s in enumerate(selected):
        s["question_id"] = i

    print(f"\n[GEN] Selected {len(selected)} questions:")
    for t, alloc in type_alloc.items():
        actual = sum(1 for s in selected if s["gold_entry_type"] == t)
        print(f"  {t:12}: {actual}")

    # Acceptance check on 10 random samples
    check_samples = random.sample(selected, min(10, len(selected)))
    check_results = acceptance_check(check_samples)
    passed = sum(1 for r in check_results if r["passed"])
    print(f"\n[ACCEPTANCE] {passed}/{len(check_results)} passed")
    if passed < 8:
        print("[WARN] Low acceptance rate — review question quality before running eval.")

    # Write output
    with out_path.open("w") as f:
        for s in selected:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Write acceptance report
    report_path = out_path.with_stem(out_path.stem + "_acceptance")
    with report_path.open("w") as f:
        json.dump({"passed": passed, "total": len(check_results),
                   "samples": check_results}, f, indent=2)

    print(f"\n[GEN] Done. {len(selected)} questions → {out_path}")
    print(f"[GEN] Acceptance report → {report_path}")
    print(f"[GEN] Spot-check: {passed}/{len(check_results)} genuinely answerable")


if __name__ == "__main__":
    main()
