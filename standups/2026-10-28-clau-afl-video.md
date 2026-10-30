# Clau — 2026-10-28 (Ambient Field Lens submission video)

Session ran from the token reset through past midnight. Lane: the submission video,
while Muse and Codi stay on the live path. No PocketBase tickets — Miguel dispatches
this project personally.

## Completed

### Rubric and submission analysis
- Pulled the Cerebral Valley rubric verbatim (the page is client-rendered; extracted from
  the embedded JSON). **Impact 30% / Meta AI Tooling 25% / Demo 25% / Technical Depth 20%.**
- Key finding: **Stage Three ranks the top 5 per track by watching the video demos.** The
  video is both the gate into the finals and the artifact ranked inside them — the single
  most leveraged asset in the submission.
- Submission form (from Miguel): **3-minute cap, YouTube-hosted**, Startups track,
  Push the Frontier, plus three required prose fields that map almost one-to-one onto the
  Meta-tooling criterion. Optional Most Viral Track X-post link.

### Corrections that affect what goes on screen
- **Codi caught a mislabel in my first draft.** 0.889 vs 0.861 is the *last candidate
  token*, not prefill. At **true prefill — where the gate actually scores — both methods
  reach 1.000.** Recorded in the brief so it cannot leak back from an old chat scroll.
- Added: even at the late endpoint the gap is one pairwise flip (32/36 vs 31/36, both
  ordering 6/6 pairs correctly). The report's own "no demonstrated Jacobian advantage"
  is the accurate sentence; "the simple one won" would have been an overclaim.
- Flagged **not to put AUROC 1.000 on screen as a win** — perfect separation on 24 pairs
  with 2 topic clusters and an unresolved length confound reads as leakage to an
  ML-literate judge. It ships stated as a pilot, with n and limits on screen.
- Conceded my px→mm clearance figures are an order-of-magnitude argument, not a
  measurement (Codi's point). Not to be cited as the basis for a containment decision.

### Demo design — three states, not two
- Followed through on Codi's architecture note: the readout assesses support for the
  instruction, the world checks detect displaced paper. **The planned two-state demo
  (well-placed vs displaced, same question) only ever exercises the world checks** — the
  grounding readout returns the same answer in both takes.
- Demo now needs **three states and a repair**, with State 3 (setup perfect, *unsupported*
  question → amber from the footing check) protected above all others. It is the only
  state where the readout fires on camera.
- If only two states are achievable, **drop green**, not State 3.

### Deliverables — `~/Downloads/afl-demo-brief/`
- `DEMO_PATH_BRIEF.md` — the directive for Muse and Codi: one scene end to end, done-means
  criteria, the split, the containment-clearance unblock, a stop-doing list, and dates
  rebuilt around Miguel's availability (Paris Sat/Sun, meetings Mon/Tue). Filming split in
  two so ~80% of footage needs no backend. Go/no-go Monday evening, not Wednesday.
- `animatic/` — **a complete 2:58 animatic of the submission video**: real Kokoro narration,
  real data graphics computed from our own saved all-layer scores, and labelled placeholder
  cards for every shot still to be filmed. Rebuilds in ~1 min (`voice.py` then `build.py`).
- `animatic/SHOTLIST.md` — generated from the placeholders, with animatic timecodes.

### Animatic — six iterations with Miguel
1. v1 structure → v2 fixed the hook per **3-7-21** (v1 wasted the first 3s on silence).
2. v3 made "the gap" concrete ("what your manual is missing") and named the **RAG**
   explicitly; added two diagrams, the second modelled on the YC knowledge-feedback loop.
3. v4 added the **real Wiki review screen** (Approve & Publish / Show Diff) at zero runtime
   cost, labelled `PRIOR WORK — DISCLOSED`. It converts "a human approves" from assertion
   to evidence and turns the disclosure into an Impact asset.
4. v5 moved the **technical flex to beat two** — a judge must wonder "they did *what* to
   Glimmer?" by 0:30, not 0:45.
5. v6 (final tonight) — activations planted at 0:10, drama dialled down, two claudisms cut,
   help-desk comparison removed, stakes made proportionate (a sheet of paper here, the part
   on a production machine), Meta glasses added to the pipeline diagram, loop diagram
   redrawn (the return arrow pointed backwards into the refusal box), close double-nails
   the activations.

Three on-screen label categories are kept visually distinct: amber = to shoot,
grey = prior work, unmarked = new.

## Notes for the team
- Codi's index entry reports live SAM/Ross/Glimmer providers verified in PR11 and an H100
  raw prefill score served — that is the hard part of State 1/3 moving.
- **Muse: confirm whether you can run autonomously off the dispatcher over the weekend.**
  If not, Sat/Sun is Codi alone and Muse's integration compresses into Thu/Fri/Mon.
- Shoot day 1 is **Friday Oct 30** regardless of code progress — it is Miguel's last full
  day and needs no backend.

## Blockers
None for the video. The animatic's remaining gaps are all labelled placeholders, and the
amber-only fallback cut shares the same structure, so neither branch costs a day.

## Status
Animatic v6 delivered at 2:58 against the 3:00 cap. Next: resync SHOTLIST timecodes,
draft the three submission-form texts, and get the Simulator HUD capture running against
the real default-deny backend.
