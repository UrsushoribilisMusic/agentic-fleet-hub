#!/usr/bin/env python3
"""
Multi-rater human IRR for CANIS-EVAL-001 (§6.3).

Raters:
  - Miguel  : human_sheet.csv  (item_id, prompt, your_label)
  - <web>   : canis_ratings.jsonl  (rater, answers{item_id: label})  -- Bunny/Mimi, Ales, ...
Original labels: human_key.json  {item_id: label}

Computes, on the shared items:
  - per rater: Cohen's kappa vs the original labels + agreement rate
  - Fleiss' kappa across all raters (the headline IRR number)
  - pairwise Cohen's kappa between raters
  - per-class agreement of each rater with the original label
"""
import csv, json, os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

def load_key():
    return json.load(open(os.path.join(HERE, "human_key.json")))

def load_miguel():
    out = {}
    with open(os.path.join(HERE, "human_sheet.csv")) as f:
        for row in csv.DictReader(f):
            lbl = (row.get("your_label") or "").strip().lower()
            if lbl:
                out[row["item_id"]] = lbl
    return out

def load_web():
    raters = {}
    p = os.path.join(HERE, "canis_ratings.jsonl")
    if not os.path.exists(p):
        return raters
    for line in open(p):
        if not line.strip():
            continue
        r = json.loads(line)
        name = (r.get("rater") or "?").strip()
        ans = {k: str(v).strip().lower() for k, v in (r.get("answers") or {}).items() if v}
        # keep the latest submission per rater
        raters[name] = ans
    return raters

def cohen_kappa(a, b, items):
    items = [i for i in items if i in a and i in b]
    if not items:
        return None, 0
    cats = set(a[i] for i in items) | set(b[i] for i in items)
    n = len(items)
    po = sum(1 for i in items if a[i] == b[i]) / n
    pa = Counter(a[i] for i in items); pb = Counter(b[i] for i in items)
    pe = sum((pa[c]/n) * (pb[c]/n) for c in cats)
    k = (po - pe) / (1 - pe) if pe != 1 else 1.0
    return k, n

def fleiss_kappa(raters, items):
    # items rated by ALL raters
    shared = [i for i in items if all(i in r for r in raters)]
    if not shared or len(raters) < 2:
        return None, len(shared)
    cats = sorted({r[i] for r in raters for i in shared})
    nR = len(raters); N = len(shared)
    P_items = []
    col = Counter()
    for i in shared:
        counts = Counter(r[i] for r in raters)
        col.update(counts)
        s = sum(v*v for v in counts.values())
        P_items.append((s - nR) / (nR * (nR - 1)))
    Pbar = sum(P_items) / N
    p_j = {c: col[c] / (N * nR) for c in cats}
    Pe = sum(v*v for v in p_j.values())
    k = (Pbar - Pe) / (1 - Pe) if Pe != 1 else 1.0
    return k, N

def main():
    key = load_key()
    items = list(key.keys())
    raters = {}
    raters["Miguel"] = load_miguel()
    for name, ans in load_web().items():
        raters[name] = ans

    print("=" * 68)
    print(f"CANIS multi-rater IRR — {len(raters)} rater(s), {len(items)} key items")
    print("=" * 68)

    print("\nPer-rater vs ORIGINAL labels (Cohen's kappa):")
    for name, r in raters.items():
        k, n = cohen_kappa(key, r, items)
        rated = sum(1 for i in items if i in r)
        agree = sum(1 for i in items if i in r and r[i] == key[i])
        print(f"  {name:10} rated {rated}/{len(items)}  agree {agree}  kappa={k:+.2f}" if k is not None else f"  {name}: no overlap")

    names = list(raters.keys())
    if len(names) >= 2:
        print("\nPairwise between raters (Cohen's kappa):")
        for x in range(len(names)):
            for y in range(x+1, len(names)):
                k, n = cohen_kappa(raters[names[x]], raters[names[y]], items)
                print(f"  {names[x]:10} vs {names[y]:10} n={n:2d}  kappa={k:+.2f}" if k is not None else f"  {names[x]} vs {names[y]}: no overlap")

        fk, ns = fleiss_kappa(list(raters.values()), items)
        print(f"\nFLEISS' kappa across all {len(names)} raters (items all rated: {ns}): "
              f"{fk:+.2f}" if fk is not None else "\nFleiss: not enough shared items")

    # per-class agreement of each rater with the original
    print("\nPer-class agreement with original (rater labels its own-class items correctly):")
    classes = sorted(set(key.values()))
    hdr = "  class".ljust(14) + "".join(f"{n[:8]:>9}" for n in names)
    print(hdr)
    for c in classes:
        cls_items = [i for i in items if key[i] == c]
        row = "  " + c.ljust(12)
        for n in names:
            r = raters[n]
            agree = sum(1 for i in cls_items if r.get(i) == c)
            row += f"{agree:>4}/{len(cls_items):<4}"
        print(row)

if __name__ == "__main__":
    main()
