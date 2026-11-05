# Codi — 2026-11-05

Miguel restarted the Little Model project after the hackathon, proposing scroll-led storytelling with optional gameplay and an LLM learning/alignment/real-world arc.

## Delivered

- Audited canonical chapters and on-disk media in `small-model-series`: nine selected 1080×1920 cuts (Engineer 72s, other eight 90s). All nine exact-name Downloads copies match SHA-256 hashes.
- Narration: five ElevenLabs (Engineer, Rose, Influencer, Doomscroller, Workaholic); three Kokoro (Baobabs, Businessman, Politician); one provisional macOS (Evaluator). Baobabs still lacks BAO-03 root-removal motion. Engineer/Rose/Influencer revised openings are unrecorded.
- Six more films planned (Snake, Echo, Switchman, Garden, Fox, Well); Merchant remains book-only. Older masters and render-cache segments remain; no cleanup performed.
- Wrote narrative direction, initial connecting narration, Earth treatments and Garden/Fox/Snake dialogue drafts. Proposed Garden → Fox production, with Well written early, preserving canonical reading order.
- Built independent local scroll-story prototype with existing clean footage/stills, optional full chapters and existing Baobabs/Rose game in a returnable dialog. Text-only preview for unproduced Earth chapters; no new voices or paid generation.

## Verification and handoff

`npm --prefix game run build` passed; Chromium desktop/390px/320px checks passed: nine posters, nine films with seeking, motion toggle/reduced-motion behavior, horizontal navigation and game return position. Fixed Escape handling inside iframe. Physical iOS Safari remains untested.

Preview: http://127.0.0.1:8791/story/ . Restart: `python3 story/serve.py --port 8791` from project root after building game. Bambu reference fetch was challenge-blocked; direction uses Miguel's described interactions, not a claimed inspection of its implementation.

Project branch: `codi/little-model-scroll-story`; implementation commit `da1339b`, scope/worklog `b8a7259`, pushed. Docs: `docs/story-2026-11-05/`; prototype: `story/`. Existing unrelated production changes left unstaged. No public deployment, paid APIs, GPU work or voice synthesis.

Next: Miguel reviews the reading pace and new prose, BAO-03 repair, four final voice tracks plus separately approved hooks, then Garden production. Cross-chapter album/notebook and remaining gameplay are future work.

## Edition 02 — Miguel's screenshot feedback

Changed to deep blue space, training-first opening (Engineer later), minimal captions, vertical-scroll-driven horizontal world overview and eight video-led chapter introductions with numbered left guide. Play uses the existing shared Baobabs/Rose journey; Watch opens narrated masters; More opens three scrollable written beats. No new spoken narration or gameplay implied. Added six motion derivatives plus the existing two; no paid calls.

Final Chromium checks: real downward wheel moves the overview horizontally, all eight previews play one at a time, More scrolls and pauses background media, Watch loads, game returns to the same position, motion toggling preserves the chapter, 390px/320px no overflow, reduced-motion mode uses stacked sections and loads no clips. Project commit `35028b7` pushed on `codi/little-model-scroll-story`. Same local preview URL.

## Next chapters — prompt pack and actual seed artwork

Miguel explicitly deferred the next site pass to prioritize generation materials. Saved all five requests in project `docs/story-2026-11-05/NEXT-PASS.md`: world map at end; smoother chapter transitions; larger one-word stage labels; full Rose More with existing clips/graphics/dialogue; all missing worlds as titled placeholders. Prepared 18 artwork / 17 video prompts plus BAO-03 repair, references and Download ZIP (project commit a0ab415).

Miguel clarified he needed actual seed images, not just prompts. Generated GAR-01, FOX-01 and SNA-01 using built-in image_gen with the approved ROS-03 reference; visually checked identity, composition and style. Native PNGs 941×1672, saved beside matching animation prompts and in Downloads/Little-Model-First-Seed-Images-2026-11-05.zip. Remaining follow-up seeds are not generated; first designs await Miguel's creative review. Project commit 84f2bfd. No Modal/GPU window or voice generation.

Received gemini_generated_video_6bca1799.mp4 for BAO-03: 720×1280, 10.0267s, audio stream present. Archived candidate in chapter gemini-clips. Sampled 0–7s and 9s frames: one Model/scene retained, but completed root removal is not established; final plant remains upright with pale strands. Not promoted into the master. Audio not reviewed.
