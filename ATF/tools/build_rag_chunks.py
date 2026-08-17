#!/usr/bin/env python3
"""
build_rag_chunks.py — regenerate the Sovereign Mind RAG (chunks.jsonl) from the
ATF markdown corpus.

Context: the live `/atf/` wiki HTML is built by build_static_views.py, but the RAG
`chunks.jsonl` that the iOS app downloads (sm.flotilla.cc/downloads/robot-ross-atf/)
had NO committed builder — it was a one-off from the Mistral hackathon. This tool
restores a reproducible build so the wiki and the RAG never drift again.

Chunk schema (matches the deployed chunks.jsonl):
    {"id": "atf-<slug>-<n>", "source": "RobotRoss_ATF_<snake>.md",
     "text": "<flattened markdown>", "chunk_index": <n>}

IMPORTANT — surgical by default:
The deployed RAG contains 3 docs that are NOT plain corpus markdown — `architecture`,
`voice_control`, and `sample_run` are synthetic/rendered pages produced elsewhere.
A naive full rebuild from the corpus would silently DROP them. So this tool operates
in --merge mode: it regenerates chunks for the markdown docs you pass and splices them
into an existing chunks.jsonl, leaving every other doc untouched. Folding the synthetic
pages into a single unified build.py (corpus -> HTML + full RAG) is the tracked follow-up.

Usage:
    # regenerate specific docs and merge into the existing RAG
    build_rag_chunks.py --base chunks.jsonl --out chunks.new.jsonl \
        Subsystems/JobOrchestration.md Subsystems/HardwareInterface.md Topics/Calibration.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent           # ATF/tools/ -> ATF/
WIKI_SRC = ROOT / "artifacts" / "wiki"
CHUNK_SIZE = 1000                                        # chars per chunk, split on word boundary


def source_name(md_path: Path) -> str:
    """Subsystems/JobOrchestration.md -> RobotRoss_ATF_job_orchestration.md"""
    stem = md_path.stem
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", stem).lower()
    return f"RobotRoss_ATF_{snake}.md"


def slug(src: str) -> str:
    """RobotRoss_ATF_job_orchestration.md -> job-orchestration (for the chunk id)"""
    return src.replace("RobotRoss_ATF_", "").replace(".md", "").replace("_", "-")


def flatten(md: str) -> str:
    """Markdown -> the plain-text form the deployed chunks use (headings inlined,
    bold/code/wikilinks unwrapped, bullets kept, whitespace collapsed)."""
    out: List[str] = []
    for line in md.splitlines():
        s = line.strip()
        if not s or s.startswith("---"):
            continue
        s = re.sub(r"^#{1,6}\s*", "", s)                       # headings
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)                 # bold
        s = re.sub(r"`([^`]*)`", r"\1", s)                     # inline code
        s = re.sub(r"\[\[([^\]|]+)(\|[^\]]+)?\]\]", r"\1", s)  # [[wikilinks]]
        out.append(s)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    words, chunks, cur = text.split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > size and cur:
            chunks.append(cur.strip())
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        chunks.append(cur.strip())
    return chunks


def build_doc_chunks(md_path: Path) -> List[Dict]:
    src = source_name(md_path)
    flat = flatten(md_path.read_text())
    return [
        {"id": f"atf-{slug(src)}-{i}", "source": src, "text": ct, "chunk_index": i}
        for i, ct in enumerate(chunk_text(flat))
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate ATF RAG chunks (merge mode).")
    ap.add_argument("docs", nargs="+", help="markdown paths relative to artifacts/wiki/")
    ap.add_argument("--base", required=True, help="existing chunks.jsonl to merge into")
    ap.add_argument("--out", required=True, help="output chunks.jsonl")
    args = ap.parse_args()

    changed_sources = {source_name(WIKI_SRC / d) for d in args.docs}

    # keep every chunk whose doc we are NOT regenerating (preserves synthetic docs)
    kept = [
        json.loads(l)
        for l in Path(args.base).read_text().splitlines()
        if l.strip() and json.loads(l)["source"] not in changed_sources
    ]
    regen: List[Dict] = []
    for d in args.docs:
        regen += build_doc_chunks(WIKI_SRC / d)

    with open(args.out, "w") as f:
        for o in kept + regen:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    print(f"kept {len(kept)} chunks + regenerated {len(regen)} ({len(changed_sources)} docs) "
          f"= {len(kept) + len(regen)} -> {args.out}")


if __name__ == "__main__":
    main()
