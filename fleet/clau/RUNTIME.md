# Clau Runtime — Canonical Path

This document describes the **one true execution path** for Clau's automated heartbeat loop.
It is the reference point for diagnosing drift, debugging launchd failures, and onboarding
any agent that needs to understand how Clau runs.

---

## End-to-End Call Chain

```
launchd (fleet.clau.plist)
  └── /Users/miguelrodriguez/fleet/clau/heartbeat_wrapper.sh
        ├── [Phase 0]  heartbeat_check.py   — checksum gate (skip if no repo changes)
        ├── [Phase 1]  summarize_session.py --pre   — refresh active_lessons.txt from PB
        ├── [Phase 2]  build prompt (base + injected lessons from active_lessons.txt)
        ├── [Phase 3]  claude --dangerously-skip-permissions -p "$FULL_PROMPT"
        └── [Phase 4]  summarize_session.py --post  — extract lessons → PB + refresh file
```

---

## Canonical File Locations

| File | Tracked source (git) | Runtime deployment |
|:---|:---|:---|
| `heartbeat_wrapper.sh` | `agentic-fleet-hub/fleet/clau/heartbeat_wrapper.sh` | `~/fleet/clau/heartbeat_wrapper.sh` |
| `summarize_session.py` | `agentic-fleet-hub/fleet/clau/summarize_session.py` | `~/fleet/clau/summarize_session.py` |
| `heartbeat_check.py`   | `agentic-fleet-hub/fleet/heartbeat_check.py`        | `~/fleet/heartbeat_check.py`        |
| `active_lessons.txt`   | *(runtime-generated, not tracked)*                  | `~/fleet/clau/active_lessons.txt`   |
| `PROGRESS.md`          | *(runtime-generated, not tracked)*                  | `~/fleet/clau/PROGRESS.md`          |
| `lessons/ledger.json`  | *(runtime-generated, not tracked)*                  | `~/fleet/lessons/ledger.json`       |

**Rule**: edits go into `agentic-fleet-hub/fleet/clau/` then synced (copy or rsync) to `~/fleet/clau/`.
Never edit the runtime copies directly — they will be overwritten on next sync.

---

## launchd Plist

- **Label**: `fleet.clau`
- **Plist path**: `~/Library/LaunchAgents/fleet.clau.plist`
- **Schedule**: every 10 minutes (:04, :14, :24, :34, :44, :54)
- **Working dir**: `~/fleet/clau/`
- **stdout/stderr**: `~/fleet/logs/clau.log` / `~/fleet/logs/clau_err.log`
- **Python interpreter**: `/usr/bin/python3` (system Python 3.9.6 on Mac Mini)

---

## summarize_session.py — CLI Reference

The canonical entrypoint is `~/fleet/clau/summarize_session.py`.

```
--pre           Pre-session: fetch top N lessons from PocketBase, write active_lessons.txt.
--post          Post-session: scan log + PROGRESS.md for new lessons, post to PB, refresh file.
--lesson JSON   Submit a single JSON-structured lesson directly to PB + ledger.
(no args)       Defaults to --post.
```

The pre/post split is intentional: `--pre` runs *before* `claude` so lessons are injected into
the prompt; `--post` runs *after* `claude` so the session's output is captured.

---

## Deprecated / Archived Files

| File | Status | Reason |
|:---|:---|:---|
| `~/fleet/summarize_session.py` | **Archived** (`.deprecated`) 2026-04-11 | Root-level duplicate with incompatible CLI (`--agent`, `--dry-run`, no `--pre`/`--post`). Never called by any wrapper. Replaced by `~/fleet/clau/summarize_session.py`. |

---

## Drift Prevention

1. `heartbeat_wrapper.sh` hardcodes `SUMMARIZE="$CLAU/summarize_session.py"` — always points to
   the `clau/` subdirectory, never the fleet root.
2. The root `~/fleet/` directory is NOT a git repo. All source-of-truth versions live in
   `agentic-fleet-hub/fleet/clau/`.
3. After any change to `heartbeat_wrapper.sh` or `summarize_session.py`, verify:
   ```bash
   /usr/bin/python3 ~/fleet/clau/summarize_session.py --pre   # exit 0
   /usr/bin/python3 ~/fleet/clau/summarize_session.py --post  # exit 0
   ```
4. Python compatibility: use `from __future__ import annotations` or `typing.List` / `typing.Dict`
   if code must run on Python < 3.9. Current system is Python 3.9.6 — `list[str]` hints are safe.
