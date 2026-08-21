# TS-8 Worklog: Fleet Hub Project Card for Tech Shorts

**Task ID**: `plzm2zioj9xns52`
**Agent**: Gem
**Status**: in_progress

## Objective
Add a `Tech Shorts` project card to the Fleet Hub dashboard (`api.robotross.art/fleet/`, UI in `salesman-cloud-infra`) linking to the TS-1 ideation intake console, documentation, kanban, and stats page.

## Implementation Steps
1. **Metadata Registration**: Add `Tech Shorts` project entry to `AGENTS/CONFIG/fleet_meta.json` with repository path, docs URL, kanban URL, stats link (`/stats/?project=tech-shorts`), and ideation link (`http://localhost:8766` or `/tech-shorts/`).
2. **Dashboard UI Support**: Update `opt/salesman-api/fleet/assets/main.js` and `opt/salesman-api/fleet/package/dashboard/engineering/assets/main.js` in `salesman-cloud-infra` to recognize `ideationLink` and render the intake button.
3. **Verification**: Validate JSON syntax of `fleet_meta.json`, verify JS syntax of `main.js`, and test project card rendering and link targets.
4. **Finalization**: Commit changes across repositories, push, record output, and advance task to `peer_review`.

