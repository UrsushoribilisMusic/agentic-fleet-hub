#!/usr/bin/env python3
"""
Big Sis review item — cross-axis B baseline.

compute_ood_cosine_B.py gives only the DIAGONAL: cos(frozen_i, refit_i). That number
is only meaningful if a frozen axis matches its OWN refit better than any OTHER axis's
refit. This computes the full 7x7 frozen-vs-refit matrix per model, plus the
in-distribution off-diagonal (frozen_i vs frozen_j), so we can answer:

  - Is the diagonal separated from the off-diagonal? (does B carry any argument?)
  - Per axis: margin = diag_i - max_{j!=i} cos(frozen_i, refit_j).  >0 = the axis is
    closer to its own refit than to any other; <=0 = not separable.
  - In-distribution: are the seven discriminants even distinct from each other?

Writes cross_axis_B.json (full matrices + per-axis margins + summary).
"""
import json, numpy as np
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
    J = np.load(str(DLENS/f"jlens_cache_{m}_3q4.npy"))
    Z = unit_rows((np.stack([htap[i] for i in ids]) @ J.T).astype(np.float32)); del J
    idx = {i:k for k,i in enumerate(ids)}
    frozen_npz = np.load(str(DLENS/f"seed_vectors_{m}_ce09.npz"))
    frozen = {cl: unit(frozen_npz[cl]) for cl in CLASSES}

    # OOD-refit discriminant per class (diagnostic only, never used to score).
    refit = {}
    for cl in CLASSES:
        pos = [idx[i] for i,r in matrix.items() if r["target_class"]==cl and r["split"]=="positive" and i in idx]
        neg = [idx[i] for i,r in matrix.items() if r["target_class"]==cl and r["split"]=="negative" and i in idx]
        refit[cl] = unit(unit(Z[pos].mean(0)) - unit(Z[neg].mean(0)))
    del Z

    # 7x7 frozen x refit, and in-distribution 7x7 frozen x frozen.
    cross = {fi: {rj: float(frozen[fi] @ refit[rj]) for rj in CLASSES} for fi in CLASSES}
    indist = {fi: {fj: float(frozen[fi] @ frozen[fj]) for fj in CLASSES} for fi in CLASSES}

    margins = {}
    for fi in CLASSES:
        diag = cross[fi][fi]
        off = max(cross[fi][rj] for rj in CLASSES if rj != fi)
        off_arg = max((rj for rj in CLASSES if rj != fi), key=lambda rj: cross[fi][rj])
        margins[fi] = {"diag": diag, "max_off": off, "max_off_axis": off_arg, "margin": diag - off}

    report[m] = {"cross": cross, "indist": indist, "margins": margins}

# ---- report ----
def fmt_row(d, cls): return "".join(f"{d[cls][c]:7.2f}" for c in CLASSES)
for m in report:
    print("="*90)
    print(f"{m}  —  7x7 frozen(row) x OOD-refit(col) cosine   [diagonal = B]")
    print(f"{'':10}" + "".join(f"{c[:6]:>7}" for c in CLASSES))
    for fi in CLASSES:
        print(f"{fi:10}" + fmt_row(report[m]['cross'], fi))
    print(f"\n  per-axis margin (diag - best competing off-diagonal):")
    for fi in CLASSES:
        mg = report[m]['margins'][fi]
        flag = "" if mg['margin'] > 0.05 else "   <-- NOT separable" if mg['margin'] <= 0 else "   <-- thin"
        print(f"    {fi:10} diag={mg['diag']:.2f}  max_off={mg['max_off']:.2f} ({mg['max_off_axis']})  margin={mg['margin']:+.2f}{flag}")

# ---- summary across models ----
print("\n" + "="*90)
print("SUMMARY — does B carry an argument? (need diag >> off-diagonal)")
for m in report:
    diags = [report[m]['cross'][c][c] for c in CLASSES]
    offs  = [report[m]['cross'][fi][rj] for fi in CLASSES for rj in CLASSES if fi != rj]
    ind_off = [report[m]['indist'][fi][fj] for fi in CLASSES for fj in CLASSES if fi != fj]
    print(f"  {m:9}  diag mean={np.mean(diags):.2f}  cross off-diag mean={np.mean(offs):.2f} (max {np.max(offs):.2f})  "
          f"| in-dist off-diag mean={np.mean(ind_off):.2f} (max {np.max(ind_off):.2f})")

json.dump(report, open(EVAL/"cross_axis_B.json","w"), indent=2)
print("\nwrote cross_axis_B.json")
