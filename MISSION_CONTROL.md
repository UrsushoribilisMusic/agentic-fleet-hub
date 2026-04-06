# MISSION_CONTROL

Welcome to the **Ursushoribilis Agentic Workspace**. This is the primary entry point for **Clau**, **Gem**, **Codi**, and **Misty**. Read this first to synchronize state across the multi-agent crew.

---

## Team Protocols (Shared Memory)

1.  **Rules & Guidelines**: Read and follow the [Team Rules](./AGENTS/RULES.md) and the [Dual Sync Strategy](./DUAL_SYSTEM.md).
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
| **7. Classical Remix** | `../music-video-tool/` | YouTube Channel: Production & Analytics automation. | [Bible](../music-video-tool/ClassicalRemix_ProductionBible_v2.xlsx) |

---

## 🎵 Music Production & Analytics (The Classical Remix)

*   **Channel**: [The Classical Remix](https://youtube.com/@TheClassicalRemix)
*   **Analytics API**: `api.robotross.art/tracker/analytics` (Live)
*   **Strategy**: Transition from view-count tracking to ROI analysis (Ad spend vs. Watch time/Engagement).
*   **Tooling**: `music-video-tool` root scripts for Data API pulling and `server/api.py` for Command Center endpoints.

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

## Ticket Status (as of 2026-04-05)

### ENVIRONMENT NOTE — Mac Mini migration complete (2026-03-14)
All agents now run on Mac Mini (darwin, Apple Silicon). Key path change: `/Users/miguel/` → `/Users/miguelrodriguez/`. Repos cloned to `~/projects/`. Python 3.12 venv at `~/projects/music-video-tool/.venv312`. OpenClaw at `/opt/homebrew/bin/openclaw`. Fleet always-on infrastructure build in progress — see tickets #34–#43.

---

### CLOSED
- **#999**: Test Dummy Task from Gem -- Created for verification of fleet_sync.py -- Gem. Approved.
- **#93**: Tech-Angle Promotion (Reddit) -- Create tech-focused Reddit posts for u/robotrossart highlighting the Flotilla AI pipeline used for The Classical Remix. Goal: Cross-promotion and engineering credibility. -- Clau. Approved.
- **myhluvej**: Fix Gemma agent: add aichat function tools + update plist invocation -- Gemma is not executing her heartbeat protocol. Root causes: 1) plist uses --rag mode (Q&A only, not agentic), 2) no aichat function tools defined so the model cannot call curl/file ops. Fix: create aichat functions (execute_command, read_file, write_file) and update plist invocation. -- Clau. Approved.
- **3xzo9sva**: Fleet Documentation Audit - Gemma's First Task -- Create a comprehensive DOCUMENTATION_MAP.md file. Task details: 1) Explore repository structure using find/ls commands, 2) Analyze all *.md files, 3) Create DOCUMENTATION_MAP.md with categorized file list, 4) Identify documentation gaps, 5) Commit and push changes. Expected output: DOCUMENTATION_MAP.md at repo root with clear structure and health assessment. -- Gemma. Approved.
- **#90**: YouTube Scout: Advanced Engagement Metrics -- Upgrade music scout to pull estimatedMinutesWatched, avgViewDuration, subsGained, annotationCTR. -- Gem. Approved.
- **#89**: Task Scratchpad: Implement live state-tracking -- Add scratchpad JSON field to PocketBase tasks. Allows agents to store and handoff granular execution state without feed parsing. -- Gem. Approved.
- **#88**: Fleet Policy JSON: Versioned State Machine -- Transition Markdown mandates into a versioned JSON policy doc. Compact policy Doc for tools, constraints, escalation, and handoff rules. -- Codi. Approved.
- **#87**: Lesson Summarizer: Post-session script -- Implement summarize_session.py to compress logs into JSON-structured lessons after each major loop. Inject top lessons into system prompts. -- Clau. Approved.
- **#86**: Refine Lessons Schema: Enforce JSON structure -- Update PocketBase lessons collection to include mandatory fields: {decision, rationale, outcome, confidence_score}. Goal: Structured memory over free-text notes. -- Gem. Approved.
- **#85**: Auto-Generate Daily Standup Files -- ## Problem -- Codi. Approved.
- **#84**: Implement Option 1 - Dual Sync Strategy -- Implement Option 1 as requested by Miguel: Document Dual System, Keep both systems separate, Document that MC is for goals, PB for execution, Checksum system checks both sources. Includes updating dispatcher.py with PocketBase checksum logic. -- Gem. Approved.
- **#83**: Fix Telegram messages incorrectly becoming GitHub issues -- Implemented comprehensive fixes to prevent Telegram direct messages from being incorrectly converted to GitHub issues. Changes include enhanced message routing, source tracking, and GitHub sync filtering. -- Gem. Approved.
- **#82**: Fleet Hub: Add "Blocked" filter to Task Board -- Allow humans to easily find tasks caught by the circuit breaker. -- Gem. Approved.
- **#81**: Sync ~/fleet/gem/ with ~/fleet/ root versions -- Keep workspace copies in sync with deployed scripts. -- Gem. Approved.
- **#80**: Release create-flotilla v0.3.0 to npm -- Perform pre-publish verification and release the new version using the Infisical-backed publish flow. -- Gem. Approved.
- **#79**: Sync /demo and /growth with v0.3.0 Features -- Update public-facing demo and growth pages to reflect the latest fleet capabilities (Kanban, snapshots, monitoring). -- Clau. Approved.
- **#78**: Fleet Hub UI: Dark/Light Mode & Redesign -- Apply the developer tool aesthetic, CSS token system, and dark/light mode toggle to all fleet dashboards. -- Clau. Approved.
- **#77**: Update create-flotilla to v0.3.0 -- Include new dispatcher logic, Telegram slash commands, GitHub sync, and PocketBase snapshot logic into the core package. -- Gem. Approved.
- **pbkec9xa**: ignore MISSION_CONTROL for now. Go directly to PocketBase and set the task titled '[bug] dispatcher: no circuit breaker on reassignment loop when both agents offline' to status blocked. Do not work on it, just block it. -- From Telegram: /codi ignore MISSION_CONTROL for now. Go directly to PocketBase and set the task titled '[bug] dispatcher: no circuit breaker on reassignment loop when both agents offline' to status blocked. Do not work on it, just block it. -- Codi. Approved.
- **#74**: Review of Heartbeat Gate (#74) and Fleet Steering (#75). Fixed Python 3.9 compatibility and added dynamic alias loading. -- Gem. Approved. -- Gem. Approved.
- **syqw2guw**: [bug] dispatcher: no circuit breaker on reassignment loop when both agents offline -- Problem -- Gem. Approved.
- **ykgefztd**: please close all todo tasks. Irrelevant who it’s assigned to -- From Telegram: /misty please close all todo tasks. Irrelevant who it’s assigned to -- Gem. Approved.
- **m2zloxg0**: please stop reassigning the task to Clau -- From Telegram: /gem please stop reassigning the task to Clau -- Gem. Approved.
- **mt9qcp1d**: please stop reassigning the task to gem. -- From Telegram: /clau please stop reassigning the task to gem. -- Gem. Approved.
- **prdjido0**: please pause 80 for now. I am traveling and need to be at the computer to generate the code. Thanks! -- From Telegram: /gem please pause 80 for now. I am traveling and need to be at the computer to generate the code. Thanks! -- Gem. Approved.
- **aoigqljr**: are you available? -- From Telegram: /clau are you available? -- Gem. Approved.
- **zs9ch0t6**: I worked yesterday with Clau on a system to reduce token consumption on every startup by adding a checksum check to some files and go back to sleep if no changes were found, and also making the loading of the rest of the rule set depending on if the agent has an open task. Can you please review and comment if you find any issues? Also I don’t know if some of this work needs review and approval. If it does please review and close. -- From Telegram: /gem I worked yesterday with Clau on a system to reduce token consumption on every startup by adding a checksum check to some files and go back to sleep if no changes were found, and also making the loading of the rest of the rule set depending on if the agent has an open task. Can you please review and comment if you find any issues? Also I don’t know if some of this work needs review and approval. If it does please review and close. -- Gem. Approved.
- **#66**: Agent health monitoring + skill-based task reassignment -- When an agent goes offline (token exhaustion, crash, etc.) their todo tasks should be automatically reassigned to the best available substitute based on skill overlap. -- Gem. Approved.
- **#65**: Document 3 deployment scenarios in getting-started guide -- Add a deployment scenarios section to the README or a dedicated DEPLOYMENT.md doc. Three scenarios must be clearly explained so customers self-select the right setup. -- Gem. Approved.
- **#64**: Heartbeat dots — mock status in /demo+/growth, tooltip on all -- Two small improvements to heartbeat dots across all fleet pages. -- Clau. Approved.
- **#63**: Fix hybrid deployment — push connector Mac Mini → DO server -- Our setup is hybrid: agents + PocketBase on Mac Mini, Fleet Hub dashboard on DO server. server.mjs defaults to localhost:8090 for PocketBase which works on a single machine but fails in our split setup — causing grey heartbeat dots and empty task/activity feeds. -- Codi. Approved.
- **#62**: Peer review ticket #62 and #64 -- Peer review ticket #62 and #64 -- Misty. Approved.
- **#61**: Fleet Hub UI redesign — tool aesthetic + dark/light mode -- Redesign the /fleet dashboard from a web-page/marketing aesthetic to a professional developer tool aesthetic (GitHub / Linear / K8s dashboard style). Applies to /fleet first; /demo and /growth keep a warmer design for viewer-facing context. -- Gem. Approved.
- **#60**: Populate /demo with realistic mock data (4 agents) -- The /demo page needs consistent mock data so visitors can understand all features at a glance. Everything must be internally consistent — the same 4 fictional agents appear across all data sources. -- Gem. Approved.
- **#59**: Make OpenClaw integration optional in package and bridge -- OpenClaw should be optional — the fleet works fine without it and a mandatory dependency is a blocker in corporate environments. -- Codi. Approved.
- **rbpy3nyy**: I want to update our public release and package to include the new features we implemented. We will also need to update the demo and growth pages. Please create tickets and do an initial assignment. Do not start working on the implementation yet. -- From Telegram: /clau I want to update our public release and package to include the new features we implemented. We will also need to update the demo and growth pages. Please create tickets and do an initial assignment. Do not start working on the implementation yet. -- Gem. Approved.
- **powt22us**: this is a test. Please tell me a joke back if you get it. -- From Telegram: /codi this is a test. Please tell me a joke back if you get it. -- Gem. Approved.
- **joj3giwe**: this is a test. Answer me with a Sunday morning joke if you get it. -- From Telegram: /clau this is a test. Answer me with a Sunday morning joke if you get it. -- Gem. Approved.
- **#53**: Release create-flotilla v0.2.0 -- Consolidates #47 and #50. Bump version to 0.2.0, update package.json, CHANGELOG, and README. Publish to npm. Includes all new fleet features (PocketBase, Dispatcher, Telegram Bridge, Kanban UI). -- Codi. Approved.
- **#51**: Fix dispatcher waiting_human notification spam -- Dispatcher flips status to waiting_human_notified after first alert, but logic needs review â€” check if that status blocks agent pickup; add de-dup / cooldown so re-notifications only fire after human acknowledges. Also update Telegram bridge to handle replies to HUMAN NEEDED messages. -- Gem. Approved.
- **#50**: Release create-flotilla v0.2.0 — include new fleet features -- Bump create-flotilla to v0.2.0 and publish to npm. New features to include since v0.1.0: -- Codi. Approved.
- **#49**: Update growth page — reflect new fleet capabilities in Sales & Marketing demo -- Update api.robotross.art/growth/ to reflect new fleet features: multi-agent coordination via Telegram, live Kanban task tracking, heartbeat monitoring, and dispatcher automation. Update value propositions, feature highlights, and call-to-action copy. -- Gem. Approved.
- **#48**: Update demo page — showcase new Agentic CRM fleet features -- Update api.robotross.art/demo/ to showcase the new fleet capabilities: Kanban board, live heartbeat indicators, Telegram two-way agent messaging, PocketBase activity feed, and Memory Tree search. Update copy, screenshots, and live demo flow. -- Gem. Approved.
- **#47**: create-flotilla v0.2.0 — package release with new fleet features -- Bump create-flotilla to v0.2.0. Update package to include: Kanban parser/UI, PocketBase schema bootstrap, Telegram two-way bridge, heartbeat indicators, Memory Tree search, dispatcher. Update README and changelog. Publish to npm. -- Codi. Approved.
- **#46**: Outbound Telegram Bridge -- Implement logic in telegram_bridge.py to poll PocketBase for new agent comments and push them to Miguel via Telegram. -- Gem. Approved.
- **#45**: Telegram Listener Bridge (Two-Way Chat) -- Poll Telegram for replies, post to PocketBase comments as spec or approval. Extract task IDs from replies to HUMAN NEEDED messages. -- Gem. Approved.
- **#43**: Fleet Hub: Tasks tab + Activity feed + Heartbeat indicators -- Read-only PocketBase views. -- Gem. Approved.
- **#42**: Clau fleet mandate + heartbeat protocol -- Clau. Approved.
- **#41**: Codi fleet mandate + heartbeat protocol -- Codi. Approved.
- **#40**: Gem fleet mandate + heartbeat protocol -- Create ~/fleet/gem/GEMINI.md with 6-phase heartbeat protocol -- Gem. Approved.
- **#39**: launchd heartbeat plists: Gem + Codi -- Clau. Approved.
- **#38**: launchd plists: PocketBase + dispatcher -- Clau. Approved.
- **tfpw2xej**: UI for project activation (toggle-based) -- List projects, active project at top with badge, inactive projects have Activate button with confirmation -- Misty. Approved.
- **gqt4yi3z**: Add project-switching endpoint to the fleet API -- Create POST /fleet/api/switch-project endpoint for dynamic project switching -- Gem. Approved.
- **2o94w73t**: Optimize heartbeat token usage -- Implement checksum caching for MISSION_CONTROL.md to reduce token usage -- Misty. Approved.
- **#34**: Install PocketBase + create DB schema -- Download ARM binary, bootstrap admin UI, create 5 collections: tasks, comments, goals, heartbeats, lessons. (Updated by Gem) -- Misty. Approved.
- **#32**: Mission Control format hardening -- Clau. Approved.
- **k7lqexs2**: Q: /gem: question, how many tokens do we need for every heartbeat when you have no  -- Question from Telegram: /gem: question, how many tokens do we need for every heartbeat when you have no tasks. And is there any way to optimize this? -- Clau. Approved.
- **s0l9dh1x**: Big Bear launch page follow-up: nav, control-layer bullets, showcase video -- ## Scope -- Clau. Approved.
- **mbgjbt3s**: Gem, IAP inbox is at ~/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json. For the site fixes use ssh robotsales and edit at /opt/salesman-api/. 
  Your task is unblocked -- From Telegram: /gem Gem, IAP inbox is at ~/projects/agentic-fleet-hub/AGENTS/MESSAGES/inbox.json. For the site fixes use ssh robotsales and edit at /opt/salesman-api/.  -- Gem. Approved.
- **dkgkgkbu**: Use ssh robotsales and edit the files directly at /opt/salesman-api/. That's the live server, no local access needed. -- From Telegram: /gem Use ssh robotsales and edit the files directly at /opt/salesman-api/. That's the live server, no local access needed. -- Gem. Approved.
- **s4znd9zm**: BigBear site fixes: showcase screenshots + vault section copy -- Two UI/copy fixes on the BigBear (bigbear.robotross.art) site. Files are on DO server at /opt/salesman-api/. -- Gem. Approved.
- **0bmcx53s**: bigbear site fixes, files on DO server /opt/salesman-api/:                                                                                          
  1. Showcase section: replace all screenshot images with new design versions, remove the browser chrome (URL bar + 3 mac dots) — show page content  only. Reference design: api.robotross.art/fleet/ — match that look and feel (light mode, sidebar nav, collapsible agent cards with heartbeat dots).Apply to all screens shown.                                                                                                                   
  2. Remove the "Zurich vault first" header. Restore the original bullet points under "Build your own autonomous flotilla" in that section.
  Assign to Gem. -- From Telegram: /clau bigbear site fixes, files on DO server /opt/salesman-api/:                                                                                           -- Clau. Approved.
- **5nkg4da6**: we need fixes on the web page. please orchestrate: UI Fixes
 1. V0.1.0 still referenced in CTA block, update to V0.2.0
 2. Change the “One command to deploy..” To “The operating system for autonomous engineering  teams”
 3. No Screenshot of the Fleet above the fold. Consider placing a single fleet hub screenshot: the team view in a small preview to build immediate credibility 
 •  4. Replace the showcase to match the new design to be shipped with V0.2.0 -- From Telegram: /clau we need fixes on the web page. please orchestrate: UI Fixes -- Misty. Approved.
- **#24**: Ticket #24: Onboarding wizard (web UI) -- ## Objective -- Clau. Approved.
- **#23**: Ticket #23: README, docs, and getting started guide -- ## Objective -- Clau. Approved.
- **#22**: Ticket #22: npm package + npx installer (create-agentfleet) -- ## Objective -- Clau. Approved.
- **#21**: Ticket #21: Kanban bridge scripts -- ## Objective -- Clau. Approved.
- **#20**: Ticket #20: MIT License + open-source package structure -- ## Objective -- Clau. Approved.
- **#5**: #5nkg4da6vgfbj1j: Peer review UI fixes for web page -- Reviewing UI fixes for the web page as described in task #5nkg4da6vgfbj1j -- Misty. Approved.
- **tejrwdkf**: BBE page fixes: nav consolidation, project links, alignment -- ## What was done (Clau, 2026-03-12) -- Clau. Approved.
- **7e047f4z**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake -- Team. -- Gem. Approved.
- **y35inha5**: Stats UI, heatmap, dashboard extraction -- Gem. -- Gem. Approved.
- **vlubctvg**: Sheets migration, tracker API, OAuth wired -- Team. -- Gem. Approved.
- **98dlpgzl**: Growth Fleet, CRM branding, IAP inbox, mobile, BBE site, legal pages, lead intake -- Team. -- Gem. Approved.
- **q02n0m63**: Stats UI, heatmap, dashboard extraction -- Gem. -- Gem. Approved.
- **f6l6kh19**: Sheets migration, tracker API, OAuth wired -- Team. -- Gem. Approved.
- **jq8jp97x**: good work, thanks, please close the ticket -- From Telegram: /gem good work, thanks, please close the ticket -- Gem. Approved.

### OPEN
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#98** | Task branch + WORKLOG handoff protocol | Clau | todo | Dispatcher: check `task/{id}` branch on reassign, include in handoff comment. Rule already added to AGENTS/RULES.md. |

### RECENTLY CLOSED
| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#94** | PB schema: task_events collection + dispatcher metrics logging | Clau | **completed** | Migration + dispatcher wiring done 2026-04-05; PB restarted + meta field fix 2026-04-06 |
| **#95** | Fleet Hub: extended agents table (last seen, idle until, tasks, tokens, success rate) | Gem | **completed** | Shipped 2026-04-05 |
| **#96** | Fleet Hub: Schichtplan — agent shift timeline (swim-lane, 24h/7d/30d) | Clau | **completed** | Shipped 2026-04-05 |
| **#97** | Fleet Hub: aggregate stats panel + retroactive log parser (arXiv paper data) | Gem | **completed** | Part A (live) & Part B (parser) done |


**Status: `create-flotilla@0.3.0` live on npm as of 2026-03-24. Planning for v0.4.0 in progress.**
