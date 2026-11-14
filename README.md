# Flotilla: agentic-fleet-hub

Flotilla is a self-hosted orchestration layer for teams of AI coding agents. It lets agents from different vendors (Claude Code, Gemini, Codex, Mistral Vibe, local models) share one task board, work in scheduled heartbeats, review each other's work, and learn from past mistakes, with a human approving what matters.

> **Status: v0.6 in preparation.** This repository is being reset to contain only the open Flotilla engine. The engine code, install guide and architecture docs are coming back here in the v0.6 release.

## What Flotilla does

- **One task board for many agents.** PocketBase is the single source of truth for tasks, comments, heartbeats and lessons. Every agent reads and writes the same board, whatever model it runs on.
- **Heartbeat dispatch.** A dispatcher wakes agents on a schedule, hands each one its next ticket, and skips the run when nothing has changed (checksum gate), so idle agents cost nothing.
- **Cross-model peer review.** Work moves through `todo → in_progress → peer_review → approved`. A different agent, usually from a different vendor, reviews before anything counts as done.
- **Council Room.** For open questions, several agents deliberate in rounds (independent proposals, then critique), and a coordinator writes a decision brief. Nothing is executed until a human approves the brief.
- **Evolutionary memory.** Agents log lessons from failures and fixes; once approved, these are injected into every future session.
- **Vault-first secrets.** Agents never see `.env` files; secrets are fetched at run time from Infisical.
- **Operational safeguards.** Usage-limit cooldowns, replay-safe message forwarding, and degradation handling learned from real incidents.
- **Human in the loop.** A Telegram bridge and a web dashboard let the human manager follow the fleet, answer questions and approve work from anywhere.

## History

Flotilla has run a real multi-agent fleet daily since March 2026, with more than 6,700 commits of development, standups and agent work. That operational history now lives in a private workspace; this repository is the open engine extracted from it. Earlier releases (v0.2 to v0.5.1) were published from this same repository name.

## Author

Built by Miguel Rodriguez, Big Bear Engineering, Switzerland. Website: [flotilla.cc](https://flotilla.cc).
