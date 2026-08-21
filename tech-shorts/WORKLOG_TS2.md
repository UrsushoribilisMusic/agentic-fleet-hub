# TS-2 WORKLOG — NotebookLM Browser Automation Harness

**Ticket:** cwkaudyrxcgosmu  
**Branch:** task/cwkaudyrxcgosmu  
**Owner:** Clau  
**Date:** 2026-08-21

## Situation

NotebookLM has no public API. The only way to generate Video Overviews is through
the web UI. TS-2 automates this via Playwright (headful Chrome so Miguel can watch
and log in if needed). The exact click-path is **blocked on Miguel's demo** — he'll
walk through the LinkedIn-article notebook tomorrow. Until then, every browser
interaction step is a stub that raises `NotImplementedError`.

## What I'm building

1. `tech-shorts/notebooklm_driver.py` — the full harness:
   - CLI: `python3 notebooklm_driver.py run <job_id> [--workdir DIR] [--dry-run]`
   - `NotebookLMDriver` class with Playwright backing
   - All 5 browser steps are stubs pointing to `CLICK_PROTOCOL.md`
   - Everything except the browser steps is real and working:
     - job loading from `jobs.json`
     - workdir creation
     - dry-run output
     - final status update (`raw_videos_ready`) + mp4 path recording

2. `tech-shorts/CLICK_PROTOCOL.md` — template for Miguel to fill in after demo:
   - One section per step with expected selectors/actions/outcomes
   - Maps directly to the stub methods in `notebooklm_driver.py`

## Key decisions

1. **Playwright** (not Selenium, not AppleScript): stable API, async-optional,
   good download interception, persistent Chrome profile for session cookies.
2. **Non-headless by default**: NotebookLM requires Google login; easiest to
   let Miguel authenticate once, then the cookie file keeps the session.
3. **Separate cookie-jar file** at `~/.ts_notebooklm_cookies` so it persists
   across runs without committing credentials.
4. **Big Sis hook**: `step_inspect()` placeholder — after demo Miguel may
   decide some steps are better driven by Claude computer-use rather than
   fixed Playwright selectors.

## Files changed

- `tech-shorts/notebooklm_driver.py` — NEW
- `tech-shorts/CLICK_PROTOCOL.md` — NEW
- `tech-shorts/WORKLOG_TS2.md` — this file

## Usage (post-demo, once steps are wired)

```bash
# Dry run — shows what would happen without opening browser
python3 tech-shorts/notebooklm_driver.py run ts-20260821-inference-moves-in-house --dry-run

# Real run — opens Chrome, drives NotebookLM, downloads mp4s
python3 tech-shorts/notebooklm_driver.py run ts-20260821-inference-moves-in-house

# Override working dir
python3 tech-shorts/notebooklm_driver.py run ts-20260821-inference-moves-in-house \
  --workdir ~/Downloads/ts-raw
```
