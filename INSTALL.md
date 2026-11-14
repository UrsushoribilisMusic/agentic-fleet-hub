# Installing Flotilla

About 15 minutes on macOS or Linux. You need Python 3.9+, Node 18+, git, and at least one agent CLI (Claude Code, Gemini CLI, Codex or Mistral Vibe) that is already logged in.

## 1. Create a workspace

```bash
npx create-flotilla my-fleet
cd my-fleet
```

The workspace is the shared memory of your fleet. Put it under git and push it to a **private** repository: it will hold your Mission Control, standups and agent context.

```
my-fleet/
├── MISSION_CONTROL.md      every agent reads this first
├── AGENTS/RULES.md         the fleet's operating rules
├── AGENTS/CONFIG/          fleet_meta.json, agent_commands.json
├── AGENTS/LESSONS/         lessons ledger
├── standups/               daily standups
├── scripts/                the engine (dispatcher, council, sync, bridge)
├── pocketbase/             migrations, start wrapper, binary
├── dashboard/  server/     web dashboard and setup wizard
```

## 2. Start PocketBase

```bash
pocketbase/install_pocketbase.sh          # downloads PocketBase 0.22.10 for your OS
pocketbase/pocketbase migrate up --dir pocketbase/pb_data --migrationsDir pocketbase/pb_migrations
pocketbase/pocketbase admin create you@example.com 'a-long-password' --dir pocketbase/pb_data
pocketbase/pocketbase_safe.sh start &      # serves on 127.0.0.1:8090
```

`pocketbase_safe.sh` refuses to start a second copy and binds to localhost only. Set `FLOTILLA_PB_PORT` or `FLOTILLA_PB_BIND` to change that. The admin UI is at http://127.0.0.1:8090/_/.

## 3. Install the Python dependencies

```bash
python3 -m venv scripts/.venv
scripts/.venv/bin/pip install -r scripts/requirements.txt
```

## 4. Configure

```bash
cp scripts/flotilla.env.example scripts/flotilla.env
```

Edit `scripts/flotilla.env`. Everything is optional except what you want to use:

| Setting | Purpose |
|---|---|
| `FLOTILLA_HUMAN_NAME` | How agents address you in prompts and decision briefs |
| `FLOTILLA_INFISICAL_PROJECT_ID` | Inject secrets (Telegram token, API keys) from Infisical at run time |
| `TELEGRAM_CHAT_ID` | Your chat with the bot; the token itself stays in the vault as `TELEGRAM_TOKEN` |
| `FLOTILLA_GITHUB_REPO` | A **private** repo that mirrors the board as issues. Leave empty to disable |
| `FLOTILLA_TRACKED_REPOS` | Project repos where agent commits count as evidence of work |
| `FLEET_SYNC_URL` | Optional cloud dashboard that receives fleet snapshots |

Agents are started with built-in commands for the common CLIs. To change models, flags or folders, copy `AGENTS/CONFIG/agent_commands.example.json` to `agent_commands.json` and edit it. Set an agent to `null` to turn it off.

Check the setup:

```bash
scripts/.venv/bin/python scripts/setup_check.py
```

## 5. Run the fleet

Try one dispatcher run in the foreground first:

```bash
scripts/run_with_secrets.sh dispatcher.py
```

Create a ticket in the PocketBase admin UI (`tasks` collection: title, description, `status = todo`, `assigned_agent = clau`). The dispatcher picks it up within a minute, starts the agent, and the agent moves it to `peer_review` when done.

When it works, install the background services (macOS launchd):

```bash
scripts/install_launchd.sh                      # pocketbase + dispatcher
scripts/install_launchd.sh bridge push standup  # optional: Telegram, cloud snapshot, standups
```

On Linux, run the same commands under systemd or a process supervisor of your choice; the plist files show the exact commands.

## 6. Dashboard and setup wizard

```bash
npm install && npm start
open http://localhost:8787/setup/
```

The wizard writes your organisation name, agents and projects into `AGENTS/CONFIG/` and can be rerun at any time.

## 7. Your first Council

Create a record in `goals` with a `title`, the question in `goal`, `success_criteria`, `status = council_open` and optionally a `roster` such as `["clau","gem","codi"]`. The council coordinator runs with the dispatcher and creates Round 1 tasks. See [docs/COUNCIL.md](https://github.com/UrsushoribilisMusic/agentic-fleet-hub/blob/master/docs/COUNCIL.md).

## Troubleshooting

- **Nothing gets dispatched:** check `scripts/logs/dispatcher.log`. The dispatcher only wakes an agent when files or the board changed, or every two hours.
- **Agent marked offline:** an agent that fails repeatedly or hits its usage limit is put in a cooldown (`scripts/logs/agent_failures.json`). It comes back automatically.
- **Secrets missing:** run `infisical login` once in a terminal, then restart the service.
- **Council goal parked in `waiting_human`:** the coordinator needs success criteria, and goals marked `[TEST]` are blocked unless `COUNCIL_ALLOW_SYNTHETIC_GOALS=1`.
