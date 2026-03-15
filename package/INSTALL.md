# Flotilla Installation

Use `create-flotilla` to scaffold a self-hosted Flotilla workspace, then complete onboarding in the browser.

## Prerequisites

- Node.js 18 or newer
- Git, if you want the scaffold to initialize a repository
- An optional target repository path for wizard-driven bootstrap and commit flow

## Quick Start

```bash
npx create-flotilla my-fleet
cd my-fleet
npm install
npm start
```

Open `http://localhost:8787/setup/`.

## What The Installer Creates

The scaffolded project includes:

- `server/` for the Flotilla HTTP server and setup helpers
- `dashboard/` for `/setup/`, `/configure/`, `/demo/`, `/growth/`, and `/fleet/`
- `data/` for local config, standups, inbox, and lessons
- `scripts/doctor.mjs` for local doctor checks
- `blueprint/` for the markdown and vault bootstrap templates

## First-Run Flow

1. Open `/setup/`
2. Choose agents and display names
3. Set repo path, vault provider, and shared links
4. Optionally write bootstrap files into the target repository
5. Use `/configure/` to run doctor, review the diff, and explicitly commit the managed files

## CLI Options

```bash
npx create-flotilla my-fleet --install
npx create-flotilla my-fleet --skip-git
```

- `--install`: runs `npm install` in the generated project
- `--skip-git`: skips `git init`

## Local Commands

```bash
npm start
npm run dev
npm run doctor
```

## Optional: Hybrid Scenario 3

If your agents and PocketBase stay on a local machine but the Fleet Hub is public on a VPS, enable the snapshot connector:

1. Ensure the remote server accepts `POST /fleet/snapshot` with `FLEET_SYNC_TOKEN`.
2. Place `scripts/fleet_push.py` in the live fleet workspace.
3. Load `scripts/fleet.push.plist` under `~/Library/LaunchAgents/`.
4. Inject `FLEET_SYNC_TOKEN` at runtime with your vault provider.

The connector pushes `heartbeats`, `tasks`, and `comments` every 60 seconds. The remote Fleet Hub then serves the cached snapshot when it cannot reach PocketBase directly.
