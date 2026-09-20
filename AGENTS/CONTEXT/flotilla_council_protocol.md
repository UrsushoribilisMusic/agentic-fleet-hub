# Flotilla Council Protocol

## Purpose

Flotilla currently excels at parallel task execution plus cross-model peer review. The next step is to add a structured deliberation layer so Miguel can provide product intent and the fleet can turn it into argued plans, decision briefs, and tickets.

The goal is not free-form agent chat. The goal is bounded, auditable, multi-model planning before execution.

## Management Model

Miguel moves from scrum master / project lead to product manager:

1. Miguel defines the goal, constraints, deadline, and success criteria.
2. The fleet runs a two-round council.
3. The fleet produces a decision brief.
4. Miguel approves, rejects, or edits the brief.
5. Tickets are generated from the approved brief.
6. Execution proceeds using the existing task and peer-review machinery.

## Core Rule

Do not let agents discuss until agreement. Deliberation is structured and capped.

- Round 1: independent proposals.
- Round 2: critique and revision.
- Synthesis: one decision brief.
- Hard stop: no third deliberation round unless Miguel explicitly reopens the goal.

## Data Model

### goals

Represents Miguel's product intent.

Suggested fields:

- title
- status: draft, council_open, synthesis_ready, waiting_human, approved, rejected, ticketed, closed
- goal
- why_now
- constraints
- success_criteria
- deadline
- output_type: code, research, sales_asset, dashboard, content, experiment, mixed
- allow_internet_research: boolean
- owner: Miguel by default
- created_at, updated_at

### deliberations

Represents one agent's structured contribution to a goal.

Suggested fields:

- goal_id
- agent
- round: 1 or 2
- role: planner, skeptic, researcher, architect, executor, reviewer, synthesizer
- recommendation
- risks
- rejected_options
- open_questions
- evidence_needed
- confidence: high, moderate, low, speculative
- created_at

### decision_briefs

Represents the synthesized plan Miguel can approve.

Suggested fields:

- goal_id
- status: draft, waiting_human, approved, rejected, ticketed
- summary
- recommended_approach
- agreement
- disagreement
- rejected_alternatives
- known_risks
- open_questions_for_miguel
- ticket_plan
- definition_of_done
- review_assignments
- created_by
- approved_by
- created_at, updated_at

## Decision Brief Template

```markdown
# Decision Brief: <goal title>

## Recommended Approach

## Why This Approach

## Agreement

## Disagreement

## Rejected Alternatives

## Known Risks

## Open Questions For Miguel

## Ticket Plan

## Definition Of Done

## Review Assignments
```

## UI Surfaces

### Goal Intake

Fleet Hub form for:

- goal
- why now
- deadline
- constraints
- success criteria
- output type
- allow internet research

This creates a `goals` record. It must not create execution tickets directly.

### Council Room

Fleet Hub view for:

- active goals
- per-agent round 1 proposals
- per-agent round 2 critiques
- synthesized decision brief
- approve / reject / request changes controls
- generated ticket list after approval

Use structured panels, not chat bubbles.

### Research Workbench

For goals with internet or source research:

- source URL
- extracted claim
- confidence tier
- usable in public copy: yes/no
- needs human review: yes/no
- notes

This may be implemented later. It is not required for the first council prototype.

## Execution Flow

1. Miguel creates a goal.
2. Dispatcher or a council coordinator creates round 1 deliberation tasks for selected agents.
3. Agents write deliberation records, not normal output prose.
4. Round 2 tasks are created after all required round 1 records arrive or a timeout expires.
5. Agents critique the other proposals and update their recommendation.
6. A synthesizer creates a decision brief.
7. Miguel reviews the brief in Fleet Hub.
8. Approved briefs generate GitHub issues / PocketBase tasks.
9. Normal Flotilla execution and cross-model peer review take over.

## Safeguards

- Two-round hard stop.
- No self-approval of execution work.
- Preserve disagreement in the decision brief.
- Confidence tiers required for claims and recommendations.
- External claims require source URLs when `allow_internet_research` is true.
- No automatic ticket creation before Miguel approves the decision brief.
- Goals that lack success criteria should be sent back to `waiting_human`, not guessed into tickets.
- Council R1, R2, and synthesis tasks are PocketBase-only internal work and must set `is_github_sync` to `false`.
- Synthetic or test-looking goals require an explicit `council_state.allow_live_test_tasks = true` flag before they can create live tasks.
- The coordinator filters out agents marked unavailable or offline before spawning new council work.
- The default roster is intentionally small (`clau,codi`) unless a goal explicitly requests more agents.
- The coordinator enforces `COUNCIL_MAX_TASKS_PER_GOAL` to cap accidental task bursts.

## Phase Plan

### Phase 1: Protocol-Only Pilot

No schema or UI changes. Add templates and run one council cycle manually using files under `AGENTS/COUNCIL/`.

### Phase 2: PocketBase Data Model

Add `goals`, `deliberations`, and `decision_briefs` collections plus helper scripts.

### Phase 3: Fleet Hub UI

Add Goal Intake and Council Room views.

### Phase 4: Orchestration

Add coordinator logic that creates round 1, round 2, and synthesis tasks from a goal.

### Phase 5: Ticket Generation

Generate GitHub issues from an approved decision brief. Keep Miguel approval as a hard gate.

### Phase 6: Research Workbench

Add source and claim tracking for research-heavy goals.
