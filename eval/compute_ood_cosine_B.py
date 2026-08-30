#!/usr/bin/env python3
"""
Task 4 — operand B: frozen (in-distribution) discriminant vs OOD-refit discriminant, per
class per model. This is the direction-drift test that separates "same axis, weaker OOD"
(high cosine) from "different axis / distribution-specific artifact" (low cosine).

The frozen CE-09 w=0 seed IS the in-distribution discriminant (unit(mu_pos_core - mu_neg_core)).
The OOD-refit discriminant is unit(mu_pos_ood - mu_neg_ood), built from the OOD h_tap — DIAGNOSTIC
ONLY, never used to score (scoring stayed 100% frozen).
"""
import json, pathlib, numpy as np
from ce09_discriminant_seeds import unit, unit_rows, CLASSES, MODELS, DLENS, EVAL

def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
matrix = {r["item_id"]: r for r in jl(EVAL/"canis_eval001_ood_matrix.jsonl")}

report = {}
for m in MODELS:
    htap_path = EVAL/"ood_run"/f"h_tap_canis_eval001_{m}.jsonl"
    if not htap_path.exists():
        print(f"[{m}] skip — no OOD h_tap"); continue
    htap = {r["item_id"]: np.asarray(r["h_tap"], np.float32) for r in jl(htap_path)}
    ids = [i for i in matrix if i in htap]
    H = np.stack([htap[i] for i in ids])
    J = np.load(str(DLENS/f"jlens_cache_{m}_3q4.npy"))
    Z = unit_rows((H @ J.T).astype(np.float32)); del J
    idx = {i:k for k,i in enumerate(ids)}
    frozen = np.load(str(DLENS/f"seed_vectors_{m}_ce09.npz"))   # in-dist discriminant (w=0)

    cos = {}
    for cl in CLASSES:
        pos = [idx[i] for i,r in matrix.items() if r["target_class"]==cl and r["split"]=="positive" and i in idx]
        neg = [idx[i] for i,r in matrix.items() if r["target_class"]==cl and r["split"]=="negative" and i in idx]
        mu_pos = unit(Z[pos].mean(0)); mu_neg = unit(Z[neg].mean(0))
        disc_ood = unit(mu_pos - mu_neg)
        cos[cl] = float(unit(frozen[cl]) @ disc_ood)
    report[m] = cos
    del Z

print("="*70)
print("Operand B — cosine(frozen in-dist discriminant, OOD-refit discriminant)")
print("high = same axis (direction stable) | low = distribution-specific")
print("="*70)
print(f"\n{'class':10}" + "".join(f"{m[:9]:>11}" for m in report))
for cl in CLASSES:
    print(f"{cl:10}" + "".join(f"{report[m][cl]:11.3f}" for m in report))
print(f"\n{'MEAN':10}" + "".join(f"{np.mean([report[m][cl] for cl in CLASSES]):11.3f}" for m in report))
json.dump(report, open(EVAL/"ood_cosine_B.json","w"), indent=2)
print("\nwrote ood_cosine_B.json")
