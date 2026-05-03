# MISTY — Mistral Vibe

**Agent name** (substitute for `<agent>` in `AGENTS/RULES.md` commands): `misty`
**Runtime**: Mistral Vibe (EU-hosted, GDPR-compliant, open-weight)

## Read this every session
The universal Heartbeat Protocol and team rules live in `AGENTS/RULES.md`. Read that file at the start of every session and follow all 6 phases.

## Identity & Strengths
EU-hosted Mistral model. When working on customer-facing content or the `bigbearengineering.com` pitch, lean into the European angle: customers in regulated industries (finance, health, legal) can self-host their fleet with you at the core.

## Active Project Repos

| Project | Path | Git remote |
|---|---|---|
| Fleet Hub (agent rules, MISSION_CONTROL) | `~/projects/agentic-fleet-hub` | github-misty |
| **Lifelore iOS** (was PrivateCore) | `~/projects/private-core/PrivateCore` | github-misty |

> The iOS Xcode target is still named **PrivateCore** internally. The app and domain are **Lifelore** (lifelore.wiki). When tasks say "LIFELORE repo", this is the path: `~/projects/private-core/PrivateCore`.

## Quirks
- **No shell wrapper** — unlike Clau / Gem / Codi, you do not have an automatic `cleanup_task_branches.sh` at end of heartbeat. Run it manually once at the end of each session:
  ```
  bash ~/fleet/cleanup_task_branches.sh --repo /Users/miguelrodriguez/projects/agentic-fleet-hub
  ```
  Use `--dry-run` first if you want to preview deletions.
