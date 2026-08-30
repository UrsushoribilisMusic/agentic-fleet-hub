#!/usr/bin/env python3
"""
Task 1 aggregation — combine the 7 blind Opus-4.8 grading batches, map A/B/C/D back to
arms via the sealed answer_map.json, and run the same paired contrasts as the Qwen set,
plus Qwen-vs-Opus Spearman + side-by-side arm means + the arm2-arm3 DIRECTION CHECK.

Grader: Claude Opus 4.8, blind (each subagent saw only question + gold + 4 unlabelled
answers), single version across all 4 arms. Reproducible API variant: grade_eval008_opus4.py.
"""
import csv, json, glob, pathlib, random
from scipy.stats import spearmanr, wilcoxon, ttest_rel

HERE = pathlib.Path(__file__).parent
G = HERE / "grading_opus48"
DIMS = ["grounded", "correct", "faithful_recall"]
SEED, NBOOT = 42, 10_000

def load(name): return [json.loads(l) for l in (HERE/name).read_text().splitlines() if l.strip()]
def comp(d):
    v=[d.get(k) for k in DIMS if d.get(k) is not None]; return sum(v)/len(v) if v else None

# ---- assemble Opus-4.8 per-question 4-arm scores ----
amap = json.loads((G/"answer_map.json").read_text())
graded = {}
nfiles = 0
for f in sorted(glob.glob(str(G/"graded_*.json"))):
    nfiles += 1
    for item in json.loads(pathlib.Path(f).read_text()):
        graded[int(item["qid"])] = item

q_opus = {}
for qid, item in graded.items():
    m = amap[str(qid)]                       # {A:arm,B:arm,C:arm,D:arm}
    q_opus[qid] = {m[lab]: comp(item[lab]) for lab in ("A","B","C","D")}

print(f"loaded {nfiles} graded batch files, {len(q_opus)} questions")
missing = [q for q in q_opus if any(q_opus[q].get(f'arm{i}') is None for i in range(4))]
if missing: print(f"  ! questions with a missing arm score: {missing}")

# ---- Qwen per-question (from the existing CSV) ----
qwen = {}
with (HERE/"eval008_per_question.csv").open() as fh:
    for r in csv.DictReader(fh):
        qid = int(r["question_id"])
        qwen[qid] = {f"arm{i}": (float(r[f"qwen_arm{i}"]) if r[f"qwen_arm{i}"] not in ("","None") else None) for i in range(4)}

qids = sorted(q_opus)
ARMS = ["arm0","arm1","arm2","arm3"]

# ---- stats helpers ----
def deltas(scores, a, b):
    return [scores[q][a]-scores[q][b] for q in qids
            if scores[q].get(a) is not None and scores[q].get(b) is not None]
def boot(d):
    rng=random.Random(SEED); m=len(d); xs=[sum(d[rng.randrange(m)] for _ in range(m))/m for _ in range(NBOOT)]
    xs.sort(); return xs[int(.025*NBOOT)], xs[int(.975*NBOOT)]
def signflip(d):
    rng=random.Random(SEED); obs=abs(sum(d)/len(d)); hit=0
    for _ in range(NBOOT):
        if abs(sum(x if rng.random()<.5 else -x for x in d)/len(d))>=obs-1e-12: hit+=1
    return hit/NBOOT
def wlt(scores,a,b):
    w=l=t=0
    for q in qids:
        x,y=scores[q].get(a),scores[q].get(b)
        if x is None or y is None: continue
        if x>y+1e-9:w+=1
        elif y>x+1e-9:l+=1
        else:t+=1
    return w,l,t

CONTRASTS = [("arm2","arm3","LoRA vs Base under equal RAG"),
             ("arm3","arm0","RAG lift on Base"),
             ("arm2","arm0","Full stack vs Base")]

print("\n"+"="*76)
print("OPUS 4.8 (blind, single version, all 4 arms) — PAIRED CONTRASTS  [n={}]".format(len(qids)))
print("="*76)
opus_dir = {}
for a,b,label in CONTRASTS:
    d=deltas(q_opus,a,b); mean=sum(d)/len(d); lo,hi=boot(d); p=signflip(d)
    wst,wp=wilcoxon(d); w,l,t=wlt(q_opus,a,b); opus_dir[(a,b)]=mean
    print(f"\n{label} ({a}-{b})")
    print(f"  n={len(d)}  Δ={mean:+.3f}  95% CI [{lo:+.3f},{hi:+.3f}]  perm p={p:.4f}  Wilcoxon p={wp:.4f}")
    print(f"  wins {w} / losses {l} / ties {t}")

# ---- side-by-side arm means ----
print("\n"+"="*76); print("ARM MEANS — side by side"); print("="*76)
print(f"{'arm':6} {'Qwen':>8} {'Opus4.8':>9}")
for a in ARMS:
    qv=[qwen[q][a] for q in qids if qwen[q].get(a) is not None]
    ov=[q_opus[q][a] for q in qids if q_opus[q].get(a) is not None]
    print(f"{a:6} {sum(qv)/len(qv):8.3f} {sum(ov)/len(ov):9.3f}")
print("  (prior unpinned manual Opus arm0-2 aggregate was 1.00/0.95/2.40; arm3 was 2.54)")

# ---- Qwen vs Opus Spearman (per-question, pooled + per arm) ----
print("\n"+"="*76); print("GRADER AGREEMENT — Spearman(Qwen, Opus4.8) per-question"); print("="*76)
pooled_q,pooled_o=[],[]
for a in ARMS:
    xs=[qwen[q][a] for q in qids if qwen[q].get(a) is not None and q_opus[q].get(a) is not None]
    ys=[q_opus[q][a] for q in qids if qwen[q].get(a) is not None and q_opus[q].get(a) is not None]
    rho,p=spearmanr(xs,ys); pooled_q+=xs; pooled_o+=ys
    print(f"  {a}: rho={rho:+.3f}  p={p:.3f}  n={len(xs)}")
rho,p=spearmanr(pooled_q,pooled_o)
print(f"  POOLED: rho={rho:+.3f}  p={p:.3f}  n={len(pooled_q)}")

# ---- DIRECTION CHECK on arm2-arm3 ----
print("\n"+"="*76); print("DIRECTION CHECK — arm2-arm3 (the LoRA-benefit sign)"); print("="*76)
qd=deltas(qwen,"arm2","arm3"); qmean=sum(qd)/len(qd); omean=opus_dir[("arm2","arm3")]
print(f"  Qwen  Δ(arm2-arm3) = {qmean:+.3f}")
print(f"  Opus  Δ(arm2-arm3) = {omean:+.3f}")
agree = (qmean<0 and omean<0) or (qmean>0 and omean>0)
print(f"  --> graders AGREE in direction: {agree}  ({'both say LoRA does not help' if agree else 'DISAGREE — STOP AND REPORT'})")

# ---- write artifacts ----
with (HERE/"results_eval008_opus48_4arm.jsonl").open("w") as fh:
    for qid in qids:
        fh.write(json.dumps({"question_id":qid,"grader":"claude-opus-4-8","blind":True,
                             **{f"{a}_opus48":graded[qid][[k for k,v in amap[str(qid)].items() if v==a][0]] for a in ARMS}})+"\n")

# augment the per-question CSV with opus48 columns
rows=[]
with (HERE/"eval008_per_question.csv").open() as fh:
    rows=list(csv.DictReader(fh))
for r in rows:
    qid=int(r["question_id"])
    for a in ARMS:
        r[f"opus48_{a}"]=round(q_opus.get(qid,{}).get(a),3) if q_opus.get(qid,{}).get(a) is not None else ""
fields=list(rows[0].keys())
with (HERE/"eval008_per_question.csv").open("w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)
print("\nwrote results_eval008_opus48_4arm.jsonl + added opus48_* columns to eval008_per_question.csv")
