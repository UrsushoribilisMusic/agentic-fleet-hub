# Lifelore iOS — Agent Context

*Previously named PrivateCore. App renamed to Lifelore on 2026-05-03. Xcode target still named `PrivateCore` until an authorised rename. Read this before picking up any PC-* ticket. Updated May 2026.*

---

## What is Lifelore?

A privacy-first on-device AI life journal for iPhone. The app turns your photos, calendar, trips, and notes into a searchable personal narrative — all processed locally, no cloud required.

**Sprint 6 (active as of May 2026):** Styles system, PDF export, onboarding flow, StoreKit 2 freemium model.

**Phase 1 goal (complete):** Working app installed on physical iPhone. Semantic photo/calendar search, wiki-style auto-generated day summaries, trip detection. v0.1.0 shipped.

---

## Repo & Links

| Resource | Value |
|---|---|
| GitHub repo | https://github.com/UrsushoribilisMusic/privatecore-ios |
| Local path | `~/projects/private-core/PrivateCore/` |
| Branch | `main` (not master) |
| Issues / Kanban | https://github.com/UrsushoribilisMusic/privatecore-ios/issues |
| Architecture doc | `~/projects/private-core/PrivateCore/ARCHITECTURE.md` |
| Mission Control | `~/projects/private-core/PrivateCore/MISSION_CONTROL.md` |
| Standups | `~/projects/private-core/PrivateCore/standups/` |

**Git pull command:**
```bash
cd ~/projects/private-core/PrivateCore && git pull origin main
```

---

## Tech Stack (locked for Phase 1)

| Component | Choice | Rationale |
|---|---|---|
| Inference | MLX Swift | Native Apple Silicon — same weights on Mac Mini (dev) and iPhone (prod) |
| Vector store | sqlite-vec | Zero cloud dependency, no FAISS build complexity |
| Embedding model | MiniLM-L6-v2 CoreML (~22MB) | Always-on, no hot-swap, handles all text types |
| OCR | Apple Vision framework | Free, fast, Japanese/Chinese/Korean native |
| Database | SQLite (single file, App Group shared) | Portable, inspectable, FTS5 built in |
| UI | SwiftUI | Target iOS 17.6+ |
| Min device | iPhone 15 Pro (8GB RAM) | Required for 7B model without excessive swap |

---

## Three Pillars

**Pillar 1 — Model Runtime** (Codi owns)
- `MLXEngine`: `generate(prompt: String) -> AsyncStream<String>`
- `ModelManager`: download, store, activate large models (Mistral 7B, Qwen2.5-VL, Gemma 3 4B)
- `ModelRouter`: hot-swap between text and vision models (cannot coexist in 8GB RAM)
- 1B model bundled in app — always available without download

**Pillar 2 — iOS Data Access** (Clau owns)
- `PhotoLibraryService`: PHAsset metadata → SQLite (no photo copying — pointer model)
- `CalendarService`: EKEvent → SQLite
- `HealthService`: steps, sleep, heart rate → SQLite daily aggregates
- `VectorStore`: sqlite-vec wrapper for semantic search

**Pillar 3 — Vision Pipeline** (Gem owns)
- `OCRService`: Apple Vision → extracted text stored in SQLite
- `EmbeddingService`: MiniLM CoreML → 384-dim vectors → VectorStore
- `VLMService`: Qwen2.5-VL 3B via MLXEngine for visual understanding

---

## Agent Ticket Assignments

| Agent | Tickets | Notes |
|---|---|---|
| **Clau** | PC-000, PC-004, PC-005, PC-006, PC-009 | Repo init + full data layer + context injection |
| **Codi** | PC-001, PC-002, PC-003, PC-007 | MLX engine + sqlite-vec — **critical path blockers** |
| **Gem** | PC-010, PC-011, PC-012 | Vision OCR, CoreML embedding conversion, VLM |
| **Misty** | PC-014, PC-015, PC-018 | Share Extension, PDF ingestion, auto-tagging |
| **Miguel** | PC-008, PC-013, PC-016, PC-017 | App shell, onboarding, search, backlinks — device only |

---

## Critical Path

```
PC-007 sqlite-vec iOS arm64 build ──┐
                                    ├──► PC-011 Embeddings ──► PC-016 Search
PC-001 MLX 1B engine ───────────────┤
                                    ├──► PC-009 First integration (THE DEMO)
PC-004 PHPhotoLibrary ──────────────┘
PC-005 EventKit ────────────────────┘
```

**Codi must validate PC-007 (sqlite-vec iOS arm64) before anyone writes code that depends on VectorStore.** Fallback: raw BLOB vectors + Swift cosine similarity for < 10K items.

---

## Mac Mini Testing

Ollama is installed on the Mac Mini. Use it to validate prompts before any Xcode work:

```bash
ollama run qwen2.5:7b          # Available now
ollama run gemma:latest        # Available now
ollama run mistral:7b-instruct-q4_K_M  # Pull first: ollama pull mistral:7b-instruct-q4_K_M
```

Test context injection prompts here before device work. Getting PC-009 prompt engineering right on the Mac Mini is the highest-leverage Sprint 1 activity.

---

## Key Risks

1. **sqlite-vec iOS arm64** — unvalidated. Codi checks this first. Fallback exists.
2. **App Group entitlement** — configure in Apple Developer portal before Share Extension code (PC-014). Miguel does this.
3. **Qwen2.5-VL preprocessing** — MLX iOS path is less documented. Gem researches before writing PC-012.
4. **Thermal throttling** — all background workers use batch-20-pause-1s pattern. Non-negotiable.
5. **Model weights in repo** — `.gitignore` excludes `*.gguf`, `*.safetensors`, `*.mlpackage`. Never commit weights.

---

## Xcode Project Structure

```
~/projects/private-core/PrivateCore/
├── PrivateCore.xcodeproj/
├── PrivateCore/
│   ├── PrivateCoreApp.swift
│   ├── ContentView.swift
│   └── Assets.xcassets/
├── ARCHITECTURE.md
├── MISSION_CONTROL.md
├── README.md
├── standups/
└── .gitignore
```

Agents draft Swift files and push to the repo. Miguel wires them into Xcode targets, adds entitlements, tests on physical device.

---

## Sprint 6 Focus Areas

| Area | What's being built |
|---|---|
| Styles | Per-view visual style switching (day/wiki/trip views) |
| PDF export | Export day summaries and trip reports as shareable PDFs |
| Onboarding | First-launch flow: permissions, style selection, first sync |
| StoreKit 2 | Freemium gating — free tier limited, Pro unlocks everything |

---

*BigBear Engineering GmbH · Lifelore iOS (formerly PrivateCore) · May 2026*
