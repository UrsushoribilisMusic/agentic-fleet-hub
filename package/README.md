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
