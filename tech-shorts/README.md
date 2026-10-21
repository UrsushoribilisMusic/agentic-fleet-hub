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

### Captions & Multi-Language Audio Staging

Caption files (`.srt`) and localized voice-over tracks (`.m4a`) are generated under each job's canonical asset directory (`~/flotilla/tech-shorts/assets/<date-slug>/`).

Because the YouTube Data API v3 does not support uploading secondary audio tracks programmatically (and caption API upload requires `youtube.force-ssl` re-consent), the automated pipeline stages all multi-language assets directly into:

```bash
~/Downloads/tech-shorts-captions/<slug>/
```

Staged files include:
- `<slug>_en.srt`, `<slug>_de.srt`, `<slug>_fr.srt`, `<slug>_ja.srt`
- `<slug>_audio_de.m4a`, `<slug>_audio_fr.m4a`
- `<slug>_hook_vo.mp3`

From there, attach the `.srt` subtitles and `.m4a` audio dubs directly in **YouTube Studio** under *Content → Video → Languages*.

### TTS & Secrets via Infisical Vault

The pipeline fetches credentials dynamically via the centralized **Infisical EU Vault** (`agentic-fleet-hub/vault/vault.py`) without requiring hardcoded keys:

1. **Vault Fetch**: `INFISICAL_TOKEN` and `INFISICAL_PROJECT_ID` are configured in `music-video-tool/.env` (or environment). Calling `from vault import get_secret; key = get_secret("ELEVENLABS_API_KEY")` queries Infisical EU (`https://eu.infisical.com/api`) and returns the active secret.
2. **Permissions Note**: The ElevenLabs API key has scoped permissions for Text-to-Speech (`/v1/text-to-speech`) with model `eleven_multilingual_v2`. Account metadata requests (`/v1/user/subscription`) return `401 missing_permissions`, which is normal for scoped operational keys and does not affect TTS generation.
3. **Approved Production Voices**:
   - **English Hook**: `Xb7hH8MSUJpSbSDYk0k2` (Alice, British female)
   - **German Dub**: `QT6va3HQK8j63EC2r9cw` (ElevenLabs Multilingual v2)
   - **French Dub**: `rS7c1woNY04WT3UAS83Y` (ElevenLabs Multilingual v2)
   - **Local Kokoro Fallback**: If ElevenLabs quota is ever fully exhausted, the local Kokoro engine is available in `.venv312` (`af_bella` for EN, `cryptomilk/kokoro-german-kerstin` for DE, `ff_siwis` for FR, `jf_alpha` for JA).

### 2026-10-21 Batch

| Job | Long (Private) | Localizations | Staged Assets |
| --- | --- | --- | --- |
| `ts-20261021-squeezing-an-autonomous-agent-into-32gb` | `https://www.youtube.com/watch?v=qs438DSa2ZY` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/squeezing-an-autonomous-agent-into-32gb/` |

### 2026-10-18 Batch

| Job | Long (Private) | Localizations | Staged Assets |
| --- | --- | --- | --- |
| `ts-20261018-conscious-and-suppressed-stimuli` | `https://www.youtube.com/watch?v=ckNAJdh26Sg` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-flickering-mind/` |
| `ts-20261018-how-employment-is-changing-at-anthropic` | `https://www.youtube.com/watch?v=MS4c5Dmiqec` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/ai-transforms-office-roles/` |
| `ts-20261018-demis-hassabis-on-choosing-whats-worth-spending-your-life-building-in-a-world-changing-this-fast` | `https://www.youtube.com/watch?v=4tJamjOCNno` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-sleep-deficit-why-ai-needs-to-dream/` |

Multilingual pass migrated to local Kokoro neural engine (`.venv312`) following ElevenLabs quota exhaustion. Local voices: `af_bella` (EN hook), `cryptomilk/kokoro-german-kerstin` (DE), `ff_siwis` (FR), `jf_alpha` (JA). Multilingual subtitles (`EN`, `DE`, `FR`, `JA`) and audio dubs (`DE`, `FR`) staged to `~/Downloads/tech-shorts-captions/`.

### 2026-10-16 Batch

| Job | Long (Published) | Localizations | Staged Assets |
| --- | --- | --- | --- |
| `ts-20261013-ai-models-may-be-capable-of-self-replicating-without-access-to-a-datacenter` | `https://www.youtube.com/watch?v=GLLa6t_MQuA` (Live) | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-convergence-point-why-ai-worms-are-targeting-your-smart-tv/` |
| `ts-20261014-how-to-be-more-ambitious-a-tutorial-for-humans-with-models` | `https://www.youtube.com/watch?v=UzrGSQ6-l6k` (Live) | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/` |
| `ts-20261012-cheap-labor-loses-its-edge` | `https://www.youtube.com/watch?v=JFhLTSY7Pxw` (Private) | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-white-collar-bypass/` |

Episodes reviewed, altered/synthetic content toggled, multilingual subtitles (EN/DE/FR/JA) and ElevenLabs audio tracks (DE/FR) attached, and published live on YouTube. For the new White-Collar Bypass video, attach staged subtitles and dub tracks in YouTube Studio under Languages before setting public.

### 2026-10-14 Batch

| Job | Long (Private) | Localizations | Staged Assets |
| --- | --- | --- | --- |
| `ts-20261014-the-convenience-paradox-why-the-internet-of-things-is-melting` | `https://www.youtube.com/watch?v=D-LV9YJN2ZM` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-convenience-paradox-why-the-internet-of-things-is-melting/` |
| `ts-20261014-the-shadow-datacenter-why-ai-worms-are-targeting-your-smart-tv` | `https://www.youtube.com/watch?v=lZ_LLtp8Ulo` | EN, DE, FR, JA | `~/Downloads/tech-shorts-captions/the-shadow-datacenter-why-ai-worms-are-targeting-your-smart-tv/` |

After upload, open YouTube Studio for each video, confirm the altered/synthetic content setting, and attach the staged subtitles and audio tracks under Languages before publishing.

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
