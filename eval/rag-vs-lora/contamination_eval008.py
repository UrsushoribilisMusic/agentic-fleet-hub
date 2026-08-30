#!/usr/bin/env python3
"""
EVAL-008 Task 4 — contamination audit.

Nearest-neighbour cosine between the LoRA training set (399 SFT + 51 DPO = 450 items)
and the 49 eval items. Embeddings: local nomic-embed-text (768-d) via Ollama.

Two views:
  (a) eval QUESTION vs training item  — what big-sis asked for literally
  (b) eval GOLD FACT (gold_entry_body) vs training item — the stronger check: did the
      answer the eval tests for leak into training?

Contamination would bias TOWARD the LoRA (it could memorise), and the LoRA still lost —
so a clean result here hardens the claim; a dirty one still doesn't rescue the adapter.
"""
import json, pathlib, urllib.request, numpy as np

FC = pathlib.Path.home()/ "projects/flotilla-corpus/out/datasets"
EV = pathlib.Path(__file__).parent / "eval008_questions.jsonl"
PREFIX = "search_document: "

def jl(p): return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l.strip()]

def flat(v):
    """Coerce a field that may be a str or a list of chat messages/strings into text."""
    if isinstance(v, str): return v
    if isinstance(v, list):
        return " ".join(flat(m.get("content","")) if isinstance(m, dict) else flat(m) for m in v)
    if isinstance(v, dict): return flat(v.get("content",""))
    return ""

def _one(t):
    body = json.dumps({"model": "nomic-embed-text", "prompt": t}).encode()
    req = urllib.request.Request("http://localhost:11434/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["embedding"]

def embed(texts):
    """Returns L2-normalised matrix. Resilient: truncates, guards empties, retries once."""
    out = []
    for i, t in enumerate(texts):
        s = (PREFIX + (t or "").strip())[:2000] or (PREFIX + "empty")
        try:
            e = _one(s)
        except Exception:
            try:
                e = _one((PREFIX + (t or "").strip())[:512] or (PREFIX + "empty"))
            except Exception as ex:
                print(f"    ! embed failed on item {i} (len={len(t or '')}): {ex} — using zero vec")
                e = [0.0] * 768
        v = np.array(e, dtype=np.float32)
        out.append(v / (np.linalg.norm(v) + 1e-9))
    return np.vstack(out)

# ---- training corpus text ----
train_texts, train_src = [], []
for r in jl(FC/"sft.jsonl"):
    txt = " ".join(m.get("content","") for m in r.get("messages", []))
    train_texts.append(txt); train_src.append("sft")
for r in jl(FC/"dpo.jsonl"):
    txt = " ".join([flat(r.get("prompt","")), flat(r.get("chosen","")), flat(r.get("rejected",""))])
    train_texts.append(txt); train_src.append("dpo")
print(f"training items: {len(train_texts)} ({train_src.count('sft')} sft + {train_src.count('dpo')} dpo)")

ev = jl(EV)
q_texts = [r["question"] for r in ev]
g_texts = [r.get("gold_entry_body","") for r in ev]
print(f"eval items: {len(ev)}")

print("embedding (local nomic-embed-text)…")
T = embed(train_texts)              # (450, 768)
Q = embed(q_texts)                  # (49, 768)
G = embed(g_texts)

def top1(M):
    sims = M @ T.T                  # cosine (all unit vectors)
    idx = sims.argmax(1)
    return sims.max(1), idx

for name, M in (("QUESTION vs training", Q), ("GOLD-FACT vs training", G)):
    top, idx = top1(M)
    print("\n" + "="*64)
    print(f"[{name}]  top-1 cosine over {len(train_texts)} training items")
    print(f"  max  top-1 = {top.max():.3f}")
    print(f"  mean top-1 = {top.mean():.3f}")
    print(f"  median     = {np.median(top):.3f}")
    over = [(ev[i]['question_id'], float(top[i]), train_src[idx[i]]) for i in range(len(top)) if top[i] > 0.9]
    print(f"  eval items with top-1 > 0.90: {len(over)}")
    for qid, s, src in sorted(over, key=lambda x:-x[1]):
        print(f"    qid {qid}: {s:.3f}  (nearest train item: {src})")
    # show the 3 highest regardless, for context
    order = np.argsort(-top)[:3]
    print("  highest-3 (for context):")
    for i in order:
        print(f"    qid {ev[i]['question_id']}: {top[i]:.3f} ({train_src[idx[i]]})  q='{ev[i]['question'][:60]}…'")
