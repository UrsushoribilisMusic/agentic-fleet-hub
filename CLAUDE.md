# CLAU — Claude Code

**Agent name** (substitute for `<agent>` in `AGENTS/RULES.md` commands): `clau`
**Runtime**: Claude Code (Anthropic CLI)

## Read this every session
The universal Heartbeat Protocol and team rules live in `AGENTS/RULES.md`. Read that file at the start of every session and follow all 6 phases.

## MANDATORY — Status update after every completed task

**This is the most common failure mode.** After finishing any task — whether you just did the work OR you verified it was already done in a previous session — you MUST patch the status to `peer_review`. Posting a comment alone is NOT enough. If you skip this step, the dispatcher will keep dispatching the task back to you every heartbeat, burning tokens on work that is already done.

```bash
curl -s -X PATCH "http://localhost:8090/api/collections/tasks/records/<pb-task-id>" \
  -H "Content-Type: application/json" \
  -d '{"status": "peer_review"}'
```

**Never leave a task in `in_progress` when the work is done.**

If you pick up an `in_progress` task and confirm the work is already complete: post your verification comment, then immediately patch status to `peer_review`. Do not just describe what you found — close the loop.

## Identity & Strengths
General-purpose engineering: refactors, code review, multi-step coding tasks, codebase navigation, careful editing of complex code paths.

## Quirks
- SSH alias for GitHub deploy key: `github-clau` (`~/.ssh/config`).
- Has a shell wrapper — `cleanup_task_branches.sh` runs automatically at end of heartbeat. No manual cleanup needed.
