# {{PROJECT_NAME}} Architecture

This file is the starter architecture map for a project bootstrapped from the `default-engineering` profile. Replace placeholders during setup and keep this document current as the system changes.

## Purpose

{{PROJECT_DESCRIPTION}}

## System Overview

| Area | Responsibility | Primary Files |
| :--- | :--- | :--- |
| Application | {{APPLICATION_RESPONSIBILITY}} | {{APPLICATION_FILES}} |
| Data | {{DATA_RESPONSIBILITY}} | {{DATA_FILES}} |
| Automation | Agent heartbeat, task coordination, and reporting. | `AGENTS/RULES.md`, `AGENTS/CONFIG/`, `standups/` |
| Operations | Local setup, vault access, deployment, and recovery steps. | `README.md`, `AGENTS/KEYVAULT.md` |

## Data Flow

1. {{DATA_FLOW_STEP_1}}
2. {{DATA_FLOW_STEP_2}}
3. {{DATA_FLOW_STEP_3}}

## Agent Coordination

- Shared rules live in `AGENTS/RULES.md`.
- Agent-specific runtime files live at the repository root.
- Project memory lives in `AGENTS/CONTEXT/`.
- Inter-agent messages live in `AGENTS/MESSAGES/inbox.json` unless a message API is configured.

## Open Decisions

| Decision | Owner | Due | Notes |
| :--- | :--- | :--- | :--- |
| {{DECISION}} | {{OWNER}} | {{DATE}} | {{NOTES}} |
