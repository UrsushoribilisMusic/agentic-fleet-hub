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

## YouTube Monetization Strategy — Three Phases

Decided 2026-04-18. Do not deviate without Miguel's explicit sign-off.

### Phase 1 — Subscriber Acquisition (current, until 1,000 subs)
- **Goal**: Hit YouTube Partner Program threshold (1,000 subscribers)
- **Ad targeting**: All countries and territories — maximize cheap volume
- **Campaign focus**: Subscriber conversions (YouTube engagements goal)
- **Cost per subscriber**: ~CHF 0.11 (blended paid + organic multiplier)
- **Do not change**: geo targeting, bid strategy, or campaign structure during this phase
- **A/B test running**: Individual CHF 4/day (Maximize conversions) vs Shared budget (Target CPA)

### Phase 2 — Watch Hours (1,000 subs → 4,000 valid public watch hours)
- **Goal**: Hit the second YPP threshold (4,000 valid public watch hours in 12 months)
- **Ad targeting**: Still broad (all countries) — watch hours count equally regardless of geography
- **Campaign focus**: Switch to promoting **full-length videos** (not Shorts — Shorts watch time does NOT count toward the 4,000 hour requirement)
- **Geo targeting**: Keep broad to maximize view volume cheaply
- **Key action**: Run ads on full-length video URLs, not Short URLs

### Phase 3 — Revenue Maximization (post-monetization)
- **Goal**: Maximize YouTube ad RPM and streaming royalties
- **Ad targeting**: Switch to high-RPM geographic markets only:
  - **Tier 1** (RPM $6-9): UK, Germany, Switzerland, Austria, Netherlands, Sweden, Norway, Denmark, Finland, USA, Canada, Australia, New Zealand
  - **Tier 2** (RPM $3-6): France, Italy, Spain, Belgium, Ireland, Japan, South Korea, Singapore
  - **Middle East** (RPM $3-5): UAE, Saudi Arabia, Qatar, Kuwait, Israel
  - **Latin America** (RPM $1-3): Brazil, Mexico, Argentina, Colombia
- **Why**: Indian/South Asian audience (currently 11.9% of views) pays ~$0.15 RPM vs $9.13 in UK. Same content, 60x revenue difference.
- **Campaign code**: Modify `tcr_campaign_manager.py` and `tcr_ads_live_executor.py` geo targeting when entering this phase

### Why This Order
Subscriber and watch hour thresholds must be hit before monetization unlocks. Cheap broad traffic is the fastest path to those thresholds. Switching to high-RPM targeting too early wastes budget acquiring subscribers from low-value markets before there's any revenue to optimize.

### Revenue Expectations (realistic)
| Stage | Monthly views | Est. monthly YouTube revenue |
|-------|--------------|------------------------------|
| Phase 1 (current) | 74K | $0 (not monetized) |
| Phase 2 | 150-300K | $0 (not monetized) |
| Phase 3 entry | 300K | ~$300-600 (high-RPM audience) |
| Phase 3 mature | 1M+ | ~$1,000-3,000 |

DistroKid streaming royalties (Spotify, Apple Music) are additive and geography-independent — pursue in parallel regardless of phase.

---

## Technical Notes
- `moviepy<2.0` required (2.x removed `.editor` submodule)
- `numpy<2.0` required (int64 frame dtype compatibility)
- Gradio 6.x: `theme` goes in `launch()` not `Blocks()`
- Windows asyncio `ConnectionResetError`: suppress with custom exception handler
