#!/usr/bin/env python3
"""
CANIS Task 1 — score the OOD test set with FROZEN seed vectors (no refit).

For each model, loads the OOD h_tap, computes z = J @ h (unit), and scores under:
  - frozen CE-09 discriminant seeds  (seed_vectors_<model>_ce09.npz)
  - naive production seeds           (seed_vectors_<model>_3q4.npz.bak-preCE09)
Reports per-class + macro recall (positives) / FP (matched-negs, predicted==target),
side-by-side with the in-distribution 5-fold CV numbers from ce09_results.json.

Also reports, per class, cosine(frozen CE-09 seed, centroid of OOD positives) — does the
frozen vector still point where the OOD data for that class actually lives?

Usage: python3 score_ood.py   (expects h_tap_ood_<model>.jsonl in eval/)
"""
import json, pathlib, numpy as np
from ce09_discriminant_seeds import wilson, unit, unit_rows, CLASSES, MODELS, DLENS, EVAL

def jl(p): return [json.loads(l) for l in open(p) if l.strip()]

matrix = {r["item_id"]: r for r in jl(EVAL/"canis_eval001_ood_matrix.jsonl")}
cv = json.load(open(EVAL/"ce09_results.json"))

def classify(Zrows, seedmat):
    return [CLASSES[j] for j in np.argmax(Zrows @ seedmat.T, axis=1)]

def score(Z, idx, seedmat):
    """Per-class recall (positives) + FP (negatives predicted==target)."""
    out = {}
    for cl in CLASSES:
        pos = [i for i, r in matrix.items() if r["target_class"]==cl and r["split"]=="positive" and i in idx]
        neg = [i for i, r in matrix.items() if r["target_class"]==cl and r["split"]=="negative" and i in idx]
        pr = classify(Z[[idx[i] for i in pos]], seedmat)
        nr = classify(Z[[idx[i] for i in neg]], seedmat)
        tp = sum(p==cl for p in pr); fp = sum(p==cl for p in nr)
        out[cl] = dict(recall=tp/len(pr) if pr else 0, npos=len(pr), tp=tp,
                       fp_rate=fp/len(nr) if nr else 0, nneg=len(nr), fp=fp)
    return out

def macro(m): return (np.mean([m[c]["recall"] for c in CLASSES]),
                      np.mean([m[c]["fp_rate"] for c in CLASSES]))

report = {}
for m in MODELS:
    htap_path = EVAL/"ood_run"/f"h_tap_canis_eval001_{m}.jsonl"
    if not htap_path.exists():
        print(f"[{m}] SKIP — {htap_path.name} not found (run the OOD tap first)"); continue
    htap = {r["item_id"]: np.asarray(r["h_tap"], np.float32) for r in jl(htap_path)}
    ids = [i for i in matrix if i in htap]
    H = np.stack([htap[i] for i in ids])
    J = np.load(str(DLENS/f"jlens_cache_{m}_3q4.npy"))
    Z = unit_rows((H @ J.T).astype(np.float32)); del J
    idx = {i:k for k,i in enumerate(ids)}

    ce09 = np.load(str(DLENS/f"seed_vectors_{m}_ce09.npz"))
    naive = np.load(str(DLENS/f"seed_vectors_{m}_3q4.npz.bak-preCE09"))
    ce09_mat = unit_rows(np.stack([ce09[c] for c in CLASSES]))
    naive_mat = unit_rows(np.stack([naive[c] for c in CLASSES]))

    s_ce09 = score(Z, idx, ce09_mat)
    s_naive = score(Z, idx, naive_mat)

    # cosine(frozen CE-09 seed, centroid of OOD positives) per class
    cos = {}
    for k, cl in enumerate(CLASSES):
        pos = [idx[i] for i, r in matrix.items() if r["target_class"]==cl and r["split"]=="positive" and i in idx]
        c_ood = unit(Z[pos].mean(0))
        cos[cl] = float(ce09_mat[k] @ c_ood)

    report[m] = dict(ce09=s_ce09, naive=s_naive, cos=cos)
    del Z

# ---- print ----
print("="*92)
print("OOD RESULTS — frozen seeds, no refit  (recall / FP per class)")
print("="*92)
for m in report:
    r = report[m]; cvw = str(cv[m]["best_w"]) if m in cv else None
    print(f"\n== {m} ==  (CV column = 5-fold in-distribution, w=0 discriminant)")
    print(f"  {'class':10} {'CVrecall':>9} {'OODrecall':>10} {'  ':2} {'CVfp':>6} {'OODfp':>7} {'  ':2} {'seed·OODcentroid':>16}")
    cvw0 = cv[m]["cv"]["0.0"] if m in cv else {}
    for cl in CLASSES:
        cvR = cvw0.get(cl,{}).get("recall", float('nan'))
        cvF = cvw0.get(cl,{}).get("fp_rate", float('nan'))
        oR = r["ce09"][cl]["recall"]; oF = r["ce09"][cl]["fp_rate"]
        print(f"  {cl:10} {cvR:9.0%} {oR:10.0%}    {cvF:6.0%} {oF:7.0%}    {r['cos'][cl]:16.3f}")
    mR,mF = macro(r["ce09"]); nR,nF = macro(r["naive"])
    cvmR = np.mean([cvw0.get(c,{}).get("recall",0) for c in CLASSES])
    cvmF = np.mean([cvw0.get(c,{}).get("fp_rate",0) for c in CLASSES])
    print(f"  {'MACRO':10} {cvmR:9.0%} {mR:10.0%}    {cvmF:6.0%} {mF:7.0%}")
    print(f"  (naive seeds on same OOD set: macro recall {nR:.0%} / FP {nF:.0%})")

json.dump(report, open(EVAL/"ood_results.json","w"), indent=2)
print("\nwrote ood_results.json")
