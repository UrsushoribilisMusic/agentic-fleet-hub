# Fleet Steering Architecture

Fleet steering lets a multi-agent workspace redirect attention to one or more active projects without editing every runtime-specific mandate file.

## Principles

1. `AGENTS/CONFIG/fleet_meta.json` is the project registry.
2. Runtime mandate files stay small and agent-specific.
3. Shared startup and coordination behavior lives in `AGENTS/RULES.md`.
4. The inbox is fleet-wide by default.
5. Lessons can be global or project-specific.
6. Missing optional services should degrade gracefully; agents should report the blocker and continue with local work when possible.

## Project Registry

Each project entry should include:

```json
{
  "title": "Example Project",
  "repo_path": ".",
  "summary": "What this project does.",
  "docs": ["https://example.com/docs"],
  "kanban": "https://example.com/kanban",
  "is_active": true
}
```

Agents should inspect all active projects for assigned work. The hub/current repository remains the fallback project.

## Startup Flow

1. Pull the current repository.
2. Run heartbeat checks if available.
3. Resolve active project context.
4. Read Mission Control for each active project.
5. Read `AGENTS/RULES.md`.
6. Read the inbox.
7. Review peer-review tasks before starting new tasks.

## Local Customization

Use placeholders in reusable profiles. Put private paths, customer names, service URLs, and secrets in local config or a vault-backed setup step after installation.
