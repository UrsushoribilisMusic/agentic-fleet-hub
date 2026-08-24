# WORKLOG: TS-11 — Ideation intake: accept uploaded file (PDF/MD/TXT)

**Task ID**: rvgclqmgq67debd  
**Branch**: task/rvgclqmgq67debd  
**Agent**: clau

## Plan

Extend `intake.py` and `notebooklm_driver.py` to accept a source file (PDF/MD/TXT) alongside or instead of source URLs.

### Key decisions
- File storage: `tech-shorts/uploads/<job_id>/<original_filename>` (relative to `HERE`)
- Job record field: `source_file: {path, original_name, size_bytes, mime_type}` (empty dict when no file)
- Max size: 50 MB; allowed extensions: `.pdf`, `.md`, `.markdown`, `.txt`
- Web console: 2-step submit — create job via JSON, then if file selected, POST multipart to `/api/jobs/<id>/source-file`
- CLI: `--source-file <path>` flag on `add` subcommand (avoids clash with top-level `--file` for jobs.json)
- Multipart parsing via `cgi.FieldStorage` (deprecated but stdlib zero-dep; suppressed warning)

### Files to change
1. `tech-shorts/intake.py` — constants, helpers, job schema, server endpoints, HTML, CLI
2. `tech-shorts/notebooklm_driver.py` — add `source_files` to driver, update dry_run_report
3. `tech-shorts/test_intake.py` — add source file tests

### Steps
1. [x] Create task branch + worklog
2. [ ] Implement intake.py changes
3. [ ] Implement notebooklm_driver.py changes
4. [ ] Implement test_intake.py additions
5. [ ] Run tests
6. [ ] Commit + push
7. [ ] Patch PB status to peer_review
