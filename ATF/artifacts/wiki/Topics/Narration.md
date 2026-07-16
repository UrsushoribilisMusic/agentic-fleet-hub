# Narration Subsystem

## 1. Role
The Narration subsystem generates Bob Ross-style poetic commentary for each drawing job, providing a unique "personality" to the robot.

## 2. Key Components
- **Local LLM**: Mistral (`ministral-3:8b`) running via Ollama — the default brain as of the 2026-07 Windows/Mistral-hackathon build. Apertus 8B (Swiss open-weights, `MichelRosselli/apertus:8b-instruct-2509-q4_k_m`) remains available as an explicit fallback via `--brain apertus`, but is no longer the default and is never auto-triggered on failure.
- **Voice Output**: Voxtral (Mistral's TTS) by default, with Kokoro (local neural TTS) and a system-TTS fallback also selectable.
- **Async generation**: narration now generates in a background thread — the arm starts drawing and a generic filler intro/commentary plays immediately, then swaps to the real request-specific lines once generation finishes, instead of blocking drawing start on the ~60-90s LLM call.

## 3. Workflow
1. **Prompt Generation**: `bob_ross.py` constructs a prompt based on the drawing job (e.g., "a happy little lighthouse").
2. **Narration JSON**: the local model generates a JSON structure containing:
    - `intro`: Spoken before drawing starts (generic filler spoken immediately; swapped for the real intro once ready, if it arrives before drawing finishes).
    - `commentary[]`: A list of short phrases spoken during drawing at regular intervals.
    - `outro`: Spoken after the job completes.
3. **Playback**: Commentary is spoken in parallel with the arm movements.

## 4. Uncertainty & Contradictions
- **Commentary Timing**: `bob_ross.py` uses a hard-coded `COMMENTARY_INTERVAL` (default 6 seconds). If the drawing is very simple, some commentary might be cut off. If it is very complex, there might be long periods of silence if the list of phrases is short.
- **Concurrency**: running narration generation at the same time as another local-model call (e.g. a sketch generation or an ATF chat question) can cause CPU contention on the CPU-only hackathon laptop and slow/timeout both — see the ATF fallback-chain incident note (2026-07-10 standup).
- **Voice cutoff (open issue)**: Voxtral voice output has been observed to cut off mid-sentence during chat replies; not yet root-caused.

---
**Sources:**
- `skills/robot-ross/bob_ross.py`, `skills/robot-ross/control_center.py`, `skills/voice/speak.py`
- `AGENTS/CONTEXT/agentegra.md`
- `AGENTS/CONTEXT/robot_ross_artist.md`
- agentic-fleet-hub standups: 2026-07-09, 2026-07-10
