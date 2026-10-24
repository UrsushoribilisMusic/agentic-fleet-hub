# WORKLOG — TSC-1 (`2gghdork1p7ch7k`) — Build compilation C1: AI Will Do the Work, Vol. 2

## Plan
1. **Verify Trim Boundaries (§3.1)**:
   - Run `comp_parts.py C1` and inspect boundary frames for all 6 parts, especially `final_long` masters (`lChiYc1A4B8`, `jxi-GUpdhYI`, `Miw8TeG3RFI`).
   - Fix `comp_parts.py` so `final_long` out-point uses `narration_end(p, d) + 0.15` directly (since `pipeline.py` appends a silent 5s `SUBSCRIBE` outro card, `narration_end` already sits before both the NotebookLM trailing silence and the `SUBSCRIBE` card; stepping back to an earlier scene cut clipped ~35s of actual narration).
   - Verified C1 trim points:
     1. `7UPyRA9cBtE` (`raw_cinematic`): `0.00` → `498.87` (`498.87s`)
     2. `lChiYc1A4B8` (`final_long`): `17.67` → `273.89` (`256.22s`)
     3. `Vritr444eKs` (`raw_cinematic`): `0.00` → `405.01` (`405.01s`)
     4. `jxi-GUpdhYI` (`final_long`): `11.53` → `311.99` (`300.46s`)
     5. `Miw8TeG3RFI` (`final_long`): `16.50` → `367.30` (`350.80s`)
     6. `JFhLTSY7Pxw` (`raw_cinematic`): `0.00` → `289.16` (`289.16s`)
     - Total parts runtime: `2100.52s` (`35m00.5s`).
2. **Generate Cold Open Motion Clips & Channel Hook VO (§3.2)**:
   - Generate two 10s 16:9 motion clips (`clip_a.mp4` and `clip_b.mp4`) using the exact prompts in `COMPILATION_PLAYBOOK.md` §3.2.
   - Composite title card overlay on Clip B and layer under ~20s channel hook VO (ElevenLabs Alice / Kokoro `af_bella`).
3. **Render Transition Cards (§3.3) & Standard Outro**:
   - Render 5×4s chapter transition cards (`TWO`..`SIX`) over dimmed stills from each following part with slow push-in (`zoompan`) and `0.5s` crossfade/fade in and out.
   - Render 5s standard `SUBSCRIBE` outro card once at the end.
4. **Assemble Final Compilation (§3.4)**:
   - Normalize all segments to `1920x1080 @ 30fps`, `yuv420p`, `aac 44100Hz mono` and concat into `final_comp.mp4` (~35m45s, right in the 35–38 min target).
5. **Captions & Private YouTube Upload (§3.5)**:
   - Generate `en,de,fr,ja` captions via `subs_gen.py`.
   - Upload private to YouTube (`The Classical Remix`) with question-framed title, chapter timestamps, and links to all 6 original videos.
6. **Close the Loop (§3.6)**:
   - Add compilation #10 (or C1 entry) to `tech-shorts/compilations.json` with exact published title, YouTube ID, date, topic (`Economy & Work`), and verbatim `members` list.
   - Re-run `python3 gen_insights.py` and verify row appears in `insights.json` and on the droplet.
   - Update `standups/2026-10-24.md` and `standups/index.json`, commit, push, and mark `2gghdork1p7ch7k` `peer_review`.
