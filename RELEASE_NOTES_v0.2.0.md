# create-flotilla v0.2.0

> **The "always-on fleet" release.** GitHub sync, dynamic Telegram commands, a fourth agent (Misty), hybrid remote/local deployment, and a complete UI overhaul.

---

## What's new

### 🔄 GitHub Issues ↔ PocketBase two-way sync
`github_sync.py` runs as a `fleet.github` launchd service and keeps your GitHub Issues and PocketBase tasks in lock-step. Open a GitHub issue → it appears as a PocketBase task. Agent posts a comment → it shows up on the GitHub issue. Task gets approved → issue gets closed automatically.

Setup: add `GITHUB_TOKEN` to your vault and run the wizard.

### 📡 Dynamic Telegram commands from `fleet_meta.json`
The Telegram bridge now reads `fleet_meta.json` at startup and auto-registers slash commands for every agent in your fleet. Add a new agent to the config file — no other step required.

### 🤖 Misty — fourth agent slot (Mistral Vibe)
`blueprint/MISTRAL.md` ships with the full 6-phase heartbeat protocol. Misty joins Clau, Gem, and Codi as a first-class fleet member.

### 🌐 Hybrid deployment: agents local, dashboard remote
New `fleet_push.py` connector posts a signed PocketBase snapshot to your remote Fleet Hub every 60 seconds. No inbound firewall rules needed. Your agents stay on-prem; stakeholders get the live dashboard.

### 🌗 Dark/light mode UI redesign
Full CSS token system, `prefers-color-scheme` auto-detection, and a manual toggle (preference persisted in `localStorage`). GitHub-style palette. Applies to all three dashboard templates.

### 📦 Dashboard assets now included
`demo/` and `growth/` dashboards previously shipped without JS or CSS — customers got a blank page. Both now include complete `assets/main.js` and `assets/style.css`.

### 🔋 Heartbeat mock status in demo dashboards
Demo/growth dashboards generate simulated `working`/`idle` agent statuses when PocketBase isn't connected. Set `"is_demo": true` in `fleet_meta.json`. Great for showcases and sales demos.

### 🔒 Demo intercept modal
Write-actions in the `/demo` dashboard (task creation, comments, status changes) are now intercepted before they hit PocketBase. A modal prompts visitors to visit the Big Bear landing page instead of silently mutating shared demo data.

### 📐 ARCHITECTURE.md v0.2.0
Updated architecture diagram and component descriptions to reflect the hybrid connector, GitHub sync service, and four-agent fleet topology.

---

## Bug fixes

- Telegram bridge no longer loops forever on messages > 4096 characters (truncates with `…`)
- `close_approved_issues()` no longer crashes on tasks without a linked GitHub issue
- Codi launchd service trusted-directory error resolved
- Dispatcher no longer spams Telegram for the same blocked task (1-hour cooldown)

---

## Upgrade notes

v0.2.0 is fully backwards-compatible. After upgrading:

```bash
cd my-fleet
npm start
# visit http://localhost:8787/setup/ to configure new integrations
```

The wizard will walk you through Telegram, GitHub sync, OpenClaw, and hybrid connector setup. Run `npm run doctor` to validate your configuration.

---

## Installation

```bash
npx create-flotilla my-fleet
cd my-fleet
npm install
npm start
```

---

## What's next (v0.3.x)

- Multi-fleet federation: connect multiple Mac Minis under one dashboard
- Scheduled task triggers: cron-style task creation from `fleet_meta.json`
- Agent capability registry: declare skills per agent, auto-route tasks by capability
- Persistent lesson library: lessons survive fleet resets and sync to team members

---

**Full changelog**: [CHANGELOG.md](./CHANGELOG.md)
