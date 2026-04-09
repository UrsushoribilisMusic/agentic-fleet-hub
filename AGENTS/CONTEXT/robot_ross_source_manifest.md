# RobotRoss Source Corpus Manifest

**Ticket ID:** #125 [ATF-2]
**Date:** 2026-04-09
**Status:** Completed Manifest for Compiled Wiki Generation
**Project:** RobotRoss Showcase

---

## 1. Overview
This manifest inventories the source documentation and code corpus for RobotRoss. It is designed to feed the "Compiled Wiki" generator (#128) by providing a structured map of available knowledge across the Artist (local), Salesman (cloud), and Integration (ACP) layers. It also bridges the gap between the "Artist" demo and the "Agentegra" industrial vision.

---

## 2. Source Inventory

### 2.1 Documentation & Architecture (Priority: High)
These sources provide the conceptual framework and should be the primary inputs for the wiki.

| Path | Category | Contribution to Wiki | Priority |
| :--- | :--- | :--- | :--- |
| `/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/CONTEXT/robot_ross_artist.md` | Architecture | Core Artist hardware/software stack, job lifecycle, and local setup. | P0 |
| `/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/CONTEXT/robot_ross_salesman.md` | Architecture | Cloud backend API, Shopify integration, and order schema. | P0 |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/docs/ROBOT_ROSS_MANIFEST.md` | Manifesto | Vision, philosophy, and brand identity. | P0 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/YOUTUBE_SCRIPT.md` | Narrative | Narrative structure, "Bob Ross" persona details, and build journey. | P1 |
| `/Users/miguelrodriguez/projects/agentic-fleet-hub/AGENTS/CONTEXT/agentegra.md` | Context | Business context: Agentegra Layer 1/2 positioning and "Sovereign AI". | P1 |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/agentegra/site/robotross.html` | Vision | Marketing copy and the critical "Pen as Drill Bit" industrial analogy. | P1 |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/README.md` | Ops | Cloud infrastructure deployment and Caddy/Systemd configuration. | P1 |

### 2.2 Skill Documentation (Priority: Medium)
Usage guides and command references extracted from skill definitions.

| Path | Category | Contribution to Wiki | Priority |
| :--- | :--- | :--- | :--- |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/SKILL.md` | Usage | CLI command reference (write, sketch, fetch) and job lifecycle. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/huenit/SKILL.md` | Low-Level | Manual control, calibration, and teach/replay instructions. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/MEMORY.md` | Dev Notes | Historical context and technical decisions made during development. | P2 |

### 2.3 Artist Source Code (Priority: Medium)
Source code to be parsed for logic, CLI arguments, and functional behavior.

| Path | Category | Contribution to Wiki | Priority |
| :--- | :--- | :--- | :--- |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/bob_ross.py` | Code | Main orchestrator logic, lock management, and job flow. | P0 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/artist_poller.py` | Code | Polling daemon behavior and retry logic. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/youtube_upload.py` | Code | Video processing (ffmpeg) and YouTube API integration. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/obs_manager.py` | Code | OBS WebSocket control and scene switching logic. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/robot-ross/wall_snapshot.py` | Code | Wall camera capture, cropping, and snapshot upload logic. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/huenit/huenit_svg.py` | Code | SVG to G-Code transformation and arm kinematics. | P0 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/huenit/huenit_draw.py` | Code | Calibration routines and basic shape primitives. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/huenit/huenit_write.py` | Code | Calligraphy and text-to-stroke logic. | P1 |
| `/Users/miguelrodriguez/.openclaw/workspace/skills/huenit/ai_sketch.py` | Code | Prompt-to-SVG generation logic (Claude Haiku). | P1 |

### 2.4 Cloud Backend Source Code (Priority: Medium)
Backend logic for queue management and marketplace integrations.

| Path | Category | Contribution to Wiki | Priority |
| :--- | :--- | :--- | :--- |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/opt/salesman-api/server.mjs` | Code | API endpoints, Shopify webhook handling, and grid logic. | P0 |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/opt/salesman-api/offering.json` | Config | Virtuals ACP offering definition (The "Marketplace Contract"). | P0 |
| `/Users/miguelrodriguez/projects/salesman-cloud-infra/tests/server.test.mjs` | Tests | Functional specifications for API behavior and edge cases. | P2 |

---

## 3. Documentation Gaps & Conflicts

### 3.1 Gaps
- **Hardware Maintenance:** No documentation on physical pen replacement, paper alignment, or arm tensioning.
- **Error Recovery:** While `bob_ross.py` handles locks, there is no guide for manual recovery if the arm stalls or loses power mid-draw.
- **ACP Implementation:** `handlers.ts` is noted as a "scaffold" in `robot_ross_salesman.md`—the wiki will reflect an incomplete integration for Virtuals Protocol.
- **Network Diagrams:** Visual representation of the data flow between Mac Mini, VPS, and Shopify is missing in markdown (though exists in Mermaid).
- **Industrial Transition:** Missing a "How-to" guide for swapping the pen with a drill bit (the "Pen as Drill Bit" analogy needs code-level mapping).

### 3.2 Conflicts
- **Grid Size:** Historically referenced as 10x10 (100 slots) in early web copy, but now standardized at 8x8 (64 slots) across all current manifests and scripts.
- **Offering Mapping:** A known bug exists in `server.mjs` where `svg` maps to `write` instead of `sketch`. The wiki should document both the "intended" and "actual" behavior.
- **Local vs Cloud Model:** `agentegra.md` mentions Apertus 7B (Swiss open-weights), while `robot_ross_artist.md` mentions Apertus 8B. The wiki should clarify the exact model used in production (likely 8B).

---

## 4. Recommendations for Wiki Generation

### First Pass (P0/P1 Documentation)
- **Home Page:** Extract vision from `ROBOT_ROSS_MANIFEST.md` and `agentegra.md`.
- **The "Pen as Drill Bit" Analogy:** Dedicate a section to the industrial transition as described in `robotross.html`.
- **System Architecture:** Synthesize `robot_ross_artist.md` and `robot_ross_salesman.md`.
- **API Reference:** Generate from `server.mjs` endpoints and `offering.json`.

### Second Pass (Code Enrichment)
- **Developer Guide:** Extract functional details from `bob_ross.py` and `huenit_svg.py`.
- **Ops Manual:** Compile from `README.md`, `SKILL.md` files, and `systemd` units.
- **Narration Engine:** Explain the Bob Ross persona logic using `YOUTUBE_SCRIPT.md`.

### Future Enrichment
- **Compliance Mapping:** Map RobotRoss components to EU AI Act requirements (Transparency, Human Oversight, Audit Logs).
- **Log Synthesis:** Incorporate `poller.log` and `bob_ross.log` patterns to show "Live Status" in the wiki.

---

## 5. Schema Alignment
This manifest follows the **ATF-1** schema contract for Source Manifests:
- **Identifier:** `robot-ross-v1`
- **Corpus Root:** `/Users/miguelrodriguez/projects/` and `/Users/miguelrodriguez/.openclaw/`
- **Output Target:** `RobotRoss Wiki`
