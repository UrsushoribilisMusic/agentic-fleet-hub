# Music Video Automation Tool

## Overview
A Gradio-based web application (Python) that automates the creation of short-form and long-form music videos by combining AI-generated audio (Suno) with a curated library of stock video clips. The tool handles the full pipeline from audio analysis to video assembly to YouTube upload.

## Architecture
- **Frontend**: Gradio 6.x web UI running on port 7860
- **Backend**: Python 3.12, moviepy 1.x, librosa
- **Storage**: Excel tracker (`video_tracker.xlsx`) with sheets: Video Tracker, Upload Tracker, Shorts, Videos
- **Location**: `C:\Users\migue\music-video-tool\`
- **Venv**: `C:\Users\migue\.venv312\`

## Key Files
| File | Purpose |
|------|---------|
| `app.py` | Main UI and orchestration logic |
| `video_processor.py` | Video assembly (full + short) |
| `audio_analyzer.py` | Drop detection via librosa |
| `file_manager.py` | Clip selection with pool exhaustion logic |
| `tracker.py` | Excel read/write for all tracking sheets |
| `narration.py` | Kokoro TTS wrapper |
| `trim_audio.py` | Auto-trim MP3 to target duration |
| `youtube_uploader.py` | YouTube Data API v3 OAuth upload |
| `config.py` | Music styles, themes, video extensions |

## Inputs
| Input | Description |
|-------|-------------|
| Audio file (MP3) | Suno-generated track |
| Song title | Used for filename and tracker |
| Music style | e.g. Vallenato, Progressive, Irish Folk |
| Video theme | Matches clips from library (e.g. "beach, golden, dancing") |
| Intro text | Bold overlay at video start |
| Outro text | Closing overlay |
| Video library path | Directory of stock video clips |
| Intro videos path | Rotating pool of intro clips |
| Output directory | Where generated files are saved |
| Generate Full / Generate Short | Checkboxes (Short defaults to True) |

## Outputs
| Output | Spec | Use |
|--------|------|-----|
| `{title}_short.mp4` | 30s, 1080×1920 (9:16 vertical) | TikTok, YouTube Shorts |
| `{title}_full.mp4` | Full song duration, 16:9 landscape | YouTube long-form |

## Video Assembly Logic
1. **Audio analysis**: librosa detects the drop point in the track
2. **Intro clip**: Selected from a rotating pool (exhausts all before reuse), tracked in `intro_tracker.json`
3. **Clip selection**: Themed clips matched from library by keyword, exhausts pool before reusing
4. **Short video**: 30s total — intro text (4s, instant bold, fade-out only) + clips synced so the drop hits at 5s pre-build + outro text (2s)
5. **Full video**: Full audio duration — intro clip + themed clips looped to fill duration + text overlays
6. **Tracker update**: New entry auto-added to Shorts or Videos sheet in Excel

## Batch Queue System
- Jobs are added to an in-memory queue via "Add to Queue" button
- "Run Queue" executes jobs sequentially in a background thread
- Real-time progress streamed to both the web UI log box and the CMD console
- Each job captures: audio, title, style, theme, overlays, gen type (full/short)

## Upload Flow
- YouTube upload via OAuth 2.0 (token stored in `youtube_token.pickle`)
- Supports: visibility (public/unlisted/private), scheduled publish time
- TikTok: opens browser to TikTok upload page with pre-filled metadata
- Instagram: manual (mobile app required — Meta Business Suite unreliable for 9:16)
- If `invalid_grant` error on YouTube: delete `youtube_token.pickle` and re-auth

## Analytics
- **Heatmap**: Piece × Style matrix showing avg views per platform
- **Leaderboard**: Top 10 by YouTube Shorts and TikTok views
- **Cross-platform chart**: Avg views by piece across YT/TT/IG
- **Piece normalization**: `KNOWN_PIECES` dict maps title substrings to display names
- Stats import: YouTube (API scan), TikTok (Excel export), Instagram (CSV export)

## Content Strategy Insights
- **Best style for YouTube full videos**: Progressive House
- **Best style overall**: Vallenato (Colombian accordion) — unique differentiator
- **Best posting day**: Saturday 18:00-22:00 Zurich
- **Top performers**: Danse Macabre Irish (1453 YT), Clair de Lune Vallenato (1274 YT), Danse Macabre Vallenato (1253 YT)
- **Rule**: Always launch new pieces with Irish or Vallenato, never Progressive first

## Technical Notes
- `moviepy<2.0` required (2.x removed `.editor` submodule)
- `numpy<2.0` required (int64 frame dtype compatibility)
- Gradio 6.x: `theme` goes in `launch()` not `Blocks()`
- Windows asyncio `ConnectionResetError`: suppress with custom exception handler
