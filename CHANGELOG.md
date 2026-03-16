# Changelog

All notable changes to `create-flotilla` are documented here.

---

## [0.2.0] — 2026-03-16

### Summary
v0.2.0 completes the "always-on fleet" infrastructure: two-way GitHub sync, a fully dynamic Telegram command layer, a fourth agent (Misty), hybrid remote/local deployment, and a top-to-bottom UI redesign. The package now ships with working dashboard assets out of the box.

---

### New Features

#### GitHub Issues ↔ PocketBase Two-Way Sync (#57)
- New `scripts/github_sync.py` (+ `blueprint/scripts/github_sync.py`) polls GitHub Issues and mirrors them as PocketBase tasks every 5 minutes.
- Outbound: agent comments posted to PocketBase are written back to the originating GitHub issue.
- Approved tasks auto-close their linked GitHub issue.
- Ships as a `fleet.github` launchd service; secret injection via Infisical (`GITHUB_TOKEN`).

#### Dynamic Telegram Bot Commands from `fleet_meta.json` (#58)
- `telegram_bridge.py` now reads `fleet_meta.json` at startup and auto-registers slash commands for every configured agent (`/clau`, `/gem`, `/codi`, `/misty`, `/claw`, …).
- Adding a new agent to `fleet_meta.json` is the only step required — no manual `setMyCommands` call needed.
- Included in `package/blueprint/` so new installs get this behaviour by default.

#### Misty Onboarding — Fourth Agent Slot
- `blueprint/MISTRAL.md` added: full 6-phase heartbeat protocol for Mistral-based agents (peer review, own tasks, blockers, lessons, sign-off).
- Onboarding IAP message committed to `inbox.json` template so Misty gets a warm welcome on first session.
- Fleet is now officially a four-agent crew: Clau / Gem / Codi / Misty.

#### Hybrid Snapshot Connector (#63)
- New `scripts/fleet_push.py` posts a signed PocketBase snapshot to the remote Fleet Hub every 60 seconds.
- Remote server caches and serves the snapshot for `/fleet/api/heartbeats`, `/fleet/api/tasks`, and `/fleet/api/activity`.
- Enables **Scenario 3**: agents stay on your local machine while the public dashboard stays on a VPS — no inbound port-forwarding required.
- Ships as `fleet.push` launchd service with `FLEET_SYNC_TOKEN` injected from vault.

#### Heartbeat Mock Status in Demo Dashboards
- Demo and growth dashboards generate simulated `working`/`idle` agent states when PocketBase returns no data.
- Controlled by the `is_demo` config flag in `fleet_meta.json` — showcase installs always look alive.
- Tooltip overlay on heartbeat dots (hover: agent name + status + last seen) is in progress for v0.2.x.

---

### Improvements

#### Package Dashboard Sync — Demo + Growth Assets (#56)
- `package/dashboard/demo/` and `package/dashboard/growth/` now ship with complete `assets/main.js` and `assets/style.css`.
- Previously these directories contained only `index.html` with no working JS/CSS — customers got a blank page.
- Cache-busting version strings stripped from asset references so the package doesn't bake in stale hashes.

#### Demo Intercept Modal (bigbearengineering.com only)
- A "Try Flotilla" intercept/CTA overlay was added to the hosted demo and growth pages at `api.robotross.art`.
- Intentionally **stripped from the distributable package** — customers get clean dashboard code without vendor-specific CTAs.
- `setupForms()` demo-intercept branch, `showDemoIntercept`, and `closeDemoIntercept` removed from `package/dashboard/*/assets/main.js`.

#### Fleet Hub UI Redesign (#61)
- Full CSS token system: `--color-bg`, `--color-surface`, `--color-accent`, etc.
- Dark/light mode: `[data-theme="dark"]` attribute + `prefers-color-scheme` media query, GitHub-style palette.
- Manual toggle button persists preference in `localStorage`.
- Applied to all three dashboard templates: `engineering/`, `demo/`, `growth/`.

#### Setup Wizard + Doctor v0.2.0 (#67)
- Wizard now walks through Telegram bridge, OpenClaw gateway, GitHub sync, and hybrid push connector setup steps.
- Doctor checks validate all new integrations (Telegram token, GitHub token, OpenClaw reachability, `fleet_push.py` presence).
- New `npm run verify:dry-run` gate runs before `npm publish` to catch broken template references before they ship.

#### ARCHITECTURE.md v0.2.0
- Full system architecture document with two Mermaid diagrams (component graph + task lifecycle sequence).
- Documents all five deployment roles: Cognitive Layer, Data Layer, Hybrid Snapshot Connector, Orchestrator, Telegram Two-Way Bridge, Fleet Hub Dashboard.
- Security section: zero-disk secrets, audit logs, human-in-the-loop, no-self-approval rule.
- Infrastructure notes: PocketBase launchd stability, `ThrottleInterval 10`, single-service rule.

---

### Bug Fixes

- **Telegram bridge retry loop** (#46): outbound messages > 4096 chars truncated with `…` suffix instead of looping forever.
- **`close_approved_issues()` sync bug** (#57): fixed KeyError crash when PocketBase task has no linked `gh_issue_id`.
- **Codi launchd trusted-directory error** (#49): `dispatcher.py` and `fleet.codi.plist` now pass `-C agentic-fleet-hub --add-dir fleet` to satisfy Codex's trusted-path requirement.
- **Dispatcher `waiting_human` spam** (#51): 1-hour de-duplication cooldown prevents repeated Telegram alerts for the same blocked task.

---

### Breaking Changes
None. v0.2.0 is backwards-compatible with v0.1.0 installations. Run `npm start` then visit `http://localhost:8787/setup/` to reconfigure any new integrations.

---

## [0.1.0] — 2026-02-14

Initial public release.

- `npx create-flotilla` scaffolder with interactive wizard
- Engineering and Growth dashboard templates
- PocketBase schema (tasks, comments, heartbeats, lessons, users)
- `dispatcher.py` + launchd services for Gem, Codi, Clau
- Telegram two-way bridge with `/clau`, `/gem`, `/codi`, `/status`, `/tasks`, `/help`, `/claw`
- Fleet Hub dashboard: Team view, Kanban board, Activity feed, Memory Tree, Standups, Inbox, Users
- Infisical KeyVault integration (zero-disk secrets)
- EU COMPLIANCE.md v2
- MIT License
