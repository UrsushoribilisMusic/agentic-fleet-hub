# Fleet Steering Architecture

## Overview

Fleet Steering is the mechanism by which the entire agent fleet is redirected to work on a different project without any per-agent reconfiguration. Setting one project as "active" in `fleet_meta.json` causes every agent's next startup to automatically read that project's context, tickets, and lessons instead of defaulting to the fleet hub's own.

## Problem Statement

Prior to this feature (#75), the fleet was hardwired to the `agentic-fleet-hub` repo:

- All agents always read `MISSION_CONTROL.md` from the hub root.
- The inbox (`AGENTS/MESSAGES/inbox.json`) was always the hub's.
- Lessons were stored only in the hub's ledger.
- Switching work to another project (music-video-tool, crm-poc, etc.) required manually editing mandate files.

Misty's earlier partial implementation (#69/#70) made the *Fleet Hub dashboard* display the active project's context, but the agents themselves remained anchored to the hub files on startup.

## Design Principles

1. **Single source of truth for project activation**: `AGENTS/CONFIG/fleet_meta.json` in the hub repo. Multiple projects can have `is_active: true` simultaneously. Agents will scan all active project Mission Controls for assigned tickets.
2. **Zero mandate file edits on project switch**: Agents determine where to read from at runtime.
3. **Hub is the IAP layer**: `inbox.json` stays in the hub repo. Inter-agent messages are fleet-wide, not project-scoped.
4. **Lessons are dual-scoped**: Global lessons in hub; project-specific lessons in the active project repo.
5. **Graceful fallback**: If the active project doesn't have a `MISSION_CONTROL.md`, agents fall back to the hub's.

## Components

### `AGENTS/CONFIG/fleet_meta.json` — Project Registry

Each project entry now has a `repo_path` field: a path relative to the `agentic-fleet-hub` root pointing to that project's repository.

```json
{
  "title": "Music Video Tool",
  "repo_path": "../music-video-tool",
  "is_active": true,
  ...
}
```

The hub itself uses `"repo_path": "."`.

**Activation rule**: The first project with `is_active: true` whose `repo_path` is not `.` is the "work project". If only the hub is active (or nothing is active), agents work on fleet infrastructure as before.

### `fleet/active_context.py` — Context Resolver

Run by agents immediately after the heartbeat check passes. Reads `fleet_meta.json`, resolves the active project, and prints the paths agents must read:

```
Active project : Music Video Tool
Mission Control: ../music-video-tool/MISSION_CONTROL.md  [exists]
Inbox          : AGENTS/MESSAGES/inbox.json  (hub IAP -- always)
Lessons (global): AGENTS/LESSONS/ledger.json  [exists]
Lessons (project): ../music-video-tool/AGENTS/LESSONS/ledger.json  [exists]

NOTE: Active project is 'Music Video Tool'. Before picking up tickets:
  1. cd ../music-video-tool && git pull origin master
  2. Read the Mission Control at the path above.
  3. Write lessons to the project lessons ledger, not just the global one.
```

### `fleet/heartbeat_check.py` — Extended Watch List

In addition to the hub's `MISSION_CONTROL.md` and `inbox.json`, the heartbeat check now:

1. Reads `fleet_meta.json` to find the active project's `repo_path`.
2. If that project has a `MISSION_CONTROL.md`, adds it to the watch list.
3. Computes checksums for all watched files (hub + project MC).
4. Runs the relevance check against *both* MC files — if either has an open ticket for this agent, exit 0.

This means agents wake up when the *project* MC changes, not just the hub MC.

## Agent Startup Protocol (Updated)

All four mandate files (CLAUDE.md, GEMINI.md, MISTRAL.md, AGENTS.md) follow this sequence:

```
1. git pull origin master           (hub repo)
2. python fleet/heartbeat_check.py --agent <name>
   → Exit 1: go idle
   → Exit 0: proceed
3. python fleet/active_context.py   (prints paths)
4. Read Mission Control at printed path
   → If non-hub project: also git pull that repo
5. Read AGENTS/RULES.md
6. Read inbox at printed path
7. Pick up first open ticket
```

## Switching Projects (Operator Workflow)

To steer the fleet to work on a different project:

1. Open `AGENTS/CONFIG/fleet_meta.json`.
2. Set all desired projects' `"is_active": true`.
3. Note: The hub project (`repo_path: "."`) is always active as a fallback.
   (Hub's `is_active` can remain `true` — it's only used as fallback.)
4. Commit and push to master.

Every agent on its next heartbeat will detect the `fleet_meta.json` change (it's inside `MISSION_CONTROL.md`'s folder — actually the heartbeat watches MC and inbox, so the operator should also bump the hub MC — see Note below), resolve the new active project, and read that project's context.

> **Note**: `fleet_meta.json` is not directly watched by the heartbeat check. To ensure agents pick up a project switch promptly, add a one-line note to `MISSION_CONTROL.md` when you flip `is_active` (e.g., "Active project switched to Music Video Tool"). This guarantees the hub MC checksum changes and agents wake up.

## Future Enhancements

- **UI toggle in Fleet Hub dashboard**: Projects tab with a single-active radio button. Clicking activates a project, triggers a commit+push to hub master automatically. This is the intended completion of tickets #69/#70.
- **Per-project inbox**: If projects need isolated agent communication (not just different work context), each project repo can have its own `AGENTS/MESSAGES/inbox.json` and `active_context.py` can route accordingly.
- **Lessons auto-routing**: When agents post a lesson to PocketBase, the project field is populated from the active project title, enabling filtered views in the Fleet Hub.
