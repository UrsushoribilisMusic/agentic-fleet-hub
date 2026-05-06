# MISSION_CONTROL - {{PROJECT_NAME}}

Welcome to the **{{ORG_NAME}} Agentic Workspace**. This is the primary entry point for the fleet crew. Read this first to synchronize state across all agents.

> Generated from the `default-engineering` profile. Replace every `{{PLACEHOLDER}}` before active use.

---

## Team Protocols

1. **Rules & Guidelines**: Read and follow [AGENTS/RULES.md](./AGENTS/RULES.md).
   - Commit and push changes promptly.
   - Use ticket IDs in session reporting.
   - Check the **Ticket Status** section below before starting work.
2. **Daily Standups**: Session logs live in [standups/](./standups/).
   - Update the standup before closing a work session.
3. **Core Context**: Project-level memory lives in [AGENTS/CONTEXT/](./AGENTS/CONTEXT/).
4. **Inter-Agent Messages**: Read [AGENTS/MESSAGES/inbox.json](./AGENTS/MESSAGES/inbox.json) at session start.

---

## Project Manifest

| Project | Local Path | Description | Docs / Reference |
| :--- | :--- | :--- | :--- |
| **{{PROJECT_NAME}}** | `.` | {{PROJECT_DESCRIPTION}} | [Architecture](./ARCHITECTURE.md) |
| **{{RELATED_PROJECT_NAME}}** | `../{{RELATED_PROJECT_SLUG}}/` | Optional related repo. Remove this row if unused. | [Context](./AGENTS/CONTEXT/fleet_steering_architecture.md) |

---

## Ticket Status (as of {{DATE}})

### OPEN

| Ticket | Description | Owner | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **#1** | {{FIRST_TICKET_DESCRIPTION}} | Unassigned | planned | |

### CLOSED

- **#0**: Project scaffolded -- System. Initial commit from `default-engineering`.

---

## Quick Start

```bash
# Read active context and rules
python3 fleet/active_context.py
sed -n '1,220p' AGENTS/RULES.md

# Start local services, if this project includes them
{{START_COMMAND}}
```
