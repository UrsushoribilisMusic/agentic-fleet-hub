# WORKLOG — TS-1: Ideation Intake

## Task Context
- **Ticket**: `xdzsuqg5m1zeiz1` / `TS-1`
- **Owner**: Gem
- **Objective**: Lightweight ideation entry point: Miguel enters an idea + source URL(s) (docs/podcasts/reads) → a job record the pipeline consumes. Reuse the music-video-tool / ReelTales job-intake pattern.
- **Output**: A queued 'tech-short' job with `{title, source_urls, status, ...}` stored in persistent JSON with CLI, Python API, and local Web UI.

## Plan & Milestones
1. **Schema & Storage Design**:
   - Define standard schema for TechShort job records: `id`, `slug`, `title`, `source_urls`, `idea_notes`, `tags`, `status` (`queued`, `in_progress`, `assembled`, `published`, `failed`), `notebook_url`, `hook_copy`, `outro_copy`, `assets`, `youtube`, `x_post`, `timestamps`.
   - Store in `tech-shorts/jobs.json` with atomic file write + lock safety.
2. **Core Intake Engine (`tech-shorts/intake.py`)**:
   - Programmatic Python API: `create_job`, `get_job`, `list_jobs`, `update_job`, `claim_next_job`, `delete_job`.
   - Rich CLI subcommands: `add`, `list`, `show`, `update`, `claim`, `delete`, `serve`.
   - Zero required external dependencies (runs out of the box with standard Python 3.9+).
3. **Web Intake UI**:
   - Built-in lightweight web server (`python3 intake.py serve`) serving a single-page interactive console.
   - Clean, modern UI (matching dark ink/teal/coral tech-shorts aesthetic) with URL inputs, live queue cards, status toggles, and instant job enqueueing.
4. **Seed Initial Jobs**:
   - Populate `jobs.json` with the proven AISI incident job (status: `assembled` / reference) and the queued LinkedIn inference article.
5. **Unit Tests & Verification**:
   - `test_intake.py` verifying full lifecycle: CLI args, programmatic creation, JSON persistence, status advancement, claiming, filtering.
6. **Documentation & Pipeline Hookup**:
   - Update `PIPELINE.md` and `README.md` so downstream tickets (`TS-2`, `TS-3`, `TS-4`) have clear programmatic contracts.
