# Team Collaboration Rules

These rules are shared by every agent in the workspace. Runtime-specific files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `MISTRAL.md`, `GEMMA.md`) declare the agent identity and any local quirks. This file owns the universal protocol.

---

## Heartbeat Protocol - Every Session

### Phase 1 - Orient

1. `git pull origin {{DEFAULT_BRANCH}}` to get the latest team state.
2. `python3 fleet/heartbeat_check.py --agent <agent>` if this install includes the heartbeat scripts.
   - Exit 1: nothing relevant changed. Post an idle heartbeat if available and stop.
   - Exit 0: continue.
3. `python3 fleet/active_context.py` if available. Note each active project block, mission-control path, inbox path, and lessons path.
4. For each active non-hub project, pull its repository and read its Mission Control.
5. Read this file.
6. Read `AGENTS/MESSAGES/inbox.json`. Unread messages may change priorities.
7. Post a working heartbeat if the local PocketBase/API service is available.

### Phase 2 - Peer Review First

1. Check tasks in `peer_review`.
2. Review tasks not assigned to you before starting new work.
3. Post either feedback or approval with traceable evidence, such as commit hashes, test commands, and files inspected.
4. Do not self-approve.

### Phase 3 - Own Tasks

1. Pick the first task assigned to you with status `todo`.
2. Set it to `in_progress`.
3. Create a branch named `task/{task-id}`.
4. Commit a `WORKLOG.md` to that branch before writing implementation files.
5. Do the work in small, reviewable commits.
6. Run the relevant verifier or tests before claiming success.
7. Post task output and set the task to `peer_review`.

### Phase 4 - Blockers

- If blocked, post a question to the task thread and mention the owner or coordinator.
- Set the task status to `waiting_human` or the local equivalent.

### Phase 5 - Lessons

- If the session produced reusable insight, record it in the lessons system.
- Use project-specific lessons for local architecture knowledge and global lessons for fleet-wide behavior.

### Phase 6 - Sign Off

- Post an idle heartbeat if available.
- Write a short progress summary if actual work was done.
- Commit only real changes. Run `git status --short` before committing.
- Push commits promptly.

---

## Git And Commits

1. Use clear feature/task branches.
2. Use descriptive commit messages such as `feat:`, `fix:`, `docs:`, or `chore:`.
3. Push commits promptly so other agents can build on them.
4. Server changes must also be committed to the repository in the same session.
5. Never claim a build or verifier succeeded unless the command exited 0.
6. Never revert another agent's work unless explicitly instructed.

---

## Architecture And Memory

1. Each project should have an `ARCHITECTURE.md` file.
2. Each project should have a developer-friendly `README.md`.
3. Project memory belongs in `AGENTS/CONTEXT/`.
4. Keep reusable coordination rules here. Keep project-specific facts in context files.

---

## Kanban And Reporting

1. Standups live in `standups/`.
2. Standup headings must identify the agent, for example `# Codi - 2026-05-05`.
3. After editing a standup file, update `standups/index.json`.
4. The task tracker is authoritative for automation; `MISSION_CONTROL.md` is the human-readable summary.
5. Do not manually edit auto-managed ticket sections unless your installation intentionally uses Markdown as the source of truth.
6. No self-approval. A different agent must approve your completed work.
7. Task branches are scratch checkpoints; final work lands on the repository's default branch according to local policy.

---

## Data Integrity

1. Do not create fake tasks, heartbeats, comments, or production records in the real task database.
2. Demo data must live in demo fixtures or mock endpoints, not in production collections.
3. Keep generated examples clearly labelled as examples.

---

## Secrets And Safety

1. Never commit secrets, tokens, API keys, or `.env` files.
2. Fetch secrets from the configured vault at runtime.
3. Do not pass sensitive information in Markdown files or task comments.

---

## Inter-Agent Protocol

- Inbox: read `AGENTS/MESSAGES/inbox.json` at session start.
- Send: add a message object to the inbox and commit it, or use the configured message API.
- Acknowledge: mark messages as read after acting on them.
