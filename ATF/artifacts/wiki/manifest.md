# RobotRoss Source Corpus Manifest

**Date:** 2026-04-09
**Owner:** Gem
**Status:** Initial Inventory + Wiki Generation (Pass 1)

## 1. Core Logic (~/.openclaw/workspace/skills/robot-ross/)

| File | Purpose | Size |
| :--- | :--- | :--- |
| `bob_ross.py` | Main job orchestrator | 42,103 bytes |
| `artist_poller.py` | Polling daemon for Salesman API | 11,093 bytes |
| `salesman_client.py` | HTTP client for Salesman API | 6,042 bytes |
| `obs_manager.py` | OBS WebSocket integration | 7,980 bytes |
| `youtube_upload.py` | YouTube upload + OAuth | 5,342 bytes |
| `order_log.py` | Excel ledger management | 5,015 bytes |
| `wall_snapshot.py` | Board photo capture + upload | 4,627 bytes |
| `SKILL.md` | Skill definition and usage | 3,219 bytes |

## 2. Huenit Hardware Interface (~/.openclaw/workspace/skills/huenit/)

| File | Purpose | Size |
| :--- | :--- | :--- |
| `huenit_svg.py` | SVG to arm movements (G-code) | 18,751 bytes |
| `huenit_write.py` | Text calligraphy | 18,834 bytes |
| `huenit_draw.py` | Basic shapes + calibration | 14,365 bytes |
| `huenit_jog_control.py` | Manual jog control | 15,485 bytes |
| `huenit_teach_replay.py` | Recording/replaying arm paths | 13,622 bytes |
| `ai_sketch.py` | Claude Haiku SVG generation | 4,970 bytes |
| `image_to_svg_potrace.py` | Image vectorization (Potrace) | 11,302 bytes |
| `image_to_svg.py` | Image vectorization (VTracer) | 8,817 bytes |
| `quickdraw_to_svg.py` | QuickDraw data to SVG | 10,902 bytes |

## 3. Documentation (AGENTS/CONTEXT/)

| File | Purpose | Size |
| :--- | :--- | :--- |
| `robot_ross_artist.md` | Comprehensive artist-side overview | 7,688 bytes |
| `robot_ross_salesman.md` | Salesman API side overview | 9,082 bytes |
| `agentegra.md` | Project branding and business context | 9,504 bytes |

## 4. Compiled Wiki Structure (ATF_WIKI/)

### Overview
- `Overview.md`: Main entry point and architecture summary.

### Subsystems
- `CommerceLayer.md`: Cloud API, bidding, and queue management.
- `JobOrchestration.md`: Main Artist-side brain (`bob_ross.py`).
- `HardwareInterface.md`: Low-level G-code control of the Huenit arm.
- `OrderManagement.md`: Polling and logging of drawing jobs.

### Topics
- `BiddingRules.md`: Wall of Fame rules and the 120% overwrite logic.
- `ShopifyIntegration.md`: Webhooks, metadata write-back, and human commerce.
- `VirtualsACP.md`: Agentic commerce protocol for autonomous hiring.
- `Calibration.md`: Hardware startup and calibration procedures.
- `Narration.md`: Local LLM poetic commentary logic.
- `VideoProof.md`: Automated recording and YouTube uploading.
