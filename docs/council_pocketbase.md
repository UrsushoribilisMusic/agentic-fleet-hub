# Council Protocol PocketBase Helpers

The Council Protocol persists product intent, capped deliberation, and Miguel-approved plans in three PocketBase collections:

- `goals`
- `deliberations`
- `decision_briefs`

Apply the migration by placing `fleet/1782094000_created_council_collections.js` in the PocketBase `pb_migrations/` directory and running `pocketbase migrate up`, or by restarting `pocketbase serve` with automigrate enabled. Do not create sample records in the live operational database.

## Create A Goal

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"

curl -s "$PB_URL/api/collections/goals/records" \
  -H "Content-Type: application/json" \
  --data '{
    "title": "Council pilot",
    "status": "draft",
    "goal": "Run one bounded council cycle from product intent to decision brief.",
    "why_now": "Validate the protocol before adding UI and orchestration.",
    "constraints": "Two deliberation rounds maximum. No execution tickets before approval.",
    "success_criteria": "Miguel can approve, reject, or request changes from a decision brief.",
    "deadline": "2026-09-30 17:00:00.000Z",
    "output_type": "mixed",
    "allow_internet_research": false,
    "owner": "miguel"
  }'
```

## List Open Goals

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"

curl -G -s "$PB_URL/api/collections/goals/records" \
  --data-urlencode 'filter=status!="closed" && status!="rejected"' \
  --data-urlencode 'sort=-updated'
```

## Create A Deliberation

Use the `id` from a `goals` record as `goal_id`.

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"
GOAL_ID="replace_with_goal_record_id"

curl -s "$PB_URL/api/collections/deliberations/records" \
  -H "Content-Type: application/json" \
  --data "{
    \"goal_id\": \"$GOAL_ID\",
    \"agent\": \"codi\",
    \"round\": 1,
    \"role\": \"architect\",
    \"recommendation\": \"Create the smallest persistent schema that supports FCP-3 orchestration and FCP-4/FCP-5 UI work.\",
    \"risks\": \"Overfitting the schema before the first manual pilot completes.\",
    \"rejected_options\": \"Free-form chat transcript storage.\",
    \"open_questions\": \"Which agents participate in the first real council pilot?\",
    \"evidence_needed\": \"FCP-1 templates and first pilot notes.\",
    \"confidence\": \"moderate\"
  }"
```

## List Deliberations For A Goal

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"
GOAL_ID="replace_with_goal_record_id"

curl -G -s "$PB_URL/api/collections/deliberations/records" \
  --data-urlencode "filter=goal_id=\"$GOAL_ID\"" \
  --data-urlencode 'sort=round,created'
```

## Create A Decision Brief

Use the `id` from a `goals` record as `goal_id`. `ticket_plan` and `review_assignments` are JSON fields so FCP-6 can generate normal execution tickets after Miguel approves the brief.

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"
GOAL_ID="replace_with_goal_record_id"

curl -s "$PB_URL/api/collections/decision_briefs/records" \
  -H "Content-Type: application/json" \
  --data "{
    \"goal_id\": \"$GOAL_ID\",
    \"status\": \"draft\",
    \"summary\": \"The fleet recommends adding a bounded Council Protocol path before normal ticket execution.\",
    \"recommended_approach\": \"Store goals, per-agent deliberations, and synthesized decision briefs in PocketBase.\",
    \"agreement\": \"Agents agree on a two-round hard stop and Miguel approval gate.\",
    \"disagreement\": \"Open design questions remain for UI density and orchestration timeouts.\",
    \"rejected_alternatives\": \"Unbounded agent chat; automatic ticket creation from raw goals.\",
    \"known_risks\": \"Poorly specified goals must pause in waiting_human rather than becoming tickets.\",
    \"open_questions_for_miguel\": \"Which first goal should run through the pilot?\",
    \"ticket_plan\": [
      {\"title\": \"Build Goal Intake UI\", \"assigned_agent\": \"gem\"}
    ],
    \"definition_of_done\": \"Miguel can review the brief and explicitly approve it before tickets are created.\",
    \"review_assignments\": [
      {\"ticket\": \"Goal Intake UI\", \"reviewer\": \"clau\"}
    ],
    \"created_by\": \"codi\",
    \"approved_by\": \"\"
  }"
```

## List Decision Briefs Waiting For Miguel

```sh
PB_URL="${PB_URL:-http://127.0.0.1:8090}"

curl -G -s "$PB_URL/api/collections/decision_briefs/records" \
  --data-urlencode 'filter=status="waiting_human"' \
  --data-urlencode 'sort=-updated'
```
