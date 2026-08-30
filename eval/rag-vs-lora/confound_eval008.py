#!/usr/bin/env python3
"""
EVAL-008 Task 3 — confound checks on the same 49 items.

Candidate mechanism for the grader gap (Qwen sees arm2-arm3 = -1.02; Opus aggregate
saw ~-0.14): does answer LENGTH or CITATION FORMAT differ systematically by arm, and
does length correlate with grade?

Length is reported in CHARACTERS and WORDS. tiktoken is unavailable here, so WORDS
(whitespace split) is the token proxy — labelled as such, not passed off as tokens.
"""
import json, re, pathlib, statistics as st
from scipy.stats import spearmanr

HERE = pathlib.Path(__file__).parent
DIMS = ["grounded", "correct", "faithful_recall"]

def load(name): return [json.loads(l) for l in (HERE/name).read_text().splitlines() if l.strip()]
def comp(g):
    v=[g.get(d) for d in DIMS if g.get(d) is not None]; return sum(v)/len(v) if v else None

qwen = {r["question_id"]: r for r in load("results_eval008_graded.jsonl")}
arm3 = {r["question_id"]: r for r in load("results_eval008_arm3.jsonl")}
arm3g = {r["question_id"]: comp(r.get("arm3_grade") or {}) for r in load("results_eval008_arm3_graded.jsonl")}
opus = {r["question_id"]: r for r in load("results_eval008_opus_graded.jsonl")}

# fleet-artifact citation pattern: rule/fact/incident/protocol IDs the wiki uses
CITE = re.compile(r"\b([RFIP]\d{2,3})\b")

rows = []
for qid, r in sorted(qwen.items()):
    gold_id = r.get("gold_entry_id", "")
    answers = {
        "arm0": r.get("arm0_answer", ""), "arm1": r.get("arm1_answer", ""),
        "arm2": r.get("arm2_answer", ""), "arm3": arm3.get(qid, {}).get("arm3_answer", ""),
    }
    qgrades = {
        "arm0": comp(r.get("arm0_grade") or {}), "arm1": comp(r.get("arm1_grade") or {}),
        "arm2": comp(r.get("arm2_grade") or {}), "arm3": arm3g.get(qid),
    }
    o = opus.get(qid, {})
    ogrades = {a: comp(o.get(f"{a}_opus") or {}) for a in ("arm0","arm1","arm2")}
    ogrades["arm3"] = None  # pending Task 1
    rows.append({"qid": qid, "gold_id": gold_id, "answers": answers,
                 "qgrades": qgrades, "ogrades": ogrades})

ARMS = ["arm0","arm1","arm2","arm3"]
def chars(a): return len(a)
def words(a): return len(a.split())

print("="*72)
print("TASK 3 — CONFOUND CHECKS (n=49)")
print("="*72)
print("\n[A] Output length per arm  (words = token proxy)")
print(f"{'arm':6} {'mean_chars':>11} {'med_chars':>10} {'mean_words':>11} {'med_words':>10}")
lens = {a: {"chars": [], "words": []} for a in ARMS}
for row in rows:
    for a in ARMS:
        lens[a]["chars"].append(chars(row["answers"][a]))
        lens[a]["words"].append(words(row["answers"][a]))
for a in ARMS:
    c, w = lens[a]["chars"], lens[a]["words"]
    print(f"{a:6} {st.mean(c):11.0f} {st.median(c):10.0f} {st.mean(w):11.0f} {st.median(w):10.0f}")

print("\n[B] Spearman(length_words, grade) — per grader, per arm + pooled")
for grader, key in (("Qwen","qgrades"), ("Opus","ogrades")):
    print(f"  {grader}:")
    pooled_len, pooled_grade = [], []
    for a in ARMS:
        L = [words(row["answers"][a]) for row in rows if row[key][a] is not None]
        G = [row[key][a] for row in rows if row[key][a] is not None]
        if len(G) >= 5 and len(set(G)) > 1:
            rho, p = spearmanr(L, G); print(f"    {a}: rho={rho:+.3f}  p={p:.3f}  n={len(G)}")
            pooled_len += L; pooled_grade += G
        else:
            print(f"    {a}: (insufficient / pending)")
    if pooled_grade:
        rho, p = spearmanr(pooled_len, pooled_grade)
        print(f"    POOLED: rho={rho:+.3f}  p={p:.3f}  n={len(pooled_grade)}")

print("\n[C] Citation / grounding format — answers citing a fleet ID (R/F/I/P nn)")
print(f"{'arm':6} {'n_cite':>7} {'rate':>6} {'cite_gold':>10} {'gold_rate':>9} {'mean_ids':>9}")
for a in ARMS:
    n_cite = gold_cite = total_ids = 0
    for row in rows:
        ids = set(CITE.findall(row["answers"][a]))
        if ids: n_cite += 1
        if row["gold_id"] and row["gold_id"] in ids: gold_cite += 1
        total_ids += len(ids)
    n = len(rows)
    print(f"{a:6} {n_cite:7d} {n_cite/n:6.2f} {gold_cite:10d} {gold_cite/n:9.2f} {total_ids/n:9.2f}")

print("\n[D] Structural drift arm2 (LoRA+RAG) vs arm3 (Base+RAG)")
def rate(a, pred): return sum(pred(row["answers"][a]) for row in rows)/len(rows)
for label, pred in [
    ("cites any fleet ID", lambda x: bool(CITE.findall(x))),
    ("has markdown header (#/**bold**)", lambda x: bool(re.search(r"(^|\n)\s*#|\*\*", x))),
    ("has numbered list", lambda x: bool(re.search(r"(^|\n)\s*\d+\.", x))),
    ("has table (| col |)", lambda x: x.count("|") >= 4),
    ("quotes gold verbatim (>=8-word run)", lambda x: False),  # filled below
]:
    if "quotes gold" in label: continue
    print(f"  {label:38} arm2={rate('arm2',pred):.2f}  arm3={rate('arm3',pred):.2f}")
