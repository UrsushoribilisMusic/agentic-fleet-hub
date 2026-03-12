# CRM POC — Multi-Agent Project Context

## Overview
A proof-of-concept CRM (Customer Relationship Manager) built to demonstrate a **multi-agent AI coding workflow**, where Claude and Gemini operate as parallel coding agents managed by a human "Switchboard Manager." The project is as much about showcasing agentic AI collaboration as it is about the CRM itself.

## Status
- **v1.0.0** — Shipped Mar 2, 2026: App shell, Kanban, multi-user, audit trail
- **v1.1.0** — Shipped: Google Calendar integration + interactive Calendar tab
- **Phase 3** — Planned: Sales Analytics, Automated Email Follow-ups, CLV calculation

## Links
| Resource | URL |
|----------|-----|
| GitHub repo | https://github.com/UrsushoribilisMusic/crm-poc |
| Showcase page | https://ursushoribilismusic.github.io/crm-poc/ |
| Kanban board | https://github.com/users/UrsushoribilisMusic/projects/2 |
| Local path | `C:\Users\migue\customer-mgmt\` |

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite via SQLAlchemy ORM
- **Auth**: Simple user model (no JWT yet — demo scope)
- **Google OAuth**: Token stored per user in `google_token` column (JSON blob)

### Frontend
- **Framework**: React + Vite
- **Styling**: CSS modules / component styles
- **Location**: `frontend/` directory

### Infrastructure
- GitHub Actions for CI
- `Makefile` for common dev commands
- `init_demo_user.py` to seed demo data
- DB file: `data/crm.db` (must create `data/` dir on fresh clone)

---

## Data Model

### Users
```
id, full_name, email, role (Admin/User), google_token, created_at
```

### Customers
```
id, first_name, last_name, email, phone, company, location,
status (active/inactive/lead), notes, created_at, updated_at
→ has many: Tags (M2M), Tasks, Activities, Opportunities
```

### Tags
```
id, name
→ M2M with Customers via customer_tags junction table
```

### Tasks
```
id, customer_id, assigned_to_id, description, due_date,
category (Call/Meeting/Follow up), status (To Do/In Progress/Closed),
completed, created_at
```

### Activities
```
id, customer_id, user_id, type (Call/Note/Meeting),
summary, details, created_at
```

### Opportunities
```
id, customer_id, name, value, stage (Lead/...),
expected_close_date, created_at
```

---

## API Routers
| Router | File | Endpoints |
|--------|------|-----------|
| Customers | `routers/customers.py` | CRUD + tag management |
| Tasks | `routers/tasks.py` | CRUD + `GET /tasks/calendar?year=&month=` |
| Activities | `routers/activities.py` | CRUD |
| Opportunities | `routers/opportunities.py` | CRUD |
| Users | `routers/users.py` | CRUD |
| Google Calendar | `routers/google_calendar.py` | OAuth + sync |

---

## Multi-Agent Workflow

### The Agents
- **Claude (Sonnet)** — API precision, GitHub operations, feature branches, PR creation, Kanban management
- **Gemini** — Synthesis, documentation, architecture updates, frontend work
- **Switchboard Manager (human)** — Assigns tickets, reviews PRs, merges to master, decides sprint priorities

### Agent Memory Files
Located in `AGENTS/` directory:
- `PROJECT_GOAL.md` — Current sprint goals and milestone status (source of truth)
- `CLAUDE_MEMORY.md` — Claude's session notes and handover context
- `GEMINI_MEMORY.md` — Gemini's session notes and handover context
- `CLAUDE_INSTRUCTIONS.md` — Claude's standing operating procedures
- `CONVENTIONS.md` — Shared coding conventions for both agents

### Workflow Rules (Claude)
- Always branch from master: `git checkout -b feature/ISSUE-NUMBER-description`
- Atomic commits, verb-first: Add / Fix / Refactor / Update
- Always append `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` to commits
- Move ticket to **In Progress** before starting, **Review** after PR
- Never self-merge, never force-push, never commit directly to master
- Tasks scoped to ≤ 30 minutes — split if larger

---

## Features Implemented

### v1.0.0
- Customer CRUD with tags, status, notes, location
- Task management with Kanban board (To Do / In Progress / Closed)
- Activity log (Call, Note, Meeting per customer)
- Opportunities pipeline with stage and value
- Multi-user support with role system
- Audit trail via Activities
- CSV export
- GitHub Kanban integration via GraphQL

### v1.1.0 — Calendar (Claude + Gemini)
- **`GET /tasks/calendar?year=YYYY&month=MM`** — returns tasks grouped by due date
- Interactive monthly grid calendar tab in React
- Today highlight (blue outline + blue date number)
- Task chips with status colors in each day cell
- Overflow display (`+N more`) when >3 tasks in a day
- Google Calendar backend (Gemini): OAuth flow, sync endpoint
- Google Calendar UI buttons (Claude): Link account + Sync buttons in Calendar tab

---

## Known Issues / Tech Debt
- `PATCH /customers/{id}` does not check email uniqueness against other records → 400 bug risk
- CORS is open `*` — tighten before any production use
- No test suite yet (pytest + httpx planned)
- `data/crm.db` — must create `data/` directory on fresh clone before running

---

## Phase 3 Roadmap (Planned)
1. **Sales Pipeline Analytics** — Conversion rates, deal velocity charts
2. **Automated Email Follow-ups** — Template system + SMTP integration
3. **Customer Lifetime Value (CLV)** — Calculation and display per customer

---

## Setup (Fresh Clone)
```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir data
python init_demo_user.py
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```
