# Robot Ross — Artist Side: Architecture, Setup & Status

**Date:** 2026-03-07
**Version:** Current production
**Hardware:** Mac Mini M4 (192.168.1.39, local network)

---

## 1. Overview

Robot Ross is a physical AI artist. It receives drawing orders via a cloud queue (Salesman API), draws them in real time using a Huenit robotic arm on paper, narrates the session using Swiss AI (Apertus 8B), records the full session via OBS Studio, and uploads the video to YouTube as proof-of-work.

The system is fully autonomous — from order intake to YouTube upload — with no human intervention required for normal operation.

---

## 2. Hardware

| Component | Details |
|-----------|---------|
| Computer | Mac Mini M4 |
| Robot Arm | Huenit (USB serial, `/dev/cu.usbserial-310`) |
| Main Camera | Reolink 4K IP camera (192.168.1.40) via RTSP |
| Board Camera | Secondary camera via macOS Screen Capture in OBS |
| Drawing Surface | 125×125mm paper, mounted on a flat surface |
| Wall of Fame | Physical 8×8 corkboard (64 slots, A1–H8, each 10×10cm) |

---

## 3. Software Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Agent brain | OpenClaw + Claude Haiku | Interprets Telegram messages, routes commands |
| Narration | Apertus 8B (Ollama, local) | Bob Ross-style voice narration |
| TTS | Kokoro (local) + macOS `say` fallback | Text to speech |
| Drawing | bob_ross.py | Main orchestrator for all draw jobs |
| Arm control | huenit_svg.py, huenit_write.py, huenit_draw.py | Serial G-code to Huenit arm |
| AI sketch | ai_sketch.py (Claude Haiku API) | Generates plotter-optimised SVGs from prompts |
| Recording | OBS Studio (WebSocket port 4455) | Records full drawing session |
| Video upload | youtube_upload.py (Google OAuth2) | Uploads MP4 to YouTube as proof-of-work |
| Order polling | artist_poller.py | Polls Salesman API every 3 minutes for new orders |
| Order ledger | order_log.py + orders.xlsx | Local record of all jobs |

---

## 4. Key File Paths

```
~/.openclaw/workspace/skills/robot-ross/
  bob_ross.py          — main job orchestrator
  artist_poller.py     — polling daemon
  salesman_client.py   — HTTP client for Salesman API
  obs_manager.py       — OBS WebSocket integration
  youtube_upload.py    — YouTube upload + OAuth
  ai_sketch.py         — Claude Haiku SVG generation (in skills/huenit/)
  wall_snapshot.py     — Board photo capture + upload
  wall_config.json     — Crop config {"crop": [512, 80, 1481, 1033]}
  order_log.py         — Excel ledger management
  orders.xlsx          — Order history
  bob_ross.log         — Full operation log
  poller.log           — Polling activity log
  .salesman_config     — API URL + Bearer token (gitignored)
  .youtube_token.json  — Google OAuth token (gitignored)

~/.openclaw/workspace/skills/huenit/
  huenit_svg.py        — SVG to arm movements
  huenit_write.py      — Text calligraphy
  huenit_draw.py       — Basic shapes + calibration
  ai_sketch.py         — AI sketch generator
```

---

## 5. Job Types

| Action | Input | Description |
|--------|-------|-------------|
| `sketch "PROMPT"` | Text prompt | Claude Haiku generates SVG → draws |
| `write "TEXT"` | Text string | Calligraphy, auto-scaled to 125mm |
| `svg FILE` | SVG file path | Draws local or ~/Downloads SVG directly |
| `fetch URL` | HTTPS URL | Downloads and draws remote SVG |
| `image FILE` | Photo path | vtracer vectorises photo → draws |
| `draw circle/square` | Shape name | Basic geometric shapes |

All sketch/SVG jobs automatically include:
- **Crop corner marks**: L-shaped marks at top-right and bottom-left corners for paper cutting
- **R.R signature**: Small stick-letter signature at bottom-right of drawing

---

## 6. Full Job Lifecycle (Automated Orders)

```
artist_poller.py polls GET /salesman/orders/incoming?status=new every 3 min
  ↓
Order claimed + acked via Salesman API
  ↓
bob_ross.py sketch "PROMPT" --direct --buyer "NAME"
  ↓
1. Readiness check (arm connected, calibrated, Ollama running)
2. Job lock acquired (/tmp/robot_ross_running.lock)
3. Claude Haiku generates SVG (ai_sketch.py) — ~200 input / ~900 output tokens
4. Corner marks + R.R signature injected into SVG
5. OBS switches to Workspace scene, starts recording (record-only mode)
6. caffeinate prevents Mac sleep
7. Apertus 8B generates narration JSON {intro, commentary[], outro}
8. Warning beep — stand clear
9. OBS switches to Artist scene (arm camera live)
10. Voice intro plays
11. Arm draws (huenit_svg.py) — ~2-5 minutes depending on complexity
12. Commentary spoken in parallel during drawing
13. Voice outro plays
14. OBS stops, recording saved to ~/Movies/ (.mov)
15. ffmpeg trims dead air before last beep
16. ffmpeg remuxes .mov → .mp4 (moov atom to front for YouTube)
17. YouTube upload → returns video URL
18. order_log.py records video URL
19. Salesman API notified: complete(proofOfWorkUrl=youtubeUrl)
20. Job lock released
```

---

## 7. OBS Setup

- **Scenes**: Workspace (intro/outro, full arm cam), Artist (arm cam + status overlay)
- **Sources**: Robot_Main_Cam (Reolink RTSP), Robot_Status (Text FreeType 2), macOS Screen Capture (board camera, Scene 2)
- **WebSocket**: port 4455, password Ross2026
- **Audio**: BlackHole 2ch routes Mac Mini system audio into OBS; camera RTSP audio muted on job start
- **LaunchAgent**: OBS auto-starts on login (`com.robotross.obs.plist`)

---

## 8. Wall Snapshot

After pinning a completed drawing to the Wall of Fame:

```bash
/usr/bin/python3 wall_snapshot.py
# or use Desktop shortcut: Wall Snapshot.command
```

- Captures OBS `macOS Screen Capture` source via WebSocket
- Crops to board area (box: [512, 80, 1481, 1033] → 969×953px)
- HTTPS POSTs JPEG to `https://api.robotross.art/wall/snapshot`
- Visible at: `https://api.robotross.art/scoreboard`

---

## 9. Startup & Operations

**Poller LaunchAgent** auto-starts on login:
```
~/Library/LaunchAgents/com.robotross.poller.plist
```

**Desktop shortcuts:**
- `Calibrate Robot Ross.command` — run at start of each session
- `Start Poller.command` — if poller needs manual restart
- `Stop Robot Ross.command` — SIGTERM, arm lifts pen safely
- `Wall Snapshot.command` — capture + upload board photo
- `Check Robot Ross.command` — readiness check

**Manual job:**
```bash
cd ~/.openclaw/workspace/skills/robot-ross
/usr/bin/python3 bob_ross.py sketch "a lighthouse" --direct --buyer "Alice"
```

---

## 10. Calibration

Must be run at the start of each physical session (after robot restart):
```bash
/usr/bin/python3 ~/.openclaw/workspace/skills/huenit/huenit_draw.py calibrate
```
- Z_UP = 6.0mm (pen-up height, confirmed working)
- Drawing area capped at 125mm in all directions

---

## 11. Current Status

| Component | Status |
|-----------|--------|
| Arm drawing | ✅ Working |
| AI sketch (Claude Haiku) | ✅ Working |
| OBS recording | ✅ Working |
| YouTube upload | ✅ Working |
| Voice narration (Apertus) | ✅ Working |
| Audio routing (BlackHole) | ✅ Working |
| Order polling (Salesman) | ✅ Working |
| Drawing markers + signature | ✅ Working |
| Wall snapshot | ✅ Working |
| Telegram control | ✅ Working |

---

## 12. Known Limitations & Open Work

- **Calibration required after every restart** — no auto-calibration
- **Table must be level** — uneven surface causes inconsistent pen pressure
- **One job at a time** — job lock prevents concurrent draws
- **Image action (vtracer)** — produces too many segments on complex photos; potrace explored but parked
- **Laser engraving** — M3/M5 G-code module planned but not started
- **Robot eyes** — K210 camera module planned, parked
