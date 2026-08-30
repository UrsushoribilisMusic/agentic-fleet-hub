#!/usr/bin/env python3
"""Re-save CE-09 discriminant seeds at the deployment operating point w=0 (lowest FP),
for all three models. Full-data build (all 350 pos + 350 matched-neg per model).
Overwrites seed_vectors_<model>_ce09.npz. Non-destructive to production npz."""
import numpy as np, pathlib
from ce09_discriminant_seeds import load_model, full_seeds, CLASSES, MODELS, DLENS

for m in MODELS:
    print(f"[{m}] building w=0 discriminant seeds...")
    Z, idx, pos_ids, neg_ids, _ = load_model(m)
    S = full_seeds(Z, idx, pos_ids, neg_ids, 0.0)   # (7, vocab), w=0 pure discriminant
    out = DLENS / f"seed_vectors_{m}_ce09.npz"
    np.savez(str(out), **{cl: S[k] for k, cl in enumerate(CLASSES)})
    del Z
    print(f"[{m}] saved {out.name}  (w=0, {len(CLASSES)} classes)")
print("done — CE-09 w=0 seeds saved for all models")
