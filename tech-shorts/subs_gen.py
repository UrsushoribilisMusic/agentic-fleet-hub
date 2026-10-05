#!/usr/bin/env python3
"""Captions-only (no dubs). Args: VIDEO OUTDIR SLUG LANGS(csv).
ASR once, translate per lang, write EN + per-lang SRT."""
import sys
from pathlib import Path
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import localize as L
import anthropic

VIDEO, OUT, SLUG, LANGS = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4].split(",")
OUT.mkdir(parents=True, exist_ok=True)
an = anthropic.Anthropic(api_key=L.env("ANTHROPIC_API_KEY"), timeout=90.0, max_retries=4)

dur = L.ffdur(VIDEO)
print(f"ASR on {VIDEO.name} ({dur:.0f}s)...", flush=True)
chunks = L.merge(L.asr(VIDEO))
print(f"  {len(chunks)} chunks", flush=True)
L.write_srt(chunks, [c["text"] for c in chunks], OUT / f"{SLUG}_en.srt")
print("  wrote EN srt", flush=True)
for lang in LANGS:
    if lang == "en":
        continue
    tr = L.translate_chunks(an, [c["text"] for c in chunks], lang)
    L.write_srt(chunks, tr, OUT / f"{SLUG}_{lang}.srt")
    print(f"  wrote {lang} srt", flush=True)
print(f"DONE -> {OUT}", flush=True)
