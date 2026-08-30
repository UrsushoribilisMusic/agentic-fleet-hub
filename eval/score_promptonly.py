#!/usr/bin/env python3
"""
CANIS Task 1 — prompt-only control.

Fit a classifier on PROMPT TEXT ONLY (TF-IDF + logistic regression; no activations, no model
internals). Train on the core matrix positives, test on the 420-item OOD set. Score with the
SAME recall/FP protocol as J-space (7-way argmax; recall on OOD positives, FP on OOD matched-
negatives predicted as their target class). Put it beside the frozen J-space OOD numbers and
report the per-class gap.

If J-space clears prompt-only by a wide margin → the probe reads the MODEL, not the prompt.
If they track each other → the OOD "signal" is prompt style. Expectation: mischief has the
smallest gap (would independently confirm it was a style artifact).
"""
import json, pathlib, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

EVAL = pathlib.Path(__file__).parent
CLASSES = ["confident","uncertain","curious","concern","reluctant","warm","mischief"]
def jl(p): return [json.loads(l) for l in open(p) if l.strip()]

# --- train: core-matrix positives (prompt -> class), 7-way ---
core = jl(EVAL/"canis_eval001_matrix.jsonl")
Xtr = [r["prompt"] for r in core if r["split"]=="positive" and r["target_class"] in CLASSES]
ytr = [r["target_class"] for r in core if r["split"]=="positive" and r["target_class"] in CLASSES]
print(f"train (core positives): {len(Xtr)}")

clf = make_pipeline(
    TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, min_df=2, stop_words="english"),
    LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced"),
)
clf.fit(Xtr, ytr)

# --- test: OOD matrix ---
ood = jl(EVAL/"canis_eval001_ood_matrix.jsonl")
pred = {r["item_id"]: p for r, p in zip(ood, clf.predict([r["prompt"] for r in ood]))}

def score(rows):
    out={}
    for cl in CLASSES:
        pos=[r for r in rows if r["target_class"]==cl and r["split"]=="positive"]
        neg=[r for r in rows if r["target_class"]==cl and r["split"]=="negative"]
        tp=sum(pred[r["item_id"]]==cl for r in pos)
        fp=sum(pred[r["item_id"]]==cl for r in neg)
        out[cl]=dict(recall=tp/len(pos) if pos else 0, npos=len(pos),
                     fp=fp/len(neg) if neg else 0, nneg=len(neg))
    return out
po = score(ood)

# --- J-space OOD (frozen CE-09) from ood_results.json ---
js = json.load(open(EVAL/"ood_results.json"))   # {model: {ce09: {cl:{recall,fp_rate}}}}
MODELS=[m for m in ("apertus","ministral","qwen") if m in js]

print("\n"+"="*88)
print("PROMPT-ONLY (text TF-IDF+LogReg) vs J-SPACE, on the SAME 420 OOD items")
print("="*88)
print(f"\nPrompt-only per class (recall / FP on OOD):")
for cl in CLASSES:
    print(f"  {cl:10} recall {po[cl]['recall']:5.0%}   FP {po[cl]['fp']:5.0%}   (n_pos={po[cl]['npos']})")
mpo=np.mean([po[cl]['recall'] for cl in CLASSES]); fpo=np.mean([po[cl]['fp'] for cl in CLASSES])
print(f"  MACRO      recall {mpo:5.0%}   FP {fpo:5.0%}")

print("\nRECALL gap = J-space − prompt-only  (positive = J-space reads more than the text):")
hdr = f"  {'class':10}" + "".join(f"{m[:4]:>7}" for m in MODELS) + f"{'prompt':>8}" + "".join(f"{'Δ'+m[:3]:>7}" for m in MODELS)
print(hdr)
gaps={m:[] for m in MODELS}
for cl in CLASSES:
    line=f"  {cl:10}"
    for m in MODELS:
        jr=js[m]["ce09"][cl]["recall"]; line+=f"{jr:7.0%}"
    line+=f"{po[cl]['recall']:8.0%}"
    for m in MODELS:
        g=js[m]["ce09"][cl]["recall"]-po[cl]['recall']; gaps[m].append(g); line+=f"{g:+7.0%}"
    print(line)
line=f"  {'MACRO':10}"
for m in MODELS: line+=f"{np.mean([js[m]['ce09'][cl]['recall'] for cl in CLASSES]):7.0%}"
line+=f"{mpo:8.0%}"
for m in MODELS: line+=f"{np.mean(gaps[m]):+7.0%}"
print(line)

print("\nsmallest per-class J-space−promptonly gap (avg across models):")
avg_gap={cl: np.mean([js[m]["ce09"][cl]["recall"]-po[cl]['recall'] for m in MODELS]) for cl in CLASSES}
for cl,g in sorted(avg_gap.items(), key=lambda x:x[1])[:3]:
    print(f"  {cl}: {g:+.0%}")

json.dump({"prompt_only": po, "avg_gap": avg_gap}, open(EVAL/"promptonly_results.json","w"), indent=2)
print("\nwrote promptonly_results.json")
