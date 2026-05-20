# ReelTales — Agent Context

*Read this before picking up any RT-* ticket. Updated May 2026.*

---

## What is ReelTales?

A Shopify-to-YouTube story video pipeline. Customers submit a personal story through the Shopify storefront; the pipeline generates a short cinematic vertical video (AI visuals + captions + narration or music-only) and uploads it to YouTube. The customer receives a proof link immediately after ordering.

**Products on the Shopify store:**
| Product ID | Language | Format |
|---|---|---|
| 10813488857425 | Swiss German (de-CH) | Modern Reel |
| 10813499834705 | Swiss French (fr-CH) | Modern Reel |
| 10813508976977 | Swiss Italian (it-CH) | Modern Reel |
| 10813513924945 | Rumantsch (rm) | Modern Reel |
| 10817592787281 | English (en) | Modern Reel |
| (legacy) | English (en) | Fable |

---

## Repo & Links

| Resource | Value |
|---|---|
| Code repo | `~/projects/music-video-tool/` |
| Order dashboard | https://api.robotross.art/reeltales/ |
| Shopify store | https://reeltales.robotross.art (separate) |
| Kanban | https://github.com/users/UrsushoribilisMusic/projects/3/views/1 |
| Auth | Google SSO via `/auth/` (same as fleet hub) |

---

## Pipeline Overview

```
Shopify webhook → server.mjs (DO)
  → stores order in /var/lib/salesman-api/reeltales-orders.json
  → status: "new"

Mac Mini polls GET /reeltales/orders/incoming
  → claims order (status: "claimed")
  → runs pipeline_runner.py

pipeline_runner.py steps:
  1. Write text.txt from story text
  2. Copy music track → audio.mp3
  3. Download style image (if provided)
  4. gen_story_modern.py (Apertus 70B for CH langs, Claude for EN)
     → hook.txt, first_image_prompt.txt, runway_prompts.txt, captions.txt
  5. runway_first_image.py → first_frame.png (Runway gen4_image t2i)
  6. runway_chain.py → clips/clip_01..09.mp4 (gen3a_turbo, fallback gen3a)
  7. narrate_fable.py → narration.wav (ElevenLabs; skipped for de-CH, rm)
  8. assemble_modern.py → final.mp4
  9. upload_fable.py → YouTube

Throughout: push_status(), push_assets(), push_thumbnail() keep the dashboard live.
```

---

## Key Scripts

| Script | Purpose |
|---|---|
| `scripts/pipeline_runner.py` | Master orchestrator — runs all steps end-to-end |
| `scripts/gen_story_modern.py` | Claude / Apertus: generates hook, prompts, captions |
| `scripts/runway_first_image.py` | Runway gen4_image: seed frame for clip chain |
| `scripts/runway_chain.py` | Runway gen3a_turbo: 9-clip video chain |
| `scripts/assemble_modern.py` | FFmpeg: assembles final video |
| `scripts/narration.py` | ElevenLabs: voice narration (EN/FR/IT only) |
| `scripts/upload_fable.py` | YouTube upload via OAuth |

---

## Language Rules

- **de-CH / rm**: Apertus 70B model, music-only (no ElevenLabs narration), Schweizerdeutsch dialect captions
- **fr-CH / it-CH**: Apertus 70B model, ElevenLabs narration in target language
- **en**: Claude Sonnet, ElevenLabs Brian voice narration
- HOOK and CAPTIONS in target language; FIRST_IMAGE_PROMPT and RUNWAY_PROMPTS always English (Runway only understands English)

## Runway Model Strategy

- **Primary**: `gen3a_turbo` — `768:1280` ratio, 10s clips, ~$0.50/clip
- **Fallback**: `gen3a` — same ratio, used only when gen3a_turbo hits daily task limit
- **Seed frame**: `gen4_image` t2i via runway_first_image.py (~$0.10-0.15)
- gen4.5 is NOT used anywhere in the pipeline

---

## DO Server Auth

- Pipeline Mac Mini uses `ARTIST_API_TOKEN` as Bearer token
- Dashboard uses Google OAuth session cookie (same SSO as fleet hub)
- POST endpoints (claim, complete, thumbnail, assets, status) require ARTIST_TOKEN
- GET /reeltales/orders/all accepts either ARTIST_TOKEN or valid session cookie

---

## Order Status Flow

`new` → `claimed` → `running` (with step label) → `complete` or `failed`

If failed: reset to `new` via `POST /reeltales/orders/{id}/status`, re-run pipeline.

---

*BigBear Engineering GmbH · ReelTales · May 2026*
