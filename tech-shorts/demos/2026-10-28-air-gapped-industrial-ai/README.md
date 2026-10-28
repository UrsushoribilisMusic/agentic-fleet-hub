# Air-gapped industrial AI — YC product demo

The approved story and reproducible first-cut tooling live here, within Tech
Shorts. This is a custom product demo, separate from the one-minute founder
video. It has no channel intro, subscribe outro, product names in narration,
music bed, burned subtitles, automated job record or upload action.

- `script-approved.md`: Miguel's approved narration, opening/ending preserved.
- `generate_voice.py`: cached/offline Kokoro narration, paragraph timing.
- `build_demo.py`:1080p/30fps composition, timed native feedback animation,
  real iPhone footage, historical images and gently panned backend captures.
- `source-manifest.json` / `CREDITS.md`: provenance, asset type and attribution.
- `validation-v1.json`: duration, frame counts, audio measurements and hash.

Canonical local media:
`~/flotilla/tech-shorts/assets/2026-10-28-yc-air-gapped-industrial-ai/`

Open `review.html` there for the MP4, chapter seeking, still contact sheet,
script, sources and shot-replacement notes. V1 is148.9s,1920×1080, local Kokoro
af_bella, narration−16.7LUFS /−4.4dBTP, no music. English SRT is separate; its
intra-paragraph times are proportional estimates for review.

Fresh captures needed before external use: a consistent target-product phone
interaction visibly offline; live backend navigation/reviewer action; camera
OCR of equipment text. Existing actual phone footage comes from Canis, backend
stills from Sovereign Mind. The old14s animated walkthrough was inspected but
is not presented as an actual screen recording in this cut.

Rebuild using the existing music-video-tool .venv312:

```sh
HF_HUB_OFFLINE=1 /Users/miguelrodriguez/projects/music-video-tool/.venv312/bin/python generate_voice.py
/Users/miguelrodriguez/projects/music-video-tool/.venv312/bin/python build_demo.py
```

Keep bulk assets local. Remove only this production's affected segment cache
files when changing a visual, then rebuild. Publishing requires a separate
user instruction. Source video masters were hard-linked to avoid disk duplication.
