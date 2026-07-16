# RobotRoss System Overview

## 1. Introduction
RobotRoss is an autonomous robotic artist platform designed to bridge AI creativity with physical execution. It uses a Huenit robotic arm to draw plotter-optimized SVGs or write calligraphy while providing poetic narration in the style of Bob Ross.

## 2. Core Architecture
The system follows a three-layer architecture:
- **Commerce Layer**: [[CommerceLayer]] handles order intake, queue management, and the competitive bidding system.
- **Orchestration Layer**: [[JobOrchestration]] (primarily `bob_ross.py`) manages the job lifecycle, narration, recording, and uploading.
- **Hardware Layer**: [[HardwareInterface]] provides low-level G-code control and calibration for the robot arm.

## 3. Key Subsystems
- [[CommerceLayer]]: Salesman API and order queue management.
- [[JobOrchestration]]: The brain of the artist side.
- [[HardwareInterface]]: Serial G-code control of the Huenit arm.
- [[OrderManagement]]: Polling and logging of drawing jobs on the Artist side.
- [[Narration]]: Local LLM-based poetic commentary.
- [[VideoProof]]: Automated OBS recording and YouTube uploading.

## 4. Key Integration Topics
- [[BiddingRules]]: Competitive overwrite rules and the 8x8 Wall of Fame.
- [[ShopifyIntegration]]: Webhooks, metadata write-back, and human e-commerce.
- [[VirtualsACP]]: Agentic commerce protocol for autonomous hiring.
- [[Calibration]]: Necessary startup procedures for hardware accuracy.
- [[Compliance]]: EU AI Act mapping and architectural traceability.

## 5. Hardware Requirements
- **Computer**: Mac Mini M4 (Apple Silicon, production/Shopify pipeline) or a Windows laptop (hackathon/demo build, browser-based Control Center)
- **Robot**: Huenit Robotic Arm
- **Cameras**: Reolink 4K (Main) + macOS Screen Capture (Board) — Mac Mini build only
- **Audio**: BlackHole 2ch for internal routing — Mac Mini build only

## 6. Software Stack
- **OS**: macOS (darwin) for Artist (production); Windows for the Mistral-hackathon build; Ubuntu (Linux) for Salesman.
- **LLM**: Mistral (`ministral-3:8b`, local via Ollama) — default as of the 2026-07 Windows/Mistral-hackathon build. Apertus 8B remains available as an explicit fallback (`--brain apertus`), not auto-triggered.
- **Agent Framework**: OpenClaw (Mac Mini production flow); `control_center.py` local web UI + ATF (`atf_local_server.py`) for the Windows hackathon build.
- **Utilities**: OBS Studio, ffmpeg, Python 3.12, Node.js

## 7. Uncertainty & Contradictions
- **Calibration Persistence**: Source code indicates calibration is required after every restart (`READY_FLAG` in `/tmp`), but some docs suggest it might be semi-persistent.
- **Pen Pressure**: Manual leveling of the table is mentioned as a physical requirement that software cannot currently compensate for.
- **Narration Latency**: Narration generation now runs asynchronously in a background thread (`bob_ross.py`, 2026-07-09) — the arm starts drawing on generic filler commentary immediately rather than blocking on the ~60-90s local LLM call, swapping to the real narration once it lands.

---
**Sources:**
- `AGENTS/CONTEXT/robot_ross_artist.md`
- `AGENTS/CONTEXT/robot_ross_salesman.md`
- `~/.openclaw/workspace/skills/robot-ross/bob_ross.py`
