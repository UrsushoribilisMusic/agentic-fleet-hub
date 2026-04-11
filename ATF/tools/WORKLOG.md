# WORKLOG — ATF-8 / #131: Local Model Runtime Adapter

**Agent:** Clau
**Branch:** task/131
**Date:** 2026-04-11
**Status:** in_work → peer_review

---

## Goal

Build `ATF/tools/runtime_adapter.py` — the stable local-model invocation layer
that `atf_qa.py` (ATF-9) and future CLI tools can import without embedding
model-specific logic everywhere.

## Plan

1. [x] Read MISSION_CONTROL.md and related context (GEMMA.md, atf_qa.py)
2. [x] Discover available local models via `ollama list`:
       `gemma:latest`, `gemma4:e4b`, `MichelRosselli/apertus:8b-instruct-2509-q4_k_m`
3. [x] Write `runtime_adapter.py` with:
       - Public `query(prompt, model, timeout) -> str` function
       - Ollama HTTP backend (primary) via `urllib` — no external deps
       - aichat subprocess backend (secondary fallback)
       - `--check`, `--list-models`, `--stdin` CLI flags
       - Model auto-selection priority: apertus > gemma4 > gemma > first listed
       - `OLLAMA_HOST` env override
4. [x] Smoke-test: `--check` and `--list-models` pass; importlib path verified
5. [x] Commit WORKLOG + adapter, push branch
6. [ ] Update standup, mark task peer_review in PocketBase

## Key Decisions

- **Ollama HTTP API** (`/api/generate`, stream=false) chosen over subprocess
  `ollama run` to avoid TTY/pty issues and get clean JSON payloads.
- **Standard library only** (urllib, json, subprocess) — zero pip install.
- **Interface kept minimal**: `query(prompt)` is the only required export so
  atf_qa.py's `mod.query(prompt)` call works without changes.
- **aichat as secondary** because it's configured for the same Ollama backend;
  only reached if Ollama is unreachable (e.g. daemon not started).
- **Apertus priority** — Miguel's custom model, prefer it when available.
