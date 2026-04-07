# Fleet Goals & Priorities

Consolidated from session history, MISSION_CONTROL.md, and agent lessons. This document answers: what is the fleet optimizing for, and what does it deliberately ignore?

---

## Primary Optimization Targets

1. **Autonomous, continuous task throughput.** Agents should run 24/7, pick up tickets, complete work, and hand off to peers with no human intervention for routine tasks.
2. **Shared state consistency.** Every agent session must inherit the same baseline: MISSION_CONTROL.md + PocketBase + IAP inbox. Divergence between agents is a bug.
3. **Predictable, fixed-cost operation.** The fleet runs on per-seat licenses (Claude Code, Gemini CLI, Codex) — not variable token APIs. Cost must be predictable regardless of throughput.
4. **Quality over speed on peer review.** Agents MUST NOT approve their own tasks. A peer review that misses a non-commit is a protocol failure, not a formality.
5. **Vault-first secrets.** Zero `.env` files in repos. All secrets through Infisical. Compromised credentials are a critical incident.

---

## Current Strategic Priorities (as of 2026-04-07)

- **create-flotilla v0.4.0** is live on npm. Planning for v0.5.0 in progress.
- **Documentation consolidation** (#103, #104): fill content gaps, then restructure file hierarchy.
- **Analytics & ROI tracking** for The Classical Remix YouTube channel.
- **Fleet Hub stability**: dispatcher circuit-breaker, health monitoring, UI polish.

---

## Deliberate Scope Constraints (What We Ignore)

- **Variable-cost API fleets.** We do not build on pay-per-token models for autonomous background work.
- **Perfect documentation coverage.** We document what agents need to act, not everything that exists.
- **Premature abstraction.** Helpers and utilities are created when there are three real use cases, not one hypothetical.
- **Backwards-compatibility shims.** If a function is removed, it is removed — no re-export aliases.
- **Single-machine lock-in.** All infrastructure decisions should be portable to a second machine or cloud instance.

---

## What "Done" Means

A task is only done when:
1. Code/content is committed and pushed to the repo.
2. Standup entry is updated with the ticket ID.
3. Task status in PocketBase is set to `peer_review`.
4. A different agent has reviewed and set status to `approved`.

Any task where step 1 did not happen is **not done**, regardless of what the task output comment says.
