#!/usr/bin/env python3
"""
ATF QA Shell — local question-answering over the RobotRoss ATF corpus.

Usage:
  python3 ATF/tools/atf_qa.py "What is the bidding rule for the Wall of Fame?"
  python3 ATF/tools/atf_qa.py --shell
  python3 ATF/tools/atf_qa.py --list-sources
  python3 ATF/tools/atf_qa.py --model aichat "How does calibration work?"

Modes:
  corpus-only (default when no model is reachable)
    Returns the top-ranked document chunks with source citations.
    No model required — always works offline.

  model-assisted (when a backend is available)
    Injects ranked chunks as context and routes the query to a local model.
    Backend priority: runtime_adapter > aichat > ollama > corpus-only fallback.

Source provenance:
  Every answer includes a "Sources:" block listing the wiki/ledger paths
  that contributed context, so results are always traceable.

Failure modes:
  - No corpus files found   → error + hint to check ATF/artifacts/ path
  - No model available      → corpus-only mode (chunks returned directly)
  - Model subprocess error  → corpus-only fallback with warning
  - Query returns no chunks → "No relevant content found" + source list

Dependencies:
  Python >= 3.9, standard library only.
  Optional: runtime_adapter.py (ATF-8/#131), aichat, or ollama in PATH.
"""

import argparse
import importlib.util
import math
import os
import re
import subprocess
import sys
import textwrap
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ATF_DIR = os.path.dirname(SCRIPT_DIR)
WIKI_DIR = os.path.join(ATF_DIR, "artifacts", "wiki")
LEDGER_DIR = os.path.join(ATF_DIR, "artifacts", "ledger")
ADAPTER_PATH = os.path.join(SCRIPT_DIR, "runtime_adapter.py")

TOP_K = 5          # chunks to include in model context
CHUNK_PREVIEW = 8  # lines shown per chunk in corpus-only mode

# ---------------------------------------------------------------------------
# Stopwords (English + domain-specific noise)
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "of", "to", "for",
    "and", "or", "but", "not", "with", "this", "that", "are", "was",
    "be", "by", "at", "as", "from", "how", "what", "which", "does",
    "do", "its", "i", "s", "can", "will", "more", "also", "has",
    "have", "been", "all", "if", "when", "then", "so", "into",
    "their", "they", "we", "you", "your", "these", "those", "there",
}

# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list:
    """Lowercase alpha-only tokens, stopwords removed."""
    return [
        t for t in re.findall(r"[a-z]+", text.lower())
        if t not in STOPWORDS and len(t) > 2
    ]


def _parse_markdown(path: str, rel_label: str) -> list:
    """
    Split a Markdown file into heading-bounded chunks.

    Returns a list of dicts:
        {
            "source": str,        # e.g. "wiki/Subsystems/JobOrchestration.md"
            "heading": str,       # heading trail, e.g. "## 2. Main Orchestrator"
            "text": str,          # full chunk text
            "tokens": list[str],  # tokenized for scoring
        }
    """
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return []

    chunks = []
    current_heading = "(preamble)"
    current_lines = []

    def flush():
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({
                "source": rel_label,
                "heading": current_heading,
                "text": text,
                "tokens": _tokenize(text),
            })

    for line in raw.splitlines():
        if re.match(r"^#{1,4} ", line):
            flush()
            current_heading = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    flush()
    return chunks


def load_corpus(wiki_dir: str = None, ledger_dir: str = None) -> list:
    """
    Walk wiki and ledger directories, return all parsed chunks.
    Each chunk dict has: source, heading, text, tokens.
    """
    wiki_dir = wiki_dir or WIKI_DIR
    ledger_dir = ledger_dir or LEDGER_DIR
    chunks = []
    for base_dir, label_prefix in [(wiki_dir, "wiki"), (ledger_dir, "ledger")]:
        if not os.path.isdir(base_dir):
            continue
        for root, _dirs, files in os.walk(base_dir):
            for fname in sorted(files):
                if not fname.endswith(".md"):
                    continue
                full_path = os.path.join(root, fname)
                rel = os.path.relpath(full_path, ATF_DIR)
                rel_label = rel.replace("\\", "/")  # normalise on Windows
                chunks.extend(_parse_markdown(full_path, rel_label))
    return chunks


def list_sources(corpus: list) -> list:
    """Return sorted unique source paths in the corpus."""
    return sorted({c["source"] for c in corpus})

# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

def _tf(token: str, doc_tokens: list) -> float:
    count = doc_tokens.count(token)
    return count / max(len(doc_tokens), 1)


def _idf(token: str, corpus: list) -> float:
    df = sum(1 for c in corpus if token in c["tokens"])
    if df == 0:
        return 0.0
    return math.log((len(corpus) + 1) / (df + 1)) + 1.0


def rank_chunks(query: str, corpus: list, top_k: int = TOP_K) -> list:
    """Return top-k chunks ranked by TF-IDF score against the query."""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    idf_cache = {t: _idf(t, corpus) for t in q_tokens}

    scored = []
    for chunk in corpus:
        score = sum(
            _tf(t, chunk["tokens"]) * idf_cache[t]
            for t in q_tokens
            if t in chunk["tokens"]
        )
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]

# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def build_context(chunks: list) -> tuple:
    """
    Format ranked chunks into a context string and a source list.

    Returns (context_text, sources) where sources is a list of unique path strings.
    """
    parts = []
    sources = []
    for i, chunk in enumerate(chunks, 1):
        src = chunk["source"]
        if src not in sources:
            sources.append(src)
        ref = f"[{i}] {src} — {chunk['heading']}"
        parts.append(f"{ref}\n{chunk['text']}")

    context = "\n\n---\n\n".join(parts)
    return context, sources

# ---------------------------------------------------------------------------
# Model backends
# ---------------------------------------------------------------------------

def _try_runtime_adapter(prompt: str) -> Optional[str]:
    """
    Use ATF/tools/runtime_adapter.py if present (from #131).
    Expected interface: query(prompt: str) -> str
    """
    if not os.path.isfile(ADAPTER_PATH):
        return None
    try:
        spec = importlib.util.spec_from_file_location("runtime_adapter", ADAPTER_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.query(prompt)
    except Exception as exc:
        print(f"[warn] runtime_adapter failed: {exc}", file=sys.stderr)
        return None


def _try_subprocess(cmd: list, prompt: str) -> Optional[str]:
    """Send prompt via subprocess and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        if result.stderr.strip():
            print(f"[warn] {cmd[0]} stderr: {result.stderr.strip()[:200]}", file=sys.stderr)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _detect_aichat_model() -> str:
    """Try to find the configured aichat model name."""
    cfg = os.path.expanduser("~/.config/aichat/config.yaml")
    if os.path.isfile(cfg):
        try:
            with open(cfg) as fh:
                for line in fh:
                    if line.strip().startswith("model:"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    return "apertus:latest"


def call_model(prompt: str, model_hint: Optional[str] = None) -> tuple:
    """
    Route prompt to a local model.

    Returns (answer: str, backend: str).
    backend is one of: "runtime_adapter", "aichat", "ollama", "corpus-only".
    """
    # 1. runtime_adapter (#131)
    answer = _try_runtime_adapter(prompt)
    if answer:
        return answer, "runtime_adapter"

    # 2. aichat
    aichat_model = model_hint or _detect_aichat_model()
    answer = _try_subprocess(["aichat", "-m", aichat_model, "-"], prompt)
    if answer:
        return answer, f"aichat ({aichat_model})"

    # 3. ollama
    ollama_model = model_hint or "gemma2:latest"
    answer = _try_subprocess(["ollama", "run", ollama_model], prompt)
    if answer:
        return answer, f"ollama ({ollama_model})"

    return None, "corpus-only"

# ---------------------------------------------------------------------------
# Answer formatting
# ---------------------------------------------------------------------------

CORPUS_ONLY_HEADER = (
    "[corpus-only mode — no local model available]\n"
    "Showing the most relevant document chunks:\n"
)


def format_answer(answer: Optional[str], chunks: list, sources: list, backend: str) -> str:
    lines = []

    if answer:
        lines.append(answer)
    else:
        lines.append(CORPUS_ONLY_HEADER)
        for i, chunk in enumerate(chunks, 1):
            preview = "\n".join(chunk["text"].splitlines()[:CHUNK_PREVIEW])
            if len(chunk["text"].splitlines()) > CHUNK_PREVIEW:
                preview += "\n  [...]"
            lines.append(f"[{i}] {chunk['heading']}\n{textwrap.indent(preview, '  ')}")

    if sources:
        lines.append("\nSources:")
        for i, src in enumerate(sources, 1):
            lines.append(f"  [{i}] {src}")
    else:
        lines.append("\n(No relevant sources found in corpus.)")

    if backend != "corpus-only":
        lines.append(f"\nBackend: {backend}")

    return "\n".join(lines)


def answer_query(query: str, corpus: list, model_hint: Optional[str] = None) -> str:
    """Full pipeline: rank → build context → call model → format."""
    chunks = rank_chunks(query, corpus)

    if not chunks:
        src_list = "\n  ".join(list_sources(corpus)) or "(corpus is empty)"
        return (
            f"No relevant content found for: {query!r}\n\n"
            f"Indexed sources:\n  {src_list}"
        )

    context, sources = build_context(chunks)

    prompt = (
        f"You are a technical assistant with access to the RobotRoss system documentation.\n"
        f"Answer the question using ONLY the context below. "
        f"Cite sources by their [N] reference number.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

    answer, backend = call_model(prompt, model_hint=model_hint)
    return format_answer(answer, chunks, sources, backend)

# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------

def cmd_list_sources(corpus: list):
    sources = list_sources(corpus)
    if not sources:
        print("No sources indexed. Check that ATF/artifacts/ contains Markdown files.")
        return
    print(f"Indexed sources ({len(sources)}):")
    for src in sources:
        print(f"  {src}")


def cmd_one_shot(query: str, corpus: list, model_hint: Optional[str] = None):
    print(answer_query(query, corpus, model_hint=model_hint))


def cmd_shell(corpus: list, model_hint: Optional[str] = None):
    sources = list_sources(corpus)
    print(f"ATF QA Shell — {len(corpus)} chunks from {len(sources)} sources")
    print("Type a question, or 'quit' / Ctrl-D to exit.\n")
    while True:
        try:
            query = input("atf> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            break
        print()
        print(answer_query(query, corpus, model_hint=model_hint))
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Local QA shell over the RobotRoss ATF corpus (wiki + ledger).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python3 ATF/tools/atf_qa.py "What is the bidding rule?"
              python3 ATF/tools/atf_qa.py --shell
              python3 ATF/tools/atf_qa.py --list-sources
              python3 ATF/tools/atf_qa.py --model apertus:latest "How does calibration work?"

            Model backend priority (first available wins):
              1. ATF/tools/runtime_adapter.py  (from ticket #131)
              2. aichat  (via subprocess, reads ~/.config/aichat/config.yaml for model)
              3. ollama  (via subprocess, default model: gemma2:latest)
              4. corpus-only fallback  (returns ranked chunks — no model needed)
        """),
    )
    parser.add_argument("query", nargs="?", help="Question to answer (omit for --shell mode)")
    parser.add_argument("--shell", action="store_true", help="Start interactive QA shell")
    parser.add_argument("--list-sources", action="store_true", help="List all indexed source files")
    parser.add_argument("--model", metavar="NAME", help="Override local model name (passed to aichat or ollama)")
    parser.add_argument("--wiki-dir", metavar="PATH", help=f"Override wiki directory (default: {WIKI_DIR})")
    parser.add_argument("--ledger-dir", metavar="PATH", help=f"Override ledger directory (default: {LEDGER_DIR})")

    args = parser.parse_args()

    # Allow path overrides
    wiki_dir = args.wiki_dir or WIKI_DIR
    ledger_dir = args.ledger_dir or LEDGER_DIR

    corpus = load_corpus(wiki_dir, ledger_dir)

    if not corpus:
        print(
            "Error: no Markdown files found in corpus directories.\n"
            f"  wiki:   {WIKI_DIR}\n"
            f"  ledger: {LEDGER_DIR}\n"
            "Check that the ATF artifacts have been generated (see ticket #128).",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.list_sources:
        cmd_list_sources(corpus)
    elif args.shell:
        cmd_shell(corpus, model_hint=args.model)
    elif args.query:
        cmd_one_shot(args.query, corpus, model_hint=args.model)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
