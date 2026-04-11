# WORKLOG — #132 [ATF-9] Build local CLI QA shell over wiki and ledger

**Agent:** Clau  
**Branch:** `task/atf9-cli-qa`  
**Started:** 2026-04-10

---

## Plan

Build `ATF/tools/atf_qa.py` — a local CLI tool that answers questions over the
compiled RobotRoss ATF corpus (wiki + ledger) with source citations.

### What it does

1. **Corpus loader** — walks `ATF/artifacts/wiki/` and `ATF/artifacts/ledger/`
   recursively, parses each Markdown file into chunks split at heading
   boundaries. Each chunk carries its source path and heading trail.

2. **Keyword ranker** — scores chunks against the user query using term-frequency
   matching with stopword removal. Returns top-K relevant chunks.

3. **Context builder** — formats the top-K chunks into a numbered prompt block
   with labelled source references (e.g. `[1] wiki/Subsystems/JobOrchestration.md`).

4. **Model caller** — tries in order:
   - `ATF/tools/runtime_adapter.py` — interface for #131 (Codi's task)
   - `aichat` subprocess (Gemma's local model tool)
   - `ollama run` subprocess
   - **Corpus-only fallback** — returns the raw ranked chunks + citations without
     invoking any model. Satisfies the acceptance criteria even before #131 lands.

5. **Output formatter** — prints the answer (or matched chunks) followed by a
   `Sources:` block listing the provenance paths.

### Modes

- **One-shot**: `python3 ATF/tools/atf_qa.py "question text"`
- **Interactive shell**: `python3 ATF/tools/atf_qa.py --shell`
- **List sources**: `python3 ATF/tools/atf_qa.py --list-sources`

### Key decisions

- Zero dependencies beyond the Python 3.9 standard library.
- The runtime_adapter interface is a single function `query(prompt: str) -> str`
  so Codi can satisfy it with any local model backend.
- Corpus-only mode is the safe default — always works, zero config.

---

## Steps

- [x] Write WORKLOG.md
- [x] Implement `ATF/tools/atf_qa.py`
- [x] Smoke-test against existing wiki pages (13 sources, queries returning correct chunks)
- [x] Write `ATF/tools/README.md` with usage and failure mode docs
- [ ] Update standup and push
