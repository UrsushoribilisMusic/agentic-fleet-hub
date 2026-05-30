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

## Ticket Status (as of 2026-05-30)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
- **pj74z1ki**: [SC-012][P1] Settings adaptation — remove cut settings, add generation counter / unlock -- Rebuild Settings for the trimmed app: models & downloads, style defaults, share options, generation counter + unlock/restore. Remove home-location, person, trip, dashboard and notification settings. -- Clau. Approved.
- **1tlq85vo**: [SC-010][P1] Branding & oracle voice pass — SiliconOracle, Delphi framing -- Apply SiliconOracle identity and Delphic voice throughout: app name, icon, accent palette, microcopy ('consult the oracle', 'the oracle has spoken', generations as 'prophecies'). Never use word 'hallucination' in first-party copy. -- Misty. Approved.
- **76lps5nd**: [SC-009][P1] Pricing: 3 free generations then one-time StoreKit unlock -- One-time non-consumable StoreKit unlock. Free users get 3 generations total, then paywalled on further generation. Sharing/viewing artifacts never gated. Unlock grants: unlimited generation, all styles, Boards, graph export, video export. -- Gem. Approved.
- **gkkr4pij**: [SC-007][P2] Oracle cosmology graph — Sun + Saturn, cosmetic, day/week -- Reskin concept graph into a decorative day/week cosmology. Two fixed celestial nodes: Sun (centre/self/today) and Saturn (the heavy node — limits, the thing weighing on you). Orbiting nodes: real material (photo clusters, journal topics, similar-pic groupings) drawn as planets/stars. Edges are aesthetic, not analytical. Output: single screenshot-ready 'birth chart of your day.' Built on existing simd_float2 + SwiftUI Canvas force layout with celestial glyphs. -- Gem. Approved.
- **r5cdiqbo**: [SC-004][P1] De-factualize Journal & Wiki — remove date/location/season chrome -- Keep day/week as the generation unit but strip factual chrome from output: exact dates/timestamps, location/place names, season, weather, day-of-week, surfaced EXIF/GPS. Rewrite wiki/journal generation prompts to forbid concrete date/place claims — evoke, do not report. -- Clau. Approved.
- **snfxf8k2**: [SC-002][P0] Strip cut modules — People, Places, Trips, Dashboard, Contacts, Notifications, Capture, Search, Library -- Remove from SiliconOracle all modules reserved for the game: Person model, Places model, Trip detection + Trips screen, Dashboard/Insights, Data-series recognition, Contacts integration, Notification rules engine, In-app camera capture, utility Search, Library filtering UI. Remove their SQLite tables, services, views, and background jobs. Keep: VLM describe, embeddings/similar-pics, wiki/style generation, video generation, background scheduler (Describe/Embed/Generate jobs only). -- Clau. Approved.
- **9opvgvso**: [CR-015][P1] fleet_push financial sync — push watch_hours_ledger + cost/income ledgers to DO -- Add watch_hours_ledger, cost_ledger, income_ledger, campaigns_snapshot to fleet_push.py build_snapshot(). Add handler on DO server to accept and cache financial collections from snapshot POST. Also: re-commit youtube_watch_hours.py source to master (currently only .pyc in __pycache__). -- Codi. Approved.
- **5y8rlwdc**: [CR-014][P1] Subscriber count — fetch from YouTube Data API v3 on DO server -- Add YOUTUBE_API_KEY to DO server env. In server.mjs, fetch channels.list from YouTube Data API v3 (no OAuth, API key only). Inject subscriber count into /fleet/api/financial/classical-remix response. Cache 1h to avoid quota burn. Read-only, no re-auth needed. -- Clau. Approved.
- **ul1r63fd**: [CR-012][P2] Investment ledger — sunk-cost tracker, visibility only -- Read-only cumulative sunk investment tracker. Seed investment_ledger PocketBase collection with CHF 300 (Miguel-confirmed 2026-05-26). Cumulative total shown on P&L view labelled: Total invested (visibility only — not a constraint). Updates automatically when cost_ledger entries are added. Does NOT affect spending rule. P2 — ship after P0/P1 stable. GitHub: #647 -- Codi. Approved.
- **146l3tu6**: [CR-011][P1] Classical Reels sub-view — four content lines, Shopify attribution -- Classical Reels sub-view inside Financial Ops tab. Four panels (Fables/Lost Coins/Soul.MD/Customer-sold), each showing: assets published last 30d, views (organic vs ad split), Shopify conversions. Aggregate Shopify orders row at top. Ad performance empty placeholder until campaigns launch. DEPENDENCY: CR-005 must ship first for per-line attribution. If CR-005 slips, ship aggregate-only view with banner: Per-line attribution pending — content tagging system (CR-005) not yet deployed. Depends on CR-001, CR-005. GitHub: #646 -- Codi. Approved.
- **du4xz6de**: [CR-010][P0] Classical Remix sub-view — chart, daily ledger, campaign phases, active ads -- Classical Remix sub-view inside Financial Ops tab. Components: (1) header metrics (current hours, projected YPP date, subscribers, 5-day velocity, hours remaining), (2) cumulative watch hours chart with 4000h goal line and phase shading (reuse existing charting lib, NO new deps), (3) last-5-days daily ledger table, (4) campaign phases table, (5) read-only active campaigns table from campaigns_snapshot. Post-4000h: header flips to monetization metrics. Depends on CR-001, CR-002, CR-003. GitHub: #645 -- Codi. Approved.
- **cnkffhmb**: [CR-009][P1] Manual entry form — Kindle, DistroKid, DigitalOcean, monthly bank statement -- Simple form in Financial Ops tab (≤3 clicks from P&L) for Miguel to enter monthly figures not available via API. Income: Kindle, DistroKid, Other. Costs: DigitalOcean, Anthropic, Mistral, OpenAI, Google Billing, Other. Entries immutable (corrections create new row with corrects_entry_id). Confirmation before submit. Written to cost_ledger / income_ledger PocketBase collections. Coordinate with Gem (CR-006) on category names. Keep it simple. GitHub: #644 -- Codi. Approved.
- **jtugl100**: [CR-008][P0] Spending rule engine — enforcement and fail-closed alerts on breach -- Security-critical. Implement spending rule as callable check + daily standing check. Rule: available_to_spend = (30d_revenue*0.7) + remaining_operating_credit. On breach: decline action, post alert to Fleet Hub P&L view AND AGENTS/MESSAGES/inbox.json. FAIL CLOSED: data unavailable = DATA UNAVAILABLE — spending blocked. Never treat missing data as zero. Write to spending_rule_log PocketBase collection. Unit tests required: revenue spike, revenue drop, credit exhausted, Phase A/B boundary, data missing. Any ambiguity: flag to Miguel. GitHub: #643 -- Clau. Approved.
- **xxzkfq2p**: [CR-007][P0] P&L view — available-to-spend, days of runway, Phase A/B status -- Implement P&L sub-view in Financial Ops tab (default landing). Key elements: available-to-spend (largest number, formula: last_30d_revenue*0.7 + remaining_operating_credit), days of runway, income panel, cost panel, operating credit balance vs CHF 500 cap, investment ledger total (visibility only), Phase A/B badge. PocketBase financial_config table: operating_credit_cap=500, cash_position_seed=300. Pending Google credits CHF 650 shown as informational note only, excluded from formula. Clau verifies math before merge. Depends on CR-001. GitHub: #642 -- Clau. Approved.
- **m1jqviy7**: [CR-006][P1] Cost ingestion — Google Ads spend, ElevenLabs, Runway (automated sources only) -- Daily job fetches automated cost sources and writes to cost_ledger PocketBase collection. Automated: Google Ads daily spend, ElevenLabs characters/cost, Runway credit balance. Manual-entry only (DO NOT automate): DigitalOcean, Anthropic, Mistral, OpenAI, Google billing — these go into CR-009 form. Also set up Suno monthly accrual entry (1/12 annual fee). Coordinate with Codi on category names for CR-009 form. Requires CR-000. GitHub: #641 -- Gem. Approved.
- **zond8lre**: [CR-005][P0] Content tagging system — per-publish line tags on Classical Reels assets -- Extend Classical Reels publishing pipeline (~/projects/music-video-tool/) to append a content-line hashtag as the last line of each video description. Tags: Fables=#crfables, Lost Coins=#crlostcoins, Soul.MD=#crsoulmd, Sold=#crsold. Pipeline rejects untagged assets. Shopify product creation sets content_line metafield. Miguel backfills existing Fables/Lost Coins/Sold videos. Soul.MD: no backfill needed. Blocking dep for CR-011. GitHub: #640 -- Codi. Approved.
- **9uh4f66u**: [CR-004][P0] Shopify ingestion — daily orders with per-content-line attribution -- Daily job pulls orders from Shopify Admin API (robotross.art store), writes to shopify_orders PocketBase collection. Fields: order_id, created_at, line_total, currency, product_handle, attributed_line, customer_country. Attribution via product metafield content_line (cr-fables/cr-lostcoins/cr-soulmd/cr-sold/unattributed). Idempotent. Currency stored as-is. Requires CR-000 credential check (Shopify Admin access token may need to be generated). GitHub: #639 -- Codi. Approved.
- **lov0tnox**: [CR-003][P0] Active campaigns viewer — read-only Google Ads campaign state snapshot -- Daily job (~10:00 CET) reads Google Ads campaign state, writes to campaigns_snapshot PocketBase collection. Fields: snapshot_date, campaign_name, status, daily_budget_chf, spend_7d_chf, locations_summary, audience_name. CRITICAL: zero write operations to Google Ads in any code path. Clau reviews for write paths before merge. Requires CR-000 credential check first. GitHub: #638 -- Gem. Approved.
- **4mg0akd2**: [CR-002][P0] Watch hours ingestion — daily YouTube Analytics pull with campaign-phase annotation -- Daily job (~10:00 CET) pulls valid public watch hours from YouTube Analytics API, appends to PocketBase watch_hours_ledger collection. Fields: audit_date, total_valid_hours, single_day_gain, campaign_phase_label, notes. Seed historical data Apr 14 – May 21 2026 (full table in GitHub issue). Manual phase-label table for Miguel. Requires CR-000 credential check first. GitHub: #637 -- Gem. Approved.
- **qkhuhnde**: [CR-001][P0] Financial Ops tab — new top-level nav and three sub-views in Fleet Hub -- Add Financial Ops tab to salesman-cloud-infra/opt/salesman-api/fleet/dashboard.html. Position between Projects and Kanban in sidebar nav (data-section-button pattern). Three sub-views: P&L (default landing), Classical Remix, Classical Reels. Follow existing visual language. Mobile-responsive at 390px. No regressions. Clau does design review before merge. Blocking dep for CR-007, CR-010, CR-011. GitHub: #636 -- Codi. Approved.
- **mlx7omw9**: [CR-000][P0] Pre-sprint credential verification — YouTube Analytics, Shopify Admin, Google Ads -- Sprint gate — nothing else in the CR sprint starts until this is done. Verify: (1) YouTube Analytics OAuth scope includes yt-analytics.readonly. (2) Shopify Admin access token exists (Client ID/Secret alone are not enough — a private app access token may need to be generated). (3) GOOGLE_ADS_CLIENT_SECRET is non-empty and functional. (4) Confirm DigitalOcean is manual-entry only (no API needed). Document results as a comment. GitHub: #635 -- Codi. Approved.
- **gv6vhzz2**: [CR-013][P0] MISSION_CONTROL update — spending rule, fleet boundaries, refresh cadence -- Review and verify the Financial Ops fleet boundaries added to MISSION_CONTROL.md (2026-05-26). The update has already been applied by Claude Code. Clau reads it, checks accuracy and completeness, corrects anything unclear, then marks peer_review. Hard prerequisite: must merge before any other CR ticket starts. Full spec in AGENTS/CONTEXT/classical_remix_financial_ops.md. GitHub: #634 -- Clau. Approved.
- **3lbwwa3s**: Security scan results: 5 shell injection risks in fleet_sync.py + 9 other findings -- Hey Miguel and the Flotilla crew — I've been following the project and really dig the vault-first approach and multi-agent architecture. -- Clau. Approved.
- **x42bo7ha**: PC-263 [P1]: VideoAssemblyEngine — no narration in generated video -- ## Bug -- Codi. Approved.
- **7d5y61ua**: PC-262 [P1]: VideoAssemblyEngine — no music plays in generated video -- ## Bug -- Gem. Approved.
- **p0yuhcav**: PC-261 [P1]: VideoAssemblyEngine — no subtitles/captions appear in generated video -- ## Bug -- Gem. Approved.
- **5971yzfq**: PC-260 [P1]: VideoAssemblyEngine — Ken Burns effect too tight, photos over-zoomed -- ## Bug -- Codi. Approved.
- **0hg403g0**: RT-011: ReelTales order dashboard -- ## Summary -- Clau. Approved.
- **0c981qnx**: PC-259 [P1]: WikiBrowserView — generated week wikis disappear after reload -- Generated week wikis appear in the browser momentarily but disappear when load() re-fires (on every view appear via .task). load() calls SQLiteStore.shared.fetchAllWikiArticles() — if the SQLite upsert failed silently the week wiki is gone after reload. Also: user wants all previously generated week wikis to remain visible in the Wiki section, not just the current week. Fix: (1) Add error logging to WikiArticleStore.save() so silent write failures surface. (2) Ensure WikiBrowserView shows ALL stored week articles (not just recent 5 weeks). (3) The .task re-fires on every appear — consider caching or only reloading on explicit pull-to-refresh. -- Codi. Approved.
- **itypd3kg**: PC-258 [P1]: WikiDayView — Add note sheet flashes and dismisses immediately -- Tapping Add Journal Entry in WikiDayView causes the JournalingView sheet to appear then immediately dismiss. Root cause: navigation to WikiDayView itself is unstable (see PC-257 — conflicting NavigationLink patterns in LibraryView cause the view to be pushed then popped). When the parent navigation unwinds, the sheet in the child view closes with it. Fix PC-257 first; this should resolve as a side effect. If it persists after PC-257, add .onChange(of: showingJournalEditor) { print("[WikiDayView] journal editor: \($0)") } to trace whether the state is being reset externally. -- Clau. Approved.
- **ugx23pr3**: PC-257 [P0]: LibraryView — day navigation broken due to mixed NavigationLink patterns -- Tapping empty day links on the library main page does not navigate. Root causes: (1) Deprecated NavigationLink(isActive:) in .background (line 87-94, document import nav) coexists with both NavigationLink(destination:) links AND .navigationDestination(isPresented:) modifiers — SwiftUI navigation stack conflicts when these mix. (2) The today + stalled day NavigationLinks (lines 304, 327) are in ScrollView > VStack without .buttonStyle(.plain), so scroll view can swallow taps. Fix: replace the NavigationLink(isActive:) in .background with a .navigationDestination(isPresented: $showCardDetail) equivalent; add .buttonStyle(.plain) to today/stalled day links. This is also the root cause of the Add note sheet flashing (PC-258). -- Clau. Approved.
- **2h1z41v5**: RT-007 [P2]: Shopify — create Swiss-language Modern Reel products and wire PRODUCT_LANGUAGE_MAP -- Shopify product IDs (robot-ross store): -- Clau. Approved.
- **kdn4oz0v**: RT-006 [P1]: gen_story_modern.py — Apertus 70B client for Swiss-language story generation -- Add --language arg to gen_story_modern.py. When language != "en": call swiss-ai/apertus-70b-instruct via https://api.publicai.co/v1/chat/completions (OpenAI-compat) using APERTUS_API_KEY from env (injected by Infisical). When language == "en": use existing LLM unchanged. Inject the target language/locale into the story generation prompt (e.g. "Write in Swiss German (Schweizerdeutsch)"). The APERTUS_API_KEY is already stored in Infisical EU project 3233b7c1-8309-447d-af5a-6541e38dc1b3 env=dev. Supported languages: de-CH (Schweizerdeutsch), fr-CH (Swiss French), it-CH (Swiss Italian). -- Clau. Approved.
- **qqiv4uw5**: RT-005 [P1]: pipeline_runner.py — add PRODUCT_LANGUAGE_MAP and detect_language() -- Add PRODUCT_LANGUAGE_MAP dict alongside PRODUCT_FORMAT_MAP in pipeline_runner.py. Implement detect_language(order) that reads product_id and returns a BCP-47 language code (default: "en"). Pass --language <code> as a CLI arg to gen_story_modern.py when fmt == "modern". Fable path unchanged — language is ignored there. Language codes to support: en, de-CH, fr-CH, it-CH. Add --language override arg to pipeline_runner.py CLI (like --format). Log the detected language alongside format. -- Codi. Approved.
- **7y2i94o3**: RT-004 [P1]: End-to-end test — Modern Story path with dummy order -- ## Goal -- Gem. Approved.
- **n4arcx7y**: RT-003 [P0]: assemble_modern.py — modern assembly with hook intro + subscribe outro -- ## Goal -- Clau. Approved.
- **w16ivb3k**: RT-002 [P0]: gen_story_modern.py — context-driven Runway prompts + hook question -- ## Goal -- Clau. Approved.
- **erwhktny**: RT-001 [P1]: pipeline_runner.py — detect product ID and pass format flag (fable|modern) -- ## Goal -- Clau. Approved.
- **hc1iggo2**: PC-256 [P1]: Video gen — com.apple.accounts Code=7 permission denied -- Codi. Approved.
- **uweus0mq**: PC-255 [P1]: WikiBrowserView — day navigation broken for ungenerated days -- Clau. Approved.
- **n3r0mzz4**: PC-254 [P1]: WikiGenerator — style application uses base sections + journaling (Step 3) -- ## Goal -- Clau. Approved.
- **57kivpe8**: PC-253 [P0]: WikiGenerator — smart VLM selection (max 1 new description per section window) -- ## Goal -- Clau. Approved.
- **flby0sfc**: PC-252 [P0]: WikiGenerator — base content layer (two-pass architecture) -- ## Goal -- Clau. Approved.
- **vw3qp1g6**: PC-251 [P1]: WikiDayView — style switch should not regenerate; reuse cached text -- **Bug:** Switching wiki style (e.g. to Shakespeare) triggers full LLM regeneration of all day sections. Unnecessary — the text can be reused; only the visual presentation changes. -- Clau. Approved.
- **jnuq7enn**: PC-250 [P1]: WikiDayView — remove loading veil; show skeleton only when zero content -- **Bug:** During wiki day generation, already-completed sections (Morning etc.) are covered by opacity/blur + WikiSkeletonView overlay. Cover photo hidden. The bottom progress spinner already handles in-progress feedback. -- Clau. Approved.
- **gpi0q42c**: PC-249 [P1]: Freemium gating — promotional vs clean outro by tier -- Video generation UNLIMITED for all tiers. Free = QR code outro. Pro = clean credit. Upgrade prompt in style confirm screen. 3pts. -- Gem. Approved.
- **2pzzrgga**: PC-248 [P0]: Video generation progress + AVPlayer preview -- Style-themed loading + Combine progress bar. AVPlayer preview on complete. Save to Camera Roll / Share / Regenerate actions. 5pts. -- Gem. Approved.
- **sk3spoxo**: PC-247 [P1]: Style confirmation screen — live CoreImage preview -- Suggested style + live filter applied to cover photo (<100ms). Style picker scroll. Music 10s preview. Narration toggle. 5pts. -- Gem. Approved.
- **uncjdgt1**: PC-246 [P0]: Photo curation screen — review LLM-selected photos -- Horizontal scroll. Remove (×), add (PHPicker), reorder (long-press). Min 3 / max 12. Privacy consent copy. Most UX-sensitive screen in sprint. 5pts. -- Gem. Approved.
- **5vun0hyb**: PC-245 [P0]: Video creation entry points in wiki article views -- video.fill SF Symbol in wiki header. Also WikiFooterView link. Opens VideoCreationFlowView as sheet. All wiki types. 3pts. -- Clau. Approved.
- **mzet0217**: PC-244 [P0]: Texture and overlay PNG assets for CoreImage filter chains -- High-resolution texture and overlay PNG assets for all 7 CoreImage filter chains. Bundled assets for VideoStyleProcessor. Part of Sprint 7 Video Generation. -- Misty. Approved.
- **17o4l9an**: PC-244 [P0]: Texture and overlay PNG assets for CoreImage filters -- 6+ textures ≥2048px: paper (1700s), grain (Vintage), halftone dots (Manga), neon glow (Cyberpunk), speed lines (Manga), watercolour paper. CC0. Miguel approves. 3pts. -- Gem. Approved.
- **8eknrrkr**: PC-243 [P1]: Music track integration and automatic selection -- 21 AAC tracks (3/style) as ODR. Auto-select by emotional tone. User override with 10s preview. Seamless loop. Note: Miguel delivers tracks. 3pts. -- Gem. Approved.
- **mgqthxya**: PC-242 [P0]: Stock clip bundle — 60 clips, 8 categories, CLIP embeddings, ODR -- Curate 60 stock video clips across 8 categories with CLIP embeddings for semantic matching fallback. ODR-backed bundle distribution. Part of Sprint 7 Video Generation. -- . Approved.
- **myowlsln**: PC-242 [P0]: Stock clip bundle — 60 clips, 8 categories, ODR -- Source CC0 clips (Pexels/Pixabay). Crop to 9:16. CLIP embedding per clip. SQLite index. ODR per style pack. Miguel approves selection. 5pts. -- Gem. Approved.
- **ucxd99fa**: PC-241 [P1]: Stock clip CLIP matching — semantic fallback -- When no user photo: embed caption, cosine similarity vs precomputed stock clip embeddings in SQLite. Min confidence 0.4. 3pts. -- Clau. Approved.
- **n8zirlgq**: PC-240 [P0]: WikiVideoScriptService — LLM moment selection -- SmolLM2 135M selects 5-8 moments from WikiArticle. Each moment: photoAssetId, captionText ≤60 chars, emotionalBeat. Test on Mac Mini first. 5pts. -- Clau. Approved.
- **e3o6vdxg**: PC-239 [P1]: Intro and outro assets — 7 style MP4s + runtime outro -- 7 bundled intro MP4s (2-3s, generated via CoreGraphics). Runtime outro renderer with QR code (free) or clean credit (Pro). 5pts. -- Gem. Approved.
- **22hfxuhp**: PC-238 [P2]: TTS narration — optional on-device AVSpeechSynthesizer voice -- Implement optional on-device AVSpeechSynthesizer narration for video generation. Narration track mixed at 1.0, music ducked to 0.4. P2 — ship after core video stable. -- Codi. Approved.
- **75ki5mr6**: PC-238 [P2]: TTS narration — optional on-device AVSpeechSynthesizer -- P2 — ship after core video stable. Optional narration track mixed at 1.0, music ducked to 0.4. 3pts. -- Codi. Approved.
- **zlcaak9u**: PC-237 [P0]: VideoAssemblyEngine — core AVFoundation compositor -- SPIKE MAC MINI FIRST. AVAssetWriter + CIContext per-frame pipeline. Ken Burns + transitions + captions + audio mix + intro/outro. Target < 30s for 5-photo video. 13pts. -- Clau. Approved.
- **le4im847**: PC-236 [P1]: CaptionLayer — styled text overlays per style -- Timed text composited per-frame. 7 typography treatments (Cinematic/Engraving/PopStar/Cartoon/Watercolour/Vintage/Manga). 5pts. -- Gem. Approved.
- **0aieglgj**: PC-235 [P1]: TransitionEngine — 7 style-appropriate cut types -- Build TransitionEngine with 7 style-appropriate cut types for the in-app video generation sprint (Sprint 7). AVFoundation-based, on-device only. -- Gem. Approved.
- **xesnfw8p**: PC-234 [P0]: KenBurnsAnimator — motion keyframes per photo -- Pan+zoom trajectories driven by EmotionalBeat. Face detection via CIDetector to prevent cropping. Pre-compute during photo curation screen. 5pts. -- Codi. Approved.
- **bhqe7fv2**: PC-233 [P0]: VideoStyle data model and CoreImage style processor -- 7 visual style filter chains, GPU-accelerated via Metal CIContext. Foundation of entire video system — must land first. 5pts. -- Codi. Approved.
- **wtb44nhk**: PC-081: Trips — tap photo opens blank detail page, no actions (add to people/board/hashtags) -- Returned to todo after review: routes through synthetic card/add-to-board only, but does not correctly implement photo-backed add-to-people / add-hashtag. -- Clau. Approved.
- **qrulqkkh**: PC-232: Concept graph — missing lines in graph view -- Imported from PrivateCore MISSION_CONTROL.md. -- Clau. Approved.
- **u5elcijk**: PC-230: Places — visit counts underreport multi-day place photos -- Imported from PrivateCore MISSION_CONTROL.md. -- Gem. Approved.
- **8d3lyfdm**: PC-228: Wiki day view — generate wiki / AI description actions do not complete -- Imported from PrivateCore MISSION_CONTROL.md. -- Codi. Approved.
- **hfng2al7**: PC-227: Wiki day view — remove duplicate edit-journal action and clarify rescan photos -- Imported from PrivateCore MISSION_CONTROL.md. -- Gem. Approved.
- **jqawd67z**: PC-225: Library — documents counter / top icon spacing is clipped -- Imported from PrivateCore MISSION_CONTROL.md. -- Misty. Approved.
- **fsj216xt**: PC-219: People — hide person should stop them reappearing in suggested groups -- Imported from PrivateCore MISSION_CONTROL.md. -- Gem. Approved.
- **5ihwuycn**: PC-218: Library wiki — weekly wiki sometimes does not show up -- Imported from PrivateCore MISSION_CONTROL.md. -- Misty. Approved.
- **sd2nwh29**: PC-217: Capture — Ask should allow writing a question before sending -- Imported from PrivateCore MISSION_CONTROL.md. -- Misty. Approved.
- **qqivywhl**: [FLOTILLA v0.5.0][P1] V05-PROFILE-006 Final v0.5.0 Release Prep -- ## Metadata -- Clau. Approved.
- **weekr00w**: [FLOTILLA v0.5.0][P1] V05-PROFILE-005 Add Smoke Tests for Profile-Pack Install Flow -- ## Metadata -- Clau. Approved.
- **xs2bnroq**: [FLOTILLA v0.5.0][P0] V05-PROFILE-004 Write PROFILE_PACKS.md as Agent Handoff Spec -- ## Metadata -- Clau. Approved.
- **j5hbqnn0**: [FLOTILLA v0.5.0][P0] V05-PROFILE-003 Add Profile Validator and Safe Overlay Rules -- ## Metadata -- Clau. Approved.
- **fwxfhcpr**: [FLOTILLA v0.5.0][P0] V05-PROFILE-002 Add Installer Support for Profile Directory and Zip Overlay -- ## Metadata -- Clau. Approved.
- **3z4r1bgw**: [FLOTILLA v0.5.0][P0] V05-PROFILE-001 Create Default Engineering Instruction Profile -- ## Metadata -- Clau. Approved.
- **sln025dz**: PC-208 [P1]: Global knowledge graph — all relationships across wikis, trips, boards -- The graph icon in the Library tab (currently wired to ConceptGraphView / the week graph) should show a full cross-entity knowledge graph, not a weekly scope. -- Gem. Approved.
- **izj6nmgp**: PC-207 [P2]: Remove Insights tab — surface top places in PlacesView header -- The Insights tab in Library is redundant: stats are already in Settings, and place information belongs in Places. Remove it and redistribute its content. -- Clau. Approved.
- **befyo4kv**: PC-206 [P1]: Documents row in Library Intelligence section -- Documents (PDF cards with type == .document) are a first-class content type but have no entry point in the Library Intelligence section. Add a "Documents" row alongside Wiki, People, Places. -- Clau. Approved.
- **rmrezewa**: PC-205 [P1]: Scoped knowledge graph per board and per trip -- After PC-198 (per-week hashtag graph) lands, add equivalent scoped graphs for boards and trips. Both reuse ConceptGraphView and the same node/edge types — only the data source changes. -- Gem. Approved.
- **t5hayl7d**: PC-204 [P0]: MLX generation queue — serialize concurrent callers to prevent app kill -- When multiple AI generation requests fire simultaneously (e.g. user taps Generate on multiple wikis at once, or VLMService.describeUndescribed() runs while WikiGenerator is generating), both callers load the 1.2GB Qwen model into memory at the same time. iOS kills the process due to memory pressure. -- Gem. Approved.
- **8aihe6xb**: PC-203 [P1]: Trip wiki stale text — fix caching of failed generation -- Trip wiki shows old text even after 3 regeneration attempts. Root cause: WikiGenerator caches the content hash after generation. When generation fails 3 times and a fallback article is returned, the fallback article hash is written to the cache. On the next generation attempt the new inputs hash matches the cached hash (because the inputs did not change), so WikiGenerator returns the stale cached article without attempting a new generation. -- Clau. Approved.
- **fnai7mul**: PC-202 [P1]: Board wiki — add regenerate button and text/hashtag edit -- When viewing a wiki for a Board (WikiContainerView opened from a board), there is no way to regenerate or edit the wiki content. The homepage wiki has a regenerate button; boards need the same. -- Clau. Approved.
- **y8gub7u7**: PC-201 [P1]: Remove generationPrompt leak from wiki article views -- WikiContainerView shows a DisclosureGroup("Generation prompt") containing the full system + user prompt stored in article.generationPrompt (set in WikiGenerator.generateStructuredWiki at line ~1155 as debugPrompt). In production this reveals internal prompting to the user and causes the "Moments" and "Highlights" section headers to appear as raw prompt text. -- Clau. Approved.
- **o9nxih0z**: PC-200 [P1]: People Photos picker — fix wrong picker and broken link button -- PersonDetailView has two bugs with the "Link to Photos People" feature (PC-191): -- Clau. Approved.
- **wetu3ozb**: PC-199 [P1]: Journaling — browse and edit previous entries -- Users need a way to view and edit journaling cards for past days, not just today. -- Clau. Approved.
- **quvxto1p**: PC-198 [P1]: Per-week hashtag graph -- Build a knowledge graph scoped to a single ISO week, accessible from the week wiki. -- Gem. Approved.
- **38lasxwv**: PC-197 [P1]: Week wiki generation -- Generate a weekly wiki article that aggregates 7 day wikis. -- Clau. Approved.
- **xz3n51oq**: PC-196 [P0]: Day wiki auto-generation pipeline -- After OCR + VLM batch complete for a given day, auto-trigger generateAndSaveDailyWiki(). -- Clau. Approved.
- **nrtcom3l**: PC-195 [P2]: Smoke test coverage for Sprint 5 features -- Extend PrivateCore SmokeTests v1 with test cases for all Sprint 5 features. Update the document at ~/Downloads/PrivateCore SmokeTests v1.docx (or create v1.1) and commit a markdown version to agentic-fleet-hub/docs/smoke_tests.md. -- Gem. Approved.
- **k5h37al4**: PC-194 [P1]: UITest target + privatecore:// deep link scheme -- Add a PrivateCoreUITests XCUITest target to the Xcode project and wire up a basic privatecore:// URL scheme so automated smoke tests can trigger app flows without human interaction. -- Clau. Approved.
- **jddbug2q**: PC-193 [P0]: Dispatcher-led agent triggering — eliminate idle heartbeat token burn -- Move from timer-based heartbeats to dispatcher-triggered agent waking. Gem has done the architecture analysis — assign to her. -- Gem. Approved.
- **8hedhdns**: PC-192 [P1]: WikiDayView — navigable day links and debug interface -- (1) Fix WikiNavigationService: parse date-format targets ('Monday 27 Apr 2026') → push WikiDayView instead of .notFound. -- Clau. Approved.
- **ywrqcxfm**: PC-191 [P1]: Link iOS Photos People to Person records + graph integration -- PersonDetailView: 'Link to Photos People' button opens PHPickerViewController with PHPickerFilter.people (iOS 16+). User selects face group → receive PHAsset IDs for all photos iOS attributes to that person. -- Clau. Approved.
- **ics2qdkg**: PC-190 [P1]: Similar photos — CLIP cosine search -- Add 'Similar photos' horizontal carousel to PhotoDetailView when clip_embedding_status = done. -- Clau. Approved.
- **y62gskkp**: PC-189 [P2]: Settings data section cleanup -- Keep in main list: Photos indexed, OCR, AI described (PC-187), Contacts, Calendar events, Cards, Trips detected, Last wiki generation, Database size. -- Clau. Approved.
- **mxsg70xg**: PC-188 [P2]: Reverse geocode lat/lon to city name -- Replace raw coordinates with city + country via CLGeocoder.reverseGeocodeLocation(). -- Gem. Approved.
- **vqtr49io**: PC-187 [P1]: Background VLM description pipeline + Settings simplification -- (1) BGProcessingTask: describe all image cards where notes == nil using Qwen2-VL, most recent first, unload model after every 5 photos. -- Clau. Approved.
- **bv5gqi37**: PC-186 [P1]: VLM hashtag extraction — tag photos from description, OCR, and location -- After VLMService generates a description, run a second pass (same model) extracting 3-6 hashtags from: (1) VLM description, (2) OCR text (photo.photoText), (3) reverse-geocoded city name (PC-188). -- Clau. Approved.
- **kaxyqid0**: [DELETE ME] test record -- Clau. Approved.
- **43gsi9nq**: [DELETE ME] test record -- Clau. Approved.
- **x18us7bn**: PC-185 [P2]: Graph search and highlight -- Add search overlay to concept graph. Typing highlights matching nodes and dims others. Useful at 50+ nodes. -- Misty. Approved.
- **j24byvvm**: PC-184 [P1]: Graph entry points — Wiki browser and Library -- Surface the concept graph from two entry points: graph icon in Wiki browser top-right, and fullscreen option from Library top-right controls menu. -- Gem. Approved.
- **n9sa2nm2**: PC-183 [P1]: ConceptGraphView — interactive SwiftUI Canvas rendering -- Build ConceptGraphView using SwiftUI Canvas. Nodes as coloured circles, edges as lines. Pinch/pan/tap interactive. NodeDetailSheet on selection. -- Clau. Approved.
- **fsjirupq**: PC-182 [P0]: Force-directed layout engine — simd_float2 implementation -- Implement force-directed layout algorithm in Swift using simd for performance. Runs on background thread, publishes settled positions via Combine. -- Misty. Approved.
- **5t0fyome**: PC-181 [P0]: Graph data assembly — nodes and edges from wiki articles -- Implement GraphDataService that assembles GraphNode and GraphEdge arrays from wiki_articles and WikiLink data. Node size derived from topic_weights. Data layer only — no rendering. -- Gem. Approved.
- **gm6tedrh**: PC-180 [P1]: Apply topic weights to surfaces -- Plug computed topic weights into homepage Highlights, wiki generation prompts, and search ranking. -- Clau. Approved.
- **58g0iaai**: PC-179 [P1]: Signal recording — wire into existing user interactions -- Wire TopicSignalRecorder into existing interaction surfaces. No new UI — instrumentation only. Minimal changes to existing code. -- Gem. Approved.
- **tl1imyva**: PC-178 [P0]: Topic weight computation and decay — nightly BGProcessingTask -- Implement nightly background task that recomputes topic_weights from topic_signals using exponential decay. 30-day half-life. Runs as BGProcessingTask. -- Misty. Approved.
- **ifrb8toe**: PC-177 [P0]: Topic signal tracking infrastructure -- Create topic_signals and topic_weights SQLite tables. Implement TopicSignalRecorder. Implement topic extraction from queries and content. Foundation for all topic weight tickets. -- Gem. Approved.
- **vxlc078r**: PC-176 [P1]: Document import UX — Files picker and Share Extension -- Surface document import from two entry points: Files.app picker from Library + button, and Share Extension extended to handle PDF files. Both routes through DocumentIngestionService. -- Misty. Approved.
- **yazeo4vc**: PC-175 [P1]: Document association with trips, boards, places -- Allow document cards to be associated with trips, boards, and places as wiki sources. Associated documents injected as additional context into wiki generation. Full implementation of PC-145 PDF sources spec. -- Clau. Approved.
- **jv83k9wo**: PC-174 [P0]: Document card UI — enriched display and detail view -- Build the enriched document card for Library display and the document detail view. Document cards are visually distinct from text and link cards. -- Clau. Approved.
- **xlow72fx**: PC-173 [P0]: PDF LLM enrichment — summary, tags, entities, document type -- After PDF text extraction (PC-172), invoke the local LLM to generate a summary, tags, entity list, and document type classification. Results stored on Card and in card_entities table. Entities become wikilink candidates. -- Clau. Approved.
- **5zjvce4s**: PC-172 [P0]: PDF ingestion pipeline — extraction, chunking, embedding -- Implement the core PDF ingestion pipeline. PDFKit extracts text. If PDFKit returns empty (scanned PDF), Apple Vision OCR is used as fallback. Text is chunked into 500-token paragraphs with 50-token overlap. Each chunk is embedded via CoreML MiniLM model and stored in VectorStore. A Card of type 'document' is created. -- Codi. Approved.
- **lcoiqu3q**: PC-171 [P2]: People badge count (514) clipped by icon corner radius -- Library > Intelligence row: the People badge showing count '514' is cut off at the top-right corner of the icon because the badge extends beyond the clipped bounds of the icon container. Fix: apply the badge overlay outside the clipped view, or increase the icon container padding to accommodate the badge. Use .overlay on the outer container rather than inside the clipped image view. -- Clau. Approved.
- **unxj53y2**: PC-170 [P1]: Highlights section shows 'No model loaded' even when models are configured -- Home wiki / Library homepage: Highlights section shows 'No model loaded. Go to Settings → Models to configure.' but user has models loaded. The model detection check (likely checking for MLX model availability) is returning false incorrectly. Check the model availability check in the highlights generation code — it may be checking the wrong path, wrong model name, or the check runs before the model is fully initialised at launch. -- Clau. Approved.
- **e9hc4vox**: PC-169 [P1]: Trip section/day generate summary crashes — Metal GPU called from background task -- Tapping 'Generate Summary' on a trip day/section crashes with: 'IOGPUMetalError: Insufficient Permission — kIOGPUCommandBufferCallbackErrorBackgroundExecutionNotPermitted'. An MLX or on-device ML model is being invoked from inside a background Task, which iOS forbids from using Metal GPU. Fix: either (1) wrap the MLX inference call in MainActor to ensure it runs on the main thread, or (2) catch the Metal exception and fall back to the Anthropic API for generation instead of local model. The crash is uncaught std::runtime_error from Metal command buffer execution. -- Clau. Approved.
- **brsr7o7j**: PC-168 [P1]: Daily note shows raw markdown timestamp list — surface OCR and caption per photo -- Home > Daily Note card: the auto-generated content shows a raw markdown bullet list of photo timestamps and raw GPS coordinates with no context. Each photo entry should show: (1) a small thumbnail, (2) OCR text if available (photo_text), (3) visual index caption if available. Raw lat/lon coordinates should be reverse-geocoded to a place name or omitted if no location data. The daily note markdown generation is in DailyNoteService.today() — rework the photos section to include OCR/caption text and human-readable location instead of raw coordinates. -- Clau. Approved.
- **q5khf7zg**: PC-167 [P1]: Weekly wiki — LLM narrative assembled from day wikis, formatted as a cohesive trip story -- The trip/weekly wiki (homepage 'This Week' and trip detail Wiki tab) should be assembled from the individual day wikis (PC-166), not generated from raw sources. Process: (1) load each day wiki article for the date range, (2) feed all day narratives to the LLM with the instruction to produce a single cohesive story with natural transitions between days — opening sentence establishes context (who, where, how long), body flows day to day with narrative connectors, closing sentence wraps up. Must NOT be a concatenation or bullet list. Blue wikilinks to each day article inline. Small cover photo thumbnail. This replaces the current flat summary in WikiGenerator.generateAndSaveHomepage() and generateAndSaveTripWiki(). Depends on PC-166 (day wikis). Part of PC-163 incremental hierarchy. -- Clau. Approved.
- **jml2bti3**: PC-166 [P1]: Daily wiki — LLM narrative assembled from morning/afternoon/evening section summaries -- Each day in TripDetailView (and standalone in the calendar/day view) should have a Wiki tab showing a daily narrative. The daily wiki is generated by: (1) running section summaries for Morning, Afternoon, Evening slots (PC-164) if not already cached, (2) feeding all three section narratives plus the day's photos OCR/visual/location/events/notes to the LLM, (3) producing a cohesive single-day narrative that flows naturally across the sections (not bullet points, not concatenation — a story with transitions like 'After a quiet morning... the afternoon picked up with...'). Store as wiki_articles id='wiki:daily:<dayStart>'. Wire a 'Generate Day Summary' button to the day header in TripDetailView. This sits between PC-164 (sections) and PC-167 (weekly) in the incremental hierarchy. -- Clau. Approved.
- **s5dgexii**: Standardize dispatcher runtime on /Users/miguelrodriguez/fleet -- Make /Users/miguelrodriguez/fleet the single runtime source of truth for the launchd-managed dispatcher and agent heartbeats. Mirror code changes from the repo checkout into that path before restarts, and avoid running a second dispatcher from /Users/miguelrodriguez/projects/agentic-fleet-hub at the same time. Update the operational docs so the canonical path is explicit. -- Clau. Approved.
- **rad91221**: PC-166 [P1]: Board wiki tab can show stale cached content after board changes -- ## Problem -- Clau. Approved.
- **mz5yzw9q**: PC-165 [P1]: Person wiki — LLM narrative from tagged photos, events, and notes -- Each person should have a Wiki tab in PersonDetailView (alongside Photos/Info). The wiki article is generated by LLM from: (1) OCR text and visual index descriptions from photos tagged with this person (via face cluster / person_links), (2) calendar events the person attended (person_links sourceType=event), (3) notes/cards that @mention this person (fetchCardsByPersonLink). Cover photo = most recent tagged photo. Use WikiGenerator.generateAndSavePersonWiki(person:) already stubbed in PC-142 — wire it to the UI with a 'Generate Wiki' button and display result in WikiContainerView. Same pattern as PC-157 (boards) and PC-164 (trips). Assigned to gem — coordinate with PC-157 to share any context-builder helpers. -- Gem. Approved.
- **ewoym3l8**: PC-164 [P0]: Trip section summaries — LLM narrative per Morning/Afternoon/Evening slot -- TripDetailView already groups photos by day and time slot (PhotoTimeSlotService). Add a 'Generate Summary' button to each slot section. When tapped: (1) collect all photos in that slot — OCR text (photo_text), visual index description, lat/lon location names; (2) collect calendar events overlapping the slot time window; (3) collect notes/cards created during that window; (4) call WikiGenerator.generateSectionSummary() with this context → 2-4 sentence narrative paragraph; (5) display the paragraph inline below the slot header with a small leading thumbnail from the slot's first photo. Implementation: add WikiGenerator.generateSectionSummary(slotTitle:photos:events:cards:) that builds a context string and calls generateStructuredWiki with type=.daily and sectionHint matching the slot. Store result in SQLiteStore wiki_articles with id 'section:<tripId>:<dayStart>:<slotName>'. This is the foundation for PC-163 (incremental hierarchy). Assigned to clau for immediate implementation — user is providing live feedback. -- Codi. Approved.
- **n68p4aoi**: PC-163 [P1]: Incremental wiki hierarchy — section wikis compose into day and trip wikis -- New wiki generation architecture: (1) Section wikis: per day, generate Morning / Afternoon / Evening micro-articles from photos/events in each time window (PhotoTimeSlotService clusters). (2) Day wiki: composed from section wikis, body links to section articles. (3) Trip wiki: composed from day wikis, body links to day articles, replacing current flat summary (keep days/photos/places/events count header). Enables incremental updates: new afternoon photo only regenerates that section wiki, then day and trip wikis. Implement WikiGenerator.generateSectionWiki(), update generateAndSaveDailyWiki() to link sections, update generateAndSaveTripWiki() to link days. -- Codi. Approved.
- **y5q4nrxh**: PC-162 [P1]: Trips summary — use OCR, location, time, and clip info for narrative -- Trip detail > Summarize: extend WikiGenerator.generateAndSaveTripWiki (PC-140) to use: (1) OCR text from trip photos (scanned receipts, menus, signs), (2) location names from geotagged photos and place visits, (3) calendar event titles for trip dates, (4) note/card text created during the trip. Output a flowing narrative paragraph ('3 days in Budapest with Bunny and Ion. Went for dinner on Friday...') not a bullet list. -- Gem. Approved.
- **nsutn834**: PC-161 [P1]: Places — saved note not shown in place detail -- Place detail > Add Note: note is saved but not displayed afterwards. Check: SQLiteStore.savePlace/updatePlace writing to correct column, PlaceDetailViewModel refreshing after save, UI observing updated model. -- Clau. Approved.
- **v4pmvfam**: PC-160 [P1]: Wiki — replace Recent Captures + Connected Wikis with LLM narrative section -- WikiArticleView: replace Recent Captures strip and Connected Wikis list with a single LLM-generated narrative paragraph. Requirements: black text, blue wikilinks (existing WikiLink tap mechanism), small inline thumbnail from cover photo (max 80pt leading float), This Week / time-slot sections remain intact. Update WikiGenerator to produce this narrative in structured wiki output. -- Gem. Approved.
- **a7vuf5rf**: PC-159 [P1]: Wiki homepage photo count shows 0 -- WikiArticleView / WikiBrowserView: photo count on the homepage wiki card shows 0. Should reflect WikiSource records with sourceType == .photo. Check WikiGenerator.generateAndSaveHomepage() sources array and how the count is rendered. -- Clau. Approved.
- **gijiwfy4**: PC-158 [P2]: Library — remove Boards and Saved Searches, move Hashtags below Wiki -- LibraryView: (1) Remove Boards entry. (2) Remove Saved Searches entry. (3) Move Hashtags below Wiki. Clean up list order: People, Wiki, Hashtags. -- Clau. Approved.
- **1rs24i9t**: PC-157 [P1]: Board wiki — LLM narrative from board photos OCR, notes, PDFs -- Each board needs a Wiki tab. Article is generated by LLM from: (1) OCR text and visual index from board photos, (2) text/note cards on the board, (3) summarised PDFs linked to the board. Cover photo as hero image. Reuse WikiGenerator.generateStructuredWiki from PC-142. Extends PC-142 with explicit OCR + visual index + PDF source inclusion. -- Gem. Approved.
- **1yab1z0c**: PC-156 [P2]: All Photos — OCR text items not tappable and font too large -- Library > All Photos > OCR section: entries should be tappable to open the source photo. Font size should be reduced to caption/footnote style to show more content per item. -- Misty. Approved.
- **ptj9vn97**: PC-155 [P1]: All Photos — visual index information not shown on photo detail -- Library > All Photos: the AI visual description (CLIP embedding label / photo_text) is missing from PhotoDetailView. It is stored in SQLite. Surface it below OCR text, labelled 'Visual'. Check SQLiteStore is reading the column and passing it to the view model. -- Codi. Approved.
- **yn3tha07**: PC-154 [P1]: Boards list view items are not navigable -- Board detail > List view: tapping items does nothing. Photos should open photo detail. Text cards should open card editor. Match navigation behaviour of the visual/masonry view. -- Codi. Approved.
- **c8srg1z4**: PC-153 [P1]: Text card (scan) missing assign-to-board and assign-to-person -- Home > Recent Captures: text cards from document scans have no way to assign them to a board or to a person. Photos have this via long-press menu. Text cards should expose: (1) assign to board (same board picker as photos), (2) assign to person via @mention (same as card edit flow). -- Codi. Approved.
- **e4a0lew6**: PC-152 [P0]: Journaling crash — type word + space triggers crash -- Home > Journaling: typing one word then pressing space causes a crash. Reproduction: open the journaling card on the home screen, type any word, press space. Crash occurs immediately. Likely TextEditor state mutation or @Published update loop. Fix and add regression guard. -- Codi. Approved.
- **vjrin29g**: PC-151 [P2]: Photo masonry should use natural PHAsset aspect ratios, not fixed cycling heights -- DayGroupedPhotoGrid and BoardPhotoTile use hardcoded cycling height patterns ([210, 150, 185] / [160, 220, 175]) instead of each photo's real pixel dimensions. True Pinterest-style stagger requires fetching PHAsset.pixelWidth/pixelHeight and computing each column cell height proportionally. This affects Places, Trips, Boards, People, and any view using DayGroupedPhotoGrid or masonry layout. -- Clau. Approved.
- **746ydyvd**: PC-150 [P1]: Boards detail Content tab still renders flat list, not masonry photo grid -- BoardDetailView Content tab shows a dated icon+text list ("26 April 2026 — Photo") instead of the masonry photo grid that PC-129 was supposed to deliver. Photos exist in the board but are not rendering as thumbnails. Expected: 2-column staggered photo grid matching the pinterest-style layout used in Places and Trips. Confirmed broken on device build 2026-04-30. -- Clau. Approved.
- **rbbf991f**: Fleet: Qwen Coder smoke test updates legacy Gemma docs -- ## Goal -- Clau. Approved.
- **r9cbf7e8**: PC-149 [P1]: Wiki PDF references should score linked PDF chunks, not global top-N -- Follow-up from PC-145 merge review: WikiGenerator.buildPDFSection searches the global vector index with limit equal to linked chunk count, then filters to linked PDF chunks. In large indexes this can omit linked PDF chunks entirely. Score linked chunks directly or add filtered vector search and regression coverage. -- Gem. Approved.
- **n63odgjs**: PC-147 [P2]: Wiki — User annotations on wiki sections -- Sprint 4 / Wiki System (was PC-057 in sprint doc) -- Clau. Approved.
- **ljva93dt**: PC-142 [P1]: Wiki — WikiGenerator board/daily/place/person wikis -- Sprint 4 / Wiki System (was PC-052 in sprint doc) -- Clau. Approved.
- **bfrln3t6**: PC-140 [P0]: Wiki — WikiGenerator trip wiki -- Sprint 4 / Wiki System (was PC-050 in sprint doc) -- Clau. Approved.
- **#129**: [ATF-6] Scaffold wiki index/log and page templates -- ## Context -- Clau. Approved.
- **#126**: [ATF-3] Scaffold Mexico raw-log dropzone and manifest template -- ## Context -- Qwen. Approved.
- **#119**: [UI] Strip emojis from /demo dashboard menu -- Gemma, please fix the encoding issues in the demo dashboard menu by removing all emoji characters from the nav labels. -- Qwen. Approved.
- **#109**: Songs PocketBase collection — migrate from Excel tracker -- Create a 'songs' collection in PocketBase to replace the Excel tracker as the live source of truth for The Classical Remix catalog. This collection will feed the Scout, Campaign Manager, and SEO audit agent. -- Qwen. Approved.
- **#107**: [Logic] Implement circuit breaker for heartbeat loops -- Demo task assigned to gemma. -- Qwen. Approved.
- **3xzo9sva**: Fleet Documentation Audit - Gemma's First Task -- Create a comprehensive DOCUMENTATION_MAP.md file. Task details: 1) Explore repository structure using find/ls commands, 2) Analyze all *.md files, 3) Create DOCUMENTATION_MAP.md with categorized file list, 4) Identify documentation gaps, 5) Commit and push changes. Expected output: DOCUMENTATION_MAP.md at repo root with clear structure and health assessment. -- Qwen. Approved.
- **m7z2prgv**: test -- Qwen. Approved.
- **a215p1a4**: [SC-001][P0] Fork PrivateCore to SiliconOracle -- COMPLETE 2026-05-29. Tag fork/siliconoracle-2026-05 on privatecore-ios. Repo silicon-oracle created, xcodeproj renamed, bundle ID com.bigbear.siliconoracle, version 0.1.0, fresh MISSION_CONTROL + README + CLAUDE.md. BUILD SUCCEEDED on simulator. -- Codi. Approved.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **fm2d6bat** | [SC-003][P0] 4-screen navigation: Journal / Wiki / Boards / Settings | misty | planned | Replace the 8-screen shell (inherited PC-019) with... |
| **v8galy0v** | [SC-005][P1] Text style system reskin — Popstar, Shakespeare, Cartoon, Manga | clau | in_work | Reduce text style set to four: Popstar (Cosmopolit... |
| **rtueyqe5** | [SC-006][P1] Video style reskin — Cinematic, Engraving-Vintage, Manga | clau | in_work | Reduce video/reel styles to three: Cinematic (film... |
| **g84mn08f** | [SC-008][P1] Reimagine Home as Journal cast surface + readings feed | clau | planned | Fold old Home/Briefing concept into Journal: one p... |
| **x0h3h158** | [QW-006][P1] Peer review network — who reviews whose work, collaboration graph | qwen | in_work | Using standup_data.json from QW-001, parse peer_re... |
| **msi5mvku** | [QW-007][P0] Fleet analytics index page — wire all QW charts into a single report | qwen | in_work | After QW-002 through QW-006 are complete, produce ... |
| **ehygr8de** | [SC-013][P0] Two-model architecture + single-swap sequential pipeline | clau | planned | Engine · 8 pts... |
| **erakto7x** | [SC-014][P0] Seven-step foreground generation flow | clau | planned | Engine · 8 pts... |
| **c2fa5vgn** | [SC-015][P0] Resumable progressive captioning (one-by-one, checkpointed) | clau | planned | Engine · 5 pts... |
| **0tw7v5pt** | [SC-016][P1] Concurrent style-pick overlay during captioning | clau | planned | App Shell · 3 pts... |
| **ch7wxnvk** | [SC-017][P0] 12-segment / 60s video timeline (segment model, pan+zoom Ken Burns) | clau | planned | Engine · 8 pts... |
| **y6in4ml7** | [SC-018][P1] Sparse-day rotation with varied Ken Burns + interleaving | clau | planned | Engine · 5 pts... |
| **v9ayz4rm** | [SC-019][P0] Visual layer cut: Original (no filter), Engraving, Cinematic only | gem | planned | Engine · 2 pts... |
| **w9ixcxxq** | [SC-020][P1] Pre-generated backing-track library (forgiving genres) | clau | planned | Content · 5 pts... |
| **ou731qzn** | [SC-021][P1] Constrained lyric generation (template + spoken-word-over-beat v1) | clau | planned | Engine · 8 pts... |
| **x2ubx6qw** | [SC-022][P1] Day/week: one pipeline, two selection surfaces | clau | planned | Engine · 5 pts... |
| **wfay6h0c** | [SC-023][P2] SmolLM2 photo pre-pick (or cut SmolLM2 if not adopted) | clau | planned | Engine · 5 pts... |
| **8vugwiik** | [SC-024][P1] Reel/PDF dual-artifact export from one warm text-model session | clau | planned | Engine · 3 pts... |
| **0k1qz3q0** | [SC-025][P0] Text-model A/B toggle (Settings: Qwen vs Ministral for text) + telemetry | clau | planned | App Shell · 5 pts... |
| **a3g34dhf** | Question about multi-model key management | clau | planned | Multi-model orchestration across Claude, Gemini, a... |

**Status: `create-flotilla@0.5.0` live on npm as of 2026-05-26.**
