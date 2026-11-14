# Flotilla v0.6.0

v0.6 turns Flotilla from "the engine that runs one fleet" into an engine anyone can install. Every script now reads its settings from configuration, the engine that runs in production is the engine that ships, and the repository contains only the open engine.

## Highlights

- **Installable engine.** `npx create-flotilla my-fleet` produces a workspace that runs end to end: PocketBase schema, dispatcher, Council Room, GitHub and Telegram bridges. Verified with a clean-install test (scaffold, migrate, dispatch a ticket to an agent, run a council round, ticket an approved brief).
- **One configuration module.** `scripts/flotilla_config.py` replaces all hardcoded paths, URLs, repository names and chat ids. Settings come from environment variables or `scripts/flotilla.env`, with defaults relative to the workspace.
- **Configurable agents.** Built-in commands for Claude Code, Gemini CLI, Codex and Mistral Vibe; override any agent (model, flags, folders) or disable it in `AGENTS/CONFIG/agent_commands.json`.
- **Council Room ships in the package.** `council_coordinator.py` (two deliberation rounds plus synthesis, intake gates, timeouts, roster checks), `council_brief_ticketer.py` (approved brief to backlog tickets, now also without GitHub) and `research_ledger.py`, with the council PocketBase migrations.
- **Privacy gate for mirrors.** New `private` and `source` task fields. Council, Telegram and private tasks are never mirrored to GitHub; tasks with a goal or marked `CONFIDENTIAL` never publish their description. GitHub mirroring is off unless you set a repository, and the docs require it to be private.
- **launchd templates and installer.** `scripts/install_launchd.sh` fills in your paths and loads the services; `scripts/run_with_secrets.sh` starts any script under Infisical.
- **PocketBase hardening.** `pocketbase_safe.sh` binds to localhost by default, uses the shipped migrations and has a configurable port; `install_pocketbase.sh` downloads the tested version (0.22.10).
- **Hash-chained audit archive** (`archive_writer.py`) included for compliance record keeping.

## Fixes

- GitHub sync again skips Telegram-sourced and private tasks and reconciles issues closed by humans back to the board.
- The dispatcher's alert for newly imported GitHub issues referenced an undefined repository name and never fired.
- The dashboard server finds `MISSION_CONTROL.md` in installed workspaces, not only in a source checkout.
- Dashboard links to issues and files use your configured workspace repository instead of a fixed one.

## Removed

- Per-agent heartbeat wrappers and their launchd jobs (the dispatcher is the only process that starts agents).
- Product-specific code that had leaked into the package: a document-to-RAG console, ad-spend approval commands, and deployment-specific prompts.
- The duplicate copy of the engine scripts under `blueprint/scripts`; the setup wizard now copies `scripts/` and `pocketbase/` from the package.

## Upgrading from v0.5

1. Run the new migrations (`1793000000_tasks_privacy_fields.js` adds `private` and `source` to `tasks`). If your `decision_briefs` collection has `open_questions_for_miguel`, rename it to `open_questions_for_human`.
2. Move any hardcoded paths from your copies of the scripts into `scripts/flotilla.env`.
3. Replace per-agent launchd jobs with `scripts/install_launchd.sh`.
4. If you mirror to GitHub, make sure the repository is private and set `FLOTILLA_GITHUB_REPO`.

## Repository

This repository was reset to contain only the open engine. The operational history of the fleet that developed Flotilla (standups, council outputs, project work) moved to a private workspace.
