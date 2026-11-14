# Team Collaboration Rules

These rules are shared by every agent in the workspace. Runtime-specific files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `MISTRAL.md`, `GEMMA.md`) declare the agent identity and any local quirks. This file owns the universal protocol.

---

## Heartbeat Protocol - Every Session

### Phase 1 - Orient

1. `git pull origin {{DEFAULT_BRANCH}}` to get the latest team state.
2. `python3 fleet/heartbeat_check.py --agent <agent>` if this install includes the heartbeat scripts.
   - Exit 1: nothing relevant changed. POST an idle heartbeat if available and stop. Do NOT read further files. Do NOT commit.
   - Exit 0: continue.
3. `python3 fleet/active_context.py` if available. Note each active project block, mission-control path, inbox path, and lessons path.
4. For each active non-hub project, pull its repository and read its Mission Control.
5. Read this file.
6. Read `AGENTS/MESSAGES/inbox.json`. ALL unread messages before anything else — they may change priorities entirely.
7. POST `{{FLEET_API_URL}}/api/collections/heartbeats/records` `{"agent": "<agent>", "status": "working"}` if the fleet API is available.

### Phase 2 - Peer Review First

1. GET `{{FLEET_API_URL}}/api/collections/tasks/records?filter=status="peer_review"` to find tasks awaiting review.
2. For each task NOT assigned to you: review the code (see **Code Review Protocol** below), then post a feedback comment (`type: "feedback"`) or approval (`type: "approval"`), and set status to `approved`.
3. Do NOT self-approve. A different agent must approve your own work.

#### Code Review Protocol

To review a task:

1. **Find the commit** — search git log by ticket number:
   ```bash
   git -C {{REPO_PATH}} log --oneline --all | grep <TICKET-ID>
   ```
2. **Inspect the diff**:
   ```bash
   git -C {{REPO_PATH}} show <hash>
   ```
3. **Verify it built or passed tests** — check for a build-green tag on that commit, or run the build verifier:
   ```bash
   cd {{REPO_PATH}} && {{BUILD_VERIFIER_COMMAND}}
   ```
4. **Check for a real commit** — if `git log` shows no commit for the ticket, the task has NOT been implemented. Do NOT approve it. Reset status to `todo` and post a `feedback` comment explaining that no code was found.
5. **Post your review** to `{{FLEET_API_URL}}/api/collections/comments/records`:
   ```json
   {"task_id": "<pb-id>", "agent": "<agent>", "type": "approval", "content": "Reviewed commit <hash>. <summary of what you verified>."}
   ```
   Always include the commit hash in your approval comment so the review is traceable.

### Phase 3 - Own Tasks

1. GET tasks assigned to you with status `todo`. Pick the first, set status `in_progress`. **Do NOT create a new task if one already exists.** Only pick up existing `todo` tasks.
2. Create a branch named `task/{task-id}` (see **Task Branch Protocol** under Kanban & Reporting).
3. Before writing any code, commit a `WORKLOG.md` to that branch describing your plan.
4. Do the work in small, reviewable commits.
5. Run the relevant verifier or tests before claiming success. Only claim "BUILD SUCCEEDED" if the verifier exits 0.
6. POST output to `{{FLEET_API_URL}}/api/collections/comments/records` `{"task_id": "...", "agent": "<agent>", "content": "...", "type": "output"}`.
7. Set task status to `peer_review`.

### Phase 4 - Blockers

- If blocked: POST comment `type: "question"`, mention `"@coordinator"` or the relevant peer agent.
- Set task status to `waiting_human`.

### Phase 5 - Lessons

- If the session produced reusable insight: POST `{{FLEET_API_URL}}/api/collections/lessons/records` `{"title": "...", "content": "...", "category": "...", "confidence": "medium", "status": "pending_review"}`.

### Phase 6 - Sign Off

- POST heartbeat `{"agent": "<agent>", "status": "idle"}` to `{{FLEET_API_URL}}/api/collections/heartbeats/records`.
- Only if you did actual work this session: write a summary to `fleet/<agent>/PROGRESS.md`.
- Only commit if there are real changes: run `git status --short` first. If output is empty, do NOT commit. If there are staged changes, commit with a descriptive message and push.

---

## Git And Commits

1. Use clear feature/task branches.
2. Use descriptive commit messages such as `feat:`, `fix:`, `docs:`, or `chore:`.
3. If the installation uses per-agent deploy keys, use the configured SSH alias for each agent (e.g. `github-<agentname>`). Document these in local setup notes, not in committed files.
4. Push commits promptly so other agents can build on them.
5. Server changes must also be committed to the repository in the same session. The repo is the source of truth — if it is not in git, it does not exist.
6. **Verify before claiming green**: For any project that ships a build-verifier script, you MUST run it before pushing and only claim "BUILD SUCCEEDED" in commit messages, comments, or task output if the verifier exits 0. Never paste a fabricated success line. If the verifier fails, fix it or push with `BUILD FAILED` so the next agent sees the real state — do not lie up the chain.
7. Never revert another agent's work unless explicitly instructed.

---

## Architecture And Memory

1. Each project should have an `ARCHITECTURE.md` file describing its core components and data flow.
2. Each project should have a developer-friendly `README.md`.
3. Project memory belongs in `AGENTS/CONTEXT/`. If you learn something new or change an architectural pattern, update the corresponding context file immediately.
4. Keep reusable coordination rules here. Keep project-specific facts in context files.

---

## Kanban And Reporting

1. **Standups**: All daily progress is reported in `standups/`. Every entry heading MUST identify the agent — use the format `# Agent — Date (optional time UTC)`. Example: `# Clau — 2026-05-07` or `# Codi — 2026-05-07 (14:32 UTC)`. Entries without an agent name in the heading are invalid and will be unattributable in dashboards.
   - **index.json rule**: After writing or updating any standup `.md` file, you MUST update `standups/index.json` to include an entry for that date. Format: `{"date": "YYYY-MM-DD", "summary": "one-line summary", "file": "YYYY-MM-DD.md"}`. Entries are sorted newest-first. NEVER use `git stash` on `standups/index.json` — merge conflicts in this file corrupt the JSON and break the standup display. If you detect conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in `index.json`, resolve them immediately before committing.
2. **Ticket Authority**: The task tracker is authoritative for automation. `MISSION_CONTROL.md` is the human-readable summary. If a discrepancy exists, the task tracker is authoritative for execution state while `MISSION_CONTROL.md` is authoritative for high-level project goals.
3. **No Manual MC Edits**: Do NOT manually edit the `Ticket Status` section of `MISSION_CONTROL.md` if a dispatcher manages that section. If you need to add a ticket, use the configured issue tracker. If you need to change a status, update the task tracker directly.
4. **Finalization**: A task is only "Done" when the code is pushed AND the standup is updated.
5. **No Self-Approval**: An agent MUST NOT approve its own task. When you complete a task, move it to `peer_review` status and stop. A *different* agent must read the output, verify the work was actually done, and post the approval comment. Marking your own work `approved` is a protocol violation regardless of how confident you are in the output.
6. **Task Branch Protocol**: When you pick up a task, immediately create a branch named `task/{task-id}` (e.g. `task/abc123xyz`) and push it. Before writing any code, commit a `WORKLOG.md` to that branch describing your plan: what you will do, in what order, and any key decisions. Commit incrementally — each meaningful step gets its own commit. This ensures that if your session ends mid-task (context limit, quota, etc.), the next agent can check out the branch, read `WORKLOG.md` and the git log, and resume rather than starting from scratch. If you are resuming a task that already has a branch, check it out and continue from the last commit.
7. **Branch Hygiene**: The `task/<id>` branches from rule 6 are scratch checkpoints, not canonical history — final work lands on `{{DEFAULT_BRANCH}}`. After a ticket is `approved`, its task branch becomes garbage. The `fleet/cleanup_task_branches.sh` script, when installed, deletes any `task/<id>` branch (local + origin) whose PB ticket is `approved`. It skips branches with status `todo`/`in_progress`/`peer_review`. Run with `--dry-run` first to preview deletions.

---

## Data Integrity

1. Do not create fake tasks, heartbeats, comments, or production records in the live task database.
2. Demo data must live in demo fixtures or mock endpoints, not in production collections.
3. Keep generated examples clearly labelled as examples.

---

## Secrets And Safety

1. Never commit secrets, tokens, API keys, or `.env` files.
2. Fetch secrets from the configured vault at runtime. See `AGENTS/KEYVAULT.md`.
3. Do not pass sensitive information in Markdown files or task comments.

---

## Inter-Agent Protocol

- Inbox: read `AGENTS/MESSAGES/inbox.json` at session start.
- Send: add a message object to the inbox and commit it, or use the configured message API.
- Acknowledge: mark messages as `"status": "read"` after acting on them and commit.
