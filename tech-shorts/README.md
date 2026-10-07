# Tech-Shorts Pipeline

Automated factory for high-yield AI/tech explainer shorts & longs (NotebookLM &rarr; hook/outro &rarr; YouTube &rarr; X &rarr; stats &rarr; FinOps).

---

## 🎯 Architecture & Data Flow

```
[ Miguel / Team ]
       │
       ▼ (TS-1: Ideation Intake)
┌─────────────────────────────────────────────────────────────┐
│ tech-shorts/intake.py (CLI / Python API / Local Web Console)│
│ Persists to: tech-shorts/jobs.json                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-2: NotebookLM Manual/Browser Step)
┌─────────────────────────────────────────────────────────────┐
│ Miguel creates/downloads NotebookLM overview video(s)       │
│ Typical current input: raw_cinematic.mp4 (16:9)             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-3: Hook/Outro Parameterization & VO)
┌─────────────────────────────────────────────────────────────┐
│ pipeline.py + local Kokoro hook/outro/Short voiceover       │
│ Assembles: final_long.mp4 and optional derived final_short  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-4: YouTube Publishing)
┌─────────────────────────────────────────────────────────────┐
│ music-video-tool OAuth & uploader                           │
│ Uploads private YouTube Short + Main Video                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-5: X Cross-Posting)
┌─────────────────────────────────────────────────────────────┐
│ FLOT publisher (X API client + local cost guard)            │
│ Posts: Hook tweet + YouTube link                            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-6 & TS-7: Stats & FinOps)
┌─────────────────────────────────────────────────────────────┐
│ api.robotross.art/stats/?project=tech-shorts                │
│ FinOps dashboard telemetry                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart — TS-1 Ideation Intake

### 1. Interactive Intake (CLI)
```bash
python3 tech-shorts/intake.py add
```

### 2. Fast Command-Line Intake
```bash
python3 tech-shorts/intake.py add \
  --title "Why Small Models Win On-Device" \
  --urls "https://arxiv.org/abs/2401.00000, https://blog.example.com/on-device" \
  --notes "Latency, privacy, and battery efficiency of sub-4B models." \
  --tags "on-device,mlx,canis"
```

### 3. Launch Local Web Console
```bash
python3 tech-shorts/intake.py serve --port 8766
# Open http://localhost:8766 in your browser
```

### 4. Queue Management
```bash
# List all jobs
python3 tech-shorts/intake.py list

# List queued jobs only
python3 tech-shorts/intake.py list --status queued

# Show full job details
python3 tech-shorts/intake.py show ts-20260821-why-ai-agents-spontaneously-lie

# Update status
python3 tech-shorts/intake.py update <id> --status assembled --notebook-url "https://notebook.google.com/..."

# Claim next available job (for worker scripts)
python3 tech-shorts/intake.py claim
```

---

## Current Production Runbook

The active 2026-10 workflow is hybrid: the ideas console tracks jobs, Miguel performs the NotebookLM video generation manually, and the Mac pipeline handles storage, intro/outro assembly, captions, metadata, private YouTube uploads, and derived Shorts.

1. Create or inspect a job in the ideas console at `https://api.robotross.art/ideas/`.
2. Generate the NotebookLM explainer video manually and download the `.mp4` to `~/Downloads`.
3. Store the downloaded video in the canonical asset store:

```bash
python3 tech-shorts/asset_store.py store-raw <job_id> --cinematic ~/Downloads/<video>.mp4
python3 tech-shorts/intake.py update <job_id> --status raw_videos_ready
```

4. Add hook copy, YouTube titles/descriptions, source citation, tags, privacy, and localizations in `tech-shorts/jobs.json` or via `pipeline.py set-copy`.
5. Generate local Kokoro hook VO into the job asset folder using a cached voice such as `af_bella`, with `HF_HUB_OFFLINE=1` when model files are already cached.
6. Build the long video:

```bash
python3 tech-shorts/pipeline.py run <job_id> --stage build
```

7. Generate captions without dubs:

```bash
/Users/miguelrodriguez/projects/music-video-tool/.venv312/bin/python3 \
  tech-shorts/subs_gen.py <final_long.mp4> <asset_dir> <slug> en,de,fr,ja
```

8. Upload private video(s):

```bash
python3 tech-shorts/pipeline.py run <job_id> --stage upload
```

The upload stage is idempotent: if the long video already has a YouTube URL, adding `final_short.mp4` later and rerunning upload will only upload the missing Short.

### Captions

Caption files are generated as SRTs under each job asset directory. For manual YouTube upload, copy them to a per-video folder under `~/Downloads`, for example:

```bash
mkdir -p ~/Downloads/tech-shorts-captions/<slug>
cp ~/flotilla/tech-shorts/assets/<date-slug>/*_{en,de,fr,ja}.srt ~/Downloads/tech-shorts-captions/<slug>/
```

Automatic caption upload is already attempted by `pipeline.py`, but the current saved YouTube OAuth token does not have a usable `youtube.force-ssl` grant. To enable automated caption upload, delete/recreate the channel token and re-consent with the scopes in `music-video-tool/youtube_uploader.py`.

### TTS Notes

Hook and derived-Short narration currently uses local Kokoro instead of ElevenLabs because ElevenLabs quota can be exhausted. Approved/cached voices known to work locally include:

- English: `af_bella`, `am_michael`
- French: `ff_siwis`
- Japanese: `jf_alpha`
- German approved: Kerstin from `cryptomilk/kokoro-german-kerstin`
- German rejected test: Thorsten from `Thorsten-Voice/Kokoro` rendered as noise and should not be used for production.
- German rejected test: Victoria from `kikiri-tts/kikiri-german-victoria` rendered as noise and should not be used for production.

German should use Kerstin for now; the voice has a noticeable non-native accent, but it is acceptable for Silicon Valley / AI topics. French uses `ff_siwis`; Japanese uses `jf_alpha`. Multilingual TTS should be isolated in a dedicated environment before production dubbing. The quick test used `music-video-tool/.venv312`, but adding Kokoro Japanese/German dependencies there introduced dependency tension with existing Mistral tooling. Prefer a future `tech-shorts/.venv-tts` for multilingual dubbing.

Current sample files:

```text
~/Downloads/tts-voice-tests/japanese_jf_alpha_test.wav
~/Downloads/tts-voice-tests/german_kerstin_test.wav  # approved
~/Downloads/tts-voice-tests/german_thorsten_test.wav  # rejected: noise
~/Downloads/tts-voice-tests/german_victoria_test.wav  # rejected: noise
```

German model notes:

- `Thorsten-Voice/Kokoro`: German Kokoro fine-tune with its own model checkpoint and `voices/thorsten.pt`.
- `cryptomilk/kokoro-german-kerstin`: German female voice `df_kerstin`, trained from the Kerstin dataset. Use the voice pack with base `KModel()`; the repo `.pth` files are training checkpoints, not direct inference checkpoints.
- `crane-local-ai/Kokoro-82M-v1.0-German-ONNX`: German-only ONNX path with a German G2P, useful if the Python Kokoro path remains brittle.

### 2026-10-07 Batch

The following jobs were assembled and uploaded as private long videos and private derived Shorts:

| Job | Long | Short |
| --- | --- | --- |
| `ts-20261006-big-blob-of-compute` | `https://www.youtube.com/watch?v=vsm1O5Czi5g` | `https://www.youtube.com/watch?v=OxlxGcICwr8` |
| `ts-20261006-how-to-hire-an-agent` | `https://www.youtube.com/watch?v=pyeTLXTLB_s` | `https://www.youtube.com/watch?v=pSjBdCtH5OM` |
| `ts-20261006-how-attachment-theory-ban-help-us-understand-ai-relationships` | `https://www.youtube.com/watch?v=v14MUulexmk` | `https://www.youtube.com/watch?v=C_NeLevxNA0` |

German, French, and Japanese `.m4a` audio tracks for this batch were generated locally from the translated SRT files with Kokoro voices and copied beside the captions under `~/Downloads/tech-shorts-captions/`.

After upload, open YouTube Studio for each video and confirm the altered/synthetic content setting before publishing.

---

## 📦 Programmatic Python API for Workers (`TS-2` .. `TS-7`)

```python
import sys
from pathlib import Path

# Add tech-shorts to path
sys.path.insert(0, "/Users/miguelrodriguez/projects/agentic-fleet-hub/tech-shorts")
import intake

# 1. Claim next queued job
job = intake.claim_next_job(status_from="queued", status_to="in_progress")
if job:
    print(f"Working on {job['id']}: {job['title']}")
    source_urls = job["source_urls"]

    # 2. Worker performs task (e.g. NotebookLM generation or video assembly)...

    # 3. Update job with generated assets / status
    intake.update_job(
        job["id"],
        status="assembled",
        notebook_url="https://notebook.google.com/notebook/...",
        assets={
            "final_short_mp4": "Why_AI_Agents_Spontaneously_Lie_FINAL.mp4",
            "final_long_mp4": "Anatomy_of_an_AI_Breach_FINAL.mp4",
        },
    )
```

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 tech-shorts/test_intake.py
```
