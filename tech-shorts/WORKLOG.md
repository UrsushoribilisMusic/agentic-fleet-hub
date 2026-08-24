# TS-13 WORKLOG — Ideation console = dashboard

**PB task**: `jsyjldnaw0kr484`
**Branch**: `task/jsyjldnaw0kr484`

## Goal
Turn the ideation page (`intake.py` web console, TS-9) into a per-job dashboard:
- Per-card pipeline progress bar (idea → processing → raw assets → assembled → published)
- Drive links section (folder, infographic, slidedeck) sourced from `job.drive.*` (TS-12)
- YouTube links section (short + long) from `job.youtube.*`
- X post link from `job.x_post.post_url`
- Published stats counter in the header strip

## Depends on
- TS-9: `intake.py` web console (deployed on DO, auth-gated)
- TS-12: `asset_store.py` — populates `job.drive.*` and wires YouTube URLs into `job.youtube.*`

## Data already in job record
```
job.drive.folder_url
job.drive.infographic_url
job.drive.slidedeck_url
job.youtube.short_url / long_url / published_at
job.x_post.post_url
```

## Plan
1. Add CSS: `.pipeline-row`, `.pipeline-step.done/active`, `.asset-section`, `.asset-row`, `.asset-link.drive/youtube/xpost`
2. Update `stats-strip` HTML: rename "Assembled" → just assembled count; add "Published" stat
3. Update `renderStats()` JS to match
4. Add `pipelineSteps(job)` helper function
5. Update `renderQueue()` job card template: insert pipeline bar + asset section between header and notes
6. No new backend endpoints needed — all data already in `/api/jobs` response

## Commit order
1. Add CSS + JS changes to `WEB_HTML` in `intake.py`
2. Commit + push
