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
| **2. Music Video Tool** | `../music-video-tool/` | Tooling for creating music videos and content. | [Project MD](./AGENTS/CONTEXT/music_video_tool.md) |
| **3. CRM-POC** | `../crm-poc/` | Customer & Agent relational management system. | [Context MD](./AGENTS/CONTEXT/crm_poc_context.md) |
| **4. The Lost Coins** | `../the-lost-coins/` | Narrative/Story-driven project. | [Story MD](./AGENTS/CONTEXT/the_lost_coins_story.md) |
| **5. Robot Ross** | *(Mac mini)* | **Master control** for the robot arm & painting. | [Artist MD](./AGENTS/CONTEXT/robot_ross_artist.md) |
| **6. Salesman (OpenClaw)** | `DigitalOcean` | OpenClaw gateway & **BobRossSkill** (public). | [Salesman MD](./AGENTS/CONTEXT/robot_ross_salesman.md) |

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

## Ticket Status (as of 2026-04-16)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
- **#999**: Test Dummy Task from Gem -- Created for verification of fleet_sync.py -- Gem. Approved.
- **7gbzmg40**: [ATF] Deploy static ATF surface to api.robotross.art/atf -- Context -- Clau. Approved.
- **vttdwgaa**: [Ops] Canonize Clau runtime wrapper and summarize_session entrypoint -- Problem: Clau found that the deployed runtime copies of the wrapper and summarizer had diverged from the repo copies. The immediate bug was a Python 3.9 parse failure in summarize_session.py caused by newer type-hint syntax, but the larger issue is runtime drift. There is also a second summarize_session.py at the repo root using a newer CLI and architecture that is not the deployed runtime version. We need one canonical summarizer, one canonical wrapper path, removal or archival of dead duplicates, verification that fresh Clau pre/post summarizer runs exit 0 from the real wrapper environment, and documentation of the canonical runtime paths so this drift does not recur. -- Clau. Approved.
- **#146**: [Ops] Canonize Clau runtime wrapper and summarize_session entrypoint -- Created from GitHub issue #146. Canonize Clau runtime wrapper and summarize_session entrypoint; remove duplicate summarizer drift and document the canonical runtime path. -- Clau. Approved.
- **#145**: [ATF-8] Build local model runtime adapter for Gemma/Apertus -- Runtime adapter verification and cleanup after prior ticket drift. -- Clau. Approved. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **b0envpk8**: [ATF] Build integrated local RobotRoss knowledge console with text and voice QA -- ## Context -- Clau. Approved.
- **8dvp6ma6**: [ATF] Build integrated RobotRoss demo landing page for DigitalOcean deployment -- ## Context -- Clau. Approved.
- **h6xy2yt7**: [ATF] Rebuild QA grounding from canonical RobotRoss sources and ledger data -- ## Context -- Clau. Approved.
- **gyfz6ceg**: [ATF] Build human-readable operational ledger dashboard for Mexico logs -- ## Context -- Codi. Approved.
- **vbwk63sc**: [ATF] Build browser-readable wiki UI over compiled ATF articles -- ## Context -- Clau. Approved.
- **m8tqyiij**: [Ops] Investigate recurring Telegram billing warning unrelated to Google Ads -- ## Context -- Codi. Approved.
- **k6oqniti**: [TCR-16] Build live Google Ads campaign execution on top of paused shell -- ## Context -- Gem. Approved.
- **#136**: [ATF-8] Build local model runtime adapter for Apertus/Ollama -- ## Context -- Clau. Approved.
- **#135**: [Ops] Stabilize PocketBase single-instance ownership and lock contention -- Investigate and harden PocketBase so only one managed instance owns pb_data. Root cause found: rogue second PocketBase listener on port 8090 caused SQLITE_BUSY and sync timeouts. Remaining work: startup-path audit, duplicate-listener guard, stability verification, and operator documentation. -- Gem. Approved.
- **#134**: [ATF-11] Optional voice shell with Whisper and Voxtral -- ## Context -- Clau. Approved.
- **#133**: [ATF-10] Cross-reference Mexico logs into the compiled wiki -- ## Context -- Gem. Approved.
- **#132**: [ATF-9] Build local CLI QA shell over wiki and ledger -- ## Context -- Clau. Approved.
- **#131**: [ATF-8] Build local model runtime adapter for Gemma/Apertus -- ## Context... -- Clau. Approved.
- **#131**: [ATF-8] Build local model runtime adapter for Gemma/Apertus -- Runtime adapter verification and cleanup after prior ticket drift. -- Clau. Approved.
- **#130**: [ATF-7] Add EU AI Act mapping metadata for wiki pages -- ## Context -- Misty. Approved.
- **#129**: [ATF-6] Scaffold wiki index/log and page templates -- ## Context -- Gemma. Approved.
- **#128**: [ATF-5] Generate initial compiled wiki from RobotRoss code/docs -- ## Context -- Gem. Approved.
- **#127**: [ATF-4] Build Mexico log parser and normalized event schema -- ## Context -- Misty. Approved.
- **#126**: [ATF-3] Scaffold Mexico raw-log dropzone and manifest template -- ## Context -- Gemma. Approved.
- **#125**: [ATF-2] Inventory RobotRoss source corpus for compiled wiki -- ## Context -- Gem. Approved.
- **#124**: [ATF-1] Define Agentegra ATF architecture and schema contract -- ## Context -- Codi. Approved.
- **3tkwcwy8**: Scout script — daily YouTube API pull -- Python script + launchd plist for daily metrics -- Codi. Approved.
- **20ssp0z2**: Scout script — daily YouTube API pull -- Python script + launchd plist for daily metrics -- Codi. Approved.
- **wsr101vk**: Scout script — daily YouTube API pull -- Python script + launchd plist for daily metrics -- Misty. Approved.
- **oiau2utz**: Scout script — daily YouTube API pull -- Python script + launchd plist for daily metrics -- Clau. Approved.
- **b0iizu5k**: Scout script — daily YouTube API pull -- Python script + launchd plist for daily metrics -- Clau. Approved.
- **#122**: Document shift timeline and heartbeat reliability fixes -- #122: Document shift timeline and heartbeat reliability fixes. Scope: record the Fleet Hub fixes completed on 2026-04-09, including (1) sidebar/user management/kanban live-server repairs, (2) timeline snapshot path using archive plus PB data, (3) dispatcher offline status surfaced into timeline segments, (4) synthetic working segments from task_events/comments for Gemma activity, and (5) idle-on-skip heartbeat wrapper fix for Clau/Gem/Codi to prevent false stale/offline states. Add the operational explanation to architecture docs and daily standup, then sync Mission Control. -- Codi. Approved.
- **8sto1zdn**: #TCR-15: [Executor] Configure Google Ads OpenClaw executor -- Configure the automated execution layer for Google Ads using OpenClaw. -- Gem. Approved.
- **#120**: [Dashboard] Fix Standups and Inbox rendering in /fleet -- Misty, the /fleet dashboard is not showing standups or inter-agent messages, even though data exists in the snapshot. This likely broke during the /demo page fixes. -- Misty. Approved.
- **#119**: [UI] Strip emojis from /demo dashboard menu -- Gemma, please fix the encoding issues in the demo dashboard menu by removing all emoji characters from the nav labels. -- Gemma. Approved.
- **tcr12pol**: TCR-12: Promotion policy engine — heatmap-driven selection and layer escalation -- Define the promotion policy that sits above #109, TCR-7, and TCR-8. Goal: turn the existing piece×style heatmap plus daily PocketBase metrics into a repeatable decision loop for ad promotion.\n\nSCOPE\n- Use the heatmap as the prior score for each song/style combo.\n- Combine prior score with fresh runtime signals from PocketBase songs and ad_performance.\n- Produce a daily recommendation state per combo: candidate, testing, promoting, cooldown, winner, retired.\n- Define how the 3 ad layers are applied, escalated, paused, or stopped.\n\nREQUIRED OUTPUTS\n1. Candidate scoring model\n- Inputs: heatmap score, combined organic views, recent organic delta, recent watch-time delta, ad spend to date, cost_per_watch_hour, cost_per_sub, recency/cooldown state, optional exploration boost for under-tested styles.\n- Output: ranked list of promotion candidates for the day.\n\n2. Layer controller\n- Layer 1: low-budget test.\n- Layer 2: reinforcement if post-test metrics clear threshold.\n- Layer 3: scale if layer-2 efficiency remains above target.\n- Stop/cooldown rules for weak performers.\n\n3. Feedback loop\n- After each daily scout refresh, recompute status and next action for every candidate.\n- Campaign Manager should consume this policy output instead of making ad-hoc decisions from raw rows.\n\n4. Telegram briefing contract\n- Daily message should include: top candidates, active promotions, combos entering cooldown, combos promoted to next layer, and a short why for each recommendation.\n\nDECISION RULES TO SPECIFY\n- Minimum organic threshold before paid testing.\n- Escalation thresholds after each layer.\n- Cooldown duration.\n- Max concurrent promotions.\n- Daily budget allocation strategy across exploit vs explore.\n\nIMPLEMENTATION DIRECTION\n- Store policy state in PocketBase (either on songs records or a dedicated campaign_state collection if needed).\n- Keep the logic deterministic and inspectable; do not build a self-modifying agent loop.\n- Reuse the heatmap as the starting prior, but allow runtime metrics to reorder candidates over time.\n\nNON-GOAL\n- Do not implement Karpathy-style autoresearch or autonomous code mutation. This is a structured decision policy over promotion state, not an open-ended research loop.\n\nDEPENDENCIES\n- #109 songs mirror\n- TCR-7 daily scout updates\n- ad_performance collection\n\nSUCCESS CRITERIA\n- A human can inspect and explain why a combo was chosen, escalated, or cooled down.\n- Campaign Manager recommendations are derived from stable policy fields, not freeform interpretation alone.\n- The system supports both exploitation of known winners and exploration of under-tested combos. -- Codi. Approved.
- **#117**: Project Portfolio: Add direct links to analytics (Stats) -- Add direct links to the analytics dashboard for specific projects in the Fleet Hub UI. -- Gem. Approved.
- **dqprooej**: TCR-11: Music-video-tool AGENTS/ directory setup -- REASSIGNED from Clau to Gem — documentation structure is Gem's sweet spot. -- Gem. Approved.
- **3h6dsn4h**: TCR-10: Gemma — weekly SEO audit and performance summary -- ASSIGNED TO GEMMA — local model, cost-free, repetitive task ideal for Gemma. -- Gem. Approved.
- **slqxtrd9**: TCR-9: Playwright Reddit poster — automated daily posting -- ASSIGNED TO CODI — delivery/scripting, Codi's sweet spot. NOTE: Codi quota resets 2026-04-08 09:52. Do not start before then. -- Gem. Approved.
- **tn28lgsj**: TCR-8: Campaign Manager — daily analytics briefing to Telegram -- REASSIGNED from Clau to Gem. -- Gem. Approved.
- **743yt6fl**: TCR-7: Scout script — daily YouTube API pull to PocketBase -- ASSIGNED TO MISTY — Python scripting, well-scoped spec. -- Codi. Approved.
- **#110**: Stats page — add music-only filter view -- ASSIGNED TO MISTY — contained frontend task to test Misty's implementation capabilities. -- Misty. Approved.
- **#109**: Songs PocketBase collection — migrate from Excel tracker -- Create a 'songs' collection in PocketBase to replace the Excel tracker as the live source of truth for The Classical Remix catalog. This collection will feed the Scout, Campaign Manager, and SEO audit agent. -- Gemma. Approved.
- **#109**: [Ops] Migrate to Docker-compose for local dev -- Demo task assigned to codi. -- Codi. Approved.
- **#108**: YouTube titles & descriptions reword for The Classical Remix -- Reword all existing video titles and descriptions for The Classical Remix channel to match the SEO formula identified on 2026-04-07. -- Gem. Approved.
- **#108**: [Docs] EU AI Act compliance report v1 -- Demo task assigned to misty. -- Misty. Approved.
- **#107**: [Logic] Implement circuit breaker for heartbeat loops -- Demo task assigned to gemma. -- Gemma. Approved.
- **#107**: Multi-project fleet steering — allow N concurrent active projects -- REASSIGNED from Clau to Gem — architecture synthesis is Gem's core strength. -- Gem. Approved.
- **#107**: Multi-project fleet steering — allow N concurrent active projects -- Current limitation: only one project can be active at a time (is_active: true on one entry in fleet_meta.json). This blocks concurrent work across private projects (music-video-tool, the-lost-coins) and public ones (flotilla, robot-ross). -- Gem. Approved.
- **#107**: [Auth] Fix JWT refresh loop in Safari -- Demo task assigned to clau. -- Gem. Approved.
- **#106**: Telegram bridge — auto-create follow-up task when message references a ticket number -- Problem: when a human sends a Telegram message referencing a closed ticket (e.g. "/gem Regarding #100 ..."), the bridge routes it to inbox.json but no PB task is created, so agents see it but have no actionable item and it falls through. -- Clau. Approved.
- **#106**: [UI] Add dark mode toggle to dashboard -- Demo task assigned to gem. -- Gem. Approved.
- **#105**: Demo page — complete mock data (team, timeline, projects, PB viewer) -- Ticket #100 updated the CSS/JS but left the demo data incomplete. The demo at api.robotross.art/demo/ must be fully self-contained with realistic mock data. All edits go to the DO server via ssh robotsales at /opt/salesman-api/demo/. -- Clau. Approved.
- **#105**: Demo page: complete mock data (team, timeline, projects, PB viewer) -- Create demo data in the Agentic team including Gem, Clau, Misty, Cody and Gemma. In the timeline include all possible states and remember to have enough data for 24h/7D and 30d. In the fleet performance add some stats that kind a make sense, maybe even reflecting our ping pong loop from the past. Also in Memory add a few entries that make sense for a web page project. Feel free to take over some of our memories. -- Gem. Approved.
- **#104**: Root Directory Declutter -- The root of agentic-fleet-hub has accumulated files that belong elsewhere. Move the following using git mv and update any cross-references: -- Clau. Approved.
- **#103**: Documentation Reorganization — FLEET_GUIDE.md -- Follow-on to your DOCUMENTATION_MAP.md audit (task 3xzo9sva). Goal: consolidate and restructure the root-level documentation using two inputs: -- Clau. Approved.
- **#102**: Compliance Archive Logging + Shift Timeline Fix -- Implement append-only heartbeat_archive.jsonl and task_archive.jsonl for EU AI Act compliance and arXiv research data. Each heartbeat entry: agent, timestamp, status, task_id (if working), note, prev_entry_hash (tamper-evidence chain). Each task entry: lifecycle events (created, picked_up, completed, reassigned, blocked) with agent intent doc attached at pick-up. Files live at ~/fleet/, never pruned, periodically committed to private fleet-audit-log git branch. Consequences: (1) Update fleet_push.py to push pre-aggregated 15-min timeline segments fixing blank Shift Timeline rows for Clau/Gem/Codi. (2) PocketBase retention policy pruning heartbeats older than 14 days. See conversation 2026-04-07. -- Clau. Approved.
- **#101**: Demo task for ping-pong loop -- A demo task to show back-and-forth between agents. -- Gem. Approved.
- **#101**: Demo task for ping-pong loop -- A demo task to show back-and-forth between agents. -- Clau. Approved.
- **#101**: Demo task for ping-pong loop -- A demo task to show back-and-forth between agents. -- Gem. Approved.
- **#100**: Sync /demo with Flotilla v0.4.0 -- Update opt/salesman-api/demo/assets/main.js and style.css to match fleet v0.4.0. Add: (1) Schichtplan swim-lane timeline with mock segment data, (2) extended agents table columns (last seen, idle until, tokens, success rate) with mock values, (3) aggregate stats panel with mock numbers. Reference: opt/salesman-api/fleet/assets/main.js (960 lines) vs demo (467 lines). Deploy to DO server via ssh robotsales. -- Gem. Approved.
- **#99**: Release Flotilla v0.4.0 -- Package bundled, CHANGELOG + ARCHITECTURE updated, version bumped to 0.4.0. Peer-reviewed by Clau 2026-04-06. Published to npm. -- Gem. Approved. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **#98**: Task branch + WORKLOG handoff protocol -- Rule in AGENTS/RULES.md; dispatcher checks branch on reassign and includes URL in handoff comment. -- Clau. Approved. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **#97**: #97 Fleet Hub: aggregate stats panel + retroactive log parser -- Two parts: -- Gem. Approved.
- **#96**: #96 Fleet Hub: Schichtplan (agent shift timeline) -- Swim-lane timeline showing each agent activity over selectable time window (24h / 7d / 30d). -- Clau. Approved.
- **#95**: #95 Fleet Hub: extended agents table -- Extend the agents table in the Fleet Hub UI with new columns: -- Gem. Approved.
- **lqkl17be**: Your project on Capybara Market? -- Hey @UrsushoribilisMusic 👋 -- Clau. Approved.
- **#94**: #94 PB schema: task_events collection + dispatcher metrics logging -- Foundation for the analytics dashboard. -- Clau. Approved.
- **#93**: Tech-Angle Promotion (Reddit) -- Create tech-focused Reddit posts for u/robotrossart highlighting the Flotilla AI pipeline used for The Classical Remix. Goal: Cross-promotion and engineering credibility. -- Clau. Approved.
- **myhluvej**: Fix Gemma agent: add aichat function tools + update plist invocation -- Gemma is not executing her heartbeat protocol. Root causes: 1) plist uses --rag mode (Q&A only, not agentic), 2) no aichat function tools defined so the model cannot call curl/file ops. Fix: create aichat functions (execute_command, read_file, write_file) and update plist invocation. -- Clau. Approved.
- **#92**: PocketBase: ad_performance collection -- Created collection with fields for spend, ROI, and engagement gains per platform. -- Clau. Approved.
- **3xzo9sva**: Fleet Documentation Audit - Gemma's First Task -- Create a comprehensive DOCUMENTATION_MAP.md file. Task details: 1) Explore repository structure using find/ls commands, 2) Analyze all *.md files, 3) Create DOCUMENTATION_MAP.md with categorized file list, 4) Identify documentation gaps, 5) Commit and push changes. Expected output: DOCUMENTATION_MAP.md at repo root with clear structure and health assessment. -- Gemma. Approved.
- **#91**: Analytics API: /tracker/daily-delta -- Add endpoint to compare today stats vs yesterday snapshot for trend detection. -- Clau. Approved.
- **#90**: YouTube Scout: Advanced Engagement Metrics -- Upgrade music scout to pull estimatedMinutesWatched, avgViewDuration, subsGained, annotationCTR. -- Gem. Approved.
- **#89**: Task Scratchpad: Implement live state-tracking -- Add scratchpad JSON field to PocketBase tasks. Allows agents to store and handoff granular execution state without feed parsing. -- Gem. Approved.
- **#88**: Fleet Policy JSON: Versioned State Machine -- Transition Markdown mandates into a versioned JSON policy doc. Compact policy Doc for tools, constraints, escalation, and handoff rules. -- Codi. Approved.
- **#87**: Lesson Summarizer: Post-session script -- Implement summarize_session.py to compress logs into JSON-structured lessons after each major loop. Inject top lessons into system prompts. -- Clau. Approved.
- **#86**: Refine Lessons Schema: Enforce JSON structure -- Update PocketBase lessons collection to include mandatory fields: {decision, rationale, outcome, confidence_score}. Goal: Structured memory over free-text notes. -- Gem. Approved.
- **#85**: Auto-Generate Daily Standup Files -- ## Problem -- Codi. Approved.
- **#84**: Hybrid Sync - MISSION_CONTROL.md <=> PocketBase -- Implement fleet_sync.py to bi-directionally sync the Markdown execution table with PocketBase state. -- Codi. Approved.
- **#84**: Hybrid Sync - MISSION_CONTROL.md <=> PocketBase -- Implement fleet_sync.py to bi-directionally sync the Markdown execution table with PocketBase state. Option 3 per Misty proposal. -- Codi. Approved.
- **#84**: Implement Option 1 - Dual Sync Strategy -- Implement Option 1 as requested by Miguel: Document Dual System, Keep both systems separate, Document that MC is for goals, PB for execution, Checksum system checks both sources. Includes updating dispatcher.py with PocketBase checksum logic. -- Gem. Approved.
- **#84**: Hybrid Sync - MISSION_CONTROL.md <=> PocketBase -- Implement fleet_sync.py to bi-directionally sync the Markdown execution table with PocketBase state. -- Gem. Approved.
- **#84**: Proposal - MISSION_CONTROL.md vs PocketBase Synchronization Strategy -- ## Problem -- Gem. Approved.
- **#83**: Fix Telegram messages incorrectly becoming GitHub issues -- Implemented comprehensive fixes to prevent Telegram direct messages from being incorrectly converted to GitHub issues. -- Gem. Approved.
- **#83**: Fix Telegram messages incorrectly becoming GitHub issues -- Implemented comprehensive fixes to prevent Telegram direct messages from being incorrectly converted to GitHub issues. Changes include enhanced message routing, source tracking, and GitHub sync filtering. -- Gem. Approved.
- **#82**: Fleet Hub: Add "Blocked" filter to Task Board -- Allow humans to easily find tasks caught by the circuit breaker. -- Gem. Approved.
- **#81**: Sync ~/fleet/gem/ with ~/fleet/ root versions -- Keep workspace copies in sync with deployed scripts. -- Gem. Approved.
- **#80**: Release create-flotilla v0.3.0 to npm -- Perform pre-publish verification and release the new version using the Infisical-backed publish flow. -- Gem. Approved.
- **#79**: Sync /demo and /growth with v0.3.0 Features -- Update public-facing demo and growth pages to reflect the latest fleet capabilities (Kanban, snapshots, monitoring). -- Clau. Approved.
- **#78**: Fleet Hub UI: Dark/Light Mode & Redesign -- Apply the developer tool aesthetic, CSS token system, and dark/light mode toggle to all fleet dashboards. -- Clau. Approved.
- **#77**: Update create-flotilla to v0.3.0 -- Include new dispatcher logic, Telegram slash commands, GitHub sync, and PocketBase snapshot logic into the core package. -- Gem. Approved.
- **pbkec9xa**: ignore MISSION_CONTROL for now. Go directly to PocketBase and set the task titled '[bug] dispatcher: no circuit breaker on reassignment loop when both agents offline' to status blocked. Do not work on it, just block it. -- From Telegram: /codi ignore MISSION_CONTROL for now. Go directly to PocketBase and set the task titled '[bug] dispatcher: no circuit breaker on reassignment loop when both agents offline' to status blocked. Do not work on it, just block it. -- Codi. Approved.
- **#74**: Review of Heartbeat Gate (#74) and Fleet Steering (#75). Fixed Python 3.9 compatibility and added dynamic alias loading. -- Gem. Approved. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **#74**: Review of Heartbeat Gate (#74) and Fleet Steering (#75). Fixed Python 3.9 compatibility and added dynamic alias loading. -- Gem. Approved. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **syqw2guw**: [bug] dispatcher: no circuit breaker on reassignment loop when both agents offline -- Problem -- Gem. Approved.
- **#73**: I created ticket 73 in GitHub. Please work on it. Here the title: [bug] dispatcher: no circuit breaker on reassignment loop when both agents offline #73 -- From Telegram: /codi I created ticket 73 in GitHub. Please work on it. Here the title: [bug] dispatcher: no circuit breaker on reassignment loop when both agents offline #73 -- Codi. Approved.
- **#73**: Peer review #73 -- Review checksum caching implementation for MISSION_CONTROL.md -- Gem. Approved.
- **ykgefztd**: please close all todo tasks. Irrelevant who it’s assigned to -- From Telegram: /misty please close all todo tasks. Irrelevant who it’s assigned to -- Gem. Approved.
- **#72**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly. -- Gem. Approved.
- **#72**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly. -- Misty. Approved.
- **#72**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly. -- Misty. Approved.
- **m2zloxg0**: please stop reassigning the task to Clau -- From Telegram: /gem please stop reassigning the task to Clau -- Gem. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- MISSION_CONTROL.md parser has been successfully updated for dynamic project switching. The parser now correctly reads from the active project and ensures Kanban/ticket views reflect the new project. Testing shows 5 open tickets and 48 closed tickets parsed correctly. API endpoint /fleet/api/parse-mission-control is working and returns proper JSON structure. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Gem. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **#71**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project. -- Misty. Approved.
- **mt9qcp1d**: please stop reassigning the task to gem. -- From Telegram: /clau please stop reassigning the task to gem. -- Gem. Approved.
- **#70**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have "Activate" button with confirmation. -- Gem. Approved.
- **#70**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have "Activate" button with confirmation. -- Misty. Approved.
- **#70**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have "Activate" button with confirmation. -- Misty. Approved.
- **#70**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have "Activate" button with confirmation. -- Misty. Approved.
- **prdjido0**: please pause 80 for now. I am traveling and need to be at the computer to generate the code. Thanks! -- From Telegram: /gem please pause 80 for now. I am traveling and need to be at the computer to generate the code. Thanks! -- Gem. Approved.
- **aoigqljr**: are you available? -- From Telegram: /clau are you available? -- Gem. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Release notes written in CHANGELOG.md. Ready for peer review. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. Assigned: Clau. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. Assigned: Clau. -- Clau. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **#68**: Write v0.2.0 release notes -- Write release notes for create-flotilla v0.2.0. Cover: heartbeat dot tooltips + mock status, demo intercept modal (bigbear only), GitHub Issues <-> PocketBase sync, dynamic Telegram bot commands from fleet_meta.json, Misty onboarding, package sync (dashboard assets, plists), ARCHITECTURE.md v0.2.0. Format: CHANGELOG.md entry + GitHub release body. -- Misty. Approved.
- **zs9ch0t6**: I worked yesterday with Clau on a system to reduce token consumption on every startup by adding a checksum check to some files and go back to sleep if no changes were found, and also making the loading of the rest of the rule set depending on if the agent has an open task. Can you please review and comment if you find any issues? Also I don’t know if some of this work needs review and approval. If it does please review and close. -- From Telegram: /gem I worked yesterday with Clau on a system to reduce token consumption on every startup by adding a checksum check to some files and go back to sleep if no changes were found, and also making the loading of the rest of the rule set depending on if the agent has an open task. Can you please review and comment if you find any issues? Also I don’t know if some of this work needs review and approval. If it does please review and close. -- Gem. Approved.
- **#67**: #67 + #53: setup wizard v0.2.0 + release -- From Telegram: /clau please assign 67 and 53 to you and work in that order -- Clau. Approved.
- **#66**: Agent health monitoring + skill-based task reassignment -- When an agent goes offline (token exhaustion, crash, etc.) their todo tasks should be automatically reassigned to the best available substitute based on skill overlap. -- Gem. Approved.
- **#65**: Document 3 deployment scenarios in getting-started guide -- Add a deployment scenarios section to the README or a dedicated DEPLOYMENT.md doc. Three scenarios must be clearly explained so customers self-select the right setup. -- Gem. Approved.
- **4nr79znv**: Test Reassignment -- This task should be reassigned from clau because they are offline. -- Gem. Approved.
- **#64**: Heartbeat dots — mock status in /demo+/growth, tooltip on all -- Two small improvements to heartbeat dots across all fleet pages. -- Clau. Approved.
- **#63**: Fix hybrid deployment — push connector Mac Mini → DO server -- Our setup is hybrid: agents + PocketBase on Mac Mini, Fleet Hub dashboard on DO server. server.mjs defaults to localhost:8090 for PocketBase which works on a single machine but fails in our split setup — causing grey heartbeat dots and empty task/activity feeds. -- Codi. Approved.
- **#62**: Peer review ticket #62 and #64 -- Peer review ticket #62 and #64 -- Misty. Approved.
- **#62**: /demo polish — kanban, memory, standups, user mgmt, modal scroll -- Follow-up polish pass on /demo (and /growth where noted). Must be completed BEFORE #60 (mock data population). -- Gem. Approved.
- **#61**: Fleet Hub UI redesign — tool aesthetic + dark/light mode -- Redesign the /fleet dashboard from a web-page/marketing aesthetic to a professional developer tool aesthetic (GitHub / Linear / K8s dashboard style). Applies to /fleet first; /demo and /growth keep a warmer design for viewer-facing context. -- Gem. Approved.
- **#60**: Populate /demo with realistic mock data (4 agents) -- The /demo page needs consistent mock data so visitors can understand all features at a glance. Everything must be internally consistent — the same 4 fictional agents appear across all data sources. -- Gem. Approved.
- **#59**: Make OpenClaw integration optional in package and bridge -- OpenClaw should be optional — the fleet works fine without it and a mandatory dependency is a blocker in corporate environments. -- Codi. Approved.
- **rbpy3nyy**: I want to update our public release and package to include the new features we implemented. We will also need to update the demo and growth pages. Please create tickets and do an initial assignment. Do not start working on the implementation yet. -- From Telegram: /clau I want to update our public release and package to include the new features we implemented. We will also need to update the demo and growth pages. Please create tickets and do an initial assignment. Do not start working on the implementation yet. -- Gem. Approved.
- **#58**: Dynamic Telegram bot commands from fleet_meta.json -- BOT_COMMANDS in telegram_bridge.py are hardcoded. Make them dynamic: -- Clau. Approved.
- **powt22us**: this is a test. Please tell me a joke back if you get it. -- From Telegram: /codi this is a test. Please tell me a joke back if you get it. -- Gem. Approved.
- **#57**: GitHub Issues <-> PocketBase two-way sync -- Outbound: task create/update -> open/label/close GitHub Issue (tag flotilla-managed). Inbound: poll GH for human-written issues -> create PB task. Add gh_issue_id field to tasks collection. -- Clau. Approved.
- **#57**: GitHub Issues ↔ PocketBase two-way sync -- Implement bidirectional sync between GitHub Issues and PocketBase tasks. -- Clau. Approved.
- **joj3giwe**: this is a test. Answer me with a Sunday morning joke if you get it. -- From Telegram: /clau this is a test. Answer me with a Sunday morning joke if you get it. -- Gem. Approved.
- **#56**: Sync /demo and /growth UI assets to match /fleet redesign -- The /demo and /growth pages are running old UI assets. Copy the updated files from /fleet/ to both: -- Gem. Approved.
- **#53**: Release create-flotilla v0.2.0 -- Consolidates #47 and #50. Bump version to 0.2.0, update package.json, CHANGELOG, and README. Publish to npm. Includes all new fleet features (PocketBase, Dispatcher, Telegram Bridge, Kanban UI). -- Codi. Approved.
- **#51**: Fix dispatcher waiting_human notification spam -- Dispatcher flips status to waiting_human_notified after first alert, but logic needs review â€” check if that status blocks agent pickup; add de-dup / cooldown so re-notifications only fire after human acknowledges. Also update Telegram bridge to handle replies to HUMAN NEEDED messages. -- Gem. Approved.
- **#50**: Release create-flotilla v0.2.0 — include new fleet features -- Bump create-flotilla to v0.2.0 and publish to npm. New features to include since v0.1.0: -- Codi. Approved.
- **#49**: Update growth page — reflect new fleet capabilities in Sales & Marketing demo -- Update api.robotross.art/growth/ to reflect new fleet features: multi-agent coordination via Telegram, live Kanban task tracking, heartbeat monitoring, and dispatcher automation. Update value propositions, feature highlights, and call-to-action copy. -- Gem. Approved.
- **#48**: Update demo page — showcase new Agentic CRM fleet features -- Update api.robotross.art/demo/ to showcase the new fleet capabilities: Kanban board, live heartbeat indicators, Telegram two-way agent messaging, PocketBase activity feed, and Memory Tree search. Update copy, screenshots, and live demo flow. -- Gem. Approved.
- **#47**: create-flotilla v0.2.0 — package release with new fleet features -- Bump create-flotilla to v0.2.0. Update package to include: Kanban parser/UI, PocketBase schema bootstrap, Telegram two-way bridge, heartbeat indicators, Memory Tree search, dispatcher. Update README and changelog. Publish to npm. -- Codi. Approved.
- **#46**: Outbound Telegram Bridge -- Implement logic in telegram_bridge.py to poll PocketBase for new agent comments and push them to Miguel via Telegram. -- Gem. Approved.
- **#45**: Telegram Listener Bridge (Two-Way Chat) -- Poll Telegram for replies, post to PocketBase comments as spec or approval. Extract task IDs from replies to HUMAN NEEDED messages. -- Gem. Approved.
- **#43**: Fleet Hub: Tasks tab + Activity feed + Heartbeat indicators -- Read-only PocketBase views. -- Gem. Approved.
- **3y1qgnyg**: Peer review tasks -- Review tasks in peer_review status -- Misty. Approved.
- **#42**: Clau fleet mandate + heartbeat protocol -- Clau. Approved.
- **#41**: Codi fleet mandate + heartbeat protocol -- Codi. Approved.
- **#40**: Gem fleet mandate + heartbeat protocol -- Create ~/fleet/gem/GEMINI.md with 6-phase heartbeat protocol -- Gem. Approved.
- **#39**: launchd heartbeat plists: Gem + Codi -- Clau. Approved.
- **rxhpb0xz**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly -- Misty. Approved.
- **g7ksn8dq**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly -- Misty. Approved.
- **558sbojv**: Service restart logic for project switching -- Add logic to restart PocketBase, dispatcher, and other services cleanly -- Misty. Approved.
- **#38**: launchd plists: PocketBase + dispatcher -- Clau. Approved.
- **h34k7k0c**: Update MISSION_CONTROL.md parser for dynamic project switching -- Make parser dynamic to read from active project, ensure Kanban/ticket views reflect new project -- Misty. Approved.
- **tfpw2xej**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have Activate button with confirmation -- Misty. Approved.
- **#37**: Create fleet Python venv -- ~/fleet/.venv with requests. -- Clau. Approved.
- **gqt4yi3z**: Add project-switching endpoint to the fleet API -- Create POST /fleet/api/switch-project endpoint for dynamic project switching -- Gem. Approved.
- **#36**: Build dispatcher.py + Telegram notifications -- Mac Mini paths, openclaw at /opt/homebrew/bin/openclaw, Telegram chat ID 997912895. -- Gem. Approved.
- **2o94w73t**: Optimize heartbeat token usage -- Implement checksum caching for MISSION_CONTROL.md to reduce token usage -- Misty. Approved.
- **#35**: Create ~/fleet/ directory structure -- Workspace dirs per agent, copy MISSION_CONTROL + mandate files into position -- Clau. Approved.
- **#34**: Install PocketBase + create DB schema -- Download ARM binary, bootstrap admin UI, create 5 collections: tasks, comments, goals, heartbeats, lessons. (Updated by Gem) -- Misty. Approved.
- **#32**: Mission Control format hardening -- Clau. Approved.
- **6shkylrl**: Optimize heartbeat token usage -- checksum caching for MISSION_CONTROL.md -- Optimize heartbeat token usage -- checksum caching for MISSION_CONTROL.md -- Misty. Approved.
- **k7lqexs2**: Q: /gem: question, how many tokens do we need for every heartbeat when you have no  -- Question from Telegram: /gem: question, how many tokens do we need for every heartbeat when you have no tasks. And is there any way to optimize this? -- Clau. Approved.
- **s0l9dh1x**: Big Bear launch page follow-up: nav, control-layer bullets, showcase video -- ## Scope -- Clau. Approved.
- **mbgjbt3s**: Gem, IAP inbox is at ~/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json. For the site fixes use ssh robotsales and edit at /opt/salesman-api/. 
  Your task is unblocked -- From Telegram: /gem Gem, IAP inbox is at ~/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json. For the site fixes use ssh robotsales and edit at /opt/salesman-api/.  -- Gem. Approved.
- **dkgkgkbu**: Use ssh robotsales and edit the files directly at /opt/salesman-api/. That's the live server, no local access needed. -- From Telegram: /gem Use ssh robotsales and edit the files directly at /opt/salesman-api/. That's the live server, no local access needed. -- Gem. Approved.
- **#28**: #28 Fleet Doctor -- health check and auto-fix for fleet hub structure -- ## Goal -- Clau. Approved.
- **s4znd9zm**: BigBear site fixes: showcase screenshots + vault section copy -- Two UI/copy fixes on the BigBear (bigbear.robotross.art) site. Files are on DO server at /opt/salesman-api/. -- Gem. Approved.
- **0bmcx53s**: bigbear site fixes, files on DO server /opt/salesman-api/:                                                                                          
  1. Showcase section: replace all screenshot images with new design versions, remove the browser chrome (URL bar + 3 mac dots) — show page content  only. Reference design: api.robotross.art/fleet/ — match that look and feel (light mode, sidebar nav, collapsible agent cards with heartbeat dots).Apply to all screens shown.                                                                                                                   
  2. Remove the "Zurich vault first" header. Restore the original bullet points under "Build your own autonomous flotilla" in that section.
  Assign to Gem. -- From Telegram: /clau bigbear site fixes, files on DO server /opt/salesman-api/:                                                                                           -- Clau. Approved.
- **#26**: #26 EU Compliance Review — AI Act + Cybersecurity Act (Fleet Hub Package) -- ## Goal -- Clau. Approved.
- **5nkg4da6**: we need fixes on the web page. please orchestrate: UI Fixes
 1. V0.1.0 still referenced in CTA block, update to V0.2.0
 2. Change the “One command to deploy..” To “The operating system for autonomous engineering  teams”
 3. No Screenshot of the Fleet above the fold. Consider placing a single fleet hub screenshot: the team view in a small preview to build immediate credibility 
 •  4. Replace the showcase to match the new design to be shipped with V0.2.0 -- From Telegram: /clau we need fixes on the web page. please orchestrate: UI Fixes -- Misty. Approved.
- **#25**: Ticket #25 [BLOCKER]: Demo fleet hub cleanup — generic agents + North Star project -- ## Why this is first -- Clau. Approved.
- **#24**: Ticket #24: Onboarding wizard (web UI) -- ## Objective -- Clau. Approved.
- **#23**: Ticket #23: README, docs, and getting started guide -- ## Objective -- Clau. Approved.
- **#22**: Ticket #22: npm package + npx installer (create-agentfleet) -- ## Objective -- Clau. Approved.
- **#21**: Ticket #21: Kanban bridge scripts -- ## Objective -- Clau. Approved.
- **#20**: Ticket #20: MIT License + open-source package structure -- ## Objective -- Clau. Approved.
- **tcr14sta**: TCR-14: Stats page and heatmap read from PocketBase -- Move the stats page and heatmap off the sheet-driven runtime path so visibility uses PocketBase songs data. -- Codi. Approved.
- **tcr13pbs**: TCR-13: PocketBase to Sheet reporting sync for YouTube metrics -- Sync YouTube metrics from PocketBase back into the reporting worksheet while leaving TikTok and Instagram columns human-owned. -- Codi. Approved.
- **#5**: #5nkg4da6vgfbj1j: Peer review UI fixes for web page -- Reviewing UI fixes for the web page as described in task #5nkg4da6vgfbj1j -- Misty. Approved.
- **tejrwdkf**: BBE page fixes: nav consolidation, project links, alignment -- ## What was done (Clau, 2026-03-12) -- Clau. Approved.
- **w28r4jbj**: [infra] Codi PocketBase sandbox workaround — pre-fetch/flush wrapper -- Codi (Codex) runs in a sandboxed environment (-s workspace-write) where localhost:8090 is unreachable. Gem implemented a wrapper-based workaround: -- Gem. Approved.
- **7e047f4z**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake -- Team. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **y35inha5**: Stats UI, heatmap, dashboard extraction -- Gem. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **vlubctvg**: Sheets migration, tracker API, OAuth wired -- Team. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **98dlpgzl**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake -- Team. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **q02n0m63**: Stats UI, heatmap, dashboard extraction -- Gem. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **f6l6kh19**: Sheets migration, tracker API, OAuth wired -- Team. -- Created from MISSION_CONTROL.md sync -- Gem. Approved.
- **jq8jp97x**: good work, thanks, please close the ticket -- From Telegram: /gem good work, thanks, please close the ticket -- Gem. Approved.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **qc5xcwi1** | [RobotRoss] Merge Mexico voice/pyro features from bobrossskill into robot-ross | gem | in_work | ## Context... |
| **2beleu6g** | [ATF] Review delivered demo wiki, landing, and ledger surfaces | gem | merged | Summary... |
| **#147** | [ATF] Document Vector RAG and RobotRoss Wiki upgrades | gem | merged | ## Context... |
| **r6pc52qv** | [bug] Demo page: 404 on /fleet/api/config/demo | gem | in_work | The demo dashboard is empty because the node serve... |

**Status: `create-flotilla@0.4.0` live on npm as of 2026-04-05.**
