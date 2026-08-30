#!/usr/bin/env python3
"""
EVAL-008 paper pack extractor.

Pulls the per-question graded scores for all four arms into a tidy CSV so a
PAIRED test can run (big-sis requirement #1), and runs the paired tests itself:
  - paired sign-flip permutation p-value (no scipy dependency, seed 42)
  - bootstrap 95% CI on the mean delta (seed 42, 10k — matches stats_eval008.py)
  - Wilcoxon signed-rank + paired t (only if scipy is importable — bonus)

Arms:  arm0 Base/no-RAG | arm1 LoRA/no-RAG | arm2 LoRA+RAG | arm3 Base+RAG
Graders: Qwen 2.5 7B (blind, per-question, ALL 4 arms)
         Opus-4 (blind, per-question, arms 0-2 only — arm3 is aggregate-only)
"""
import csv
import json
import pathlib
import random

HERE = pathlib.Path(__file__).parent
DIMS = ["grounded", "correct", "faithful_recall"]
N_BOOT = 10_000
SEED = 42


def load_jsonl(name):
    return [json.loads(l) for l in (HERE / name).read_text().splitlines() if l.strip()]


def composite(grade):
    vals = [grade.get(d) for d in DIMS if grade.get(d) is not None]
    return sum(vals) / len(vals) if vals else None


# ---- build per-question matrix ------------------------------------------------
qwen = load_jsonl("results_eval008_graded.jsonl")          # arm0/1/2 (_grade)
arm3 = load_jsonl("results_eval008_arm3_graded.jsonl")      # arm3 (_grade)
opus = load_jsonl("results_eval008_opus_graded.jsonl")      # arm0/1/2 (_opus)

arm3_by_q = {r["question_id"]: composite(r.get("arm3_grade") or {}) for r in arm3}
opus_by_q = {
    r["question_id"]: {a: composite(r.get(f"{a}_opus") or {}) for a in ("arm0", "arm1", "arm2")}
    for r in opus
}

rows = []
for r in sorted(qwen, key=lambda x: x["question_id"]):
    qid = r["question_id"]
    o = opus_by_q.get(qid, {})
    rows.append({
        "question_id": qid,
        "qwen_arm0": composite(r.get("arm0_grade") or {}),
        "qwen_arm1": composite(r.get("arm1_grade") or {}),
        "qwen_arm2": composite(r.get("arm2_grade") or {}),
        "qwen_arm3": arm3_by_q.get(qid),
        "opus_arm0": o.get("arm0"),
        "opus_arm1": o.get("arm1"),
        "opus_arm2": o.get("arm2"),
        "opus_arm3": "",  # MISSING per-question — aggregate-only (2.54)
    })

out_csv = HERE / "eval008_per_question.csv"
with out_csv.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {out_csv}  ({len(rows)} questions)")


# ---- paired stats -------------------------------------------------------------
def paired_deltas(a_key, b_key):
    d = []
    for r in rows:
        a, b = r[a_key], r[b_key]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            d.append(a - b)
    return d


def bootstrap_ci(deltas, n=N_BOOT, seed=SEED):
    rng = random.Random(seed)
    m = len(deltas)
    means = []
    for _ in range(n):
        s = [deltas[rng.randrange(m)] for _ in range(m)]
        means.append(sum(s) / m)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n)]


def sign_flip_p(deltas, n=N_BOOT, seed=SEED):
    """Paired randomization test: H0 = symmetric around 0. Two-sided."""
    rng = random.Random(seed)
    obs = abs(sum(deltas) / len(deltas))
    hits = 0
    for _ in range(n):
        s = sum(d if rng.random() < 0.5 else -d for d in deltas)
        if abs(s / len(deltas)) >= obs - 1e-12:
            hits += 1
    return hits / n


def wins(a_key, b_key):
    w = l = t = 0
    for r in rows:
        a, b = r[a_key], r[b_key]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a > b + 1e-9: w += 1
            elif b > a + 1e-9: l += 1
            else: t += 1
    return w, l, t


try:
    from scipy import stats as _sp
except Exception:
    _sp = None

COMPARISONS = [
    ("qwen_arm2", "qwen_arm3", "LoRA vs Base under equal RAG (arm2-arm3) — the LoRA benefit"),
    ("qwen_arm3", "qwen_arm0", "RAG gain on Base (arm3-arm0) — the retrieval lift"),
    ("qwen_arm2", "qwen_arm0", "Full stack vs Base (arm2-arm0)"),
    ("qwen_arm1", "qwen_arm0", "LoRA vs Base, both no-RAG (arm1-arm0)"),
    ("opus_arm2", "opus_arm1", "Opus: LoRA+RAG vs LoRA-only (arm2-arm1)"),
]

print("\n" + "=" * 78)
print("PAIRED TESTS  (positive delta = first arm scores higher)")
print("=" * 78)
for a, b, label in COMPARISONS:
    d = paired_deltas(a, b)
    if not d:
        print(f"\n{label}\n  no paired data"); continue
    mean = sum(d) / len(d)
    lo, hi = bootstrap_ci(d)
    p = sign_flip_p(d)
    w, l, t = wins(a, b)
    line = (f"\n{label}\n"
            f"  n={len(d)}  mean Δ={mean:+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  "
            f"perm p={p:.4f}\n"
            f"  wins {w} / losses {l} / ties {t}")
    if _sp is not None:
        try:
            wstat, wp = _sp.wilcoxon(d)
            tstat, tp = _sp.ttest_rel(
                [r[a] for r in rows if isinstance(r[a], (int, float)) and isinstance(r[b], (int, float))],
                [r[b] for r in rows if isinstance(r[a], (int, float)) and isinstance(r[b], (int, float))])
            line += f"\n  Wilcoxon p={wp:.4f}   paired-t p={tp:.4f}"
        except Exception as e:
            line += f"\n  (scipy test skipped: {e})"
    print(line)

print("\nNOTE: opus_arm3 per-question is MISSING (aggregate 2.54 only) — the Opus")
print("2.54-vs-2.40 paired test CANNOT run until arm3 is graded per-question by Opus.")
