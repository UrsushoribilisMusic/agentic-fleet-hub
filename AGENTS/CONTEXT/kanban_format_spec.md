# MISSION_CONTROL Kanban Parsing Spec -- v1

This document defines the canonical format for the Ticket Status section of
MISSION_CONTROL.md and the rules for parsing it into a normalized ticket model.
Codi (#30) and Gem (#31) should treat this as the source of truth.

---

## 1. Open Ticket Table

### Column definitions

| Column | Type | Rules |
| :--- | :--- | :--- |
| Ticket | string | Always `**#N**` (bold, hash prefix, integer). Parser extracts N as ticket ID. |
| Description | string | Free text. Human-readable only -- do not parse. |
| Owner | string | Single agent name: `Clau`, `Gem`, `Codi`, `Misty`, or `Unassigned`. |
| Status | enum | One of: `planned`, `in_work`, `merged`. See section 2. |
| Notes | string | Free text. Human-readable only -- do not parse for status. |

### Rules
- Every row in the `### OPEN` table is a live ticket.
- Rows outside the `### OPEN` table are never open tickets.
- The table header row and separator row are skipped by the parser.
- A ticket not in the table does not exist -- no exceptions (lessons learned lesson: stale-examples-in-docs).

---

## 2. Status Values

| Status | Meaning | When to use |
| :--- | :--- | :--- |
| `planned` | Ticket is queued, no active work started. | Default for new tickets. |
| `in_work` | Agent has picked up the ticket and is actively working it. | Set when agent starts work. |
| `merged` | Implementation complete, pending review or integration. | Set when code is done but ticket not yet closed. |

Parser maps these directly to Kanban columns: `planned` -> Backlog, `in_work` -> In Progress, `merged` -> Review.

---

## 3. Closed Tickets

The `### CLOSED` section is a flat bullet list, not a table.

### Format per line
```
- **#N**: Short description -- Owner. Optional extra note.
```

### completed_today derivation

The parser cannot determine `completed_today` from MISSION_CONTROL.md alone.
Use the following cross-reference logic:

1. Parse today's standup file (`standups/YYYY-MM-DD.md` where date = today).
2. Look for lines matching: `Ticket #N`, `#N (`, `Closed #N`, or `**#N**` within a Done/Closed section.
3. Any ticket ID found in both CLOSED and today's standup Done section = `completed_today`.

If the standup is unavailable, all CLOSED tickets are labelled `completed` (not `completed_today`).

---

## 4. Full Normalized Ticket Model

Each parsed ticket should produce this structure:

```json
{
  "id": 30,
  "label": "#30",
  "description": "Flotilla Kanban parser + normalized ticket model",
  "owner": "Codi",
  "status": "in_work",
  "notes": "Parse MISSION_CONTROL.md + today standup into planned/in_work/merged/completed_today",
  "completed_today": false
}
```

For closed tickets:

```json
{
  "id": 22,
  "label": "#22",
  "description": "npx create-flotilla installer",
  "owner": "Codi",
  "status": "completed",
  "notes": "Published to npm as create-flotilla@0.1.0.",
  "completed_today": true
}
```

---

## 5. Date Header

The section header `## Ticket Status (as of YYYY-MM-DD)` provides the canonical
last-updated date for the board. The parser should surface this as `board_date`.

---

## 6. Parsing Failure Rules

- If the `### OPEN` table is missing or malformed: return empty `open` array, do not crash.
- If a Status value is not one of the three valid enums: treat as `planned` and log a warning.
- If Owner is missing or blank: set to `Unassigned`.
- Never infer ticket data from sections other than `### OPEN` and `### CLOSED`.

---

## 7. Format Maintenance Rules (for all agents)

- When picking up a ticket: change its Status from `planned` to `in_work`. Commit immediately.
- When implementation is done but not yet closed: change to `merged`. Commit.
- When closing: move the row from OPEN to a CLOSED bullet. Use format: `- **#N**: Description -- Owner. Notes.`
- Never leave a ticket in `planned` status if you are actively working on it.
- The Owner column is a single agent name -- no comma-separated lists.
