#!/usr/bin/env python3
"""Two-panel IRR: large-model judges vs humans, same 50 items (§6.3)."""
import json, glob, os
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))

def cohen(a, b, items):
    items = [i for i in items if i in a and i in b]
    if not items: return None
    cats = set(a[i] for i in items) | set(b[i] for i in items); n=len(items)
    po = sum(1 for i in items if a[i]==b[i])/n
    pa=Counter(a[i] for i in items); pb=Counter(b[i] for i in items)
    pe = sum((pa[c]/n)*(pb[c]/n) for c in cats)
    return (po-pe)/(1-pe) if pe!=1 else 1.0

def fleiss(raters, items):
    shared=[i for i in items if all(i in r for r in raters)]
    if len(raters)<2 or not shared: return None
    cats=sorted({r[i] for r in raters for i in shared}); nR=len(raters); N=len(shared)
    Ps=[]; col=Counter()
    for i in shared:
        c=Counter(r[i] for r in raters); col.update(c)
        Ps.append((sum(v*v for v in c.values())-nR)/(nR*(nR-1)))
    Pbar=sum(Ps)/N; pj={c:col[c]/(N*nR) for c in cats}; Pe=sum(v*v for v in pj.values())
    return (Pbar-Pe)/(1-Pe) if Pe!=1 else 1.0

def majority(raters, items):
    out={}
    for i in items:
        votes=[r[i] for r in raters if i in r]
        if votes: out[i]=Counter(votes).most_common(1)[0][0]
    return out

key = json.load(open(f"{HERE}/human_key.json"))
items = list(key.keys())

# model panel
models={}
for p in sorted(glob.glob(f"{HERE}/model_ratings/*.json")):
    models[os.path.basename(p)[:-5]] = {k:str(v).lower() for k,v in json.load(open(p)).items()}
# human panel
humans={}
for line in open(f"{HERE}/canis_ratings.jsonl"):
    if line.strip():
        r=json.loads(line); humans[r["rater"]]={k:str(v).lower() for k,v in (r.get("answers") or {}).items()}

def panel(name, P):
    print(f"\n{name} panel — {len(P)} raters: {', '.join(P)}")
    for n,r in P.items():
        print(f"  {n:8} vs key κ={cohen(key,r,items):+.2f}  (agree {sum(1 for i in items if r.get(i)==key[i])}/50)")
    print(f"  >>> {name} Fleiss κ = {fleiss(list(P.values()),items):+.2f}")

panel("MODEL", models); panel("HUMAN", humans)

mc=majority(list(models.values()),items); hc=majority(list(humans.values()),items)
print(f"\nMODEL-consensus vs HUMAN-consensus (majority vote each): Cohen κ = {cohen(mc,hc,items):+.2f}")
print(f"MODEL-consensus vs key κ={cohen(mc,key,items):+.2f} | HUMAN-consensus vs key κ={cohen(hc,key,items):+.2f}")

print("\nPer-class: fraction of a class's own items each panel's MAJORITY labeled correctly")
print(f"  {'axis':10}{'MODEL':>8}{'HUMAN':>8}")
for c in sorted(set(key.values())):
    ci=[i for i in items if key[i]==c]
    m=sum(1 for i in ci if mc.get(i)==c); h=sum(1 for i in ci if hc.get(i)==c)
    print(f"  {c:10}{m:>4}/{len(ci):<3}{h:>4}/{len(ci):<3}")
