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
                               ▼ (TS-2: NotebookLM Browser Automation)
┌─────────────────────────────────────────────────────────────┐
│ Claude-in-Chrome / Big Sis creates NotebookLM overview      │
│ Produces: raw_short.mp4 (9:16) + raw_long.mp4 (16:9)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-3: Hook/Outro Parameterization & VO)
┌─────────────────────────────────────────────────────────────┐
│ build_techshort.sh + ElevenLabs "Alice" Hook Voiceover      │
│ Assembles: Final 9:16 Short + Final 16:9 Long               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (TS-4: YouTube Publishing)
┌─────────────────────────────────────────────────────────────┐
│ music-video-tool OAuth & uploader                           │
│ Publishes: YouTube Short + Main Video                       │
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
