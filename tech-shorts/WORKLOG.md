# WORKLOG — TSC-2 (`9o8v196i9cd8ppi`) — Build compilation C2: The Attack Surface in Your House

## Plan & Execution
1. **Verify Trim Boundaries (§3.1)**:
   - Run `python3 -I comp_parts.py C2` and inspect boundary frames for all 7 parts, including the 3 `final_long` masters (`ECuneH0hPcg`, `KbxsK1LlVSw`, `n0J3a4-1rmY`).
   - Record human-verified `in = 12.96s` override for `KbxsK1LlVSw` in `comp_parts.py` (`VERIFIED_IN_OVERRIDES`), because the hook card (`#0b1d26`) cuts to a dark 3D glass cube on black at `12.96s` (`lavfi.scene_score = 0.177 < 0.40`).
   - Verified C2 trim points:
     1. `ECuneH0hPcg` (`final_long`): `16.70` → `301.98` (`285.28s`)
     2. `KbxsK1LlVSw` (`final_long`): `12.96` → `296.80` (`283.84s`)
     3. `n0J3a4-1rmY` (`final_long`): `12.90` → `228.04` (`215.14s`)
     4. `D-LV9YJN2ZM` (`raw_cinematic`): `0.00` → `309.67` (`309.67s`)
     5. `GLLa6t_MQuA` (`raw_cinematic`): `0.00` → `304.02` (`304.02s`)
     6. `lZ_LLtp8Ulo` (`raw_cinematic`): `0.00` → `355.55` (`355.55s`)
     7. `cRgmoG-XqkQ` (`raw_cinematic`): `0.00` → `480.46` (`480.46s`)
     - Total parts runtime: `2233.96s` (`37m13.96s`).
2. **Cold Open Motion Clips & Channel Hook VO (§3.2)**:
   - Built `intro.mp4` (`20.00s`) using `gemini_intro_20s.mp4` in `/Users/miguelrodriguez/flotilla/tech-shorts/assets/2026-10-25-compilation-c2-the-attack-surface-in-your-house/` with `_intro_title_overlay.png` composited over the second half (`t >= 10.8s`) and Kokoro `af_bella` channel hook VO (`c2_hook_vo.mp3`) underneath.
   - Guarded `shutil.copy2(GEMINI_INTRO, raw_dest)` in `build_c2.py` so reruns reuse `OUT_DIR / "gemini_intro_20s.mp4"` without requiring `~/Downloads` access.
3. **Render Transition Cards (§3.3) & Standard Outro**:
   - Rendered 6×4s chapter transition cards (`TWO`..`SEVEN`) over dimmed stills from each following part with slow push-in (`zoompan`) and `0.5s` fade in and out.
   - Rendered 5s standard `SUBSCRIBE` outro card once at the end.
4. **Assemble Final Compilation (§3.4)**:
   - Normalized all segments to `1920x1080 @ 30fps`, `yuv420p`, `aac 44100Hz mono` and concatenated into `final_comp.mp4` (`2283.17s` = `38m03s`).
5. **Captions & Private Upload (§3.5)**:
   - Stitched `en,de,fr,ja` `.srt` captions (223 blocks each) via `stitch_c2_subs.py` and uploaded private via `upload_c1_c2.py` to YouTube (`https://www.youtube.com/watch?v=S2vV_Nca80g`).
   - Added Compilation `#11` (`S2vV_Nca80g`, *"What Is Running on Your Living Room Network? The Attack Surface in Your House"*, `"status": "private"`) to `tech-shorts/compilations.json` with all 7 verbatim member titles (kept separate from queued compilation `#8`).
6. **Human Release Gate (§3.5, §3.6 & Codi Peer Review `eif6frkopq5gvo0`)**:
   - Checked live YouTube status via YouTube Data API v3: unlike C1 (`6y2y-4UETU4`, now `public`), C2 (`S2vV_Nca80g`) is still `privacyStatus: "private"` (`uploaded 2026-10-25T11:37:04Z`).
   - Per Playbook §3.5, Clau's note (`u7zy8c4ffkw7x36`), and Codi's review (`eif6frkopq5gvo0`), retain `waiting_human` with a clear question to `@miguel` to review `https://www.youtube.com/watch?v=S2vV_Nca80g` in YouTube Studio (attach staged EN/DE/FR/JA `.srt` captions, confirm synthetic content setting, and flip to `public`), after which `#11` can be flipped to `"status": "live"` in `compilations.json` and `gen_insights.py` re-run.
