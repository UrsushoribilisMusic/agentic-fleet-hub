# 🤝 Team Collaboration Rules

Welcome to the **{{ORG_NAME}} Agentic Workspace**. These rules apply to all agents in the fleet.

---

## 🛠️ GitHub & Commits

1. **Branch naming**: `feat/`, `fix/`, `docs/`, `chore/` prefixes.
2. **Commit messages**: `feat: add X`, `fix: correct Y`, `docs: update Z`.
3. **Deploy keys**: Use SSH aliases (`github-clau`, `github-codi`, `github-gem`) in `~/.ssh/config`.
4. **Push immediately** after every commit — the next agent starts from HEAD.

---

## 🏗️ Architecture & Memory

1. Every project MUST have an `ARCHITECTURE.md` and a `README.md`.
2. If you learn something new or change a pattern, update `AGENTS/CONTEXT/` immediately.
3. Lessons learned go in `AGENTS/LESSONS/ledger.json` via the fleet API (`POST /fleet/api/lessons`).

---

## 📊 Kanban & Standups

1. Record daily progress in `standups/YYYY-MM-DD.md` (or via `POST /fleet/api/standup`).
2. A ticket is only **Done** when code is pushed AND standup is updated.
3. Blocked? Add it to the `## Blockers` section — never silently skip.

---

## 🔐 Secrets & Safety

1. **NEVER** commit API keys, tokens, or `.env` files.
2. Use `vault/agent-fetch.sh` (Unix) or `vault/agent-fetch.ps1` (Windows) to load secrets.
3. Secrets in memory only — never write them to logs or markdown files.

---

## 💬 Inter-Agent Protocol (IAP)

- **Send**: `POST /fleet/api/messages` with `{from, to, subject, body, ref_ticket}`
- **Read**: `GET /fleet/api/messages`
- **Acknowledge**: `PATCH /fleet/api/messages/:id` with `{status: "read"}`
- Check the inbox at the **start** of every session.
