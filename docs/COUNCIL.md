# The Council Room

Most fleet work is execution: a ticket, an owner, a review. Some questions are different: which approach to take, what to build first, how to frame a proposal. For those, Flotilla runs a **council**: several agents from different vendors deliberate in rounds, and one of them writes a decision brief for the human to approve.

The point is not consensus. Different models have different blind spots, and the brief must show where they genuinely disagree.

## Lifecycle

```
goal (council_open)
  │  intake gate: success criteria present? roster available? not a [TEST] goal?
  │      no → waiting_human (+ Telegram note)
  ▼
Round 1   one task per agent, each with a role; independent proposals → deliberations
  ▼
Round 2   each agent reads all proposals and critiques them → deliberations
  ▼
Synthesis one agent writes the decision brief (status waiting_human)
  ▼
Human     approves (status approved, approved_by set), rejects, or edits
  ▼
Ticketing council_brief_ticketer.py turns the ticket plan into backlog tickets
  ▼
Human     releases tickets from backlog to todo when ready
```

## Opening a goal

Create a record in the `goals` collection:

| Field | Required | Meaning |
|---|---|---|
| `title` | yes | Short name |
| `goal` | yes | The question, with all context the agents need |
| `success_criteria` | yes | What a good answer contains. Goals without it are parked |
| `status` | yes | `council_open` |
| `roster` | no | Agents to include, e.g. `["clau","gem","codi"]`. Defaults to `COUNCIL_DEFAULT_ROSTER` |
| `constraints`, `why_now`, `output_type` | no | Extra framing for the agents |
| `deadline` | no | Informational for the agents |
| `allow_internet_research` | no | Whether agents may research the web |

Put confidential inputs (customer lists, partner data) in files on the machine and reference their paths in the goal. Council tasks are created with `private = true` and never mirrored to GitHub, but files are still the safest place for sensitive material.

## Roles

Each agent gets a role for the goal, in this order: architect, planner, executor, skeptic, researcher, reviewer. A roster of four or more agents therefore always includes a skeptic, which is what keeps briefs honest; with a smaller roster, ask for critique explicitly in the goal.

## The decision brief

| Field | Content |
|---|---|
| `summary` | Two or three sentences |
| `recommended_approach` | What the council recommends |
| `agreement` | What all agents agreed on |
| `disagreement` | What was genuinely contested, not papered over |
| `rejected_alternatives` | Options considered and why they were dropped |
| `known_risks` | Main risks |
| `open_questions_for_human` | Decisions only the human can make |
| `ticket_plan` | Proposed execution tickets (title, agent, description) |
| `definition_of_done` | How we will know the goal is achieved |

The synthesizer must not create execution tickets. Only an approved brief becomes tickets, and those start in `backlog`.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `COUNCIL_DEFAULT_ROSTER` | `clau,codi,gem` | Roster when the goal has none |
| `COUNCIL_MAX_TASKS_PER_GOAL` | `10` | Hard cap on coordinator-created tasks per goal |
| `COUNCIL_R1_TIMEOUT_HOURS` | `4` | Round 1 timeout; late agents are reported, the round proceeds |
| `COUNCIL_R2_TIMEOUT_HOURS` | `4` | Round 2 timeout |
| `COUNCIL_SYNTHESIS_TIMEOUT_HOURS` | `6` | Synthesis timeout |
| `COUNCIL_SKIP_UNAVAILABLE` | off | `1` drops unavailable agents instead of parking the goal |
| `COUNCIL_ALLOW_SYNTHETIC_GOALS` | off | `1` allows goals whose title starts with `[TEST]` |

## Research goals

For goals that depend on public sources (market research, prospect lists, articles), `research_ledger.py` keeps a ledger of sources and claims with confidence tiers, so every claim in a brief can be traced to a source.

## What a council costs

A four-agent council creates nine agent runs (four proposals, four critiques, one synthesis). In practice a council with prepared inputs finishes in 15 to 60 minutes, depending on the agents' quotas and the research involved.
