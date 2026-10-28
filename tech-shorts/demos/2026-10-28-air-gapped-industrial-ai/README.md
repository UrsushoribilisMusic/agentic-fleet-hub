# Air-gapped industrial AI — YC product demo

## Current cut: V2

`~/flotilla/tech-shorts/assets/2026-10-28-yc-air-gapped-industrial-ai/v2/review.html`

MP4: `~/Downloads/Air-Gapped-Industrial-AI-Demo-v2.mp4` (148.9s,1080p/30fps).
The original approved narration/AAC is reused exactly, with separate captions.
All four newly supplied Sovereign Mind recordings are used: technical questions,
sourced answers, settings/knowledge packs/models/personas, abrasives Wiki and
figures, chat history, German/Spanish interactions, camera capture and OCR.
Canis appears only for its disposition panel at62.67–69.87s. Backend reviewer
visual remains an existing console capture; no new live approval is fabricated.

Camera lead-in starts before the camera narration. Capture view begins112.7s,
“camera” is spoken113.1675s; extracted text is visible114.65s while “available
text” is spoken114.7425s. The extracted-text field is then enlarged for clarity.
Some typing/generation/focusing waits are trimmed; this is not a speed benchmark.

- `build_v2.py`: composition using real footage and the original audio.
- `validation-v2.json`: exact frame counts, source hashes and matching audio hash.
- `source-manifest-v2.json`: all four master recordings and content mapping.
- `script-approved.md`: unchanged approved narration.

The canonical root `review.html` opens the current V2. V1 remains intact at
`review-v1.html` and its original MP4. New recordings and exports are hard-linked
where possible, avoiding duplicate master/final data. No upload or automatic
Tech Shorts publishing job is created.

Rebuild with music-video-tool's existing .venv312:

```sh
/Users/miguelrodriguez/projects/music-video-tool/.venv312/bin/python build_v2.py
```

V2 uses V1's existing historical/diagram segments and approved audio as inputs.

## Original V1 production notes

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
