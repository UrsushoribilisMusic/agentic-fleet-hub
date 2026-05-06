# Mission Control Kanban Format

This file defines a Markdown format that agents and lightweight parsers can use when a task tracker is mirrored into `MISSION_CONTROL.md`.

## Open Tickets

Open tickets live only under `### OPEN`.

| Column | Rules |
| :--- | :--- |
| Ticket | Bold ticket key, for example `**#1**` or `**ABC-123**`. |
| Description | Human-readable task title. |
| Owner | One agent name or `Unassigned`. |
| Status | `planned`, `in_work`, or `merged`. |
| Notes | Human-readable notes. |

Rows outside `### OPEN` are not active tickets.

## Closed Tickets

Closed tickets are a flat bullet list under `### CLOSED`.

```markdown
- **#1**: Short description -- Owner. Optional note.
```

## Status Values

- `planned`: queued, no active work started.
- `in_work`: an agent has picked up the ticket.
- `merged`: implementation is complete and awaiting review or final closeout.

## Maintenance Rules

- Do not infer live work from prose outside the open table.
- Do not leave a ticket in `planned` once active work starts.
- Do not self-approve completed work.
- If PocketBase or another tracker is authoritative, treat this file as a readable mirror.
