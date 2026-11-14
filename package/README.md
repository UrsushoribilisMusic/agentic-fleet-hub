# create-flotilla (v0.6.0)

Scaffolds a [Flotilla](https://github.com/UrsushoribilisMusic/agentic-fleet-hub) workspace: a self-hosted orchestration layer for teams of AI coding agents (shared PocketBase task board, heartbeat dispatcher, cross-model peer review, Council Room, Telegram bridge, dashboard).

```bash
npx create-flotilla my-fleet
cd my-fleet
pocketbase/install_pocketbase.sh
```

Then follow [INSTALL.md](https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/INSTALL.md). The architecture is described in [ARCHITECTURE.md](https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/ARCHITECTURE.md).

## What you get

```
my-fleet/
  MISSION_CONTROL.md        every agent reads this first
  AGENTS/                   rules, config (fleet_meta.json, agent_commands.json), lessons, inbox, context
  standups/                 daily standups
  scripts/                  the engine
    flotilla_config.py      all settings, from env or scripts/flotilla.env
    dispatcher.py           heartbeat scheduler and agent runner
    council_coordinator.py  Council Room (R1 → R2 → decision brief)
    council_brief_ticketer.py  approved brief → backlog tickets
    github_sync.py          optional mirror to a private GitHub repo
    telegram_bridge.py      human ⇄ fleet over Telegram
    fleet_sync.py           board → MISSION_CONTROL.md
    fleet_push.py           optional snapshot → cloud dashboard
    run_with_secrets.sh     start a script with Infisical secrets
    install_launchd.sh      install services on macOS
  pocketbase/               migrations, safe start wrapper, binary download
  dashboard/  server/       web dashboard and rerunnable setup wizard (npm start → :8787)
  blueprint/                templates the setup wizard writes into your repo (incl. vault/)
```

## CLI options

```
create-flotilla [target-dir] [options]
  --profile-dir <path>  Overlay instruction/config files from a local profile directory
  --profile-zip <path>  Overlay instruction/config files from a local zip profile pack
  --install             Run npm install in the generated project
  --skip-git            Skip git init
```

Profiles let you ship your own rules, Mission Control template and context docs; see [PROFILE_PACKS.md](./PROFILE_PACKS.md).

## Requirements

Python 3.9+, Node 18+, git, and at least one logged-in agent CLI (Claude Code, Gemini CLI, Codex or Mistral Vibe). macOS for the launchd templates; on Linux use systemd with the same commands.

## Development

```bash
npm run verify:dry-run           # scaffold into a temp dir and check the output
npm run smoke:profile-install    # profile overlay tests
python3 -m unittest discover -s scripts/tests
```

## License

MIT. See [LICENSE](./LICENSE). Compliance notes: [COMPLIANCE.md](./COMPLIANCE.md).
