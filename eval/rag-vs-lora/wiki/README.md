# EVAL-002: Retrieval Wiki — Hard-Facts Corpus

Frozen pre-cutoff gold corpus (records created < 2026-06-22). Used by the retrieval harness (EVAL-002b) to answer questions about fleet behavior, rules, metrics, and incidents.

## Structure

```
eval/wiki/
├── README.md          — this file
├── index.json         — searchable index (id, title, type, source_ref per entry)
└── entries/
    ├── R01.json … R30.json   — 30 behavioral rules (from rules.md)
    ├── F001.json … F025.json — 25 hard facts (metrics, corpus stats, API shape)
    ├── I001.json … I005.json — 5 documented incidents
    └── P001.json … P006.json — 6 escalation/workflow protocols
```

## Entry schema

Each `entries/*.json` file contains exactly one entry:

```json
{
  "id": "R01",
  "title": "Short imperative or declarative title",
  "body": "One-paragraph body — atomic, one fact/rule/metric per entry.",
  "source_ref": "Citable source: file:section or PB collection/field",
  "type": "rule | fact | incident | protocol"
}
```

## Types

| Type | Count | What it covers |
|---|---|---|
| `rule` | 30 | Behavioral rules R01–R30 from rules.md (Arm 1 source) |
| `fact` | 25 | Hard metrics, corpus stats, API shape, date anchors |
| `incident` | 5 | Documented failure events (death spiral, spam, self-approval) |
| `protocol` | 6 | Step-by-step escalation and workflow procedures |

## Constraints

- **Frozen**: no records added after 2026-06-22; no FX- task references (FX-NNN are pipeline tasks, not fleet work)
- **Atomic**: one fact per entry — body is one paragraph, not a list of sub-facts
- **Cited**: every entry has a `source_ref` traceable to a file, collection, or corpus record
- **Searchable**: index.json lists all entry ids, titles, types, and source_refs for BM25/keyword retrieval

## Usage by harness (EVAL-002b)

```python
from eval.retrieve import retrieve
snippets = retrieve("can I approve my own task", k=3)
# returns top-k entries as {"id", "title", "body", "source_ref", "type"}
```

The retrieval layer (EVAL-002b) implements keyword/BM25 search over the `title` + `body` fields of `index.json`. No embeddings, no GPU, deterministic.
