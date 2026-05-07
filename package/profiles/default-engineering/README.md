# Default Engineering Profile

This profile is the reusable engineering instruction pack for a Flotilla fleet. It bootstraps the shared coordination rules, agent-specific mandate files, starter memory folders, and placeholder configuration needed for a new multi-agent engineering workspace.

This README explains the pack itself. If you copy the profile directly into a new repository, replace this file with a project README after setup or move this content into onboarding docs.

## Contents

- `MISSION_CONTROL.md` — root project coordination template.
- `ARCHITECTURE.md` — starter architecture map required by the shared rules.
- `.gitignore` and `gitignore.template` — starter ignore rules. The template copy exists because npm packages omit `.gitignore`.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `MISTRAL.md`, `GEMMA.md` — runtime-specific mandate files (Codex, Claude Code, Gemini CLI, Mistral Vibe, local model slot).
- `AGENTS/RULES.md` — shared fleet heartbeat, task lifecycle, code review, reporting, and safety rules.
- `AGENTS/KEYVAULT.md` — vault usage rules without secrets.
- `AGENTS/CONFIG/fleet_meta.json` — fleet roster and project registry template.
- `AGENTS/CONFIG/fleet_settings.json` — heartbeat and task-tracker configuration template.
- `AGENTS/CONFIG/demo_meta.json` — empty demo/showcase metadata template.
- `AGENTS/CONFIG/growth_meta.json` — optional growth/marketing fleet preset (Scout, Echo, Closer roles). Remove if unused.
- `AGENTS/CONTEXT/fleet_steering_architecture.md` — explains the project registry model and startup flow.
- `AGENTS/CONTEXT/kanban_format_spec.md` — defines the Markdown Kanban format for `MISSION_CONTROL.md`.
- `AGENTS/CONTEXT/pocketbase_schema.md` — PocketBase collections schema reference for new installs.
- `AGENTS/MESSAGES/inbox.json` — starter inter-agent inbox (empty array).
- `AGENTS/LESSONS/ledger.json` — starter lessons ledger (empty array).
- `standups/` — starter daily-reporting directory with a README and empty index.

## How To Use

Copy the contents of this directory into a new repository root, then replace all `{{PLACEHOLDER}}` values with project-specific values. Keep private machine paths, deploy keys, secrets, and customer details out of the profile; put those in local config or vault-backed files after installation.

Agent-specific files should stay small. Shared coordination behavior belongs in `AGENTS/RULES.md`, and project memory belongs in `AGENTS/CONTEXT/`.

Common placeholders to replace:

| Placeholder | Where it appears | What to put |
|---|---|---|
| `{{PROJECT_NAME}}` | `MISSION_CONTROL.md`, `ARCHITECTURE.md`, `fleet_meta.json` | Your project or org name |
| `{{PROJECT_DESCRIPTION}}` | `MISSION_CONTROL.md`, `ARCHITECTURE.md`, `fleet_meta.json` | One-line project summary |
| `{{ORG_NAME}}` | `MISSION_CONTROL.md`, `fleet_meta.json` | Team or organization name |
| `{{PROJECT_PATH}}` | `fleet_meta.json` | Absolute path to the repo on the local machine |
| `{{PROJECT_REPO_URL}}` | `fleet_meta.json` | GitHub or remote repo URL |
| `{{DEFAULT_BRANCH}}` | `AGENTS/RULES.md`, `fleet_settings.json` | e.g. `main` or `master` |
| `{{KANBAN_URL}}` | `fleet_meta.json`, `growth_meta.json` | GitHub Projects URL or other board URL |
| `{{FLEET_API_URL}}` | `AGENTS/RULES.md` | Base URL for PocketBase API, e.g. `http://localhost:8090` |
| `{{REPO_PATH}}` | `AGENTS/RULES.md` (Code Review Protocol) | Absolute path to the project repo for git commands |
| `{{BUILD_VERIFIER_COMMAND}}` | `AGENTS/RULES.md` (Code Review Protocol) | Build or test command that exits 0 on success |
| `{{VAULT_PROVIDER}}` | `AGENTS/KEYVAULT.md` | Vault provider name (e.g. `infisical`, `1password`, `hashicorp`) |
| `{{VAULT_REGION}}` | `AGENTS/KEYVAULT.md` | Vault region (e.g. `EU`, `US`) |
| `{{START_COMMAND}}` | `MISSION_CONTROL.md` | Local dev start command |
| `{{MAIN_REPO}}` | `growth_meta.json` | Full repo URL (growth fleet config only) |
| `{{CRM_URL}}` | `growth_meta.json` | CRM dashboard URL (growth fleet config only) |

## Quick Verification After Setup

Run these from the repo root to confirm all placeholders are replaced:

```bash
# Find remaining placeholders
grep -r "{{" . --include="*.md" --include="*.json" | grep -v node_modules

# Verify profile has no private machine paths
grep -r "/Users/" .
grep -r "/home/" .
```

## Agent Separation Principle

Agent-specific files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `MISTRAL.md`, `GEMMA.md`) declare the agent's identity key and local quirks only. All shared coordination behavior — the heartbeat protocol, Kanban rules, git conventions, secrets policy, and inter-agent messaging — lives exclusively in `AGENTS/RULES.md`. Keep agent files thin; rules file rich.
