#!/usr/bin/env python3
"""
ATF Local Server — serves the ATF static site and exposes a /api/qa endpoint.

Usage:
    python3 ATF/tools/atf_local_server.py [--port 8770]

Then open http://localhost:8770/ in your browser.
The "Local Reasoning Session" on the landing page will call the real Apertus model
instead of rotating mock examples.

Endpoints:
    GET  /           → serves ATF/index.html
    GET  /<path>     → serves static files from ATF/
    POST /api/qa     → {"query": "..."} → {"answer": "...", "backend": "...", "sources": [...]}
    GET  /api/status → health check + model info
"""

import argparse
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ATF_DIR = os.path.dirname(SCRIPT_DIR)

# Lazy-load atf_qa corpus once on first request
_corpus = None

def get_corpus():
    global _corpus
    if _corpus is None:
        sys.path.insert(0, SCRIPT_DIR)
        import atf_qa
        _corpus = atf_qa.load_corpus()
    return _corpus


def handle_qa(query: str, model_hint: str = None) -> dict:
    """Run the real ATF QA pipeline and return a structured result."""
    sys.path.insert(0, SCRIPT_DIR)
    import atf_qa
    import runtime_adapter

    corpus = get_corpus()
    if not corpus:
        return {"answer": "No corpus loaded. Check ATF/artifacts/ for Markdown files.", "backend": "none", "model": None, "sources": []}

    chunks = atf_qa.rank_chunks(query, corpus)
    if not chunks:
        src_list = atf_qa.list_sources(corpus)
        return {
            "answer": f"No relevant content found for: {query!r}",
            "backend": "corpus-only",
            "model": None,
            "sources": src_list,
        }

    context, sources = atf_qa.build_context(chunks)
    prompt = (
        "You are a technical assistant with access to the RobotRoss system documentation.\n"
        "Answer the question using ONLY the context below. "
        "Cite sources by their [N] reference number.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

    # Use runtime_adapter directly so we get the real model name back
    try:
        answer_text, model_name = runtime_adapter.query_with_model(prompt, model=model_hint or None)
        backend = "ollama" if model_name != "aichat" else "aichat"
    except RuntimeError as exc:
        # Fall back to corpus-only
        formatted = atf_qa.format_answer(None, chunks, sources, "corpus-only")
        return {"answer": formatted, "backend": "corpus-only", "model": None, "sources": list(sources)}

    formatted = atf_qa.format_answer(answer_text, chunks, sources, backend)
    return {
        "answer": formatted,
        "backend": backend,
        "model": model_name,
        "sources": list(sources),
    }


class ATFHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, file_path: str):
        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except OSError:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/status":
            corpus = get_corpus()
            return self.send_json(200, {
                "status": "ok",
                "corpus_chunks": len(corpus),
                "corpus_sources": len(atf_qa_sources(corpus)),
            })

        if path == "/api/models":
            sys.path.insert(0, SCRIPT_DIR)
            import runtime_adapter
            models = runtime_adapter.list_models()
            selected = runtime_adapter._select_model(models) if models else None
            return self.send_json(200, {"models": models, "selected": selected})

        # Map URL path to filesystem
        if path == "/" or path == "":
            file_path = os.path.join(ATF_DIR, "index.html")
        else:
            # Strip leading slash and resolve under ATF_DIR
            rel = path.lstrip("/")
            file_path = os.path.join(ATF_DIR, rel)
            # Directory index
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, "index.html")

        # Security: stay inside ATF_DIR
        try:
            real = os.path.realpath(file_path)
            atf_real = os.path.realpath(ATF_DIR)
            if not real.startswith(atf_real + os.sep) and real != atf_real:
                self.send_response(403)
                self.end_headers()
                return
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        if not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            return

        self.send_file(file_path)

    def do_POST(self):
        path = self.path.split("?")[0]

        if path != "/api/qa":
            self.send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_json(400, {"error": "invalid JSON"})
            return

        query = (payload.get("query") or "").strip()
        if not query:
            self.send_json(400, {"error": "query is required"})
            return

        model_hint = (payload.get("model") or "").strip() or None

        try:
            result = handle_qa(query, model_hint=model_hint)
            self.send_json(200, result)
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def atf_qa_sources(corpus):
    return sorted({c["source"] for c in corpus})


def main():
    parser = argparse.ArgumentParser(description="ATF local server")
    parser.add_argument("--port", type=int, default=8771, help="Port to listen on (default: 8771)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"ATF Local Server")
    print(f"  Serving: {ATF_DIR}")
    print(f"  URL:     http://{args.host}:{args.port}/")
    print(f"  QA API:  http://{args.host}:{args.port}/api/qa")
    print()

    # Pre-load corpus at startup
    corpus = get_corpus()
    import atf_qa as _q
    sources = atf_qa_sources(corpus)
    print(f"  Corpus:  {len(corpus)} chunks from {len(sources)} sources")
    print()
    print("Press Ctrl+C to stop.\n")

    server = HTTPServer((args.host, args.port), ATFHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
