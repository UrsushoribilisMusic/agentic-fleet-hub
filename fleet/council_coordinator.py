#!/usr/bin/env python3
"""Council Coordinator — FCP-3.

Advances goals through the two-round council lifecycle:

  council_open
    → (safeguard) missing success_criteria → waiting_human
    → create Round 1 deliberation tasks
    → wait / timeout → create Round 2 critique tasks
    → wait / timeout → create Synthesis task
    → synthesis complete → synthesis_ready

Safeguards enforced:
- Maximum two deliberation rounds; no third round.
- No execution tickets are ever created here.
- Council deliberation tasks are PocketBase-only; GitHub tickets are created
  only from approved decision briefs.
- Synthetic/test goals require an explicit allow flag before live task creation.
- Unavailable agents are filtered before any new council tasks are created.
- Per-goal task creation is capped to prevent accidental token burn.
- Goals lacking success_criteria go to waiting_human immediately.

Reuses PB_URL, post_comment, and log_task_event patterns from dispatcher.py.

Usage:
    python3 fleet/council_coordinator.py [--dry-run]

Can also be imported and called from dispatcher.py:
    from council_coordinator import run_council_cycle
    run_council_cycle()
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PB_URL = os.environ.get("PB_URL", "http://127.0.0.1:8090/api")
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FLEET_DIR = os.path.dirname(__file__)
OFFLINE_AGENTS_FILE = os.path.join(FLEET_DIR, "logs", "offline_agents.json")
AGENT_FAILURES_FILE = os.path.join(FLEET_DIR, "logs", "agent_failures.json")

# How long to wait for all agents in a round before declaring a timeout and
# moving on.  Timed-out incomplete tasks are left in their current status so
# peer-reviewers can still inspect them; the coordinator just proceeds.
R1_TIMEOUT_HOURS = float(os.environ.get("COUNCIL_R1_TIMEOUT_HOURS", "4"))
R2_TIMEOUT_HOURS = float(os.environ.get("COUNCIL_R2_TIMEOUT_HOURS", "4"))
SYNTHESIS_TIMEOUT_HOURS = float(os.environ.get("COUNCIL_SYNTHESIS_TIMEOUT_HOURS", "6"))

# Default roster when a goal has no explicit roster field. Keep this small and
# token-safe; goals can still request a broader explicit roster.
DEFAULT_ROSTER = [
    a.strip()
    for a in os.environ.get("COUNCIL_DEFAULT_ROSTER", "clau,codi").split(",")
    if a.strip()
]

# Hard cap for coordinator-created internal tasks per goal. With the default
# two-agent roster, a normal goal creates 2 R1 + 2 R2 + 1 synthesis tasks.
MAX_TASKS_PER_GOAL = int(os.environ.get("COUNCIL_MAX_TASKS_PER_GOAL", "8"))
ALLOW_SYNTHETIC_GOALS = os.environ.get("COUNCIL_ALLOW_SYNTHETIC_GOALS") == "1"

# Role assignment order — coordinator cycles through roles for each agent.
ROLE_CYCLE = ["architect", "planner", "executor", "skeptic", "researcher", "reviewer"]

# Sentinel prefix used in task titles so the coordinator can find its own tasks.
TITLE_PREFIX_R1 = "[Council R1]"
TITLE_PREFIX_R2 = "[Council R2]"
TITLE_PREFIX_SYN = "[Council Synthesis]"

# Agent to assign the synthesis task to (falls back to first in roster).
SYNTHESIS_AGENT = "clau"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [council] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PocketBase helpers (mirrors dispatcher.py patterns)
# ---------------------------------------------------------------------------

def _pb_get(path: str, params: dict | None = None) -> dict:
    try:
        r = requests.get(f"{PB_URL}{path}", params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("GET %s failed: %s", path, exc)
        return {}


def _pb_post(path: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{PB_URL}{path}", json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("POST %s failed: %s", path, exc)
        return None


def _pb_patch(path: str, data: dict) -> dict | None:
    try:
        r = requests.patch(f"{PB_URL}{path}", json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("PATCH %s failed: %s", path, exc)
        return None


def _post_comment(task_id: str, agent: str, content: str, comment_type: str = "output") -> None:
    """Mirror of dispatcher.post_comment."""
    _pb_post("/collections/comments/records", {
        "task_id": task_id,
        "agent": agent,
        "content": content,
        "type": comment_type,
    })


def _log_task_event(
    event_type: str,
    task_id: str,
    agent: str = "council_coordinator",
    from_status: str | None = None,
    to_status: str | None = None,
    meta: dict | None = None,
) -> None:
    """Mirror of dispatcher.log_task_event."""
    payload: dict[str, Any] = {
        "task_id": task_id,
        "event_type": event_type,
        "timestamp": _utcnow_str(),
        "agent": agent,
    }
    if from_status is not None:
        payload["from_status"] = from_status
    if to_status is not None:
        payload["to_status"] = to_status
    if meta is not None:
        payload["meta"] = meta
    _pb_post("/collections/task_events/records", payload)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def _utcnow_str() -> str:
    return _utcnow().strftime("%Y-%m-%d %H:%M:%S.000Z")


def _parse_utc(value: str) -> datetime:
    """Parse PocketBase timestamp strings into UTC-aware datetime."""
    if not value:
        raise ValueError("empty timestamp")
    value = value.replace("Z", "+00:00").replace(" ", "T")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # Strip microseconds and retry
        return datetime.fromisoformat(value[:19] + "+00:00")


def _hours_since(ts: str) -> float:
    try:
        dt = _parse_utc(ts)
        return (_utcnow() - dt).total_seconds() / 3600
    except Exception:
        return 0.0


def _load_json_file(path: str) -> dict:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception as exc:
        log.warning("Could not load %s: %s", path, exc)
    return {}


def _agent_unavailable_reason(agent: str) -> str:
    failures = _load_json_file(AGENT_FAILURES_FILE)
    failure = failures.get(agent, {})
    blocked_until_raw = failure.get("blocked_until")
    if blocked_until_raw:
        try:
            if _parse_utc(blocked_until_raw) > _utcnow():
                return failure.get("reason") or f"cooldown until {blocked_until_raw}"
        except Exception:
            pass

    offline = _load_json_file(OFFLINE_AGENTS_FILE)
    if agent in offline:
        details = offline.get(agent) or {}
        last_seen = details.get("last_seen")
        return f"offline: {last_seen}" if last_seen else "offline"

    return ""


# ---------------------------------------------------------------------------
# Goal helpers
# ---------------------------------------------------------------------------

def _get_council_open_goals() -> list[dict]:
    result = _pb_get("/collections/goals/records", {
        "filter": 'status = "council_open"',
        "perPage": 50,
        "sort": "created",
    })
    return result.get("items", [])


def _get_roster(goal: dict) -> list[str]:
    """Return the agent roster for this goal, falling back to default."""
    raw = goal.get("roster")
    if raw and isinstance(raw, list) and len(raw) > 0:
        return [str(a) for a in raw if a]
    if raw and isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return [str(a) for a in parsed if a]
        except ValueError:
            pass
    return list(DEFAULT_ROSTER)


def _dedupe_roster(roster: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for agent in roster:
        agent = str(agent).strip()
        if agent and agent not in seen:
            seen.add(agent)
            deduped.append(agent)
    return deduped


def _filter_available_roster(roster: list[str]) -> tuple[list[str], dict[str, str]]:
    available = []
    skipped = {}
    for agent in _dedupe_roster(roster):
        reason = _agent_unavailable_reason(agent)
        if reason:
            skipped[agent] = reason
        else:
            available.append(agent)
    return available, skipped


def _roster_from_tasks(tasks: list[dict]) -> list[str]:
    return _dedupe_roster([t.get("assigned_agent", "") for t in tasks])


def _is_synthetic_goal(goal: dict) -> bool:
    title = goal.get("title", "")
    markers = ("[TEST]", "Test Goal", "FCP-4 Test", "FCP-5 Test")
    return any(marker in title for marker in markers)


def _allows_live_synthetic_goal(state: dict) -> bool:
    return ALLOW_SYNTHETIC_GOALS or state.get("allow_live_test_tasks") is True


def _send_goal_waiting_human(goal_id: str, reason: str, meta: dict | None = None, dry_run: bool = False) -> None:
    log.warning("Goal %s → waiting_human: %s", goal_id, reason)
    if dry_run:
        return
    payload = {"reason": reason}
    if meta:
        payload.update(meta)
    _log_task_event(
        "council_waiting_human",
        goal_id,
        to_status="waiting_human",
        meta=payload,
    )
    _update_goal_status(goal_id, "waiting_human")


def _get_council_state(goal: dict) -> dict:
    raw = goal.get("council_state")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _save_council_state(goal_id: str, state: dict) -> None:
    _pb_patch(f"/collections/goals/records/{goal_id}", {"council_state": state})


def _update_goal_status(goal_id: str, status: str, from_status: str = "council_open") -> None:
    _pb_patch(f"/collections/goals/records/{goal_id}", {"status": status})
    log.info("Goal %s: %s → %s", goal_id, from_status, status)


# ---------------------------------------------------------------------------
# Task helpers
# ---------------------------------------------------------------------------

def _get_council_tasks_for_goal(goal_id: str) -> list[dict]:
    """Return all coordinator-created tasks that reference this goal."""
    result = _pb_get("/collections/tasks/records", {
        "filter": f'goal_id = "{goal_id}"',
        "perPage": 100,
        "sort": "created",
    })
    return result.get("items", [])


def _tasks_for_round(tasks: list[dict], prefix: str) -> list[dict]:
    return [t for t in tasks if t.get("title", "").startswith(prefix)]


def _is_round_complete(tasks: list[dict], timeout_hours: float, created_at: str) -> tuple[bool, bool]:
    """Return (is_complete, is_timed_out).

    is_complete: all tasks are in a terminal state (approved or peer_review).
    is_timed_out: created_at is older than timeout_hours, regardless of completion.
    """
    if not tasks:
        return False, False

    terminal = {"approved", "peer_review"}
    complete = all(t.get("status") in terminal for t in tasks)
    timed_out = _hours_since(created_at) >= timeout_hours if created_at else False
    return complete, timed_out


def _deliberations_for_goal_round(goal_id: str, round_num: int) -> list[dict]:
    result = _pb_get("/collections/deliberations/records", {
        "filter": f'goal_id = "{goal_id}" && round = {round_num}',
        "perPage": 50,
        "sort": "created",
    })
    return result.get("items", [])


# ---------------------------------------------------------------------------
# Task creation
# ---------------------------------------------------------------------------

def _role_for_agent(agent: str, roster: list[str]) -> str:
    idx = roster.index(agent) if agent in roster else 0
    return ROLE_CYCLE[idx % len(ROLE_CYCLE)]


def _create_deliberation_task(
    goal: dict,
    agent: str,
    round_num: int,
    role: str,
    dry_run: bool,
    extra_context: str = "",
) -> dict | None:
    """Create a single deliberation task for one agent."""
    goal_id = goal["id"]
    title = f"{TITLE_PREFIX_R1 if round_num == 1 else TITLE_PREFIX_R2} {agent}: {goal['title']}"

    instructions = _build_deliberation_instructions(goal, agent, round_num, role, extra_context)

    scratchpad = {"council": True, "round": round_num, "role": role}

    payload = {
        "title": title,
        "description": instructions,
        "assigned_agent": agent,
        "status": "todo",
        "goal_id": goal_id,
        "is_github_sync": False,
        "scratchpad": scratchpad,
    }

    log.info("  → %s task for %s (round %d, role %s)%s",
             "Creating" if not dry_run else "DRY-RUN would create",
             agent, round_num, role,
             " [DRY RUN]" if dry_run else "")

    if dry_run:
        return {"id": f"dry-run-{agent}-r{round_num}", **payload}

    created = _pb_post("/collections/tasks/records", payload)
    if created:
        _log_task_event(
            "council_task_created",
            created["id"],
            meta={"goal_id": goal_id, "round": round_num, "role": role, "agent": agent},
        )
    return created


def _create_synthesis_task(goal: dict, dry_run: bool, roster: list[str] | None = None) -> dict | None:
    """Create the synthesis task after both deliberation rounds complete."""
    goal_id = goal["id"]
    title = f"{TITLE_PREFIX_SYN} {goal['title']}"

    # Pull round 2 deliberations to inject into the prompt
    r2_delibs = _deliberations_for_goal_round(goal_id, 2)
    if not r2_delibs:
        # Fall back to round 1 if round 2 is empty (e.g. solo roster)
        r2_delibs = _deliberations_for_goal_round(goal_id, 1)

    delib_summary = _format_deliberation_summary(r2_delibs, "Round 2 Deliberations")

    instructions = _build_synthesis_instructions(goal, delib_summary)

    # Assign to SYNTHESIS_AGENT if available, otherwise first agent in roster
    roster = roster or _get_roster(goal)
    synthesizer = SYNTHESIS_AGENT if SYNTHESIS_AGENT in roster else roster[0]

    scratchpad = {"council": True, "round": 0, "role": "synthesizer", "synthesis": True}

    payload = {
        "title": title,
        "description": instructions,
        "assigned_agent": synthesizer,
        "status": "todo",
        "goal_id": goal_id,
        "is_github_sync": False,
        "scratchpad": scratchpad,
    }

    log.info("  → %s synthesis task for %s%s",
             "Creating" if not dry_run else "DRY-RUN would create",
             synthesizer,
             " [DRY RUN]" if dry_run else "")

    if dry_run:
        return {"id": f"dry-run-synthesis", **payload}

    created = _pb_post("/collections/tasks/records", payload)
    if created:
        _log_task_event(
            "council_synthesis_created",
            created["id"],
            meta={"goal_id": goal_id, "synthesizer": synthesizer},
        )
    return created


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_deliberation_instructions(
    goal: dict,
    agent: str,
    round_num: int,
    role: str,
    extra_context: str,
) -> str:
    goal_id = goal["id"]
    round_label = "Round 1 (Independent Proposal)" if round_num == 1 else "Round 2 (Critique & Revision)"

    header = f"""[Council {round_label}] Goal: {goal['title']}
Role assigned to you: **{role}**

---

GOAL:
{goal.get('goal', '(not set)')}

WHY NOW:
{goal.get('why_now', '(not set)')}

CONSTRAINTS:
{goal.get('constraints', '(not set)')}

SUCCESS CRITERIA:
{goal.get('success_criteria', '(not set)')}

DEADLINE: {goal.get('deadline', '(not set)')}
OUTPUT TYPE: {goal.get('output_type', '(not set)')}
"""

    if extra_context:
        header += f"\n---\n{extra_context}\n"

    instructions = f"""{header}
---

## Your Task

Write a deliberation record in PocketBase for this goal, then post a brief summary as a comment on this task.

### 1. Create the deliberation record

```sh
PB_URL="${{PB_URL:-http://127.0.0.1:8090}}"
curl -s "$PB_URL/api/collections/deliberations/records" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "goal_id": "{goal_id}",
    "agent": "{agent}",
    "round": {round_num},
    "role": "{role}",
    "recommendation": "YOUR RECOMMENDATION HERE",
    "risks": "KEY RISKS",
    "rejected_options": "ALTERNATIVES YOU CONSIDERED AND REJECTED",
    "open_questions": "QUESTIONS THAT REMAIN OPEN",
    "evidence_needed": "WHAT EVIDENCE WOULD CHANGE YOUR VIEW",
    "confidence": "high|moderate|low|speculative"
  }}'
```

### 2. Post a summary comment on this task

After creating the deliberation record, post a comment (type: output) summarising your recommendation in 2–3 sentences.

### 3. Move this task to peer_review

After the deliberation record and comment exist, mark this task as `peer_review`.

---

## Rules (non-negotiable)

- **DO NOT create execution tickets.** Deliberation only.
- **DO NOT approve other agents' work** in this session.
- Write your honest, independent view. Preserve genuine disagreement.
- Confidence tier is required.
- If you are round 2, reference specific proposals from round 1 that you agree or disagree with.
"""
    return instructions


def _build_synthesis_instructions(goal: dict, delib_summary: str) -> str:
    goal_id = goal["id"]
    return f"""[Council Synthesis] Goal: {goal['title']}

---

GOAL:
{goal.get('goal', '(not set)')}

SUCCESS CRITERIA:
{goal.get('success_criteria', '(not set)')}

---

## All Deliberations (for synthesis)

{delib_summary}

---

## Your Task

You are the synthesizer. Read all deliberations above and create a decision brief that Miguel can approve or reject.

### 1. Create the decision brief record

```sh
PB_URL="${{PB_URL:-http://127.0.0.1:8090}}"
curl -s "$PB_URL/api/collections/decision_briefs/records" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "goal_id": "{goal_id}",
    "status": "waiting_human",
    "summary": "2-3 sentence executive summary",
    "recommended_approach": "The approach the council recommends",
    "agreement": "What all agents agreed on",
    "disagreement": "What was genuinely contested — do NOT paper over this",
    "rejected_alternatives": "Approaches considered and rejected, with reasons",
    "known_risks": "Key risks",
    "open_questions_for_miguel": "Questions only Miguel can answer",
    "ticket_plan": null,
    "definition_of_done": "How we know this goal is achieved",
    "review_assignments": null,
    "created_by": "clau"
  }}'
```

### 2. Post a summary comment on this task

After creating the decision brief, post a comment with the brief summary and a link to the full record.

### 3. Move this task to peer_review

After the decision brief and comment exist, mark this task as `peer_review`.

---

## Rules (non-negotiable)

- **DO NOT create execution tickets.** Leave ticket_plan as null.
- **DO NOT approve your own synthesis.** Set status to waiting_human.
- Preserve genuine disagreement — do not merge conflicting views into false consensus.
- If success criteria were absent or the deliberations were inconclusive, note it in open_questions_for_miguel.
"""


def _format_deliberation_summary(delibs: list[dict], heading: str) -> str:
    if not delibs:
        return f"## {heading}\n\n(No deliberations found.)"

    parts = [f"## {heading}\n"]
    for d in delibs:
        parts.append(f"### {d.get('agent', '?')} — Role: {d.get('role', '?')} — Confidence: {d.get('confidence', '?')}")
        parts.append(f"**Recommendation:** {d.get('recommendation', '(empty)')}")
        parts.append(f"**Risks:** {d.get('risks', '(empty)')}")
        if d.get("rejected_options"):
            parts.append(f"**Rejected options:** {d['rejected_options']}")
        if d.get("open_questions"):
            parts.append(f"**Open questions:** {d['open_questions']}")
        if d.get("evidence_needed"):
            parts.append(f"**Evidence needed:** {d['evidence_needed']}")
        parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

def _process_goal(goal: dict, dry_run: bool) -> None:
    goal_id = goal["id"]
    title = goal.get("title", goal_id)
    log.info("Processing goal %s: %s", goal_id, title)
    state = _get_council_state(goal)
    all_tasks = _get_council_tasks_for_goal(goal_id)

    # Safeguard: goals without success criteria go to waiting_human
    if not (goal.get("success_criteria") or "").strip():
        _send_goal_waiting_human(goal_id, "missing success_criteria", dry_run=dry_run)
        return

    if _is_synthetic_goal(goal) and not _allows_live_synthetic_goal(state):
        _send_goal_waiting_human(
            goal_id,
            "synthetic_goal_requires_allow_live_test_tasks",
            meta={"title": title},
            dry_run=dry_run,
        )
        return

    if len(all_tasks) >= MAX_TASKS_PER_GOAL:
        _send_goal_waiting_human(
            goal_id,
            "council_task_cap_reached",
            meta={"task_count": len(all_tasks), "max_tasks_per_goal": MAX_TASKS_PER_GOAL},
            dry_run=dry_run,
        )
        return

    requested_roster = _get_roster(goal)
    r1_tasks = _tasks_for_round(all_tasks, TITLE_PREFIX_R1)
    r2_tasks = _tasks_for_round(all_tasks, TITLE_PREFIX_R2)
    syn_tasks = _tasks_for_round(all_tasks, TITLE_PREFIX_SYN)

    if state.get("effective_roster"):
        roster = _dedupe_roster(state["effective_roster"])
    elif r1_tasks:
        roster = _roster_from_tasks(r1_tasks)
    else:
        roster, skipped_agents = _filter_available_roster(requested_roster)
        if skipped_agents:
            state["skipped_agents"] = skipped_agents
            log.info("Goal %s: skipped unavailable agents: %s", goal_id, skipped_agents)

    if not roster:
        _send_goal_waiting_human(
            goal_id,
            "empty_or_unavailable_roster",
            meta={"requested_roster": requested_roster, "skipped_agents": state.get("skipped_agents", {})},
            dry_run=dry_run,
        )
        return

    # --- Round 1 ---
    if not r1_tasks:
        log.info("Goal %s: creating Round 1 tasks for %s", goal_id, roster)
        created = []
        for agent in roster:
            role = _role_for_agent(agent, roster)
            t = _create_deliberation_task(goal, agent, 1, role, dry_run)
            if t:
                created.append(t)

        if not dry_run and created:
            state["r1_created_at"] = _utcnow_str()
            state["effective_roster"] = roster
            _save_council_state(goal_id, state)
            _log_task_event(
                "council_round1_started",
                goal_id,
                meta={
                    "agents": roster,
                    "requested_roster": requested_roster,
                    "skipped_agents": state.get("skipped_agents", {}),
                    "task_ids": [t["id"] for t in created],
                },
            )
        return  # Wait for the next coordinator run once tasks complete

    r1_complete, r1_timed_out = _is_round_complete(
        r1_tasks, R1_TIMEOUT_HOURS, state.get("r1_created_at", "")
    )

    # --- Round 2 ---
    if not r2_tasks:
        if not (r1_complete or r1_timed_out):
            log.info(
                "Goal %s: Round 1 in-flight (%d/%d done)",
                goal_id,
                sum(1 for t in r1_tasks if t.get("status") in {"approved", "peer_review"}),
                len(r1_tasks),
            )
            return

        # Inject round 1 deliberation summaries into round 2 prompts
        r1_delibs = _deliberations_for_goal_round(goal_id, 1)
        extra = _format_deliberation_summary(r1_delibs, "Round 1 Proposals (read and critique these)")

        if r1_timed_out and not r1_complete:
            log.warning("Goal %s: Round 1 timed out; proceeding to Round 2 with partial results", goal_id)
            state.setdefault("timed_out_rounds", [])
            if 1 not in state["timed_out_rounds"]:
                state["timed_out_rounds"].append(1)

        log.info("Goal %s: creating Round 2 tasks", goal_id)
        created = []
        for agent in roster:
            role = _role_for_agent(agent, roster)
            t = _create_deliberation_task(goal, agent, 2, role, dry_run, extra_context=extra)
            if t:
                created.append(t)

        if not dry_run and created:
            state["r2_created_at"] = _utcnow_str()
            _save_council_state(goal_id, state)
            _log_task_event(
                "council_round2_started",
                goal_id,
                meta={
                    "agents": roster,
                    "task_ids": [t["id"] for t in created],
                    "r1_timed_out": r1_timed_out,
                },
            )
        return

    r2_complete, r2_timed_out = _is_round_complete(
        r2_tasks, R2_TIMEOUT_HOURS, state.get("r2_created_at", "")
    )

    # --- Synthesis ---
    if not syn_tasks:
        if not (r2_complete or r2_timed_out):
            log.info(
                "Goal %s: Round 2 in-flight (%d/%d done)",
                goal_id,
                sum(1 for t in r2_tasks if t.get("status") in {"approved", "peer_review"}),
                len(r2_tasks),
            )
            return

        if r2_timed_out and not r2_complete:
            log.warning("Goal %s: Round 2 timed out; proceeding to synthesis", goal_id)
            state.setdefault("timed_out_rounds", [])
            if 2 not in state["timed_out_rounds"]:
                state["timed_out_rounds"].append(2)

        log.info("Goal %s: creating Synthesis task", goal_id)
        syn_task = _create_synthesis_task(goal, dry_run, roster=roster)

        if not dry_run and syn_task:
            state["synthesis_created_at"] = _utcnow_str()
            _save_council_state(goal_id, state)
            _log_task_event(
                "council_synthesis_started",
                goal_id,
                meta={"task_id": syn_task["id"], "r2_timed_out": r2_timed_out},
            )
        return

    # --- Synthesis complete? ---
    syn_complete, syn_timed_out = _is_round_complete(
        syn_tasks, SYNTHESIS_TIMEOUT_HOURS, state.get("synthesis_created_at", "")
    )

    if syn_complete:
        # Check if a decision_brief was actually written for this goal
        briefs = _pb_get("/collections/decision_briefs/records", {
            "filter": f'goal_id = "{goal_id}"',
            "perPage": 1,
        }).get("items", [])

        if briefs:
            log.info("Goal %s: synthesis complete → synthesis_ready", goal_id)
            if not dry_run:
                _update_goal_status(goal_id, "synthesis_ready")
                _log_task_event(
                    "council_complete",
                    goal_id,
                    to_status="synthesis_ready",
                    meta={"brief_id": briefs[0]["id"]},
                )
        else:
            # Synthesis task marked done but no decision_brief record — needs human
            log.warning("Goal %s: synthesis done but no decision_brief found → waiting_human", goal_id)
            if not dry_run:
                _update_goal_status(goal_id, "waiting_human")
                _log_task_event(
                    "council_waiting_human",
                    goal_id,
                    to_status="waiting_human",
                    meta={"reason": "synthesis_complete_but_no_brief"},
                )
    elif syn_timed_out:
        log.warning("Goal %s: synthesis timed out → waiting_human", goal_id)
        if not dry_run:
            _update_goal_status(goal_id, "waiting_human")
            _log_task_event(
                "council_waiting_human",
                goal_id,
                to_status="waiting_human",
                meta={"reason": "synthesis_timeout"},
            )
    else:
        log.info("Goal %s: synthesis in-flight", goal_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_council_cycle(dry_run: bool = False) -> None:
    """Process all council_open goals. Called by dispatcher or standalone."""
    goals = _get_council_open_goals()
    log.info("Council cycle: %d council_open goal(s) found", len(goals))
    for goal in goals:
        try:
            _process_goal(goal, dry_run=dry_run)
        except Exception as exc:
            log.error("Error processing goal %s: %s", goal.get("id"), exc, exc_info=True)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        log.info("Running in DRY-RUN mode — no PocketBase writes will be made (except reading state)")
    run_council_cycle(dry_run=dry_run)
