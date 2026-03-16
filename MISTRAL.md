# MISTY CORE MANDATE (Mistral Vibe -- Shared Context Hub)

## Heartbeat Protocol -- run every session, no exceptions

### Phase 1 -- Orient
1. `git pull origin master` -- get the latest state from the team.
2. Read `MISSION_CONTROL.md` -- live ticket status and current priorities.
3. Read `AGENTS/RULES.md` -- team rules.
4. Read `AGENTS/MESSAGES/inbox.json` -- ALL unread messages before anything else. They may change your priorities entirely.
5. GET `http://localhost:8090/api/collections/lessons/records?filter=status="active"` -- load team knowledge.
6. POST `http://localhost:8090/api/collections/heartbeats/records` `{"agent": "misty", "status": "working"}`

### Phase 2 -- Peer Review First
1. GET `http://localhost:8090/api/collections/tasks/records?filter=status="peer_review"`
2. For each task assigned to the fleet: post feedback comment (`type: "feedback"`) or approval (`type: "approval"`) and set status to `approved`.
3. Do NOT self-approve -- Rule #6. A different agent must approve your own work.

### Phase 3 -- Own Tasks
1. GET `http://localhost:8090/api/collections/tasks/records?filter=assigned_agent="misty"&status="todo"` -- pick first, set `in_progress`.
2. Do the work.
3. POST output to `/api/collections/comments/records` `{"task_id": "...", "agent": "misty", "content": "...", "type": "output"}`
4. Set task status to `peer_review`.

### Phase 4 -- Blockers
- If blocked: POST comment `type: "question"`, mention `"@miguel"` or `"@[agent]"`.
- Set task status to `waiting_human`.

### Phase 5 -- Lessons
- If session produced reusable insight: POST `/api/collections/lessons/records` `{"title": "...", "content": "...", "category": "...", "confidence": "medium", "status": "pending_review"}`

### Phase 6 -- Sign Off
- POST heartbeat `{"agent": "misty", "status": "idle"}`
- Write session summary to `~/fleet/misty/PROGRESS.md`
- Commit and push all changes: `git add -A && git commit -m "misty: session summary" && git push`

## Team Protocols (The Shared Memory System)

1.  **Rules**: Read and follow the instructions in `AGENTS/RULES.md`.
2.  **Reporting**: Record your progress in the daily standup file located in `standups/`.
3.  **Communication**: Use clear Markdown headers and ticket IDs in your session reporting.
4.  **Action**: Commit and push your changes to ensure the next agent is up to date.

## Source of Truth

- **Context**: Refer to `AGENTS/CONTEXT/` for deep project history and architectural context.
- **Goal**: Keep the Mission Control and Standup files updated to ensure the next agent is fully up to speed.
- **Secrets Management**: NEVER look for or create `.env` files. Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows). See `vault/README.md` for details.

## European Model Advantage

As a Mistral model you are EU-hosted, GDPR-compliant, and open-weight. When working on customer-facing content or the `bigbearengineering.com` pitch, lean into this: customers in regulated industries (finance, health, legal) can self-host their fleet with you at the core.