# Flotilla Profile Packs — Agent Handoff Spec

*How to inspect, compare, export, and install custom fleet instruction packs.*

---

## What Is Flotilla?

Flotilla is a self-hosted, open-source framework for running a team of AI agents — Claude Code, Gemini CLI, Codex, Mistral, and local models — on a shared coordination layer. Agents share state through PocketBase (a local SQLite-backed API), exchange tasks via a Kanban protocol, post session summaries to a standup log, and alert a human operator through Telegram.

The coordination layer is defined by a set of plain-text markdown and JSON files that live in the repository alongside the project code. These files tell each agent how to behave, what projects to work on, what rules to follow, and how to hand off work to peers.

A **profile pack** is a portable, sanitized snapshot of that instruction layer. It contains no live operational data (tasks, heartbeats, comments, lessons) and no machine-specific paths or secrets. A profile pack can be copied into a new repository to give a fresh Flotilla install a pre-configured instruction set, or shared with a friend so their local Claude or Codex instance can bootstrap a fleet with your conventions already in place.

---

## The Four Layers of Fleet Instructions

Understanding which layer a file belongs to is essential for producing a correct profile pack.

### 1. Default Rules

These files are provided by the `default-engineering` profile inside the Flotilla package. They define the universal heartbeat protocol, Kanban rules, secrets policy, and inter-agent messaging conventions. Any Flotilla install that has not customized these files is using the defaults.

Key files:
- `AGENTS/RULES.md` — heartbeat phases, task lifecycle, peer review, Git conventions
- `AGENTS/KEYVAULT.md` — vault usage policy (no secrets in markdown)
- `AGENTS/CONFIG/fleet_meta.json` — roster template with placeholder values

These are the baseline. A profile pack that contains only the defaults adds no new information.

### 2. Team-Specific Rules

Additions or overrides that your team has made to the default rules. These are the most valuable things to export. Examples:

- Additional heartbeat phases (e.g., a pre-LLM checksum gate in `heartbeat_check.py`)
- Custom task status values beyond the defaults
- Project-specific Kanban conventions documented in `AGENTS/RULES.md`
- A standup format constraint (e.g., the `# Agent — Date` heading rule)
- A build-verifier obligation (e.g., run `scripts/build-tag.sh` before claiming green)

### 3. Agent-Specific Instructions

Each runtime gets its own mandate file. These files are small by design — shared coordination behavior belongs in `AGENTS/RULES.md`, not in per-agent files.

| Agent | File |
|---|---|
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| Codex / OpenAI | `AGENTS.md` |
| Mistral Vibe | `MISTRAL.md` |
| Local model (Ollama/aichat) | `GEMMA.md` |

These files declare the agent's identity key (the value substituted for `<agent>` in rules), runtime quirks, SSH alias for deploy keys, and any agent-specific scripts. Customize them for your fleet's naming conventions and tooling.

### 4. Project and Repo References

Context documents that give agents background on the project they are working on:

- `AGENTS/CONTEXT/*.md` — architecture summaries, domain knowledge, project-specific conventions
- `MISSION_CONTROL.md` — active sprint, open tickets (human-readable summary)
- `ARCHITECTURE.md` — system component map

Context documents are the most project-specific part of a profile. A profile pack for a solo developer working on a Python API looks very different from one for a team shipping an iOS app. Include your context docs only if the recipient is working on the same or similar domain.

---

## What Profile Packs Do NOT Contain

A profile pack distributes **rules and setup**, not live operational state.

The following data stays on the machine where Flotilla runs and is never part of a profile pack:

| Item | Where it lives | Why it stays local |
|---|---|---|
| Open and closed tasks | PocketBase `tasks` collection | Ticket state is per-installation; a friend's fleet has its own backlog |
| Heartbeat records | PocketBase `heartbeats` collection | These track a specific machine's agent liveness |
| Task comments and output | PocketBase `comments` collection | Audit log for a specific project run |
| Lessons ledger content | PocketBase `lessons` collection | Accumulated session memory; starts fresh on a new install |
| GitHub issue sync state | `github_sync.py` runtime state | Bound to a specific GitHub org/repo |
| Secrets and API keys | Infisical / vault | Never in profile packs |
| Machine-local paths | launchd plists, `.env` | Machine-specific; use `{{PLACEHOLDER}}` or vault injection |

**PocketBase is always the local source of truth for execution state.** A profile pack cannot replicate, restore, or transfer that state to another machine. Two installs running the same profile pack are still operationally independent.

---

## Inspecting Your Current Instructions

Run the following from your fleet repository root to see what each instruction layer contains:

```bash
# Shared fleet rules
cat AGENTS/RULES.md

# Agent mandate files
cat CLAUDE.md
cat GEMINI.md
cat AGENTS.md
cat MISTRAL.md
cat GEMMA.md      # local model slot, if used

# Fleet roster and project configuration
cat AGENTS/CONFIG/fleet_meta.json

# Project context documents
ls AGENTS/CONTEXT/
cat AGENTS/CONTEXT/<filename>.md

# Root coordination docs
cat MISSION_CONTROL.md
cat ARCHITECTURE.md
```

To see all instruction files in one pass:

```bash
find . \
  -not -path './.git/*' \
  -not -path './node_modules/*' \
  -not -path './__pycache__/*' \
  \( -name "*.md" -o -name "fleet_meta.json" \) \
  | sort
```

---

## Comparing Against the Default Profile

The default profile ships at `profiles/default-engineering/` inside the Flotilla package. Use `diff` to see what your installation has added or changed:

```bash
# If you scaffolded with create-flotilla and have the package locally:
PROFILE=path/to/flotilla-package/profiles/default-engineering

diff -r --brief \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  "$PROFILE" \
  /path/to/your-fleet-repo/ \
  2>/dev/null

# For a side-by-side view of a specific file:
diff -y "$PROFILE/AGENTS/RULES.md" /path/to/your-fleet-repo/AGENTS/RULES.md
```

Items that appear only in your repo (not in the profile) are your team-specific additions. Items where the content differs are your customizations. Files that match the default exactly can be omitted from a custom pack — a recipient will already have them after running `npx create-flotilla`.

If the Flotilla package is not available locally, install it temporarily to get the reference:

```bash
npx create-flotilla /tmp/flotilla-ref --skip-git
PROFILE=/tmp/flotilla-ref/profiles/default-engineering
```

---

## Exporting a Custom Profile Pack

A profile pack is a directory you can zip and share, or commit to a public repository. Follow these steps:

### Step 1 — Create an export directory

```bash
mkdir -p ~/my-fleet-profile
```

### Step 2 — Copy the instruction files

Copy only files that belong to the instruction layer. Skip PocketBase data, secrets, logs, and machine-specific paths.

```bash
REPO=/path/to/your-fleet-repo
DEST=~/my-fleet-profile

# Shared and agent-specific rules
cp "$REPO/AGENTS/RULES.md"          "$DEST/AGENTS/RULES.md"
cp "$REPO/AGENTS/KEYVAULT.md"       "$DEST/AGENTS/KEYVAULT.md"
cp "$REPO/CLAUDE.md"                "$DEST/CLAUDE.md"
cp "$REPO/GEMINI.md"                "$DEST/GEMINI.md"
cp "$REPO/AGENTS.md"                "$DEST/AGENTS.md"
cp "$REPO/MISTRAL.md"               "$DEST/MISTRAL.md"
cp "$REPO/GEMMA.md"                 "$DEST/GEMMA.md"   # if you use a local model

# Configuration (sanitize first — see Step 3)
mkdir -p "$DEST/AGENTS/CONFIG"
cp "$REPO/AGENTS/CONFIG/fleet_meta.json" "$DEST/AGENTS/CONFIG/fleet_meta.json"

# Project context (include only if relevant to the recipient)
mkdir -p "$DEST/AGENTS/CONTEXT"
cp "$REPO/AGENTS/CONTEXT/your-relevant-doc.md" "$DEST/AGENTS/CONTEXT/"

# Root docs
cp "$REPO/MISSION_CONTROL.md" "$DEST/MISSION_CONTROL.md"
cp "$REPO/ARCHITECTURE.md"    "$DEST/ARCHITECTURE.md"

# Starter inbox and lessons (always empty/minimal in a profile pack)
mkdir -p "$DEST/AGENTS/MESSAGES" "$DEST/AGENTS/LESSONS"
echo '[]' > "$DEST/AGENTS/MESSAGES/inbox.json"
echo '[]' > "$DEST/AGENTS/LESSONS/ledger.json"
```

### Step 3 — Sanitize private details

Before sharing, replace or remove:

- Absolute machine paths (`/Users/yourname/...`) — replace with `{{PROJECT_PATH}}` or relative paths
- GitHub org names and repo URLs — replace with `{{PROJECT_REPO_URL}}`
- Telegram chat IDs — remove entirely
- Agent SSH key aliases (e.g., `github-clau`) — replace with a generic note
- Any customer or project names that should not be public

In `fleet_meta.json`, check for `repo_path` values and `memoryLink` URLs pointing to private repos. Replace with `{{PLACEHOLDER}}` values.

Quick check for private paths:

```bash
grep -r "/Users/" ~/my-fleet-profile/
grep -r "github.com/YourOrg/" ~/my-fleet-profile/
```

### Step 4 — Add a README to the pack

Document what the pack contains, what placeholders need replacing, and what the intended use case is. See the `default-engineering/README.md` for the format.

### Step 5 — Package it

```bash
cd ~/my-fleet-profile
zip -r ../my-fleet-profile.zip .
```

Or commit it to a public repo under `profiles/my-team-name/`.

---

## Installing a Profile Pack into a Flotilla Install

For a new install, pass the profile directly to `create-flotilla`:

```bash
npx create-flotilla my-fleet --profile-dir ~/my-fleet-profile
npx create-flotilla my-fleet --profile-zip ~/my-fleet-profile.zip
```

If no profile flag is provided, `create-flotilla` uses the built-in `profiles/default-engineering/` pack. Profile overlays are constrained to the instruction/config layer: root agent mandate files, `MISSION_CONTROL.md`, `ARCHITECTURE.md`, `AGENTS/RULES.md`, `AGENTS/KEYVAULT.md`, `AGENTS/CONFIG/*.json`, `AGENTS/CONTEXT/*.md`, starter inbox/lessons files, standup starters, and `.gitignore`. Other files in the pack are skipped and counted in the installer output.

For an existing repo, use a manual merge only after reviewing the diff:

```bash
cd my-fleet
unzip ../my-fleet-profile.zip -d ./profile-import
diff -r ./profile-import .
cp -r ./profile-import/* .
rm -r ./profile-import
```

Then replace all remaining `{{PLACEHOLDER}}` values:

```bash
# Find all placeholders
grep -r "{{" . --include="*.md" --include="*.json" | grep -v node_modules

# Replace them (example using sed)
sed -i '' 's/{{ORG_NAME}}/MyCompany/g' MISSION_CONTROL.md AGENTS/CONFIG/fleet_meta.json
sed -i '' 's/{{PROJECT_NAME}}/my-api/g' MISSION_CONTROL.md
sed -i '' 's|{{PROJECT_PATH}}|/Users/you/projects/my-api|g' AGENTS/CONFIG/fleet_meta.json
```

Finish with the Flotilla doctor to verify the setup:

```bash
npm run doctor
```

If you installed a profile into a repo that already has Flotilla running, restart the dispatcher after updating the instruction files so agents pick up the new rules:

```bash
launchctl kickstart -k gui/$(id -u)/fleet.dispatcher
```

---

## Prompt Template — Ask Your Local Agent to Generate a Profile Pack

Paste the following prompt into Claude Code, Codex, or any local AI agent. The agent will inspect your current instruction files, diff them against the Flotilla default profile, and produce a sanitized profile pack.

---

```
You are helping me export a custom Flotilla profile pack from my current fleet repository.

My fleet repository is at: <PATH_TO_YOUR_FLEET_REPO>
The Flotilla default profile is at: <PATH_TO_FLOTILLA_PACKAGE>/profiles/default-engineering/

## Step 1 — Read the current instruction files

Read every file in the instruction layer:
- AGENTS/RULES.md
- CLAUDE.md, GEMINI.md, AGENTS.md, MISTRAL.md, GEMMA.md (whichever exist)
- AGENTS/CONFIG/fleet_meta.json
- AGENTS/CONTEXT/*.md (all context docs)
- MISSION_CONTROL.md
- ARCHITECTURE.md

## Step 2 — Compare against the default profile

Diff each file above against its counterpart in the default-engineering profile directory.
Identify:
1. Files I have that the default does not (new additions).
2. Files where my version differs from the default (customizations).
3. Files that are identical to the default (these can be omitted — a recipient already has them).

## Step 3 — Sanitize

In each file to be exported, replace or remove:
- Absolute machine paths (/Users/...) → use {{PROJECT_PATH}} placeholder
- Private GitHub org/repo URLs → use {{PROJECT_REPO_URL}} placeholder
- Telegram chat IDs → remove
- SSH key aliases (github-clau, etc.) → replace with a generic note
- Any customer or project names I flag as private → use {{PLACEHOLDER}}

## Step 4 — Write the profile pack

Create a directory called `profile-export/` in my current working directory.
Write only the customized or new files into that directory, preserving the same path structure.
Write an empty `AGENTS/MESSAGES/inbox.json` (value: []) and an empty `AGENTS/LESSONS/ledger.json` (value: []).
Write a `profile-export/README.md` that lists every included file, explains what each one customizes relative to the default, and lists all {{PLACEHOLDER}} values the recipient must fill in.

## Step 5 — Report

After writing all files, output:
1. A list of files written and whether each was new or a customization.
2. A list of files skipped because they matched the default exactly.
3. Any placeholders you were unsure about and left as TODO comments.

## Constraints

- Do NOT include PocketBase data (tasks, heartbeats, comments, lessons content).
- Do NOT include machine-local paths without replacing them.
- Do NOT include secrets, tokens, or .env files.
- Do NOT include launchd plists unless I explicitly ask.
- Profile packs distribute rules and setup, not live operational state.
```

---

## FAQ

**Can a profile pack transfer my open tasks to a friend's fleet?**
No. Tasks live in PocketBase, which is a local database. Profile packs contain only the instruction layer (markdown files and JSON config). Your friend's fleet will start with an empty backlog.

**Can two installs using the same profile pack share a PocketBase?**
Only if they are both on the same machine or if PocketBase is hosted on a shared server accessible to both. By default, each Flotilla install runs its own local PocketBase on port 8090. Profile packs do not change this.

**Should I version-control my profile pack?**
Yes, committing it to a repo (or as a directory under `profiles/` in a fork of agentic-fleet-hub) makes it versionable and discoverable. If you publish it, make sure the sanitization step above removed all private information.

**What happens if my profile pack conflicts with files already in the target repo?**
The install step above overwrites the target files. Back up the target repo before merging, or use `diff` to review conflicts first.

**Does a profile pack include the scripts (dispatcher.py, telegram_bridge.py, etc.)?**
No. Fleet scripts are part of the Flotilla package itself and are installed by `create-flotilla`. A profile pack is the instruction layer only — the markdown and JSON files that agents read to understand their mandate. If you have customized the scripts, document the customizations in `ARCHITECTURE.md` or `AGENTS/CONTEXT/` and ship the modified scripts separately.
