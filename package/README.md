# AgentFleet Package

This directory contains the open-source core of **Flotilla** and now ships the `create-flotilla` scaffolder.

```bash
npx create-flotilla my-fleet
cd my-fleet
npm install
npm start
```

Then open `http://localhost:8787/setup/` and complete the rerunnable onboarding wizard.
For a step-by-step installation walkthrough, see [INSTALL.md](./INSTALL.md).

---

## Structure

```
package/
  package.json              npm package manifest for create-flotilla
  bin/
    create-flotilla.mjs     CLI scaffolder entrypoint
  LICENSE                   MIT
  README.md                 This file
  server/
    fleet-server.mjs        Generic fleet API + static serving (Node 18+)
    setup-lib.mjs           Shared setup/bootstrap/doctor helpers
    package.json            Server-only manifest kept for standalone use
  blueprint/                Template files copied into new projects
    MISSION_CONTROL.md      Project HQ (fill in {{PLACEHOLDER}} vars)
    AGENTS/
      RULES.md              Team collaboration rules
      KEYVAULT.md           Secrets management guide
      CONFIG/
        fleet_meta.json     Engineering fleet config template
        growth_meta.json    Sales & marketing fleet config template
      CONTEXT/              Project context docs (add your own)
      LESSONS/ledger.json   Evolutionary memory (starts empty)
      MESSAGES/inbox.json   IAP inbox (starts empty)
    vault/
      vault.py              Python secrets helper (Infisical)
      agent-fetch.sh        Shell secrets fetcher
      agent-fetch.ps1       PowerShell secrets fetcher
      README.md             Vault setup guide
  scripts/                  Kanban bridge (Ticket #21)
    fleet_push.py           Hybrid connector: local PocketBase -> remote Fleet snapshot
    fleet.push.plist        launchd wrapper for the hybrid connector
    kanban_fetch.py         List project items by status
    kanban_update.py        Update item status
    kanban_standup.py       Generate standup from project board
    kanban.sh               Shell wrapper for all three
```

---

## Quick Start

1. Scaffold a new flotilla:
   ```bash
   npx create-flotilla my-fleet
   cd my-fleet
   npm install
   npm start
   ```
2. Open `http://localhost:8787/setup/`.
3. Use the wizard to set repo path, agent roster, vault provider, and template links.
4. If you provide a git repo, use `/configure/` to run doctor, review the diff, and explicitly commit the managed bootstrap files.

Before publishing package changes, run:

```bash
npm run verify:dry-run
```

That smoke test scaffolds a temporary fleet, bootstraps the current wizard profile, runs the generated doctor, and verifies the engineering dashboard files expose the expected sections, theme toggle, and Add Agent hooks.

## Telegram Control

When the always-on fleet services are enabled, the Telegram bridge can accept slash commands and either:
- queue real PocketBase tasks for agent lanes such as `/clau`, `/gem`, and `/codi`
- answer operational queries inline such as `/status`, `/tasks`, and `/help`
- forward synchronous robot/artist prompts to OpenClaw with `/claw`

Current command surface:

```text
/clau <task>
/gem <task>
/codi <task>
/claw <message>
/ask <question>
/spec <idea>
/status
/tasks
/go
/help
```

Security note:
- `OPENCLAW_GATEWAY_TOKEN` must come from runtime secret injection or the local OpenClaw config.
- Do not hardcode gateway tokens in `telegram_bridge.py`, launchd plists, or committed docs.

## Hybrid Deployment

Scenario 3 uses a push connector so the public dashboard can stay current while PocketBase remains private on the local machine.

Files included for this mode:
- `scripts/fleet_push.py`
- `scripts/fleet.push.plist`

Runtime secrets:
- `FLEET_SYNC_TOKEN` on both the local connector and the remote server
- `FLEET_SYNC_URL` on the local connector if your public dashboard is not `/fleet/snapshot`

What gets synced:
- latest `heartbeats`
- latest `tasks`
- latest `comments`

The remote Fleet server caches that snapshot and uses it as a fallback for `/fleet/api/heartbeats`, `/fleet/api/tasks`, and `/fleet/api/activity` whenever it cannot reach PocketBase directly.

## CLI Options

```bash
npx create-flotilla my-fleet --install
npx create-flotilla my-fleet --skip-git
```

- `--install`: runs `npm install` in the generated project.
- `--skip-git`: does not initialize a git repository.

---

## Templates

| Template | URL path | Auth | Use case |
| :--- | :--- | :--- | :--- |
| `engineering` | `/fleet/` | OAuth (optional) | Private team hub |
| `growth` | `/growth/` | Public | Sales & marketing fleet |
| `demo` | `/demo/` | Public | Live product demo |

---

## Kanban Bridge (scripts/)

Requires: `GITHUB_TOKEN`, `KANBAN_ORG`, `KANBAN_PROJECT_NUMBER` env vars.

```bash
# List all In Progress tickets
./scripts/kanban.sh fetch --status "In Progress"

# Mark ticket #14 as Done
./scripts/kanban.sh update --ticket 14 --status Done

# Generate today's standup
./scripts/kanban.sh standup --repo MyOrg/my-repo --agent "Clau" --output standups/$(date +%F).md
```

---

## Compliance

The AgentFleet Hub package is compliant with the **EU AI Act** and **Cybersecurity Act**. See the [COMPLIANCE.md](./COMPLIANCE.md) document for details.

## License

MIT — see [LICENSE](./LICENSE).
