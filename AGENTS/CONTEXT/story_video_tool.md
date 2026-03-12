# Story Video Generation Tool

## Overview
A Gradio-based web application (Python) that produces short-form narrative videos for "The Lost Coins" — a sci-fi thriller story published on Substack. For each chapter, the tool assembles AI-generated video clips with a music track and optional narration, producing two video outputs ready for TikTok, YouTube Shorts, and Instagram Reels.

## The Story
- **Title**: The Lost Coins
- **Genre**: Sci-Fi Thriller
- **Published on**: scifibymiguel.substack.com
- **Length**: 54 chapters (Ch0–Ch52 + Post-Credits), ~32,000 words
- **Plot**: Crypto heist thriller involving a frozen Hal Finney Bitcoin wallet, Interpol, a Macau crime boss, a Mexican cartel, and a brain-reading neuroscientist
- **Characters**: Lena (scout/double agent), Paul (crypto hacker), Erica (neuroscientist), Inspector Pinto (Interpol), Captain Meier (Swiss police), Mr. Zheng (antagonist), Gonzales "Speedy" (antagonist), Chen (comic relief)

## Architecture
- **Frontend**: Gradio web UI running on port 7861
- **Backend**: Python 3.12, moviepy 1.x, Kokoro TTS, librosa
- **Location**: `C:\Users\migue\music-video-tool\story_tool.py`
- **Venv**: `C:\Users\migue\.venv312\`
- **Output directory**: `C:\Users\migue\Videos\StoryVideos\`

## Production Pipeline

```
Substack Text → Runway Prompts → Suno Audio → Runway Clips → Assemble Video
                                    ↓
                              Trim to 60s
                                    ↓
                         Music-only + Narrated versions
```

### Step 1: Text
- Source of truth: Substack API (`/api/v1/posts`) — bypasses CDN cache
- 54 chapters downloaded and stored in `StoryVideos/`
- Full story compiled: `the_lost_coins_full.txt` (~32,087 words)

### Step 2: Runway Prompts
- 10 visual prompts per chapter (540 total)
- Generated via Claude Haiku for cost efficiency
- Character profiles in `C:\Users\migue\Videos\StoryCharacters\` ensure visual consistency
- Prompts capped at 1000 chars (Runway limit)
- Prompt strategy: side/back angles only, no frontal faces
- Hub page: `StoryVideos/runway_hub.html` — self-contained HTML with all 540 prompts, status tracking via localStorage

### Step 3: Suno Audio
- 60-second music track per chapter (trimmed via `trim_audio.py` using librosa)
- Auto-trim finds quiet moment to cut cleanly

### Step 4: Runway Clip Generation
- Model: Kling 3.0 Pro (required for 9:16 vertical — Gen-4.5 only does 16:9)
- Resolution: 9:16 vertical, 10 seconds per clip
- 10 clips per chapter → 540 clips total for full story
- Generation method: Chrome extension driving Runway web UI (unlimited subscription ~$100/mo)
- Max 2 concurrent generations, human-like delays
- Download watcher: `runway_watcher.py` monitors Downloads folder, auto-renames to `ch{N}_clip{Y}.mp4`, moves to `Chapter{N}/`
- Current chapter tracked in `current_chapter.txt`

### Step 5: Video Assembly
- Assembles 10 clips (10s each = 100s raw) with 60s audio track
- Clips trimmed/looped to match audio duration

## Outputs Per Chapter
| File | Description |
|------|-------------|
| `ch{N}_final.mp4` | Music-only version |
| `ch{N}_narrated_{lang}.mp4` | Narrated version with Kokoro TTS |

## Narration Feature
- **Engine**: Kokoro TTS v0.9.4 (local, offline)
- **Default voice**: `am_michael` (warm US male), speed 0.92
- **Source**: Chapter captions (not full text) — ~30–40 seconds
- **Languages**: 9 languages supported; auto-translated via Claude Haiku if non-English selected
- **Model download**: ~300MB on first run (appears to hang — just wait)
- `numpy<2.0` required for moviepy compatibility

## Folder Structure
```
StoryVideos/
├── Chapter0/
│   ├── ch0_clip1.mp4 ... ch0_clip10.mp4
│   ├── ch0_final.mp4
│   └── ch0_narrated_en.mp4
├── Chapter1/ ... Chapter52/
├── PostCredits/
├── runway_hub.html      ← prompt management UI
├── runway_watcher.py    ← download auto-renamer
├── current_chapter.txt  ← active chapter for watcher
├── the_lost_coins_full.txt
└── story_tool.log
```

## Character Visual Profiles
Stored in `C:\Users\migue\Videos\StoryCharacters\` — one file per character with physical description for Runway prompt consistency:
- `lena.txt` — blonde long hair, blue eyes, 1.70m, black pencil skirt
- `paul.txt` — black hair, 5-day stubble, always glasses, graphic t-shirt
- `erica.txt` — brunette short bob, 1.65m, smart casual
- `pinto.txt` — Macanese, 45, dark suits, stocky
- `smith.txt` — FBI, navy suit, badge on belt
- `chen.txt` — Chinese, 26, oversized hoodie, headphones, energy drink

## Distribution Strategy
| Platform | Format | Performance |
|----------|--------|-------------|
| TikTok | Vertical short (~60s) | ~750 avg views (outperforms YouTube) |
| YouTube Shorts | Vertical short (~60s) | ~70 avg views |
| Instagram Reels | Vertical short (~60s) | Bookstagrammer audience — funnel to Substack |

- **Goal**: Story shorts → Substack subscribers → book readers
- **Instagram**: Story chapters ONLY (bookstagrammer niche, no music content)
- **Caption strategy**: Character tension over plot mechanics. Always end with "full story on Substack, link in bio"
- Story rows tracked in `video_tracker.xlsx` Shorts sheet with Video Theme = "Chapter X"

## Production Status (Mar 2026)
- Ch1–9: Final videos posted ✓
- Ch20: All 10 Runway clips generated ✓
- Ch10–19, Ch21–52, PostCredits: Suno audio → Runway clips needed
- All 54 chapters have texts and 10 prompts each ✓

## Technical Notes
- `moviepy<2.0` required
- `numpy<2.0` required (int64 frame dtype issue)
- Story tool venv: `.venv312` (Python 3.12)
- Launch: `launch_story_tool.bat`
- Log: `C:\Users\migue\Videos\StoryVideos\story_tool.log`
