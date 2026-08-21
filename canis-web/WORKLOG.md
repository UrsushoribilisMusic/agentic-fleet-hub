# WORKLOG — CANIS-F: Canis Project Explainer Web Page

## Task Metadata
- **Ticket ID**: `h3du5d5vooyazvp` (CANIS-F / GitHub #983)
- **Assigned Agent**: Gem (`gem`)
- **Status**: `in_progress`

## Plan
1. **Research & Copy Coordination**:
   - Align terminology with CANIS-0 epic, CANIS-A/B/C/D/G specs, and `disposition-lens/SPEC.md`.
   - Incorporate the 8 dispositions (`idle`, `confident`, `uncertain`, `curious`, `concern`, `reluctant`, `warm`, `mischief`).
   - Frame the dual models: Canis Apertus (`swiss-ai/Apertus-v1.1-4B-Instruct-MLX-INT4`) + Canis Mistralis (`mlx-community/Ministral-3-3B-Instruct-2512-4bit`).
   - Structure narrative: Accessible intro first (human conversational analogy) -> Progressive deep technical dive (Jacobian lens, forward-only MLX adaptation, seed vectors, entropy gate, on-device sovereignty).

2. **Web Artifact Implementation**:
   - Build a standalone, high-fidelity responsive web application at `canis-web/index.html` (with bundled SVG avatar, interactive disposition state switcher, real-time parametric face updates, J-space token inspector, entropy meter, and architectural diagrams).
   - Theme: Premium dark submarine / sci-fi observability aesthetic with warm brass and teal accents.
   - Interactive components:
     - Live interactive Dog Avatar (Bunny / Dev Groar) with real-time slider controls and 8 pre-tuned disposition presets.
     - Interactive J-Space Token & Seed-Vector visualizer.
     - Interactive Entropy Gauge and formula breakdown.
     - Product comparison matrix (Apertus 4B vs Ministral 3B).
     - Signal Contract Inspector (live JSON output viewer).

3. **Verification**:
   - Validate HTML/CSS/JS syntax and test rendering.
   - Verify all 8 disposition states, SVG math, and responsive breakpoints.

4. **Peer Review Handoff**:
   - Commit incrementally to `task/h3du5d5vooyazvp` and merge to `master`.
   - Post task output comment and advance status to `peer_review`.
