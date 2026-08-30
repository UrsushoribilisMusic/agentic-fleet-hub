#!/usr/bin/env python3
"""
CE-09: Discriminant-direction seed rebuild for the epistemic cluster (and all 7 axes),
cross-validated, across all three models.

Motivation (from CE-08): confident/uncertain/curious/concern are near-collinear in J-space
(seed-phrase cosine 0.97-0.99), so uncertain/curious/concern under-fire and confident
over-fires (65% FP on Qwen). CE-07 showed the discriminant direction mu_pos - mu_neg
rescues a collapsed axis (mischief 0% -> 76-100%). This applies the same idea uniformly.

Rigor upgrade over CE-07: CE-07 built the seed on all positives and scored the SAME
positives (in-sample, optimistic). CE-09 uses 5-fold CV — seeds are built on train folds
and scored on held-out items — so recall/FP are honest out-of-sample numbers.

Uses ONLY data already captured: J @ h_tap for all 890 items (350 positives + 350 matched
negatives + ... ) per model. No model inference, no new elicitation. Non-destructive:
writes new seeds to seed_vectors_<model>_ce09.npz; production npz is untouched.

Classifier = argmax cosine over the 7 non-idle class seeds (arm1 / J-space-only style,
directly comparable to CE-08 arm1). FP = a class-c matched-negative predicted as c.
"""
from __future__ import annotations
import json, math, pathlib, gc
import numpy as np

REPO = pathlib.Path(__file__).parent.parent
EVAL = pathlib.Path(__file__).parent
DLENS = REPO / "disposition-lens"

CLASSES = ["confident", "uncertain", "curious", "concern", "reluctant", "warm", "mischief"]
EPISTEMIC = ["confident", "uncertain", "curious", "concern"]
WS = [1.0, 0.5, 0.0]          # centroid-only / blend / pure-discriminant
KFOLD = 5
MODELS = ["apertus", "ministral", "qwen"]

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0., c-m), min(1., c+m))

def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
def unit(v):
    n = np.linalg.norm(v)
    return v/n if n > 1e-8 else v
def unit_rows(M):
    n = np.linalg.norm(M, axis=1, keepdims=True); n[n < 1e-8] = 1.0
    return M/n

def cfg(m):
    return dict(J=DLENS/f"jlens_cache_{m}_3q4.npy",
               sv=DLENS/f"seed_vectors_{m}_3q4.npz",
               htap=EVAL/f"h_tap_canis_eval001_{m}.jsonl")

def load_model(m):
    c = cfg(m)
    matrix = {r["item_id"]: r for r in jl(EVAL/"canis_eval001_matrix.jsonl")}
    mneg   = {r["item_id"]: r for r in jl(EVAL/"canis_eval001_matched_negatives.jsonl")}
    htap   = {r["item_id"]: np.asarray(r["h_tap"], np.float32) for r in jl(c["htap"])}
    pos_ids = {cl: [i for i, r in matrix.items()
                    if r["target_class"] == cl and r["split"] == "positive" and i in htap] for cl in CLASSES}
    neg_ids = {cl: [i for i, r in mneg.items()
                    if r.get("target_class") == cl and i in htap] for cl in CLASSES}
    all_ids = [i for cl in CLASSES for i in pos_ids[cl]] + [i for cl in CLASSES for i in neg_ids[cl]]
    H = np.stack([htap[i] for i in all_ids])                 # (N, hidden)
    J = np.load(str(c["J"]))                                 # (vocab, hidden)
    Z = unit_rows((H @ J.T).astype(np.float32))              # (N, vocab) unit rows
    del J, H, htap; gc.collect()
    idx = {i: k for k, i in enumerate(all_ids)}
    sv = np.load(str(c["sv"]))
    naive = unit_rows(np.stack([sv[cl] for cl in CLASSES]).astype(np.float32))  # (7, vocab)
    return Z, idx, pos_ids, neg_ids, naive

def classify(Zrows, seedmat):
    """Return predicted class name per row (argmax cosine over the 7 seeds)."""
    return [CLASSES[j] for j in np.argmax(Zrows @ seedmat.T, axis=1)]

def eval_seeds(Z, idx, pos_ids, neg_ids, seedmat):
    """Per-class recall (on positives) + FP (on matched-negs)."""
    out = {}
    for cl in CLASSES:
        pr = classify(Z[[idx[i] for i in pos_ids[cl]]], seedmat)
        nr = classify(Z[[idx[i] for i in neg_ids[cl]]], seedmat)
        tp = sum(p == cl for p in pr); fp = sum(p == cl for p in nr)
        out[cl] = dict(recall=tp/len(pr), tp=tp, npos=len(pr),
                       fp_rate=fp/len(nr), fp=fp, nneg=len(nr),
                       rci=wilson(tp, len(pr)), fci=wilson(fp, len(nr)))
    return out

def build_seed(Z, idx, p_train, n_train, w):
    mu_pos = unit(Z[[idx[i] for i in p_train]].mean(0))
    mu_neg = unit(Z[[idx[i] for i in n_train]].mean(0))
    disc = unit(mu_pos - mu_neg)
    return unit(w*mu_pos + (1.0-w)*disc)

def cv_eval(Z, idx, pos_ids, neg_ids, w):
    """5-fold CV: seeds built on train folds, held-out items scored. Honest out-of-sample."""
    pos_pred = {cl: [] for cl in CLASSES}
    neg_pred = {cl: [] for cl in CLASSES}
    for fold in range(KFOLD):
        seeds = []
        test = {"pos": [], "neg": []}
        for cl in CLASSES:
            p, n = pos_ids[cl], neg_ids[cl]
            p_te = p[fold::KFOLD]; p_tr = [x for x in p if x not in set(p_te)]
            n_te = n[fold::KFOLD]; n_tr = [x for x in n if x not in set(n_te)]
            seeds.append(build_seed(Z, idx, p_tr, n_tr, w))
            test["pos"] += [(i, cl) for i in p_te]
            test["neg"] += [(i, cl) for i in n_te]
        S = np.stack(seeds)
        for grp in ("pos", "neg"):
            ids = [i for i, _ in test[grp]]
            preds = classify(Z[[idx[i] for i in ids]], S)
            for (i, cl), pred in zip(test[grp], preds):
                (pos_pred if grp == "pos" else neg_pred)[cl].append(pred)
    out = {}
    for cl in CLASSES:
        pr, nr = pos_pred[cl], neg_pred[cl]
        tp = sum(p == cl for p in pr); fp = sum(p == cl for p in nr)
        out[cl] = dict(recall=tp/len(pr), tp=tp, npos=len(pr),
                       fp_rate=fp/len(nr), fp=fp, nneg=len(nr),
                       rci=wilson(tp, len(pr)), fci=wilson(fp, len(nr)))
    return out

def full_seeds(Z, idx, pos_ids, neg_ids, w):
    return np.stack([build_seed(Z, idx, pos_ids[cl], neg_ids[cl], w) for cl in CLASSES])

def collisions(seedmat, classes=EPISTEMIC):
    idxs = [CLASSES.index(c) for c in classes]
    out = []
    for a in range(len(idxs)):
        for b in range(a+1, len(idxs)):
            out.append((classes[a], classes[b], float(seedmat[idxs[a]] @ seedmat[idxs[b]])))
    return out

def macro(metrics, subset=CLASSES):
    return (np.mean([metrics[c]["recall"] for c in subset]),
            np.mean([metrics[c]["fp_rate"] for c in subset]))

def main():
    all_out = {}
    for m in MODELS:
        print(f"\n{'='*66}\nMODEL: {m}\n{'='*66}")
        Z, idx, pos_ids, neg_ids, naive = load_model(m)
        print(f"  Z: {Z.shape}  positives={sum(len(v) for v in pos_ids.values())}  matched-negs={sum(len(v) for v in neg_ids.values())}")

        base = eval_seeds(Z, idx, pos_ids, neg_ids, naive)
        print("  [naive seeds] per-class recall / FP:")
        for cl in CLASSES:
            b = base[cl]; print(f"    {cl:10} recall {b['recall']:5.1%}  fp {b['fp_rate']:5.1%}")
        mr, mf = macro(base); print(f"    MACRO recall {mr:.1%}  fp {mf:.1%}")

        cvres = {}
        for w in WS:
            cvres[w] = cv_eval(Z, idx, pos_ids, neg_ids, w)
            mr, mf = macro(cvres[w])
            tag = {1.0: "centroid", 0.5: "blend", 0.0: "discriminant"}[w]
            print(f"  [CV w={w:.1f} {tag}] MACRO recall {mr:.1%}  fp {mf:.1%}")

        # pick best w by macro recall with macro FP <= naive macro FP + 5pp (guard against FP blow-up)
        naive_mf = macro(base)[1]
        best_w = max(WS, key=lambda w: macro(cvres[w])[0] if macro(cvres[w])[1] <= naive_mf + 0.05 else -1)
        print(f"  -> selected w={best_w} (best CV macro recall with FP guard)")

        full = full_seeds(Z, idx, pos_ids, neg_ids, best_w)
        col_naive = collisions(naive); col_new = collisions(full)
        out_npz = DLENS/f"seed_vectors_{m}_ce09.npz"
        np.savez(str(out_npz), **{cl: full[k] for k, cl in enumerate(CLASSES)})
        print(f"  saved discriminant seeds -> {out_npz.name}")

        all_out[m] = dict(naive=base, cv=cvres, best_w=best_w,
                          col_naive=col_naive, col_new=col_new)
        del Z; gc.collect()

    (EVAL/"ce09_results.json").write_text(json.dumps(
        {m: {"best_w": all_out[m]["best_w"],
             "naive": {c: {k: all_out[m]["naive"][c][k] for k in ("recall","fp_rate","tp","fp","npos","nneg")} for c in CLASSES},
             "cv": {str(w): {c: {k: all_out[m]["cv"][w][c][k] for k in ("recall","fp_rate","tp","fp")} for c in CLASSES} for w in WS},
             "col_naive": all_out[m]["col_naive"], "col_new": all_out[m]["col_new"]}
         for m in MODELS}, indent=2))
    print("\nwrote ce09_results.json")
    return all_out

if __name__ == "__main__":
    main()
