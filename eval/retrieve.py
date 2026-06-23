"""
EVAL-002b: retrieve(query, k) — BM25 keyword retriever over eval/wiki/entries/.

Usage:
    from eval.retrieve import retrieve
    hits = retrieve("peer review rejected", k=5)
    for h in hits:
        print(h["id"], h["title"])
        print(h["body"])
        print(h["source_ref"])

Deterministic: same query → same ranked results. No embeddings, no GPU.
"""
import json
import math
import re
import pathlib

WIKI_DIR = pathlib.Path(__file__).parent / "wiki" / "entries"

# BM25 constants
K1 = 1.5
B  = 0.75

# Module-level cache — loaded once per process
_corpus = None
_idf: dict = {}
_tf: list = []
_avg_dl: float = 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _load() -> None:
    global _corpus, _idf, _tf, _avg_dl

    entries = []
    for path in sorted(WIKI_DIR.glob("*.json")):
        with path.open() as fh:
            entries.append(json.load(fh))
    _corpus = entries

    # Build term frequencies per document (title weighted 3×, body 1×)
    doc_tokens: list[list[str]] = []
    for entry in entries:
        tokens = _tokenize(entry.get("title", "") * 3 + " " + entry.get("body", ""))
        doc_tokens.append(tokens)

    _avg_dl = sum(len(t) for t in doc_tokens) / max(len(doc_tokens), 1)

    # IDF: log((N - df + 0.5) / (df + 0.5) + 1)
    N = len(entries)
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    _idf = {
        term: math.log((N - freq + 0.5) / (freq + 0.5) + 1)
        for term, freq in df.items()
    }

    # TF per document
    _tf = []
    for tokens in doc_tokens:
        counts: dict[str, float] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        _tf.append(counts)


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return top-k wiki entries for query, ranked by BM25 score."""
    if _corpus is None:
        _load()

    q_terms = _tokenize(query)
    if not q_terms:
        return []

    scores: list[tuple[float, int]] = []
    for idx, tf_doc in enumerate(_tf):
        dl = sum(tf_doc.values())
        score = 0.0
        for term in q_terms:
            if term not in _idf:
                continue
            tf_val = tf_doc.get(term, 0)
            numerator = tf_val * (K1 + 1)
            denominator = tf_val + K1 * (1 - B + B * dl / _avg_dl)
            score += _idf[term] * (numerator / denominator)
        scores.append((score, idx))

    scores.sort(key=lambda x: (-x[0], x[1]))  # deterministic tie-break by index

    results = []
    for score, idx in scores[:k]:
        if score <= 0:
            break
        entry = _corpus[idx]
        results.append({
            "id":         entry["id"],
            "title":      entry["title"],
            "body":       entry["body"],
            "source_ref": entry["source_ref"],
            "type":       entry["type"],
            "score":      round(score, 4),
        })
    return results


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "peer review rejected change"
    hits = retrieve(query, k=5)
    print(f"\nQuery: {query!r}\n{'─'*60}")
    for h in hits:
        print(f"[{h['id']}] ({h['type']}) {h['title']}  score={h['score']}")
        print(f"  {h['body'][:120]}...")
        print(f"  source: {h['source_ref']}\n")
