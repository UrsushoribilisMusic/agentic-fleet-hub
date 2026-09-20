# Worklog: FCP-2 PocketBase Council Data Model

Task ID: `x7zem99utzyr90v`
Agent: Codi
Date: 2026-09-20

## Plan

1. Inspect the existing PocketBase migration convention and any schema docs.
2. Add idempotent PocketBase migrations for `goals`, `deliberations`, and `decision_briefs`.
3. Add a validation script that checks the migration files define the expected collections and fields without touching the live PocketBase database.
4. Document curl examples for creating and listing Council Protocol records.
5. Update `ARCHITECTURE.md` with the new collections and lifecycle.
6. Run validation, commit, push, and move the task to `peer_review`.

## Notes

- Do not create sample records in the live PocketBase database.
- Preserve existing task/comment/heartbeat behavior.
- Use explicit PocketBase relation fields from deliberations and decision briefs back to goals.
