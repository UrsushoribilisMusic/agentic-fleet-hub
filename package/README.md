# AgentFleet Package

> **Status**: Pre-release. Use `create-agentfleet` (coming soon) for the zero-install scaffolder.

This directory contains the open-source core of **AgentFleet** — the multi-agent fleet management framework. It is the source for `npx create-agentfleet`.

---

## Structure

```
package/
  LICENSE                   MIT
  README.md                 This file
  server/
    fleet-server.mjs        Generic fleet API + static serving (Node 18+)
    package.json
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
    kanban_fetch.py         List project items by status
    kanban_update.py        Update item status
    kanban_standup.py       Generate standup from project board
    kanban.sh               Shell wrapper for all three
```

---

## Quick Start (manual)

1. Copy `blueprint/` into your project root.
2. Replace all `{{PLACEHOLDER}}` values in `MISSION_CONTROL.md`, `AGENTS/RULES.md`, and the `CONFIG/*.json` files.
3. Start the server:
   ```bash
   cd server
   npm install
   node fleet-server.mjs
   ```
4. Open `http://localhost:8787/demo/` — add your dashboard HTML to `dashboard/engineering/` and `dashboard/demo/`.

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
