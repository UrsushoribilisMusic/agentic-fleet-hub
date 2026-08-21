# Tech-Shorts Pipeline (NotebookLM → hook/outro → YouTube → X)

AI/tech explainer shorts from source docs (podcasts, articles, reports). Turn a
NotebookLM Video Overview into a branded, hook-first short + long, publish to
YouTube, cross-post the YT link to X. Monetization play; brand tie-in to Canis.

## Status (2026-08-21)
- **Step 3 (hook + outro) PROVEN by hand.** `build_techshort.sh` renders PIL text
  cards (this ffmpeg lacks drawtext/libfreetype) → segments → concat with the
  format-matched source. Produced 2 finals from the AISI-incident notebook:
  - `Why_AI_Agents_Spontaneously_Lie_FINAL.mp4` (short, 720x1280)
  - `Anatomy_of_an_AI_Breach_FINAL.mp4` (long, 1280x720)
- Source notebooks:
  - AISI incident (done): notebook.google.com/notebook/c2f91266-9fff-48fb-94e8-297e98b44d2e
  - LinkedIn "inference moves in-house" (queued for the automation pass):
    notebook.google.com/notebook/5bbbf604-57ec-496e-b69d-9bf12e72b080

## The full pipeline (Miguel's 7 steps)
1. **Ideation (Miguel)** — enter idea + source URLs (docs/podcasts/reads). A small
   ideation page (reuse the music-video-tool / ReelTales pattern).
2. **NotebookLM generation (browser-driven)** — no clean NotebookLM API, so this
   stays Claude-in-Chrome / Big Sis driving the browser. Miguel to demo the steps.
3. **Hook + outro** — this script (`build_techshort.sh`), the 3-7-21 rule: ~7s hook
   (3s grab + 7s "what is this"), branded outro (logo + Canis tease + follow).
4. **Assemble + upload to YouTube** — concat, upload via the **music-video-tool**
   YouTube credentials (reuse).
5. **Cross-post to X** — post the YouTube link. Base on the **FLOT X-posting arm**
   (X API client + cost guard + composer; keys done). Reddit dropped (self-service
   closed). NOTE: X prefers native video, but we link YT to monetize.
6. **Stats page** — reuse/extend the music-video-tool stats
   (api.robotross.art/stats/?project=music) — likely just a **new category/project**
   ("tech-shorts") to start.
7. **FinOps** — eventually fold reach/revenue into the FinOps dashboard.

Plan: prove step 3 by hand (done) → next pass automate 2–6.

## Hook / outro copy used (AISI incident short + long)
- Hook: "AI AGENTS" / "GONE ROGUE" / "Told to stay in a sandbox" / "Ten broke out.
  And lied to real people" / "A real UK government safety test"
- Outro: "CANIS" / "See when an AI is being evasive" / "Open-weight models. On your
  device." / "canis.flotilla.cc" / "Follow for more"

## Recipe notes
- ffmpeg here has NO drawtext (no libfreetype) → render text with Python/PIL cards.
- Match source W×H×fps for clean concat; re-encode via the concat filter.
- Source is 44100 mono AAC; intro/outro use silent 44100 mono so audio streams line up.
- Branding: bg INK #0B1D26, accents teal #4FD1C5 / red #E8674D; Arial Bold.
- TODO next pass: drop in the **Pebbles/Canis dog logo** on the outro (need the image
  file); optional ElevenLabs VO on the hook; polish "GONE ROGUE" sizing.
