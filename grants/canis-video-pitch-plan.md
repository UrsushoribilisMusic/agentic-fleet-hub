# Canis — Prototype Fund video pitch plan (≤3 min)

**Goal:** a ≤3-min pitch (target 2:45–2:55) that the jury watches. Not a promo reel — the fund wants to meet the team + hear the vision, and see the project **answer the programme questions** (responsible + sustainable AI). Must cover: a strong hook, the expressions reel, J-Space (Jacobian), Apple MLX / on-device, Apertus + Ministral, personal RAG, and the responsible/sustainable framing.

## Approach
- **Format:** founder-authentic. Mix of (a) PL briefly on camera (hook + close, for warmth/credibility), (b) screen-recording of the app / the **existing expressions reel** as the main b-roll, (c) minimal text cards for the technical terms (J-Space, MLX, Apertus/Ministral, the 3 pillars).
- **Voice:** PL's own voice recommended (this is a "meet the team" video) — Alice British VO is the fallback.
- **Captions burned in** (accessibility + muted viewers). Subtle music bed. Canis palette (ink/teal/coral). Hard cap 3:00.

## Beat sheet (~2:55)

| # | Time | Beat | Visual | Narration (draft) | Programme axis |
|---|---|---|---|---|---|
| 1 | 0:00–0:18 | **HOOK** | Chatbot gives a confident answer → cut to the avatar beside it showing *uncertain/evasive* (expressions reel) | "This AI just answered with total confidence. But watch the avatar — it's not sure. And you'd never know from the words. Canis shows you what the AI won't." | grab |
| 2 | 0:18–0:38 | **Problem** | PL on camera, or text over reel | "As AI starts to act on its own, the real risk isn't what it says — it's that it looks equally confident whether it knows or is guessing. The public has no way to see the difference. That's a trust problem, and an AI-literacy problem." | Responsible AI |
| 3 | 0:38–1:00 | **What Canis is** | App demo — avatar cycling the ~8 expressions live | "Canis is an open-source app that reads a model's inner disposition — confident, uncertain, evasive, concerned — and shows it in real time as an expressive avatar, right on your phone." | Solution |
| 4 | 1:00–1:45 | **How it works** (the tech) | Text cards: J-Space (+ tiny formula), "Apple MLX · on-device", Apertus + Ministral logos | "Under the hood, instead of trusting the model's words, we read its hidden state directly — a technique we call **J-Space**: a forward-only Jacobian read of the model's own activations. No gradients, no second pass — light enough to run live on a phone. We run it **on-device with Apple's MLX**, on open-weight models: Switzerland's own **Apertus**, and **Ministral**. No data center required." | Feasibility + Sustainable |
| 5 | 1:45–2:10 | **Personal RAG** | User loads documents → avatar answers, face showing grounded vs guessing | "You can load your own documents to build specialized knowledge packs — and the avatar shows when the answer is grounded in your material, or when the model is just guessing. A hobby, a course, a manual — and we want people to share the packs they build." | Adoption / engagement |
| 6 | 2:10–2:35 | **Responsible & Sustainable** | Three text cards: Transparency · Accountability · Sufficiency | "This is responsible AI you can *see* — and sustainable AI by design: small, open models on your device, not a data center. Built on Switzerland's public model, it makes AI's inner state legible to everyone." | Responsible + Sustainable (core) |
| 7 | 2:35–2:55 | **Team + ask + vision** | PL on camera | "I'm [name] — I build on-device AI. In four months, kicking off at the Apertus hackathon, we'll ship the app, an honest evaluation of what it can and can't detect, and open it all up. Help us make what an AI is really thinking — visible." | Feasibility / motivation |

## Asset checklist
- [ ] **Reuse:** the existing avatar-expressions reel (primary b-roll for beats 1, 3).
- [ ] **Record:** 2 short talking-head clips — problem (beat 2, optional) + close (beat 7). Good light, clean audio.
- [ ] **Screen-record:** app demo — avatar reacting live (beat 3); personal-RAG document load + grounded/guessing (beat 5).
- [ ] **Text cards (5):** J-Space + formula `J = lm_head·(ln_weight/std(h_mid))`; "Apple MLX · on-device"; Apertus + Ministral logos; the 3 pillars (Transparency/Accountability/Sufficiency); title + end card (canis.flotilla.cc).
- [ ] Captions/subtitles burned in. Subtle music. Export ≤3:00, 1080p.

## Two decisions for Miguel
1. **On-camera vs voiceover-only?** (recommend PL on camera for beats 2 + 7, reel/screen-record for the rest.)
2. **Your voice vs Alice (British) VO?** (recommend your own — it's a team pitch.)

## Reuse from our pipeline
- The FFmpeg hook/outro + PIL text-card recipe (`tech-shorts/build_techshort.sh`) can render the text cards + title/end cards.
- ElevenLabs Alice VO path already wired if we go VO.

---

## FINAL NARRATION SCRIPT (locked 2026-08-23 — Miguel's hook, polished)
- **[0–3s · hook]** "Imagine you could **read** the disposition of the AI you're talking to."
- **[3–7s]** "When you speak with someone in person, their body language tells you a lot — are they being truthful? Do they doubt their own answer?"
- **[7–20s]** "That's what Canis does: it shows you the disposition of a language model *as you interact with it*. Because today, AI always sounds confident — whether it actually knows the answer, or is hallucinating it."
- **[20–45s · tech]** "Canis builds on Anthropic's disposition-lens research. It uses a **Jacobian-space read** to peek at the model's mid layers and capture its hidden state *as it prepares an answer*. We add an **entropy read** to resolve that into a disposition — mapped to eight states: idle, confident, uncertain, curious, concern, reluctant, warm, and mischief."
- **[45–62s · product]** "The result is an **iOS app** running local, **open-weight models**, presenting those dispositions as a friendly **dog avatar** — hence the name, Canis."
- **[62–82s · personal RAG]** "To make it genuinely useful, you can give the model the facts and documents you want it to base its answers on — and the avatar shows when it's **grounded** in your material, or just **guessing**."
- **[82–108s · responsible & sustainable]** "Everything runs **on your device**, on small open models — no data center — built on Switzerland's own **Apertus**, and **Ministral**. It's responsible AI you can *see*, and sustainable AI by design."
- **[108–128s · close]** "Over four months, kicking off at the Apertus hackathon, we'll ship the app, honestly evaluate what it can and can't detect, and open it all up. **Canis makes what an AI is really thinking — visible.**"

> Note: 8 core states confirmed in code (`DISPOSITIONS`); a 9th "searching" is visual-only — don't count it on camera.

## FINAL EDIT LIST (locked 2026-08-23 — Miguel's cut)
Intro is the ONLY on-camera part (authentic dev-office background — kept deliberately). Everything after is VO + screens.

| Section (narration) | Audio | On screen |
|---|---|---|
| **Intro** — hook + body-language + "what Canis does" | Miguel on camera (recorded `Teleprompter-2026-23-08_21-05-30.mov`; I boost audio) | the talking-head clip (dev office, carousel visible on the ultrawide) |
| **Tech** — "Jacobian-space read… entropy read…" | VO | **Fig 3 · J-Space** (formula/flow — purpose-built for this line) |
| **…"mapped to eight states…" → Product** | VO | **Fullscreen carousel** — avatar cycles the 8 states as they're named, runs on through the product line |
| **Personal RAG** | VO | **Fig 2 · two-flow diagram** (Flow A build/share + the grounds-the-answer connector) |
| **Responsible & Sustainable** | VO | **Fig 1 · Architecture** (on-device, no data center) |
| **Close** | VO | carousel settles on a warm expression → **end card** (below) |

**Close (proposed):** the carousel lands on a warm/confident expression, we push in on the avatar, then cut to a clean **end card** — "Canis" wordmark · tagline *"Makes what an AI is really thinking — visible."* · three chips *Open-source · On-device · Built on Apertus* · canis.flotilla.cc. It ties the closing "visible" line to the avatar's face; no camera needed. (Alt: an 8-expression grid resolving to the wordmark.)

**Voice for the VO:** recommend **Miguel's own voice** (audio-only, easy in Voice Memos) for cohesion with the on-camera intro; Alice British is the fallback.

**Assembly (me):** boost intro audio → VO over the cues above → PIL end card → export ≤3:00. Reuses `tech-shorts/build_techshort.sh`.
Diagrams artifact (export PNGs): https://claude.ai/code/artifact/b2a957cb-d880-47e7-ad48-f04c88e4c695
