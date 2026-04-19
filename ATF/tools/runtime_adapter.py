#!/usr/bin/env python3
"""
ATF Runtime Adapter — local model invocation for Gemma and Apertus.

This module is the stable interface layer between callers (atf_qa.py, future
CLI tools) and the local model runtime.  Callers import this module and call
``query(prompt)``; they never need to know whether the backend is Ollama,
aichat, or anything else.

Public interface
----------------
    query(prompt, model=None, timeout=120) -> str
    list_models() -> list[str]

CLI usage
---------
    python3 ATF/tools/runtime_adapter.py --check
    python3 ATF/tools/runtime_adapter.py --list-models
    python3 ATF/tools/runtime_adapter.py "Your prompt here"
    python3 ATF/tools/runtime_adapter.py --model gemma:latest "Explain X."
    echo "Hello" | python3 ATF/tools/runtime_adapter.py --stdin

Machine / runtime prerequisites
--------------------------------
    Ollama >= 0.3.0 must be running:
        ollama serve                     # starts the daemon on :11434
    At least one of these models must be pulled (pull once, reuse forever):
        ollama pull MichelRosselli/apertus:8b-instruct-2509-q4_k_m   # preferred
        ollama pull gemma4:e4b                                         # alt
        ollama pull gemma:latest                                       # baseline
    Python >= 3.9, standard library only — no pip install required.
    Optional: aichat in PATH (secondary fallback if Ollama is unreachable).

Model selection
---------------
    When model=None the adapter probes Ollama and picks the first available
    model from this priority list:
        1. apertus (any tag)  — custom local model, highest priority
        2. gemma4  (any tag)  — Gemma 4, strong general-purpose
        3. gemma   (any tag)  — Gemma baseline
        4. first model listed — last-resort: whatever Ollama has pulled
    Pass a substring hint via model= to steer selection manually.
    Set OLLAMA_HOST env var to override the default endpoint (localhost:11434).

Context handling
----------------
    Prompts are passed verbatim to the model.  Callers (e.g. atf_qa.py) are
    responsible for injecting corpus context before calling query().

Output conventions
------------------
    Returns the model's response text, stripped of surrounding whitespace.
    Raises RuntimeError if no backend is reachable or the response is empty.
    Never returns an empty string; always raises instead.

Failure modes
-------------
    Ollama unreachable      -> falls through to aichat subprocess backend
    aichat also missing     -> RuntimeError with actionable hint
    Model not found         -> warning printed; auto-selection used instead
    Empty model response    -> RuntimeError (not silent empty string)
    Timeout                 -> RuntimeError wrapping TimeoutExpired
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from typing import List, Optional

# ---------------------------------------------------------------------------
# Backend configuration
# ---------------------------------------------------------------------------

OLLAMA_BASE: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_TIMEOUT: int = 120  # seconds

# Substring keywords in priority order — first match in available models wins
MODEL_PRIORITY: List[str] = ["apertus", "gemma4", "gemma"]


# ---------------------------------------------------------------------------
# Ollama HTTP backend (primary)
# ---------------------------------------------------------------------------

def _ollama_list_models() -> List[str]:
    """Return names of all models currently pulled in Ollama, or [] on error."""
    url = f"{OLLAMA_BASE}/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _select_model(models: List[str], hint: Optional[str] = None) -> Optional[str]:
    """
    Choose the best model from *models*.

    If *hint* matches any model name (case-insensitive substring), that model
    is returned.  Otherwise, MODEL_PRIORITY is walked and the first keyword
    match is returned.  Falls back to models[0] if nothing matches.
    """
    if not models:
        return None

    if hint:
        for m in models:
            if hint.lower() in m.lower():
                return m
        print(
            f"[warn] runtime_adapter: requested model '{hint}' not found in Ollama; "
            "auto-selecting from priority list.",
            file=sys.stderr,
        )

    for keyword in MODEL_PRIORITY:
        for m in models:
            if keyword.lower() in m.lower():
                return m

    return models[0]


def _ollama_generate(prompt: str, model: str, timeout: int) -> str:
    """
    POST to Ollama /api/generate (stream=false) and return the response text.
    Raises RuntimeError on HTTP error or empty output.
    """
    url = f"{OLLAMA_BASE}/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama HTTP error: {exc}") from exc

    text = body.get("response", "").strip()
    if not text:
        raise RuntimeError(
            f"Ollama returned an empty response for model '{model}'. "
            "The model may still be loading; try again in a few seconds."
        )
    return text


# ---------------------------------------------------------------------------
# aichat subprocess backend (secondary fallback)
# ---------------------------------------------------------------------------

def _aichat_query(prompt: str, model: Optional[str], timeout: int) -> Optional[str]:
    """
    Send *prompt* to aichat via subprocess.  Returns output text or None.
    Used only when Ollama is unreachable.
    """
    cmd = ["aichat"]
    if model:
        cmd += ["-m", model]
    cmd.append("-")  # read prompt from stdin

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        if result.stderr.strip():
            print(
                f"[warn] runtime_adapter: aichat stderr: {result.stderr.strip()[:200]}",
                file=sys.stderr,
            )
    except FileNotFoundError:
        pass  # aichat not installed — silent
    except subprocess.TimeoutExpired:
        print("[warn] runtime_adapter: aichat timed out.", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_models() -> List[str]:
    """Return the names of all locally available models (from Ollama)."""
    return _ollama_list_models()


def generate(
    prompt: str,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Alias for :func:`query`.  Provided for callers that expect the ATF-8
    ticket-spec interface name (``generate``) rather than ``query``.
    """
    return query(prompt, model=model, timeout=timeout)


def query(
    prompt: str,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Invoke a local model and return its response.

    Parameters
    ----------
    prompt:
        The full prompt text.  Callers are responsible for injecting context.
    model:
        Optional model name or substring hint (e.g. ``"apertus"``,
        ``"gemma:latest"``).  When None, auto-selection from MODEL_PRIORITY
        is used.
    timeout:
        Seconds to wait for the model response before raising RuntimeError.

    Returns
    -------
    str
        Response text, stripped of leading/trailing whitespace.

    Raises
    ------
    RuntimeError
        When no local model backend is reachable or the response is empty.
    """
    text, _ = query_with_model(prompt, model=model, timeout=timeout)
    return text


def query_with_model(
    prompt: str,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple:
    """
    Like :func:`query` but returns ``(response_text, model_name)`` so callers
    can surface which model was actually used.

    ``model_name`` is the full Ollama model tag (e.g.
    ``"MichelRosselli/apertus:8b-instruct-2509-q4_k_m"``) or ``"aichat"``
    when the subprocess fallback is used.
    """
    # --- Primary: Ollama HTTP ---
    available = _ollama_list_models()
    if available:
        chosen = _select_model(available, hint=model)
        if chosen:
            return _ollama_generate(prompt, chosen, timeout), chosen

    # --- Secondary: aichat subprocess ---
    answer = _aichat_query(prompt, model, timeout)
    if answer:
        return answer, "aichat"

    raise RuntimeError(
        "No local model backend is reachable.\n"
        "  1. Start Ollama:  ollama serve\n"
        "  2. Pull a model:  ollama pull MichelRosselli/apertus:8b-instruct-2509-q4_k_m\n"
        f"  OLLAMA_HOST={OLLAMA_BASE}"
    )


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _cmd_check() -> None:
    """Print backend and model status."""
    models = _ollama_list_models()
    if models:
        print(f"Ollama: reachable at {OLLAMA_BASE}")
        chosen = _select_model(models)
        print(f"  Models pulled ({len(models)}):")
        for m in models:
            tag = "  <-- auto-selected" if m == chosen else ""
            print(f"    {m}{tag}")
    else:
        print(f"Ollama: NOT reachable at {OLLAMA_BASE}")
        print("  Run: ollama serve")

    # aichat probe
    try:
        result = subprocess.run(
            ["aichat", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"aichat: {result.stdout.strip()}")
        else:
            print("aichat: installed but --version failed")
    except FileNotFoundError:
        print("aichat: not in PATH (optional fallback unavailable)")


def _cmd_list_models() -> None:
    models = _ollama_list_models()
    if not models:
        print(
            "No models available.  Ollama may not be running.\n"
            "  Run: ollama serve"
        )
        return
    chosen = _select_model(models)
    print(f"Available models ({len(models)}) -- [*] = would be auto-selected:")
    for m in models:
        mark = "[*]" if m == chosen else "   "
        print(f"  {mark} {m}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "ATF runtime adapter: invoke Gemma or Apertus via Ollama "
            "(or aichat fallback)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
            Prerequisites (one-time setup):
              ollama serve
              ollama pull MichelRosselli/apertus:8b-instruct-2509-q4_k_m
              ollama pull gemma:latest     # alternative

            Model selection priority (auto when --model not given):
              {", ".join(MODEL_PRIORITY)} -> first listed Ollama model

            Environment:
              OLLAMA_HOST   override Ollama endpoint (default: {OLLAMA_BASE})

            Examples:
              python3 ATF/tools/runtime_adapter.py --check
              python3 ATF/tools/runtime_adapter.py --list-models
              python3 ATF/tools/runtime_adapter.py "What is the Wall of Fame?"
              python3 ATF/tools/runtime_adapter.py --model gemma:latest "Explain X."
              echo "Hello" | python3 ATF/tools/runtime_adapter.py --stdin
        """),
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt text (inline; omit if using --stdin)",
    )
    parser.add_argument(
        "--model",
        metavar="NAME",
        help="Model name or substring hint (e.g. 'apertus', 'gemma:latest')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        metavar="SEC",
        help=f"Response timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Show backend / model status and exit",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all locally available models and exit",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read prompt from stdin (also triggered automatically when stdin is a pipe)",
    )

    args = parser.parse_args()

    if args.check:
        _cmd_check()
        return

    if args.list_models:
        _cmd_list_models()
        return

    # Resolve prompt: explicit flag, piped stdin, or positional arg
    prompt: Optional[str] = None
    if args.stdin or not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(0)

    if not prompt:
        print("Error: empty prompt.", file=sys.stderr)
        sys.exit(1)

    try:
        answer = query(prompt, model=args.model, timeout=args.timeout)
        print(answer)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
