# Job Orchestration Subsystem

## 1. Role
The Job Orchestration subsystem is the central "brain" of the RobotRoss artist side. It is primarily implemented in `bob_ross.py` and coordinates all other subsystems to fulfill drawing orders.

## 2. Main Orchestrator: `bob_ross.py`
This script manages the high-level workflow of a drawing job:
1. **Order Intake**: Accepts commands like `sketch`, `write`, `draw`, or `svg`.
2. **Readiness Check**: Verifies hardware connection, calibration state, and local model (Ollama) availability.
3. **Locking Mechanism**: Uses `/tmp/robot_ross_running.lock` to ensure only one job runs at a time.
4. [[Narration]] **Generation**: Calls the local LLM (Mistral `ministral-3:8b` by default, Apertus 8B as an explicit fallback) in a background thread to generate poetic commentary based on the job prompt — drawing starts immediately on generic filler commentary rather than waiting for generation.
5. [[VideoProof]] **Control**: Triggers OBS Studio recording via WebSocket.
6. **Execution Control**: Spawns hardware-level scripts (`huenit_svg.py`, etc.) to move the arm.
7. **Cleanup**: Releases the job lock and triggers post-processing of the video proof.

## 3. Job Lifecycle
The full job lifecycle is documented in [[Overview#Full Job Lifecycle]].

## 4. Uncertainty & Contradictions
- **Error Recovery**: The current implementation of `bob_ross.py` uses a job lock but does not explicitly document how it handles mid-job hardware failures or power loss. If a job is interrupted, the lock might remain, requiring manual intervention. **Confirmed by the operational log — see FAQ below.**
- **Hyphenation Logic**: `bob_ross.py` includes a custom `_hyphenate_word` function for text wrapping. It is unclear if this logic is optimized for all languages or only English/German.

## 5. FAQ (from `bob_ross.log`, 101 job runs 2026-03-19 to 2026-07-18)

**Q: Control Center (or the CLI) says "Robot Ross is already drawing (action=svg content='X.svg'). Please wait." but nothing is actually drawing — how do I fix it?**
A: This is a stale `/tmp/robot_ross_running.lock` (on Windows: `C:\tmp\robot_ross_running.lock`) left behind by a job that never reached its cleanup step. Confirmed in the log on 2026-07-18: a `Bear.svg` job started normally, drew for about 2 minutes (only 2% complete), then the log simply stops for that job — no `STOP`, no `JOB END` — before the next job starts 24 minutes later. That pattern is consistent with the process being killed directly rather than exited via Ctrl+C/SIGTERM, since the signal handler is the only path that removes the lock file. **Fix**: confirm no `bob_ross.py` / `huenit_*.py` process is actually running, then delete the lock file. Across the log's 101 job runs, roughly 64 never logged a `JOB END` at all — this is a recurring failure mode, not a one-off.

---
**Sources:**
- `~/.openclaw/workspace/skills/robot-ross/bob_ross.py`
- `AGENTS/CONTEXT/robot_ross_artist.md`
- `skills/robot-ross/bob_ross.log` (operational log)
