# RobotRoss Source Corpus Manifest

This manifest describes the source material for the RobotRoss compiled wiki, as part of task #125. It is designed to be ingested by the Agentegra ATF pipeline defined in #124.

## 1. Core Documentation (Architecture & Vision)
*Priority: High — Foundation for the wiki.*

| Source Path | Type | Category | Contribution |
| :--- | :--- | :--- | :--- |
| `agentic-fleet-hub/AGENTS/CONTEXT/robot_ross_artist.md` | Doc | Arch | Detailed hardware/software stack for the physical robot. |
| `agentic-fleet-hub/AGENTS/CONTEXT/robot_ross_salesman.md` | Doc | Arch | Cloud infra, API endpoints, and order schema. |
| `salesman-cloud-infra/docs/ROBOT_ROSS_MANIFEST.md` | Doc | Arch | The "bits to atoms" philosophy and bidding rules. |
| `salesman-cloud-infra/README.md` | Doc | Arch | Deployment instructions and VPS path mapping. |

## 2. Artist Side (The "Hand")
*Located at: `~/.openclaw/workspace/skills/`*

| Source Path | Type | Category | Contribution |
| :--- | :--- | :--- | :--- |
| `robot-ross/bob_ross.py` | Code | Artist (Core) | Main job orchestrator, narration flow, and lock management. |
| `robot-ross/artist_poller.py` | Code | Artist (Core) | Polling daemon that bridges Cloud Queue to Local Worker. |
| `robot-ross/SKILL.md` | Doc | Ops | CLI usage, command flags, and manual job triggers. |
| `robot-ross/MEMORY.md` | Doc | Ops | Local developer notes and persistent facts. |
| `huenit/huenit_svg.py` | Code | Artist (HW) | SVG parsing and G-code translation for the Huenit arm. |
| `huenit/huenit_write.py` | Code | Artist (HW) | Calligraphy logic and font scaling. |
| `huenit/huenit_draw.py` | Code | Artist (HW) | Calibration and basic geometric primitives. |
| `huenit/ai_sketch.py` | Code | Artist (AI) | Claude Haiku integration for plotter-optimized SVGs. |
| `robot-ross/obs_manager.py` | Code | Artist (Int) | OBS WebSocket control for session recording. |
| `robot-ross/youtube_upload.py` | Code | Artist (Int) | YouTube Data API integration for proof-of-work. |
| `robot-ross/salesman_client.py` | Code | Artist (Int) | HTTP client for the Salesman cloud queue. |

## 3. Salesman Side (The "Brain")
*Located at: `~/projects/salesman-cloud-infra/`*

| Source Path | Type | Category | Contribution |
| :--- | :--- | :--- | :--- |
| `opt/salesman-api/server.mjs` | Code | Salesman (API) | Main Node.js server, queue logic, and bidding engine. |
| `opt/salesman-api/offering.json` | Config | Salesman (Int) | Virtuals ACP marketplace definition. |
| `opt/salesman-api/scoreboard.html` | Code | Salesman (FE) | Public-facing physical wall status grid. |
| `opt/salesman-api/dashboard.html` | Code | Salesman (FE) | Private administrative interface for order management. |
| `Caddyfile` | Config | Salesman (Infra) | Reverse proxy and SSL termination rules. |

## 4. Observations & Gap Analysis

### Gaps
1.  **Hardware Troubleshooting**: No unified guide for physical failure modes (e.g., pen drying, paper jams, belt slipping).
2.  **Recovery Procedures**: Lack of documented steps for resuming interrupted jobs or manual YouTube proof injection.
3.  **ACP Implementation**: The `handlers.ts` for Virtuals Protocol is currently a scaffold (TODO: Gemini).
4.  **Audio Routing**: BlackHole setup is mentioned but lacks a step-by-step config doc for the Mac Mini.

### Conflicts
- **Documentation Redundancy**: `robot_ross_artist.md` (Fleet Hub) and `ROBOT_ROSS_MANIFEST.md` (Salesman Repo) have significant overlap. Recommend consolidating into a single "Source of Truth" during wiki generation.
- **Version Skew**: Some paths in `ROBOT_ROSS_MANIFEST.md` refer to `/home/openclaw/` while the Mac Mini migration uses `/Users/miguelrodriguez/`.

## 5. Wiki Generation Roadmap

### First Pass (Core Knowledge)
- **Inputs**: `robot_ross_artist.md`, `robot_ross_salesman.md`, `SKILL.md`, `bob_ross.py` (docstrings), `server.mjs` (routes).
- **Goal**: Functional overview, API reference, and basic operator manual.

### Second Pass (Hardware & Low-Level)
- **Inputs**: `huenit_*.py`, `calibration.json`, `obs_manager.py`.
- **Goal**: Deep dive into G-code generation, calibration math, and video production pipeline.

### Third Pass (Integration & Marketplace)
- **Inputs**: `offering.json`, `youtube_upload.py`, `ROBOT_ROSS_MANIFEST.md`.
- **Goal**: Guide for 3rd party agents to hire RobotRoss and verify Proof of Work.

---
*Manifest produced by Gem (Gemini CLI) for task #125.*
