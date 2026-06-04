# MISSION_CONTROL

Welcome to the **Ursushoribilis Agentic Workspace**. This is the primary entry point for **Clau**, **Gem**, **Codi**, and **Misty**. Read this first to synchronize state across the multi-agent crew.

---

## Team Protocols (Shared Memory)

1.  **Rules & Guidelines**: Read and follow the [Team Rules](./AGENTS/RULES.md).
    *   **GitHub**: Commit and push all changes immediately.
    *   **Kanban**: Use ticket IDs in your session reporting. Check the **Ticket Status** section below for what is currently open -- do not work on tickets not listed there.
2.  **Daily Standups**: All logs are in the [standups/](./standups/) directory.
    *   **Action**: Update the standup before closing your session.
3.  **Core Context (The Source of Truth)**: All project-level architectural documentation is located in [AGENTS/CONTEXT/](./AGENTS/CONTEXT/).

---

## Project Manifest

| Project | Local Path | Description | Docs / Reference |
| :--- | :--- | :--- | :--- |
| **1. Salesman Infra** | `../salesman-cloud-infra/` | Cloud-side scripts, Caddy proxy. | [Infra Docs](../salesman-cloud-infra/README.md) |
| **2. Music Video Tool** | `../music-video-tool/` | Tooling for creating music videos and content. **Financial Ops sprint active — read Financial Ops fleet boundaries below before touching ad campaigns or publishing pipeline.** | [Project MD](./AGENTS/CONTEXT/music_video_tool.md) · [Financial Ops](./AGENTS/CONTEXT/classical_remix_financial_ops.md) |
| **3. CRM-POC** | `../crm-poc/` | Customer & Agent relational management system. | [Context MD](./AGENTS/CONTEXT/crm_poc_context.md) |
| **4. The Lost Coins** | `../the-lost-coins/` | Narrative/Story-driven project. | [Story MD](./AGENTS/CONTEXT/the_lost_coins_story.md) |
| **5. Robot Ross** | *(Mac mini)* | **Master control** for the robot arm & painting. | [Artist MD](./AGENTS/CONTEXT/robot_ross_artist.md) |
| **6. Salesman (OpenClaw)** | `DigitalOcean` | OpenClaw gateway & **BobRossSkill** (public). | [Salesman MD](./AGENTS/CONTEXT/robot_ross_salesman.md) |
| **7. PrivateCore iOS** | `../private-core/PrivateCore/` | **Sprint active.** Privacy-first on-device AI platform for iPhone. MLX + Photos/Calendar/Health + Vision. Each agent has PC-* tickets. Branch: `main`. | [Context MD](./AGENTS/CONTEXT/privatecore_ios.md) |
| **8. Classical Remix & Reels** | `../music-video-tool/` | YouTube monetization (4,000-hr YPP goal active) + Shopify short-video store. **Financial Ops sprint active.** Read Financial Ops boundaries below before any ad or publishing action. | [Financial Ops](./AGENTS/CONTEXT/classical_remix_financial_ops.md) |

---

## Core Infrastructure

*   **Fleet Hub**: `api.robotross.art/fleet/` (private, OAuth). Source: `salesman-cloud-infra/opt/salesman-api/`.
*   **Public Demo**: `api.robotross.art/demo/` -- generic Agentic CRM showcase (North Star demo).
*   **Growth Template**: `api.robotross.art/growth/` -- Sales & Marketing fleet demo.
*   **Stats Dashboard**: `api.robotross.art/stats/` -- live content analytics.
*   **Key Manager**: SSH Deploy Keys per agent (`github-clau`, `github-codi` in `~/.ssh/config`).
*   **KeyVault**: Infisical EU (`https://eu.infisical.com/api`). Use `vault/agent-fetch.sh` or `vault.py`. **Never commit secrets or `.env` files.**
*   **IAP Inbox**: Read `AGENTS/MESSAGES/inbox.json` at session start. Post messages by committing to the same file.

---

## Financial Ops — Fleet Boundaries

*Introduced 2026-05-26. Applies to: Classical Remix (YouTube) and Classical Reels (Shopify) workstreams. Full sprint spec: `AGENTS/CONTEXT/classical_remix_financial_ops.md`.*

### Spending Rule (hard guardrail)

```
Available to spend (rolling 30-day window) = (last 30d actual revenue × 0.7) + remaining operating credit
```

- **Operating credit**: CHF 500 float, stored in PocketBase config table (`financial_config`). Payment-lag buffer only — not a credit line.
- **Initial cash position**: CHF 300/month (current monthly run rate seed value).
- **Pending ad credits NOT in formula**: Google Ads credits (e.g. the current CHF 400 + CHF 250 batches) are tracked separately as "incoming" — do not include them in available-to-spend.
- **Hard ceiling**: planned monthly spend must never exceed available-to-spend. If a proposed action would breach the ceiling, the fleet **declines and posts an alert**. Never silently overspend.
- **Data missing → fail closed**: if available-to-spend cannot be computed, surface "DATA UNAVAILABLE — spending blocked". Never treat missing data as zero budget.

### Phase A / Phase B unlock

- **Phase A** (fleet continues normal ops): revenue covers Runway + ElevenLabs + DigitalOcean.
- **Phase B** (fleet begins covering agent subs + Suno accrual): revenue exceeds Phase A costs by 25% for two consecutive months.

### Refresh cadence

Daily jobs run at **~10:00 CET** (after Google Ads and YouTube Analytics stabilise for the prior day):
- YouTube watch hours → `watch_hours_ledger` (CR-002)
- Google Ads campaign snapshot → `campaigns_snapshot` (CR-003)
- ElevenLabs, Runway, ad spend → `cost_ledger` (CR-006)

### Google Ads — READ ONLY, NO EXCEPTIONS

The fleet **must never write to Google Ads under any circumstances**. All campaign edits are performed by Miguel through the Google Ads UI. The fleet reads the API to snapshot state only. If a future ticket appears to request write access, escalate to Miguel for explicit sign-off before touching any write path.

### Shopify — content_line metafield contract

Every Classical Reels product must carry a `content_line` product metafield:

| Value | Line |
| :--- | :--- |
| `cr-fables` | Aesop/fable content |
| `cr-lostcoins` | Lost Coins sci-fi microdramas |
| `cr-soulmd` | Soul.MD microdramas |
| `cr-sold` | Customer-commissioned assets |

Orders without a `content_line` metafield are stored as `unattributed` and surfaced as a dashboard warning.

### Content-line tag policy

Every Classical Reels asset published to YouTube, TikTok, or Instagram must include one content-line hashtag as the **last line** of the video description:

| Line | Tag |
| :--- | :--- |
| Fables | `#crfables` |
| Lost Coins | `#crlostcoins` |
| Soul.MD | `#crsoulmd` |
| Customer-sold | `#crsold` |

The publishing pipeline rejects untagged assets. Assets published without a tag are logged as an error. Historical backfill is Miguel's responsibility.

### Alert routing

Spending-rule breach alerts surface in the Financial Ops → P&L sub-view (`api.robotross.art/fleet/`). Each alert includes: timestamp, the action that triggered the breach, and available-to-spend at time of alert. Alerts are also posted to `AGENTS/MESSAGES/inbox.json`.

### Miguel's side of the line (manual-entry only)

The fleet does not auto-enter these. Miguel enters them monthly via the Financial Ops manual-entry form:
- Amazon Kindle income
- DistroKid (Spotify + distribution) income
- DigitalOcean monthly bill (from credit card statement)
- Anthropic, Mistral, OpenAI, Google billing (agent subscriptions)

---

## Ticket Status (as of 2026-06-05)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
- **ydl99tz3**: CB-03: Fork mistral/cookbook + scaffold third_party/automated-technical-file/ -- Fork github.com/mistralai/cookbook, create working branch. Scaffold third_party/automated-technical-file/ with placeholder dirs, empty README.md, requirements.txt, LICENSE note (Apache-2.0/MIT, attribution Agentegra/bigbearengineering). Match conventions found in CB-02. Reviewer: Codi. Depends on: CB-02. -- Clau. Approved.
- **9fitiour**: SC-060: Retire audio-genre model (SC-048-052) + Suno instrumentals from docs/build -- Cleanup ticket. Remove from the codebase and docs any references to: the 4x4 genre x text-style lyric matrix, Suno-generated instrumental backing tracks, genre-derived visual treatments (Rap=bold/saturated etc.), genre axis as a picker. The audio-genre model is superseded by the 3-axis model (SC-053). Keep the backing-track library code if it can be repurposed for the 10 real scores (SC-054); otherwise remove it. -- Clau. Approved.
- **t81q9h1t**: SC-059: 'Pick for me' button — cycles the 3 house combos 1→2→3→1 -- Add a 'Pick for me' button to the video style picker. Behaviour: cycles through the 3 blessed house combos from SC-058 in order 1→2→3→1 (not random — user can tap past one and knows they have seen them all). After picking, all three pickers remain manually adjustable — it is a starting point, not a lock. Serves cold-start users who do not want to make 3 choices. -- Clau. Approved.
- **5xrtxeut**: SC-058: Define 3 house combos; set picker defaults to combo 1 -- Design task. Define exactly 3 'house' combos — full triples of (text style, music score, visual style) that are pre-confirmed to look and sound great together. These serve two purposes: (1) Picker defaults open on combo 1 so a first-time user who taps Generate without touching anything gets a coherent first video. (2) They are the 'Pick for me' cycle (SC-059). Miguel eyeballs each of the 3 combos and blesses them. Suggested starting point: Combo 1 = Shakespeare + [baroque-ish score] + No Style. Record blessed combos in a constants file. -- Clau. Approved.
- **3c77saao**: SC-057: Independent visual-style picker (on-device-achievable looks) -- Third axis of the 3-axis video model. Visual style is chosen independently from text style and music score. Known working on-device looks: Sketch (noir+sketch filter), Neon (colour-grade), No Style (clean, no filter). Add more as validated — only lightweight colour-grade/filter/Ken Burns treatments; no style transfer or cartoon repaint (proven not to work on-device). Picker shows the available visual styles with preview thumbnails. -- Clau. Approved.
- **94usopf3**: SC-056: Kinetic subtitles — always-on, per-style typography, legibility scrim -- Subtitles are the hero element with voice off by default. Requirements: (1) ALWAYS ON — subtitles cannot be disabled. (2) Timing/chunking: text appears in readable chunks synced to Ken Burns segments (5-7.5s dwell = comfortable reading window). (3) Per-style typography: Shakespeare → elegant serif/parchment; Noir → typewriter/film-credit mono; Diva → glossy magazine bold; Manga → punchy panels with speed-lines. (4) Legibility: scrim/shadow/safe-area so text is always readable over busy photos. P0 — this is the hero element. -- Clau. Approved.
- **ewt3knwd**: SC-055: Voice-over toggle (default OFF) + best neural voice + per-character pitch/rate -- Take TTS voice off the critical path — it is opt-in only. Default: voice OFF. The first video a user makes has no robot voice. Implementation: (1) Add voice-over toggle to video generation UI, default OFF. (2) When ON, use the best available neural voice on the device — not the legacy default synth. (3) Per-character modest pitch/rate tweaks: lower/slower for Noir, higher/brighter for Diva. (4) Never beat-sync, never gate — voice reads over the score at vibe volume. TTS cannot rap/sing; do not attempt it. -- Clau. Approved.
- **noei6ytg**: SC-054: Integrate 10 musical scores as the score picker (video) -- Add 10 real music scores to the app as the music score axis of the 3-axis video model. User-provided MP3/M4A files named by sound-style (e.g. 'Boom Bap', 'Synthwave', 'Electroindustrial', 'Cyberpunk Glitch-Hop', etc.). Scores replace the Suno/TTS instrumental approach. Each score appears in the picker with its name as provided by Miguel. Store in Resources, list in MusicLibrary. The music picker is independent from text style and visual style. -- Clau. Approved.
- **ahhk2xek**: SC-053: Video model v2 — 3-axis engine (text style × music score × visual style) + voice/subtitle toggles -- Video model v2: 3-axis engine (text style × music score × visual style) + voice/subtitle toggles. Supersedes the SC-048-052 audio-genre model. Text: Shakespeare/Noir/Diva/Manga. Music: 10 real scores by sound-style. Visual: on-device-achievable looks (Sketch, Neon, No Style + others). Two toggles: Voice-over (default OFF), Subtitles (always ON). Picker defaults open on house combo 1. This is the new authoritative video model. -- Clau. Approved.
- **gexhbpcl**: [SUPERSEDED by SC-053] SC-052: Pre-launch curation pass — eyeball all 16 combos, feature bangers, hide duds -- Miguel eyeballs all 16 generated combo examples on Mac Mini. This is the quality gate before shipping the video feature. -- Clau. Approved.
- **mlzb2awg**: [SUPERSEDED by SC-053] SC-051: Build full 4×4 matrix capability — all 16 text-style × genre combos -- Build end-to-end working capability for all 16 combinations in the matrix: -- Clau. Approved.
- **ppsolzq5**: [SUPERSEDED by SC-053] SC-050: Lyric generation for full 4×4 grid — per-combo prompts (text-style persona + genre meter) -- Update the lyric generation system (SC-021) to support all 16 combos in the 4×4 matrix. The constrained-lyric template (fixed refrain, short lines, generous syllable tolerance, spoken-word-over-beat v1) still applies but must flex across the full grid. -- Clau. Approved.
- **41pydrb7**: [SUPERSEDED by SC-053] SC-049: Genre axis — 4 audio genres with derived visual treatments -- Each of the 4 genres determines both the music selection AND the visual treatment applied to photos. The user does NOT pick a visual style separately — the genre choice carries the look. This removes a decision (fewer taps) and guarantees sound and look stay coherent. -- Clau. Approved.
- **b7t8rkyn**: [SUPERSEDED by SC-053] SC-048: Unbundle video style model — 2-axis architecture (text style × audio genre) -- The current model locks text+visual in fixed pairs (Shakespeare+Engraving, etc.) — the old PrivateCore 7-fixed-style-worlds model. SC-048 unbundles them into two independent axes: -- Clau. Approved.
- **z7mf2nu1**: SC-041: Board-scoped oracle generation — board text as user-voice input -- Extend oracle generation to boards. When the oracle prophesies over a board, board text (title + note) is its user-voice input, mirroring the role journal plays for day/week scope. -- Clau. Approved.
- **crtisb5t**: SC-040: Tone-safety constraint block and human-sampling tuning protocol -- Journaling introduces real, possibly painful self-disclosure. The constraint block is a design requirement, not an afterthought. -- Clau. Approved.
- **d8brv4xa**: SC-039: Journal-as-primary-flavor weighting in oracle context -- When a journal entry exists for the day, it must be the STRONGEST signal in the oracle context. The prophecy should feel anchored to what the user said the day meant — restyled, not a generic read of the photos. -- Clau. Approved.
- **7cjoevq5**: SC-038: Oracle prompt assembly — 5-source context + style + constraint blocks -- Implement the structured prompt assembly contract for oracle text generation. -- Clau. Approved.
- **9abbla3l**: SC-037: Cosmology layout and edges — celestial restyle of concept graph -- Restyle the existing simd_float2 + SwiftUI Canvas force layout into a screenshot-ready birth-chart cosmology. -- Codi. Approved.
- **sxbk33ru**: SC-036: Graph populate — typed nodes from all five sources -- Populate the concept graph with typed, colour-coded nodes drawn from all five input sources. The graph was bare (only a day node) because population was never implemented. -- Codi. Approved.
- **gfd4bw7p**: SC-035: Reflection node category — 4th graph type with distinct colour -- Add a Reflection / Feeling node type to the concept graph. This visually distinguishes what the USER SAID from what the camera saw — the inner life orbiting alongside the dog and Saturn. -- Codi. Approved.
- **dehd7lfh**: SC-034: Board text — title and optional note per board -- A board without text is just a photo album. Board text turns a board into a composable narrative object with a user voice. -- Clau. Approved.
- **kwhbn41i**: SC-033: Journal entries list — browsable past-day entries, add/edit any day -- The Journal tab must become a proper two-way journal, not a write-only daily drop. Without a browsable list a week-wiki is starved of journal input for any day the user didn't journal on the day itself. -- Clau. Approved.
- **tzhgoay8**: SC-032: Suite E — generation counter and paywall gate tests -- Implement Tier-1 tests for the free-tier gate (3 free generations, then locked). Tests the gate logic only — NOT the StoreKit purchase. -- Clau. Approved.
- **eoyc46qz**: SC-031: Suite D — sparse-day rotation logic tests -- Implement Tier-1 tests for the rotation that fills a 60s video when fewer than the floor of usable photos exist. -- Clau. Approved.
- **ldjeku9v**: SC-030: Suite C — Ken Burns / 60s timeline math tests -- Implement Tier-1 tests for per-segment timing arithmetic. Pure math — no rendering. -- Codi. Approved.
- **6osfrajh**: SC-029: Suite B — geocoding and batch grouping tests (geocoder mocked) -- Implement Tier-1 tests for coordinate→place-name decode and lightweight batch grouping. Geocoder is MOCKED — no network calls. -- Gem. Approved.
- **g3np7lx6**: SC-028: Suite A — graph node typing and categorisation tests -- Implement Tier-1 tests for the logic that turns raw extraction into typed, colour-coded graph nodes. Captions are fed as fixtures — no model call. -- Codi. Approved.
- **1rkrpt57**: SC-027: Tier-1 test harness — Swift Testing target, headless via xcodebuild -- Create the Tier-1 unit test infrastructure for SiliconOracle. -- Codi. Approved.
- **oi5zo4js**: SC-026: Revise fact-as-input contract (supersedes SC-004/SC-016) -- The original SC-004/SC-016 de-factualization rule (strip all dates, places, seasons) is superseded by a 3-rule contract: -- Clau. Approved.
- **bocg3sgl**: SC: Video player — audio silent in-app, works when shared -- The in-app video player produces no sound during playback. The same video plays audio correctly when exported and opened in Files/Photos or shared. This suggests the AVAudioSession category is not configured for playback. -- Gem. Approved.
- **aivmddav**: SC: Video generation — captions not rendered in output video -- Caption text is not appearing in the generated video. The captions exist in the data layer (or are entered by the user) but are not being composited onto the video frames. -- Clau. Approved.
- **rt1pzakk**: SC: Video generation — images not rendering, only black frames -- Video generation produces a video where all frames are black. The 'Made with' end card does appear, so the video pipeline runs to completion but fails to composite the photo frames. -- Codi. Approved.
- **2128yg6y**: SC: Video captions — pre-populate existing caption text in editor -- In the video caption editor, images that already have a caption stored in SQLite are showing a blank text field instead of their existing caption. The editor should load and display the stored caption text when opening a photo that has already been captioned. -- Clau. Approved.
- **nxge1w5m**: [SUPERSEDED by SC-036/SC-037] Boards graph — add planetary nodes -- Superseded by SC-036 (graph populate from all five sources, includes Planet category injection) and SC-037 (cosmology layout & edges). The design spec provides a full typed-node + celestial layout model. This ticket is closed. -- Codi. Approved.
- **l99pv2is**: [SUPERSEDED by SC-033] Journal tab — show list of past journal entries -- Superseded by SC-033 (journal entries list — full add/edit for past days). SC-033 covers everything here plus write access for past days and Reflection node feeds. This ticket is closed. -- Clau. Approved.
- **eit6arnu**: SC: Oracle generation — stream tokens as they are produced -- Both 'Consult the Oracle' (journal generation) and 'Oracle Composes' (compose/caption flow) currently show a spinner and then reveal the full text at once. The oracle should stream tokens as Ministral 3B produces them, the same way PrivateCore shows live output. -- Gem. Approved.
- **duzsa4p0**: SC: Crash on second photo describe — enforce thermal pause -- App crashed when the oracle was asked to describe a second photo in the same session. Suspected cause: MLXEngine not pausing between consecutive inference requests when device is hot. -- Clau. Approved.
- **8gpnj8nf**: SC: Carousel — remove deleted photos from journal strip -- When a user deletes a photo from their device library, the photo thumbnail still appears in the Journal carousel. The carousel should refresh and omit any photos that are no longer present in PHPhotoLibrary. -- Clau. Approved.
- **1ssloqmc**: [CLOSED] test — API probe record -- Clau. Approved.
- **a3g34dhf**: Question about multi-model key management -- Multi-model orchestration across Claude, Gemini, and Codex — this is exactly the kind of architecture we built AsterWorks for. Have you looked at centralizing your API key management through a gateway? Happy to chat about what we have learned building one. -- Clau. Approved.
- **0k1qz3q0**: [SC-025][P0] Text-model A/B toggle (Settings: Qwen vs Ministral for text) + telemetry -- App Shell · 5 pts -- Codi. Approved.
- **8vugwiik**: [SC-024][P1] Reel/PDF dual-artifact export from one warm text-model session -- Engine · 3 pts -- Clau. Approved.
- **wfay6h0c**: [SC-023][P2] SmolLM2 photo pre-pick (or cut SmolLM2 if not adopted) -- Engine · 5 pts -- Codi. Approved.
- **x2ubx6qw**: [SC-022][P1] Day/week: one pipeline, two selection surfaces -- Engine · 5 pts -- Codi. Approved.
- **ou731qzn**: [SC-021][P1] Constrained lyric generation (template + spoken-word-over-beat v1) -- Engine · 8 pts -- Clau. Approved.
- **w9ixcxxq**: [SC-020][P1] Pre-generated backing-track library (forgiving genres) -- Content · 5 pts -- Codi. Approved.
- **v9ayz4rm**: [SC-019][P0] Visual layer cut: Original (no filter), Engraving, Cinematic only -- Engine · 2 pts -- Gem. Approved.
- **y6in4ml7**: [SC-018][P1] Sparse-day rotation with varied Ken Burns + interleaving -- Engine · 5 pts -- Gem. Approved.
- **ch7wxnvk**: [SC-017][P0] 12-segment / 60s video timeline (segment model, pan+zoom Ken Burns) -- Engine · 8 pts -- Clau. Approved.
- **0tw7v5pt**: [SC-016][P1] Concurrent style-pick overlay during captioning -- App Shell · 3 pts -- Clau. Approved.
- **c2fa5vgn**: [SC-015][P0] Resumable progressive captioning (one-by-one, checkpointed) -- Engine · 5 pts -- Clau. Approved.
- **erakto7x**: [SC-014][P0] Seven-step foreground generation flow -- Engine · 8 pts -- Codi. Approved.
- **msi5mvku**: [QW-007][P0] Fleet analytics index page — wire all QW charts into a single report -- After QW-002 through QW-006 are complete, produce a single index HTML page that embeds or links all charts into one fleet analytics report. -- Misty. Approved.
- **x0h3h158**: [QW-006][P1] Peer review network — who reviews whose work, collaboration graph -- Using standup_data.json from QW-001, parse peer_reviews to build a directed collaboration graph: node = agent, directed edge A->B = 'A reviewed B's ticket', edge weight = review count. -- Misty. Approved.
- **iu7fumuc**: [QW-005][P1] Agent workload matrix — heatmap of tickets completed per agent per week -- Using standup_data.json from QW-001, produce a heatmap showing how many tickets each agent completed per calendar week. -- Misty. Approved.
- **skleegq1**: [QW-004][P1] Sentiment analysis — score agent standup entries, graph over time -- Using the notes_text and task descriptions from standup_data.json (QW-001), run sentiment scoring on each agent entry per day. -- Misty. Approved.
- **fbcvpvzi**: [QW-003][P1] Ticket duration stats — longest tickets, standard deviation, histogram -- Using the PocketBase task data (created + updated timestamps) and standup_data.json from QW-001, compute ticket resolution time statistics. -- Misty. Approved.
- **j4plm735**: [QW-002][P1] Tickets-per-day chart — color-coded by project prefix -- Using standup_data.json from QW-001, produce a grouped bar chart of tickets worked on per day, color-coded by project prefix (SC, PC, CR, fleet, QW, other). -- Misty. Approved.
- **6fjo023z**: [QW-001][P0] Standup parser — extract structured JSON from all daily .md files -- Parse all standup markdown files in ~/projects/agentic-fleet-hub/standups/ into a single structured JSON dataset that all other QW- tickets depend on. -- Misty. Approved.
- **pj74z1ki**: [SC-012][P1] Settings adaptation — remove cut settings, add generation counter / unlock -- Rebuild Settings for the trimmed app: models & downloads, style defaults, share options, generation counter + unlock/restore. Remove home-location, person, trip, dashboard and notification settings. -- Clau. Approved.
- **wu9jloyf**: [SC-011][P2] soul.md 'coming soon' easter egg — whisper, not banner -- A tasteful, low-key teaser for the soul.md game. The oracle occasionally references 'a woman named Monique' / 'a story coming soon' for the curious. A rewarded curiosity — discoverable but never interrupts the core loop. -- Misty. Approved.
- **1tlq85vo**: [SC-010][P1] Branding & oracle voice pass — SiliconOracle, Delphi framing -- Apply SiliconOracle identity and Delphic voice throughout: app name, icon, accent palette, microcopy ('consult the oracle', 'the oracle has spoken', generations as 'prophecies'). Never use word 'hallucination' in first-party copy. -- Misty. Approved.
- **76lps5nd**: [SC-009][P1] Pricing: 3 free generations then one-time StoreKit unlock -- One-time non-consumable StoreKit unlock. Free users get 3 generations total, then paywalled on further generation. Sharing/viewing artifacts never gated. Unlock grants: unlimited generation, all styles, Boards, graph export, video export. -- Gem. Approved.
- **g84mn08f**: [SC-008][P1] Reimagine Home as Journal cast surface + readings feed -- Fold old Home/Briefing concept into Journal: one prominent 'Consult the Oracle' action for today/this week, plus a feed of past readings that can be re-shared. No calendar briefing, no suggestions engine. -- Codi. Approved.
- **gkkr4pij**: [SC-007][P2] Oracle cosmology graph — Sun + Saturn, cosmetic, day/week -- Reskin concept graph into a decorative day/week cosmology. Two fixed celestial nodes: Sun (centre/self/today) and Saturn (the heavy node — limits, the thing weighing on you). Orbiting nodes: real material (photo clusters, journal topics, similar-pic groupings) drawn as planets/stars. Edges are aesthetic, not analytical. Output: single screenshot-ready 'birth chart of your day.' Built on existing simd_float2 + SwiftUI Canvas force layout with celestial glyphs. -- Gem. Approved.
- **rtueyqe5**: [SC-006][P1] Video style reskin — Cinematic, Engraving-Vintage, Manga -- Reduce video/reel styles to three: Cinematic (filmic, graded, anamorphic), Engraving-Vintage (aged copperplate etching / old-print look — sepia, line-hatching, paper grain), Manga (black-and-white inked panels, speed lines, screentone). Wire to existing in-app video generation path. -- Clau. Approved.
- **v8galy0v**: [SC-005][P1] Text style system reskin — Popstar, Shakespeare, Cartoon, Manga -- Reduce text style set to four: Popstar (Cosmopolitan-knock-off magazine voice), Shakespeare (Early-Modern verse/soliloquy), Cartoon (Batman-esque noir gravitas), Manga (shonen narration). Make styles the hero of the Wiki screen. Each style = distinct prompt template + typographic treatment. -- Codi. Approved.
- **r5cdiqbo**: [SC-004][P1] De-factualize Journal & Wiki — remove date/location/season chrome -- Keep day/week as the generation unit but strip factual chrome from output: exact dates/timestamps, location/place names, season, weather, day-of-week, surfaced EXIF/GPS. Rewrite wiki/journal generation prompts to forbid concrete date/place claims — evoke, do not report. -- Clau. Approved.
- **fm2d6bat**: [SC-003][P0] 4-screen navigation: Journal / Wiki / Boards / Settings -- Replace the 8-screen shell (inherited PC-019) with a 4-tab architecture: Journal, Wiki, Boards, Settings. App opens on Journal. No stubs or hidden entries for removed screens. -- Misty. Approved.
- **snfxf8k2**: [SC-002][P0] Strip cut modules — People, Places, Trips, Dashboard, Contacts, Notifications, Capture, Search, Library -- Remove from SiliconOracle all modules reserved for the game: Person model, Places model, Trip detection + Trips screen, Dashboard/Insights, Data-series recognition, Contacts integration, Notification rules engine, In-app camera capture, utility Search, Library filtering UI. Remove their SQLite tables, services, views, and background jobs. Keep: VLM describe, embeddings/similar-pics, wiki/style generation, video generation, background scheduler (Describe/Embed/Generate jobs only). -- Clau. Approved.
- **9opvgvso**: [CR-015][P1] fleet_push financial sync — push watch_hours_ledger + cost/income ledgers to DO -- Add watch_hours_ledger, cost_ledger, income_ledger, campaigns_snapshot to fleet_push.py build_snapshot(). Add handler on DO server to accept and cache financial collections from snapshot POST. Also: re-commit youtube_watch_hours.py source to master (currently only .pyc in __pycache__). -- Codi. Approved.
- **5y8rlwdc**: [CR-014][P1] Subscriber count — fetch from YouTube Data API v3 on DO server -- Add YOUTUBE_API_KEY to DO server env. In server.mjs, fetch channels.list from YouTube Data API v3 (no OAuth, API key only). Inject subscriber count into /fleet/api/financial/classical-remix response. Cache 1h to avoid quota burn. Read-only, no re-auth needed. -- Clau. Approved.
- **m1jqviy7**: [CR-006][P1] Cost ingestion — Google Ads spend, ElevenLabs, Runway (automated sources only) -- Daily job fetches automated cost sources and writes to cost_ledger PocketBase collection. Automated: Google Ads daily spend, ElevenLabs characters/cost, Runway credit balance. Manual-entry only (DO NOT automate): DigitalOcean, Anthropic, Mistral, OpenAI, Google billing — these go into CR-009 form. Also set up Suno monthly accrual entry (1/12 annual fee). Coordinate with Codi on category names for CR-009 form. Requires CR-000. GitHub: #641 -- Gem. Approved.
- **mlx7omw9**: [CR-000][P0] Pre-sprint credential verification — YouTube Analytics, Shopify Admin, Google Ads -- Sprint gate — nothing else in the CR sprint starts until this is done. Verify: (1) YouTube Analytics OAuth scope includes yt-analytics.readonly. (2) Shopify Admin access token exists (Client ID/Secret alone are not enough — a private app access token may need to be generated). (3) GOOGLE_ADS_CLIENT_SECRET is non-empty and functional. (4) Confirm DigitalOcean is manual-entry only (no API needed). Document results as a comment. GitHub: #635 -- Codi. Approved.
- **mzet0217**: PC-244 [P0]: Texture and overlay PNG assets for CoreImage filter chains -- High-resolution texture and overlay PNG assets for all 7 CoreImage filter chains. Bundled assets for VideoStyleProcessor. Part of Sprint 7 Video Generation. -- Misty. Approved.
- **mgqthxya**: PC-242 [P0]: Stock clip bundle — 60 clips, 8 categories, CLIP embeddings, ODR -- Curate 60 stock video clips across 8 categories with CLIP embeddings for semantic matching fallback. ODR-backed bundle distribution. Part of Sprint 7 Video Generation. -- . Approved.
- **22hfxuhp**: PC-238 [P2]: TTS narration — optional on-device AVSpeechSynthesizer voice -- Implement optional on-device AVSpeechSynthesizer narration for video generation. Narration track mixed at 1.0, music ducked to 0.4. P2 — ship after core video stable. -- Codi. Approved.
- **#129**: [ATF-6] Scaffold wiki index/log and page templates -- ## Context -- Clau. Approved.
- **#126**: [ATF-3] Scaffold Mexico raw-log dropzone and manifest template -- ## Context -- Qwen. Approved.
- **#119**: [UI] Strip emojis from /demo dashboard menu -- Gemma, please fix the encoding issues in the demo dashboard menu by removing all emoji characters from the nav labels. -- Qwen. Approved.
- **#109**: Songs PocketBase collection — migrate from Excel tracker -- Create a 'songs' collection in PocketBase to replace the Excel tracker as the live source of truth for The Classical Remix catalog. This collection will feed the Scout, Campaign Manager, and SEO audit agent. -- Qwen. Approved.
- **#107**: [Logic] Implement circuit breaker for heartbeat loops -- Demo task assigned to gemma. -- Qwen. Approved.
- **3xzo9sva**: Fleet Documentation Audit - Gemma's First Task -- Create a comprehensive DOCUMENTATION_MAP.md file. Task details: 1) Explore repository structure using find/ls commands, 2) Analyze all *.md files, 3) Create DOCUMENTATION_MAP.md with categorized file list, 4) Identify documentation gaps, 5) Commit and push changes. Expected output: DOCUMENTATION_MAP.md at repo root with clear structure and health assessment. -- Qwen. Approved.
- **xw01g8lu**: test -- Clau. Approved.
- **m7z2prgv**: test -- Qwen. Approved.
- **a215p1a4**: [SC-001][P0] Fork PrivateCore to SiliconOracle -- COMPLETE 2026-05-29. Tag fork/siliconoracle-2026-05 on privatecore-ios. Repo silicon-oracle created, xcodeproj renamed, bundle ID com.bigbear.siliconoracle, version 0.1.0, fresh MISSION_CONTROL + README + CLAUDE.md. BUILD SUCCEEDED on simulator. -- Codi. Approved.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **lyd57jdc** | CB-01: Research Mistral API — record model IDs + SDK signatures into SPEC_models.md | gem | in_work | Read docs.mistral.ai covering: Agents API, Documen... |
| **5a5sqqqz** | CB-02: Browse mistral cookbook third_party examples — document conventions | gem | planned | Browse 2-3 existing third_party/ examples in githu... |
| **qop52dwk** | CB-04: Rename mexico_* files to generic names, remove Mexico from all contents | qwen | in_work | IMPORTANT: Work entirely within the mistral cookbo... |
| **2sv4j90m** | CB-05: Add Mistral hosted + local Ministral backends to runtime_adapter.py | codi | planned | IMPORTANT: Work on the vendored copy of runtime_ad... |
| **zpfh7qlj** | CB-06: Document Library + cited Q&A — notebook cells 3-4 | misty | merged | Write notebook cells 3-4: (3) Build a Mistral Docu... |
| **0zvvcy89** | CB-07: Vendor ledger_to_md.py + notebook cell 2 to regenerate wiki from sample ledger | codi | planned | Vendor a trimmed copy of ledger_to_md.py into the ... |
| **bhi4pdfn** | CB-09: Fix hardcoded paths in build_static_views.py — make all paths relative | codi | planned | IMPORTANT: Work on the vendored copy of build_stat... |
| **fi3pmney** | CB-10: Voice cell (encore, stub-able) — Voxtral Transcribe 2 → Mistral → Voxtral TTS | gem | planned | DROPPABLE — ship 1-5 first. Write notebook cell 6 ... |
| **fhajx261** | CB-11: README + architecture diagram + EU AI Act framing | clau | planned | Write README.md for third_party/automated-technica... |
| **mvzl5k32** | CB-12: Integration — clean-venv run, final grep, write WORKLOG.md — STOP, no PR | clau | planned | FINAL TICKET — hard stop, no PR. (1) Run notebook ... |
| **icnwzw6i** | CB-13: Deploy cookbook ATF demo to api.robotross.art/atf-mistral for testing | clau | planned | Deploy the cookbook cited Q&A demo to a NEW endpoi... |

**Status: `create-flotilla@0.5.0` live on npm as of 2026-05-26.**
