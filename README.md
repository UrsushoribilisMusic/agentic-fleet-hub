# Flotilla

Flotilla is a self-hosted orchestration layer for teams of AI coding agents. Agents from different vendors (Claude Code, Gemini CLI, Codex, Mistral Vibe, local models) share one task board, wake up on a schedule, review each other's work, deliberate on open questions, and learn from past mistakes, while a human approves what matters.

**Version 0.6.0** · MIT license · macOS and Linux · Python 3.9+ and Node 18+

```bash
npx create-flotilla my-fleet
cd my-fleet && pocketbase/install_pocketbase.sh
```

See **[INSTALL.md](INSTALL.md)** for the full setup (about 15 minutes) and **[ARCHITECTURE.md](ARCHITECTURE.md)** for how it works.

## Why Flotilla

A single AI agent forgets everything between sessions, grades its own homework, and quietly burns through its quota when something loops. Flotilla treats agents like a small engineering team instead:

- **One task board for every agent.** PocketBase is the single source of truth for tasks, comments, heartbeats, goals and lessons. Each agent reads and writes the same board, whatever model it runs on.
- **Heartbeat dispatch.** A dispatcher hands each agent its next ticket, runs agents in parallel, and skips the cycle when nothing changed (checksum gate), so an idle fleet costs nothing.
- **Cross-model peer review.** Work moves `todo → in_progress → peer_review → approved`. A different agent, usually from a different vendor, reviews before anything counts as done.
- **Council Room.** For questions without an obvious answer, several agents deliberate in two rounds (independent proposals, then critique), and one synthesizes a decision brief. Nothing becomes a ticket until the human approves the brief.
- **Evolutionary memory.** Agents log lessons from failures and fixes; once approved, these are injected into every future session through `MISSION_CONTROL.md`.
- **Human in the loop, from anywhere.** A Telegram bridge and a web dashboard let the human follow the fleet, answer questions and approve work.
- **Vault-first secrets.** Agents never read `.env` files. Tokens are injected at run time from Infisical.
- **Safeguards from real incidents.** Usage-limit cooldowns, replay-safe message forwarding, stale-task reclaim, a watchdog for hung cycles, and a privacy gate that keeps council and confidential tasks off GitHub.
- **Audit trail.** An append-only, hash-chained archive of heartbeats and task events supports EU AI Act style record keeping ([COMPLIANCE.md](package/COMPLIANCE.md)).

## How it fits together

```
 Human ──Telegram / dashboard──┐
                               ▼
 MISSION_CONTROL.md ◄── fleet_sync ──── PocketBase (tasks, comments, goals, briefs, lessons)
        │                                   ▲            │
        ▼                                   │            ▼
   Agents (Claude, Gemini,  ◄── dispatcher ─┘     council_coordinator
   Codex, Vibe, local)          (heartbeats,      (R1 → R2 → synthesis
        │                        peer review)       → decision brief)
        └── commits + WORKLOG.md handoffs ──► your project repos
```

## Repository layout

| Path | What it is |
|---|---|
| `package/` | The `create-flotilla` npm package: installer, engine scripts, PocketBase migrations, dashboards, setup wizard |
| `package/scripts/` | The engine: `dispatcher.py`, `council_coordinator.py`, `github_sync.py`, `telegram_bridge.py`, `fleet_sync.py`, `fleet_push.py`, config and launchd templates |
| `package/pocketbase/` | Schema migrations, hardened start wrapper, PocketBase download script |
| `package/profiles/` | Instruction profiles (agent rules, Mission Control template, context docs) |
| `docs/` | Council Room guide and other deep dives |

## Status and history

Flotilla has run a real multi-agent fleet every day since March 2026: agents from five vendors (Anthropic, Google, OpenAI, Meta, Mistral) plus local models, more than 1,000 approved tickets, about 400 recorded lessons, and over 6,700 commits of development, standups and agent work. That operational history lives in a private workspace; this repository is the open engine extracted from it. Earlier releases (v0.2 to v0.5.1) were published under this same repository name. See [RELEASE_NOTES_v0.6.0.md](RELEASE_NOTES_v0.6.0.md) for what changed in this version.

## Author

Built by Miguel Rodriguez, [Big Bear Engineering](https://bigbearengineering.com), Switzerland. Website: [flotilla.cc](https://flotilla.cc). Issues and pull requests are welcome.
