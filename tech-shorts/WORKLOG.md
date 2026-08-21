# TS-0 WORKLOG — tech-shorts pipeline coordinator (EPIC)

**Ticket:** ji7fpbit3c96c1o  
**Branch:** task/ji7fpbit3c96c1o  
**Owner:** Clau  
**Date:** 2026-08-21

## What this EPIC delivers

The `pipeline.py` coordinator that wires together all proven pieces:

```
job (jobs.json) → build (PIL cards + ElevenLabs VO + ffmpeg) → YouTube upload → X cross-post
```

Sub-tickets TS-3/4/5 are implemented INSIDE this coordinator (they share code
with the pipeline rather than being separate scripts).

## Key decisions

1. **Replicate PIL card rendering in Python** (not env-var-passing build_techshort.sh)  
   — cleaner parameterization; same ffmpeg invocations underneath.

2. **ElevenLabs VO** uses Alice voice ID `Xb7hH8MSUJpSbSDYk0k2` (British female),  
   model `eleven_multilingual_v2`, key from music-video-tool/.env.

3. **YouTube upload** delegates to `music-video-tool/youtube_uploader.py` via  
   `sys.path` injection (no re-provisioning of credentials).

4. **X post** delegates to `flotilla/publisher/flotilla_publisher/x_client.py`.

5. **Job schema** uses intake.py's `jobs.json`; pipeline updates job in-place.

## Pipeline stages

| Stage | Command flag | What it does |
|-------|--------------|--------------|
| build | `--stage build` | PIL cards + VO + ffmpeg concat → final mp4s |
| upload | `--stage upload` | YT upload short + long; writes youtube.{short,long}_url to job |
| post | `--stage post` | X post with YT URL in caption; writes x_post.post_url to job |

## Files changed

- `tech-shorts/pipeline.py` — NEW: master coordinator
- `tech-shorts/jobs.json` — updated second job (inference-moves-in-house) with hook copy
- `tech-shorts/WORKLOG.md` — this file
- `tech-shorts/PIPELINE.md` — update status section

## Usage

```bash
# 1. Set raw source paths (after downloading from NotebookLM)
python3 pipeline.py set-sources <job_id> --short /path/to/notebooklm_short.mp4 --long /path/to/notebooklm_long.mp4

# 2. Set hook copy (if not set at intake)
python3 pipeline.py set-copy <job_id> \
  --vo "Companies are racing to run AI inference in-house. Here is why." \
  --hook-a-main "BIG TECH" --hook-a-sub "IS MOVING AI" --hook-a-footer "inference in-house is here" \
  --hook-b-main "Why run it yourself?" --hook-b-sub "Cost. Control. Speed." --hook-b-footer "The numbers explain everything" \
  --x-caption "Why every company is running AI inference in-house {yt_url} #AI #inference"

# 3. Build (PIL cards + ElevenLabs VO + ffmpeg)
python3 pipeline.py run <job_id> --stage build

# 4. Upload to YouTube (dry-run first)
python3 pipeline.py run <job_id> --stage upload --dry-run
python3 pipeline.py run <job_id> --stage upload

# 5. Post to X
python3 pipeline.py run <job_id> --stage post

# Or run all stages in one go
python3 pipeline.py run <job_id>
```
