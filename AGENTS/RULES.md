# Team Collaboration Rules (The Shared Memory System)

Welcome to the **Ursushoribilis Agentic Workspace**. These rules are followed by **Clau**, **Gem**, **Codi**, and **Misty**.

Each agent's runtime-specific file (`CLAUDE.md` / `GEMINI.md` / `AGENTS.md` / `MISTRAL.md`) declares its own identity, the value to substitute for `<agent>` in commands below, and any agent-specific quirks. The Heartbeat Protocol and rules in this file are universal.

---

## Heartbeat Protocol — every session, no exceptions

### Phase 1 — Orient
1. `git pull origin master` — get the latest state from the team.
2. `python3 fleet/heartbeat_check.py --agent <agent>`
   - **Exit 1**: nothing relevant changed — POST idle heartbeat and stop. Do NOT read further files. Do NOT commit.
   - **Exit 0**: continue with the steps below.
3. `python3 fleet/active_context.py` — prints ALL active project blocks. Note each block (Mission Control, inbox, and lessons paths).
4. For EACH active project block:
   - If it is a non-hub project, `cd` to its `repo_path` and `git pull origin master`.
   - Read the **Mission Control** at the path from that block.
   - Note ALL open tickets assigned to you across all active projects.
5. Read `AGENTS/RULES.md` (this file).
6. Read the inbox at the path from the first block (always hub inbox). ALL unread messages before anything else — they may change your priorities entirely.
7. POST `http://localhost:8090/api/collections/heartbeats/records` `{"agent": "<agent>", "status": "working"}`.

### Phase 2 — Peer Review First
1. GET `http://localhost:8090/api/collections/tasks/records?filter=status="peer_review"`.
2. For each task NOT assigned to you: review the code (see **Code Review Protocol** below), then post a feedback comment (`type: "feedback"`) or approval (`type: "approval"`), and set status to `approved`.
3. Do NOT self-approve — see Rule #7 under Kanban & Reporting. A different agent must approve your own work.

#### Code Review Protocol
The PrivateCore iOS project does **not** use GitHub Pull Requests. All work is committed directly to `main`. To review a task:

1. **Find the commit** — search git log by ticket number:
   ```
   git -C /Users/miguelrodriguez/projects/private-core/PrivateCore log --oneline --all | grep PC-XXX
   ```
2. **Inspect the diff**:
   ```
   git -C /Users/miguelrodriguez/projects/private-core/PrivateCore show <hash>
   ```
3. **Verify it compiled** — check for a `build-green-*` tag on that commit, or run the build verifier yourself:
   ```
   cd /Users/miguelrodriguez/projects/private-core/PrivateCore && ./scripts/build-tag.sh
   ```
4. **Check for a real commit** — if `git log` shows no commit for the ticket, the task has NOT been implemented. Do NOT approve it. Reset status to `todo` and post a `feedback` comment explaining that no code was found.
5. **Post your review** to `/api/collections/comments/records`:
   ```json
   {"task_id": "<pb-id>", "agent": "<agent>", "type": "approval", "content": "Reviewed commit <hash>. <summary of what you verified>."}
   ```
   Always include the commit hash in your approval comment so the review is traceable.

### Phase 3 — Own Tasks
1. GET tasks assigned to you with status `todo`. Pick the first, set status `in_progress`. **Do NOT create a new task if one already exists.** Only pick up existing todo tasks.
2. Do the work. Follow the Task Branch Protocol (Rule #6 under Kanban & Reporting).
3. Before claiming success, run any project build-verifier (e.g. `scripts/build-tag.sh` in PrivateCore). Only claim "BUILD SUCCEEDED" if it exits 0 — see Rule #6 under GitHub & Commits.
4. POST output to `/api/collections/comments/records` `{"task_id": "...", "agent": "<agent>", "content": "...", "type": "output"}`.
5. Set task status to `peer_review`.

### Phase 4 — Blockers
- If blocked: POST comment `type: "question"`, mention `"@miguel"` or `"@<peer-agent>"`.
- Set task status to `waiting_human`.

### Phase 5 — Lessons
- If the session produced reusable insight: POST `/api/collections/lessons/records` `{"title": "...", "content": "...", "category": "...", "confidence": "medium", "status": "pending_review"}`.

### Phase 6 — Sign Off
- POST heartbeat `{"agent": "<agent>", "status": "idle"}`.
- Only if you did actual work this session: write a summary to `~/fleet/<agent>/PROGRESS.md`.
- Only commit if there are real changes: run `git status --short` first. If output is empty, do NOT commit. If there are staged changes, commit with a descriptive message (not "session summary") and push.

---

## GitHub & Commits

1.  **Branching Strategy**: Use clear, feature-based branches.
2.  **Commit Messages**: Standardize on prefixing (e.g., `feat:`, `fix:`, `docs:`).
3.  **Deploy Keys**: For SSH access, use the `github-clau`, `github-codi`, or `github-gem` aliases in your `~/.ssh/config`.
4.  **Action**: Every commit must be pushed immediately to ensure the next agent is up to date.
5.  **Server = repo**: If you deploy a file directly to a production server (e.g. via SSH or `scp`), you MUST commit that same file to the repo in the same session. Never leave server-only changes uncomitted. The repo is the source of truth — if it is not in git, it does not exist.
6.  **Verify before claiming green**: For any project that ships a build-verifier script (e.g. `scripts/build-tag.sh` in PrivateCore), you MUST run it before pushing and only claim "BUILD SUCCEEDED" in commit messages, comments, or task output if the verifier exits 0. Never paste a fabricated success line. Precedent: PC-057 commit `697a0c0` claimed `Build: BUILD SUCCEEDED` while shipping references to undefined types (`NewPeopleGroupSheet`, `PeopleGroupCard`), forcing the next two agents to clean up. If the verifier fails, fix it or push the broken state with `BUILD FAILED` so the next agent sees the real state — do not lie up the chain.

---

## Architecture & Memory

1.  **Project Root**: Every project MUST have an `ARCHITECTURE.md` file describing its core components and data flow.
2.  **README**: Every project MUST have a developer-friendly `README.md`.
3.  **Memory Updates**: If you learn something new or change an architectural pattern, update the corresponding file in `AGENTS/CONTEXT/` immediately.

---

## Kanban & Reporting

1.  **Standups**: All daily progress is reported in `standups/`. Every entry heading MUST identify the agent — use the format `# Agent — Date (optional time UTC)`. Examples: `# Clau — 2026-04-06`, `# Codi — 2026-04-06 (14:32 UTC)`. Entries without an agent name in the heading are invalid and will be unattributable in the Fleet Hub dashboard. Do NOT use generic headings like `# Session (timestamp)`.
    **index.json rule**: After writing or updating any standup `.md` file, you MUST update `standups/index.json` to include an entry for that date. The entry format is `{"date": "YYYY-MM-DD", "summary": "one-line summary", "file": "YYYY-MM-DD.md"}`. Entries are sorted newest-first. NEVER use `git stash` on `standups/index.json` — merge conflicts in this file corrupt the JSON and break the Fleet Hub standup display. If you detect conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in `index.json`, resolve them immediately before committing.
2.  **Kanban Flow**: Ticket-based system tracked in `MISSION_CONTROL.md` and PocketBase.
    *   **GitHub-First**: To create a new task, you MUST **open a GitHub Issue**. The Dispatcher will automatically import it into PocketBase and update `MISSION_CONTROL.md`. 
    *   **In Progress**: Documented in the active session's standup.
    *   **Blocked**: Explicitly listed in the Blockers section of the standup.
3.  **Finalization**: A task is only "Done" when the code is pushed AND the standup is updated.
4.  **Ticket Authority**: The Ticket Status table in `MISSION_CONTROL.md` is the primary human-readable source of truth. However, agents should use the PocketBase `tasks` collection for precise execution state. If a discrepancy exists, PocketBase is authoritative for automation, while `MISSION_CONTROL.md` is authoritative for high-level project goals.
5.  **No Manual MC Edits**: Do NOT manually edit the `Ticket Status` section of `MISSION_CONTROL.md`. This section is auto-managed by the Dispatcher. If you need to add a ticket, use GitHub. If you need to change a status, update the PocketBase task or post a comment.
6.  **Task Branch Protocol**: When you pick up a task, immediately create a branch named `task/{pb-task-id}` (e.g. `task/abc123xyz`) and push it. Before writing any code, commit a `WORKLOG.md` to that branch describing your plan: what you will do, in what order, and any key decisions. Commit incrementally as you work — each meaningful step gets its own commit. This ensures that if your session ends mid-task (context limit, quota, etc.), the next agent can check out the branch, read `WORKLOG.md` and the git log, and resume rather than starting from scratch. If you are resuming a task that already has a branch, check it out and continue from the last commit.
7.  **No Self-Approval**: An agent MUST NOT approve its own task. When you complete a task, move it to `peer_review` status and stop. A *different* agent must read the output, verify the work was actually done, and post the approval comment. If no peer is available in the same session, leave it in `peer_review` — it will be picked up at the next heartbeat. Marking your own work `approved` is a protocol violation regardless of how confident you are in the output.
8.  **Branch Hygiene** (automated by wrappers, documented here for awareness): The `task/<pb-id>` branches from rule 6 above are scratch checkpoints, not the canonical history — final work commits to `main`/`master`. After a ticket is `approved`, the corresponding `task/<pb-id>` branch becomes garbage. The shared script `~/fleet/cleanup_task_branches.sh` runs at the end of every Codi/Clau/Gem heartbeat and deletes any `task/<id>` branch (local + origin) whose PB ticket is `approved` (or whose ticket no longer exists). It skips branches with status `todo`/`in_progress`/`peer_review` so you can safely return to in-flight work. **Misty: you have no shell wrapper — run `bash ~/fleet/cleanup_task_branches.sh --repo /Users/miguelrodriguez/projects/agentic-fleet-hub` once at the end of each session.** Run with `--dry-run` first if you want to see what it would delete.

---

## Data Integrity

1. **No fake data in real PocketBase**: When generating demo or example content (for `/demo/`, showcases, or testing), write it to static files under `opt/salesman-api/demo/` or to the hardcoded mock blocks in `server.mjs`. Never create fake tasks, heartbeats, or any records in the real PocketBase instance. The real PB is the live operational database — polluting it with hallucinated content breaks the kanban, the Fleet Hub dashboard, and audit logs.
2. **Demo data ownership**: The demo endpoints in `server.mjs` already have hardcoded mock blocks that bypass PocketBase entirely for `/demo/` requests. All demo data changes go there or in the static JSON files — not in PB.

---

## Secrets & Safety

1.  **Credential Protection**: Never commit secrets or API keys.
2.  **Vault Access**: Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows) to fetch secrets at runtime.
3.  **Communication**: Do not pass sensitive info in Markdown files.

---

## Inter-Agent Protocol (IAP)

- **Inbox**: Read `AGENTS/MESSAGES/inbox.json` at the start of every session. Messages from teammates may change your priorities.
- **Send**: Add a message object to `AGENTS/MESSAGES/inbox.json` and commit it.
- **Acknowledge**: Mark your messages as `"status": "read"` after acting on them and commit.
