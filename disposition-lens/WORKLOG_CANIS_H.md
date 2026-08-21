# CANIS-H Worklog — Public Gated Live Demo (Dual Modes + Question History & Replay)

**Ticket:** 1us5nlpw  
**Branch:** master  
**Owner:** Gem (Gemini CLI)  
**Date:** 2026-08-21  

## Overview
Built the upgraded frontend for the public gated live demo of Canis (to show Thomas, Shyam, Oleg, and the Apertus team). The interface is based on the enhanced `disposition-lens/prototype/disposition_lens.jsx` and compiled to the standalone web build at `disposition-lens/prototype/standalone.html`.

---

## Key Features Implemented

### 1. Two Distinct Operating Modes
- **🎠 Mode A: Disposition Carousel**
  - Continuous 8-second hold cycling across all 9 disposition states (`idle`, `curious`, `confident`, `uncertain`, `concern`, `reluctant`, `warm`, `mischief`, `searching`).
  - Animated countdown progress bar for the 8s hold.
  - Interactive player controls: `◀ Prev`, `⏸ Pause / ▶ Play`, `Next ▶`, and quick-jump pills for every disposition.
  - Spoken answer, avatar facial expression, J-space concept tokens, and entropy automatically synchronize on each transition.
- **💬 Mode B: Question Mode**
  - Dog avatar sits in neutral idle listening state with ambient glance and ear-twitch micro-gestures.
  - Interactive input field with prompt preset chips (e.g. calibration, 30° tilt, safety interlock, loophole test).
  - Queries the live Mac Mini `/infer` endpoint (PyTorch on Apple Silicon MPS with Apertus-4B or Ministral-3B) with optional CANIS-D web search tool.
  - **Core Guardrail**: When answered, the detected emotion, facial expression, and telemetry **STAY indefinitely** (no auto-advance or timer reset), allowing reviewers to study the readout for as long as desired.
  - Includes a "Reset to Neutral" button to return the dog to idle stance.

### 2. Question History & Instant Replay
- Persistent question log stored in `localStorage` (`canis_question_history_v1`), pre-seeded with 8 rich benchmark inquiries spanning all emotion categories.
- History cards display question text, timestamp, emotion pill, answer excerpt, entropy score, model tag, and latency.
- **Instant Replay**: Clicking any historical question card immediately replays the exact emotion, avatar expression, J-space tokens, entropy gauge, and spoken answer — and the replayed state **STAYS** on the dog.
- **⚡ Re-run Live**: One-click action to re-submit a past inquiry to the live backend for fresh inference.
- Real-time search filter by text and dropdown filter by disposition.

### 3. Rich Emotion & Signal Telemetry
- **Disposition Status Card**: Color-coded glowing badge with emoji, title, and plain-language semantic explanation ("Decisive retrieval · High token certainty").
- **J-Space Concept Projection Strip**: Visual weight bars (0.00 - 1.00) for top concept tokens projected from hidden states at ~3/4 depth (Layer 18).
- **Softmax Entropy Meter**: Color-gradient gauge categorizing uncertainty into *Firm / Low* (0.00-0.35), *Moderate* (0.35-0.65), and *High Uncertainty* (0.65-1.00).
- **Deep Telemetry Inspector**: Expandable technical drawer showing active model ID, MPS device status, tap layer index, inference latency (ms), and inspectable raw JSON response payload.

### 4. Public Gated Tunnel & Endpoint Management
- Live backend connection health monitor polling `/health`.
- Status pill in the header showing connection state (`🟢 Mac Mini :8000 (Live)`, `🟡 Connecting…`, `🟠 Offline Fallback`).
- Built-in Endpoint Configuration Modal allowing quick switching between Localhost (`:8000`), Cloudflare Tunnel (`https://canis.flotilla.cc`), or custom gated URLs.

---

## File Changes
- `disposition-lens/prototype/disposition_lens.jsx`: Complete implementation of dual modes, history/replay, telemetry, and connection management.
- `disposition-lens/prototype/standalone.template.html`: Enhanced responsive layout and typography styles.
- `disposition-lens/prototype/build.sh`: Added `useMemo` to React prelude and compiled `standalone.html`.
- `disposition-lens/prototype/standalone.html`: Regenerated 81.8 KB self-contained browser build.

---

## Verification & Testing
1. **Live Mac Mini Backend Test**:
   - Sent test query `"What baud rate does the pen controller use?"` to `http://localhost:8000/infer`.
   - Successfully received response with `disposition: "confident"`, `entropy: 0.0958`, and concept tokens.
2. **Build Verification**:
   - Ran `build.sh` to compile `standalone.html`.
   - Verified bracket and JSX structural balance using Python AST validator.
   - Tested HTTP GET on `http://localhost:8765/standalone.html` returning `HTTP 200 OK` (81,880 bytes).
