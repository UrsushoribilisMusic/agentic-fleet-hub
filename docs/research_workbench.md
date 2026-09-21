# Research Workbench: Source and Claim Ledger Guide

## Purpose & Philosophy

The **Research Workbench** is the evidence ledger for research-heavy Flotilla Council goals. Whether analyzing customer accounts for prospect intelligence, researching competitive claims for sales assets, drafting public technical articles, or producing AI tech shorts:

> **Accuracy is the moat.** Claims require source discipline. Unverified assertions must never be stored or presented as established facts.

Every claim produced by fleet agents in research-heavy workflows must be auditable, grounded, and traceable to a source.

---

## Data Model

The Research Workbench is backed by two PocketBase collections (with an automatic file-backed fallback at `AGENTS/COUNCIL/research/{goal_id}.json` when working offline).

### 1. `research_sources`

Represents an upstream publication, filing, repository, or interview.

| Field | Type | Required | Notes |
|---|---|---|---|
| `goal_id` | relation → `goals` | Yes | Parent council goal |
| `url` | text | Yes | Source URL (HTTP/HTTPS/file) |
| `title` | text | Yes | Publication or document title |
| `author` | text | No | Organization, author, or creator |
| `source_type` | select | Yes | `primary`, `secondary`, `tertiary`, `interview`, `internal_telemetry`, `other` |
| `reliability` | select | Yes | `high`, `moderate`, `low`, `unknown` |
| `agent` | text | No | Agent that cataloged the source (e.g. `gem`, `clau`, `codi`, `misty`) |
| `notes` | text | No | Context, caveats, methodology |

### 2. `research_claims`

Represents an extracted assertion, metric, quote, or factual proposition.

| Field | Type | Required | Notes |
|---|---|---|---|
| `goal_id` | relation → `goals` | Yes | Parent council goal |
| `extracted_claim` | text | Yes | The factual proposition or finding |
| `confidence` | select | Yes | `high`, `moderate`, `low`, `speculative` |
| `verification_status` | select | Yes | `unverified`, `verified`, `contested`, `refuted` |
| `source_id` | relation → `research_sources` | No | Linked source record |
| `source_url` | text | Conditional | **Mandatory** if `usable_in_public_copy` is true |
| `source_title` | text | No | Publication or document title |
| `source_type` | select | No | `primary`, `secondary`, `tertiary`, `interview`, `internal_telemetry`, `other` |
| `quote_snippet` | text | No | Verbatim excerpt from source for quick peer audit |
| `usable_in_public_copy` | bool | No | Eligible for public articles, tech shorts, or sales collateral |
| `needs_human_review` | bool | No | High-stakes, contentious, or uncertain claims requiring Miguel review |
| `reviewed_by` | text | No | Peer agent or human who verified the claim |
| `agent` | text | No | Agent extracting the claim |
| `notes` | text | No | Contextual qualifiers or caveats |

---

## Core Rules for Fleet Agents

1. **Do Not Store Unverified Claims as Facts**:
   - New claims default to `verification_status: "unverified"`.
   - A claim can only be marked `verified` if it has a primary or reliable source URL and an evidence quote snippet or methodology note.
2. **Confidence Tiers**:
   - `high`: Verified from primary documentation, official filings, or direct instrumentation.
   - `moderate`: Reputable secondary reporting or consensus across multiple industry sources.
   - `low`: Single unconfirmed source, marketing claim, or ambiguous statement.
   - `speculative`: Inference, hypothesis, projection, or agent estimate.
3. **Public-Facing Discipline**:
   - If `usable_in_public_copy` is true, a valid `source_url` is **mandatory**.
   - Speculative claims (`confidence: "speculative"`) and refuted claims **cannot** be marked usable in public copy.
4. **Prefer Primary Sources**:
   - Always prioritize SEC filings, official documentation, source code repositories, and raw telemetry over secondary summaries or aggregator articles.

---

## Agent CLI Usage (`fleet/research_ledger.py`)

Agents can record and audit sources and claims using `fleet/research_ledger.py`.

### 1. Recording a Source
```bash
python3 fleet/research_ledger.py record-source \
  --goal "begxm6xs2otoeyx" \
  --url "https://investor.nvidia.com/sec-filings/10-k" \
  --title "NVIDIA FY2026 Annual Report (Form 10-K)" \
  --type primary \
  --reliability high \
  --agent misty \
  --notes "Item 1 Business Overview, Data Center revenue breakdown"
```

### 2. Recording a Claim
```bash
python3 fleet/research_ledger.py record-claim \
  --goal "begxm6xs2otoeyx" \
  --claim "Data Center revenue grew 112% year-over-year driven by Hopper and Blackwell architectures." \
  --url "https://investor.nvidia.com/sec-filings/10-k" \
  --title "NVIDIA FY2026 10-K" \
  --source-type primary \
  --confidence high \
  --status verified \
  --quote "Data Center revenue was $47.5B, up 112% from the prior fiscal year..." \
  --public \
  --agent misty
```

### 3. Verifying / Critiquing an Existing Claim (Round 2 Peer Review)
```bash
python3 fleet/research_ledger.py verify-claim \
  --claim-id "clm_0001" \
  --status verified \
  --reviewer clau \
  --notes "Cross-checked against SEC EDGAR filing. Citation verified verbatim."
```

### 4. Auditing a Goal's Evidence Trail
```bash
python3 fleet/research_ledger.py audit --goal "begxm6xs2otoeyx"
```
Output:
```
=== RESEARCH EVIDENCE AUDIT FOR GOAL: begxm6xs2otoeyx ===
Total Sources: 4
Total Claims:  12
Verification:  {'verified': 9, 'unverified': 2, 'contested': 1, 'refuted': 0} (75.0% verified)
Confidence:    {'high': 7, 'moderate': 4, 'low': 1, 'speculative': 0}
Public Ready:  8
Needs Review:  1
Integrity Gap: NONE (Auditable)
```

### 5. Exporting an Evidence Ledger into Markdown
```bash
python3 fleet/research_ledger.py export-markdown --goal "begxm6xs2otoeyx"
```

---

## Fleet Hub API Endpoints

The Fleet Hub backend (`salesman-cloud-infra/opt/salesman-api/server.mjs`) provides standard REST endpoints:

- `GET /fleet/api/council/research/sources?goal_id=<id>`: Fetch all registered sources.
- `POST /fleet/api/council/research/sources`: Register a new source.
- `GET /fleet/api/council/research/claims?goal_id=<id>&confidence=<tier>&status=<status>&public_only=true`: Fetch filtered claims.
- `POST /fleet/api/council/research/claims`: Create a claim (validates confidence, URL for public copy).
- `PATCH /fleet/api/council/research/claims/:id`: Update claim verification status or flags.

### Curl Example: Add Claim via API
```bash
curl -s -X POST "http://localhost:3001/fleet/api/council/research/claims" \
  -H "Content-Type: application/json" \
  -d '{
    "goal_id": "begxm6xs2otoeyx",
    "extracted_claim": "On-device Ministral 3B achieves 38 tokens/sec on Apple M4 Neural Engine.",
    "source_url": "https://flotilla.cc/benchmarks/m4",
    "source_title": "Flotilla On-Device Eval Suite",
    "source_type": "internal_telemetry",
    "confidence": "high",
    "verification_status": "verified",
    "usable_in_public_copy": true,
    "agent": "gem"
  }'
```

---

## Definition of Done Verification

1. **Evidence Trail Preserved**: Claims persist with exact URL, author/source title, quote snippet, and confidence tier.
2. **Auditability**: Any agent can audit claims by running `python3 fleet/research_ledger.py audit --goal <goal_id>` or inspecting the Fleet Hub Council Room Research Workbench table.
3. **Public Gate**: Unverified or speculative claims are blocked from being marked `usable_in_public_copy`.
