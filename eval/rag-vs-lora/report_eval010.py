#!/usr/bin/env python3
"""
FLOT-106 / EVAL-010: Report multi-turn grounding decay.

Reads results_eval010_graded.jsonl and prints:
  1. Per-turn decay table (naive vs session_mgr, mean grounding_score)
  2. Turn-1 vs Turn-10 comparison (the headline metric)
  3. Recall-only comparison (turn 10, is_recall=True)
  4. Verdict: does session manager hold grounding past window saturation?

Usage:
    python3 eval/report_eval010.py [--in eval/results_eval010_graded.jsonl]
                                   [--out eval/EVAL010_report.md]
"""
import argparse
import json
import pathlib
from collections import defaultdict

TURNS = list(range(1, 11))
CONDITIONS = ["naive", "session_mgr"]


def load(path: pathlib.Path) -> list[dict]:
    records = []
    for line in path.read_text().splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def pivot(records: list[dict]) -> dict:
    """Returns {condition: {turn: [grounding_score, ...]}}"""
    data: dict = {c: defaultdict(list) for c in CONDITIONS}
    for r in records:
        c = r.get("condition")
        t = r.get("turn")
        s = r.get("grounding_score", 0)
        if c in data and t in TURNS:
            data[c][t].append(s)
    return data


def mean(lst: list) -> float:
    return round(sum(lst) / len(lst), 3) if lst else float("nan")


def bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="eval/results_eval010_graded.jsonl")
    ap.add_argument("--out", default="eval/EVAL010_report.md")
    args = ap.parse_args()

    records = load(pathlib.Path(args.inp))
    if not records:
        print("No records found. Run run_eval010.py and grade_eval010.py first.")
        return

    data = pivot(records)

    lines = []
    lines.append("# EVAL-010: Multi-turn Grounding Decay Report")
    lines.append(f"\n*Generated from {len(records)} records across "
                 f"{len(set(r['thread_id'] for r in records))} threads × "
                 f"{len(set(r['turn'] for r in records))} turns × 2 conditions.*\n")

    lines.append("## 1. Decay curve — mean grounding_score per turn\n")
    lines.append("grounding_score = keyword_hit (1 if check_phrase in response, else 0)\n")
    hdr = f"{'Turn':<6} {'Naive':>12} {'SessionMgr':>12}   {'Naive bar':<22}  {'SessionMgr bar':<22}"
    lines.append(hdr)
    lines.append("-" * len(hdr))

    naive_scores = []
    sm_scores = []
    for t in TURNS:
        n = mean(data["naive"][t])
        s = mean(data["session_mgr"][t])
        naive_scores.append(n)
        sm_scores.append(s)
        row = (f"T{t:<5} {n:>12.3f} {s:>12.3f}   "
               f"{bar(n):<22}  {bar(s):<22}")
        lines.append(row)

    lines.append("")
    lines.append(f"Mean across all turns — Naive: {mean(naive_scores):.3f}  "
                 f"SessionMgr: {mean(sm_scores):.3f}")

    # Turn-1 vs Turn-10 headline
    lines.append("\n## 2. Turn-1 vs Turn-10 (headline)\n")
    n1, n10 = naive_scores[0], naive_scores[9]
    s1, s10 = sm_scores[0], sm_scores[9]
    lines.append(f"| Condition   | Turn 1 | Turn 10 | Delta   |")
    lines.append(f"|-------------|--------|---------|---------|")
    lines.append(f"| Naive       | {n1:.3f}  | {n10:.3f}   | {n10-n1:+.3f}  |")
    lines.append(f"| SessionMgr  | {s1:.3f}  | {s10:.3f}   | {s10-s1:+.3f}  |")

    # Recall-only (is_recall=True, turn 10)
    recall_records = [r for r in records if r.get("is_recall")]
    lines.append("\n## 3. Recall turns only (turn 10, anchor fact recall)\n")
    for cond in CONDITIONS:
        subset = [r for r in recall_records if r["condition"] == cond]
        scores = [r["grounding_score"] for r in subset]
        kw = [r["keyword_hit"] for r in subset]
        llm = [r["llm_hit"] for r in subset]
        lines.append(f"**{cond}** — N={len(subset)}  "
                     f"keyword_hit={mean(kw):.2f}  llm_hit={mean(llm):.2f}")
        for r in subset:
            lines.append(f"  Thread {r['thread_id']} [{r.get('anchor_entry_id','?')}]"
                         f"  kw={r['keyword_hit']} llm={r['llm_hit']}  "
                         f"phrase={r['check_phrase']!r}")
    lines.append("")

    # Verdict
    lines.append("## 4. Verdict\n")
    recall_naive = mean([r["grounding_score"] for r in recall_records
                         if r["condition"] == "naive"])
    recall_sm = mean([r["grounding_score"] for r in recall_records
                      if r["condition"] == "session_mgr"])
    delta = recall_sm - recall_naive

    if delta > 0.1:
        verdict = (
            f"**CONFIRMED — session manager holds grounding past window saturation.**\n"
            f"Recall grounding: naive={recall_naive:.2f} → session_mgr={recall_sm:.2f} "
            f"(+{delta:.2f}). Compression preserves anchor facts in T1 cache while "
            f"naive accumulation pushes them out of the 4096-token context window."
        )
    elif delta >= 0:
        verdict = (
            f"**MARGINAL — session manager holds grounding slightly better.**\n"
            f"Recall grounding: naive={recall_naive:.2f} → session_mgr={recall_sm:.2f} "
            f"(+{delta:.2f}). Difference is small; both conditions avoid severe decay "
            f"at this context size. Consider re-running at smaller num_ctx or longer threads."
        )
    else:
        verdict = (
            f"**INCONCLUSIVE / REFUTED — session manager did not outperform naive baseline.**\n"
            f"Recall grounding: naive={recall_naive:.2f} → session_mgr={recall_sm:.2f} "
            f"({delta:.2f}). Investigate T2 summarizer faithfulness and T1 cache rendering."
        )

    lines.append(verdict)

    lines.append("\n### Decay curve summary\n")
    n_decay = naive_scores[9] - naive_scores[0]
    s_decay = sm_scores[9] - sm_scores[0]
    lines.append(f"- Naive: turn-1={naive_scores[0]:.3f} → turn-10={naive_scores[9]:.3f}  (Δ={n_decay:+.3f})")
    lines.append(f"- SessionMgr: turn-1={sm_scores[0]:.3f} → turn-10={sm_scores[9]:.3f}  (Δ={s_decay:+.3f})")

    lines.append("\n### Evaluation parameters\n")
    lines.append("- num_ctx: 4096 (simulates window saturation at ~turn 5 for naive)")
    lines.append("- Threads: 5 multi-turn conversations × 10 turns each")
    lines.append("- RAG k: 3 entries per turn")
    lines.append("- Primary grounding signal: keyword_hit (check_phrase in response)")
    lines.append("- Secondary signal: llm_hit (qwen2.5:7b judge)")
    lines.append("- Model under test: apertus-flotilla")

    report = "\n".join(lines)
    print(report)

    out_path = pathlib.Path(args.out)
    out_path.write_text(report)
    print(f"\nReport written → {out_path}")


if __name__ == "__main__":
    main()
