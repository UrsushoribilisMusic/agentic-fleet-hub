# TS-10 WORKLOG — DO→Mac sync + NotebookLM integration

**Ticket:** 8wjnn00nnyqoyzb  
**Branch:** task/8wjnn00nnyqoyzb  
**Owner:** Clau  
**Date:** 2026-08-22

## Goal

Conflict-free sync so ideas captured on the DO droplet (via ideas.flotilla.cc)
reach the Mac Mini assembly pipeline — and status flows back.

End state: capture idea on phone → NotebookLM generates → Mac assembles → YouTube uploads → X posts. Hands-free.

## Architecture decision

**Single source of truth = DO jobs.json** (served by intake.py at 127.0.0.1:8766).

- DO intake API is the authoritative queue.
- Mac Mini is a *pull worker* only: claim via API, run pipeline, PATCH status back via API.
- Two new files:
  1. `do_sync.py` — thin stdlib-only DO intake API client
  2. `mac_worker.py` — end-to-end orchestrator (pull → NotebookLM → build → upload → post → report)

**Connection:** Mac reaches the DO API via SSH tunnel (robotsales alias).  
`DO_INTAKE_URL=http://localhost:8766` + `mac_worker.py --tunnel` opens the tunnel automatically.  
Once ideas.flotilla.cc DNS + a machine token land, this can switch to HTTPS directly.

## What was built

### do_sync.py
- Zero-dependency stdlib-only HTTP client around the intake API
- `claim_queued_job(base_url)` — atomic POST /api/jobs/claim
- `post_status(base_url, job_id, status, **extra)` — PATCH fields back
- `get_job(base_url, job_id)` — GET /api/jobs/<id>
- `merge_job_local(job, local_jobs_file)` — upserts job into local jobs.json so pipeline.py continues working as-is

### mac_worker.py
- `mac_worker.py run [--job JOB_ID] [--tunnel] [--stage STAGE] [--dry-run]`
  - One-shot: claim next queued (or run a specific job)
  - Stages: `notebooklm` → `build` → `upload` → `post`
- `mac_worker.py watch [--interval N] [--tunnel]`
  - Daemon loop, polls DO every N seconds (default 120s)
- `mac_worker.py status [--tunnel]`
  - Show DO queue alongside local pipeline state
- SSH tunnel helper: opens `ssh -N -L 8766:localhost:8766 robotsales` subprocess
- NotebookLM integration: calls `notebooklm_driver.py run <job_id>`
  - Current stubs will raise NotImplementedError → worker logs it and halts at that stage
  - Once TS-2 selectors are filled in, the whole pipeline runs hands-free
- Status post-back after every stage (raw_videos_ready → assembled → published)

### launchd plist (ts10_worker.plist)
- Runs `mac_worker.py watch --tunnel` every 2 minutes via launchd KeepAlive=false
- Logs to ~/Library/Logs/ts10_worker.{out,err}
