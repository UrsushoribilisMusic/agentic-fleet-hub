#!/usr/bin/env python3
"""Bootstrap 95% CIs on the human (3-rater) and model (4-rater) Fleiss kappa,
their difference, and the human Fleiss with the author (R2) excluded.
Resamples the 50 items with replacement; fixed seed for reproducibility."""
import json, glob, os, random
from collections import Counter
random.seed(20260902)
HERE = os.path.dirname(os.path.abspath(__file__))
B = 5000

def fleiss(raters, items):
    """raters: list of {item: label}; items: list of item ids (repeats allowed)."""
    nR = len(raters)
    if nR < 2 or not items:
        return None
    cats = sorted({r[i] for r in raters for i in set(items) if i in r})
    N = len(items); col = Counter(); Ps = []
    for i in items:
        c = Counter(r[i] for r in raters if i in r)
        if sum(c.values()) != nR:
            return None
        col.update(c)
        Ps.append((sum(v*v for v in c.values()) - nR) / (nR*(nR-1)))
    Pbar = sum(Ps)/N
    pj = {c: col[c]/(N*nR) for c in cats}
    Pe = sum(v*v for v in pj.values())
    return (Pbar-Pe)/(1-Pe) if Pe != 1 else 1.0

key = json.load(open(f"{HERE}/human_key.json"))
items = list(key.keys())

humans = {}
for line in open(f"{HERE}/canis_ratings.jsonl"):
    if line.strip():
        r = json.loads(line)
        humans[r["rater"]] = {k: str(v).lower() for k, v in (r.get("answers") or {}).items()}
models = {os.path.basename(p)[:-5]: {k: str(v).lower() for k, v in json.load(open(p)).items()}
          for p in sorted(glob.glob(f"{HERE}/model_ratings/*.json"))}

H = list(humans.values())
M = list(models.values())
H_noR2 = [humans[k] for k in humans if k != "R2"]   # exclude the author (R2)

def ci(vals):
    v = sorted(x for x in vals if x is not None)
    lo = v[int(0.025*len(v))]; hi = v[int(0.975*len(v))-1]
    return lo, hi

pt_h = fleiss(H, items); pt_m = fleiss(M, items); pt_hno = fleiss(H_noR2, items)
bh, bm, bd, bhno = [], [], [], []
for _ in range(B):
    s = [random.choice(items) for _ in range(len(items))]
    h = fleiss(H, s); m = fleiss(M, s)
    if h is not None: bh.append(h)
    if m is not None: bm.append(m)
    if h is not None and m is not None: bd.append(m-h)
    hn = fleiss(H_noR2, s)
    if hn is not None: bhno.append(hn)

hlo, hhi = ci(bh); mlo, mhi = ci(bm); dlo, dhi = ci(bd); hnlo, hnhi = ci(bhno)
print(f"HUMAN Fleiss κ (3 raters) = {pt_h:.2f}  95% CI [{hlo:.2f}, {hhi:.2f}]")
print(f"MODEL Fleiss κ (4 raters) = {pt_m:.2f}  95% CI [{mlo:.2f}, {mhi:.2f}]")
print(f"DIFFERENCE (model - human) = {pt_m-pt_h:.2f}  95% CI [{dlo:.2f}, {dhi:.2f}]  (excludes 0: {dlo>0})")
print(f"HUMAN Fleiss WITHOUT author R2 (2 raters R1+R3) = {pt_hno:.2f}  95% CI [{hnlo:.2f}, {hnhi:.2f}]")
print(f"\nPer-rater vs key (Cohen): " + ", ".join(
    f"{k}={sum(1 for i in items if humans[k].get(i)==key[i])}/50" for k in sorted(humans)))
print(f"(bootstrap B={B}, seed 20260902, resampling the 50 items)")
