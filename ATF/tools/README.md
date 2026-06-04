# ATF Tools

Local tooling for the Agentegra ATF (Agentegra Training Framework) corpus.

---

## atf_qa.py — Local QA Shell

Question-answering CLI over the compiled RobotRoss wiki and operational ledger.
No cloud APIs required.

### Usage

```bash
# One-shot query
python3 ATF/tools/atf_qa.py "What is the bidding rule for the Wall of Fame?"

# Interactive shell
python3 ATF/tools/atf_qa.py --shell

# List all indexed source files
python3 ATF/tools/atf_qa.py --list-sources

# Force a specific model hint
BACKEND=local python3 ATF/tools/atf_qa.py --model ministral "How does calibration work?"

# Override corpus directories (e.g. for testing)
python3 ATF/tools/atf_qa.py --wiki-dir /tmp/test_wiki "What is the arm?"
```

### Answer format

Every answer includes a **Sources:** block with provenance paths:

```
[corpus-only mode — no local model available]
Showing the most relevant document chunks:

[1] ## 2. Overwrite Rule
  A new order can overwrite an existing slot only if its bid is at least
  120% of the price paid for the current occupant. [...]

Sources:
  [1] artifacts/wiki/Topics/BiddingRules.md
  [2] artifacts/wiki/Subsystems/CommerceLayer.md
```

### Model backend priority

The tool tries each backend in order, falling back automatically:

| Priority | Backend | How to activate |
| :--- | :--- | :--- |
| 1 | Mistral hosted | Set `MISTRAL_API_KEY`; defaults to `mistral-medium-3-5`, then `mistral-large-2512` |
| 2 | local Ministral | Set `BACKEND=local` or pull a Ministral Ollama tag for auto mode |
| 3 | `aichat` | Install and configure `aichat`; optional subprocess fallback |
| 4 | generic `ollama` | Install `ollama`; Apertus/Gemma/fallback pulled model |
| 5 | corpus-only | **Always available** — returns ranked chunks, no model needed |

### Failure modes

| Situation | Behaviour |
| :--- | :--- |
| No Markdown files in `ATF/artifacts/` | Hard exit with path hint |
| No model available | Falls back to corpus-only; prints warning header |
| Model subprocess error | Logs stderr warning; falls back to corpus-only |
| Query matches nothing | Returns "No relevant content found" + full source list |
| Ledger directory empty | Silently skipped; wiki-only answers returned |

### Requirements

- Python >= 3.9, standard library only.
- No pip installs required.

### Runtime adapter interface

When `ATF/tools/runtime_adapter.py` exists, the tool imports it and calls:

```python
def query(prompt: str, model: str | None = None, backend: str | None = None) -> str:
    ...
```

Set `BACKEND=auto|hosted|local|aichat|ollama|corpus-only` or use
`ATF/tools/runtime_adapter.py --backend ...` when invoking the adapter CLI
directly. Hosted Mistral reads `MISTRAL_API_KEY` from the environment only.
