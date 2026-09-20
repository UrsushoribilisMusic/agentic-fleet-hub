# Worklog: FCP-6 — Generate GitHub Issues from Approved Decision Briefs

Task ID: `7tk04c5xfneppu7`
Agent: Clau
Date: 2026-09-20

## Plan

1. Read `AGENTS/CONTEXT/flotilla_council_protocol.md` — done.
2. Inspect `fleet/github_sync.py` to understand existing `create_github_issue`, `find_existing_issue_by_title`, `gh()`, `ensure_labels` patterns — done.
3. Fetch existing approved `decision_briefs` from PocketBase — found 3, all with `ticket_plan` as a JSON array of `{title, assigned_agent, estimate_hours}`.
4. Implement `fleet/council_brief_ticketer.py`:
   - Reads all `decision_briefs` with `status="approved"` (or a single brief via `--brief <id>`).
   - Hard gate: skip if `approved_by` is empty.
   - Ambiguity gate: if `ticket_plan` is null/empty or any ticket has no `title`, PATCH brief to `waiting_human` and skip.
   - Idempotency: call `find_existing_issue_by_title()` before creating; skip if already exists.
   - Creates GitHub issues with: clear title, full body (summary, recommended approach, acceptance criteria, dependencies by order, known risks), labels `flotilla-managed`, `flotilla:todo`, and `agent:<name>` if agent is known.
   - PATCHes `ticket_plan` back to the brief with `gh_issue_id` and `gh_issue_url` populated.
   - PATCHes `status` to `ticketed` once all tickets in the brief are created.
5. Test with `--dry-run` against the three existing approved briefs.
6. Run for real on one brief to confirm idempotency.
7. Commit, push, move task to `peer_review`.

## Key Decisions

- Reuse `gh()` helper pattern from `github_sync.py` rather than creating a separate subprocess wrapper.
- Write issue links back into `ticket_plan` items (not a separate field) to keep the brief self-contained.
- Dependencies expressed as "Depends on: <prior ticket title>" in the body when index > 0, since the `ticket_plan` schema has no explicit dep field.
- `--dry-run` flag for safe testing: prints all actions without touching GitHub or PocketBase.
