# Agentegra ATF (Automated Technical File) Architecture & Schema Contract

**Status:** Finalized / active
**Project:** RobotRoss Showcase Compliance (ATF-1)
**Owner:** Gem (Gemini CLI)
**Date:** 2026-04-09

---

## 1. Overview
The **Agentegra ATF** (Automated Technical File) is a local-first compliance and explainability workspace. It is designed to provide "evidence-based transparency" for industrial AI systems, starting with the **RobotRoss** painting robot.

The ATF transforms raw, immutable source material (code, docs, logs) into a navigable, auditable wiki and operational ledger, supported by a local Q&A CLI tool for human or automated inspection.

---

## 2. Four-Layer Architecture

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Layer 1** | **Compiled Wiki** | A structured markdown knowledge base built from source code (docstrings), READMEs, and architecture docs. |
| **Layer 2** | **Operational Ledger** | A normalized, queryable record of production activity, derived from rich logs (e.g., Mexico wood-marking). |
| **Layer 3** | **Local Q&A CLI** | A tool for querying the Wiki and Ledger using local LLMs (Gemma, Apertus) without cloud dependency. |
| **Layer 4** | **Voice Interface** | (Optional) Hands-free interaction via Whisper (STT) and Voxtral (TTS). |

---

## 3. Directory & Artifact Contract

All ATF assets reside in the `ATF/` root of the repository.

```text
ATF/
├── raw_sources/            # Immutable evidence (References/Symlinks)
│   ├── docs/               # Manuals, specs, and architectural docs
│   ├── code/               # Snapshots of source files with docstrings
│   └── logs/               # Production logs (Mexico wood-marking)
├── artifacts/              # Generated, derived assets
│   ├── wiki/               # Compiled markdown pages
│   └── ledger/             # Normalized JSON/CSV operational records
├── parsers/                # Ingestion logic (The "Builders")
│   ├── doc_ingest.py       # Converts docs to wiki pages
│   ├── code_ingest.py      # Extracts docstrings and logic flow to wiki
│   └── log_ingest.py       # Normalizes raw logs to ledger artifacts
├── tools/                  # Runnable interfaces
│   ├── atf_cli.py          # Local Q&A shell
│   └── atf_voice.py        # Voice shell (Optional)
└── manifest.json           # Central registry of all sources and artifacts
```

---

## 4. Schema & Conventions

### 4.1 Markdown Frontmatter (Wiki & Ledger)
All generated markdown files MUST include the following frontmatter for provenance and compliance mapping:

```markdown
---
id: ATF-WIKI-XXXX             # Unique artifact ID (e.g., ATF-WIKI-0001)
title: "Page Title"
type: wiki_page | ledger_entry
category: arch | ops | compliance
tags: [robotross, safety, huenit]
eu_ai_act_obligations:        # Mapping to EU AI Act (Reference: ATF-7)
  - transparency
  - traceability
  - record-keeping
  - human_oversight
compliance_theme: "Theme Name"
provenance:                   # Explicit links to immutable raw sources
  - source: "ATF/raw_sources/code/bob_ross.py"
    version: "git-hash-or-timestamp"
    lines: "100-150"          # Optional
    entry_id: "E-001"         # For logs
last_updated: 2026-04-09
---
```

### 4.2 Cross-Linking
Use standard Markdown wikilinks `[[PageName]]` or `[Label](ATF-WIKI-XXXX.md)` for internal navigation. All pages must be discoverable from the `Overview.md` entry point.

### 4.3 Provenance Requirement
Every claim in the wiki MUST have a corresponding `provenance` entry in its frontmatter pointing to a file in `ATF/raw_sources/`. This is non-negotiable for EU AI Act compliance.

### 4.4 `manifest.json` and `manifest.md`
- **`manifest.json`**: The machine-readable, tamper-evident index in the ATF root. It tracks hashes and provenance for all artifacts.
- **`artifacts/wiki/manifest.md`**: A human-readable version of the corpus inventory, used for quick inspection and as a wiki navigation aid.

#### `manifest.json` Schema
The `manifest.json` file in the ATF root acts as the central registry.

```json
{
  "project": "RobotRoss",
  "version": "1.0.0",
  "last_synced": "2026-04-09T18:00:00Z",
  "sources": {
    "code/bob_ross.py": { "hash": "sha256...", "last_updated": "..." },
    "logs/mexico_log.json": { "hash": "sha256...", "last_updated": "..." }
  },
  "artifacts": {
    "wiki/Overview.md": {
      "id": "ATF-WIKI-0001",
      "sources": ["code/bob_ross.py", "docs/manual.md"],
      "hash": "sha256..."
    }
  }
}
```

---

## 5. EU AI Act Mapping
Agentegra ATF is designed to fulfill the **Transparency** and **Traceability** requirements of the EU AI Act for high-risk AI systems.

- **Traceability**: Achieved via the Compiled Wiki linked directly to code and design specs.
- **Record-keeping**: Achieved via the Operational Ledger (Mexico logs).
- **Human Oversight**: Documented in the Wiki via the [[HardwareInterface]] and [[OperatorManual]].

Reference: `AGENTS/CONTEXT/atf_eu_ai_act_mapping.md` for the full mapping schema.

---

## 6. Dependency Graph & Workflow

1.  **Ingestion**: `parsers/doc_ingest.py` and `parsers/code_ingest.py` read from `raw_sources/` and generate `artifacts/wiki/`.
2.  **Normalization**: `parsers/log_ingest.py` reads raw logs and produces `artifacts/ledger/`.
3.  **Indexing**: A background process updates `manifest.json` with new artifact-source mappings.
4.  **Inquiry**: `tools/atf_cli.py` loads the `wiki/` and `ledger/` into a local RAG context (Gemma) for user interaction.

---

## 7. Working Conventions for the Fleet

- **Immutability**: Files in `raw_sources/` are considered evidence. DO NOT edit them.
- **Traceable Commits**: Any changes to the `ATF/` directory must reference the relevant ticket (e.g., `#127`).
- **Gemma/Apertus First**: The QA CLI must default to local models to maintain data sovereignty.
- **Mexico Logs**: The `vault/raw_sources/robotross/mexico_wood_marking/` directory is the canonical dropzone for new logs.

---

## 8. Downstream Execution (Next Steps)

| Ticket | Task | Owner | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **#125** | Inventory source corpus | Gem | P1 | COMPLETE |
| **#126** | Scaffold Mexico log dropzone | Gemma | P1 | IN_WORK |
| **#127** | Build Mexico log parser | Misty | P2 | PLANNED |
| **#128** | Generate initial wiki | Gem | P1 | COMPLETE |
| **#129** | Scaffold wiki templates | Gemma | P2 | PLANNED |
| **#130** | EU AI Act metadata mapping | Misty | P1 | COMPLETE |
| **#131** | Local model adapter (Gemma) | Codi | P2 | PLANNED |
| **#132** | CLI QA Tooling | Clau | P1 | PLANNED |
| **#133** | Cross-reference logs into wiki | Misty | P2 | PLANNED |
| **#134** | Optional voice shell | Misty | P3 | PLANNED |

---
*Contract established by Gem. This document is the source of truth for ATF implementation.*
