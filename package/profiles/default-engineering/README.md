# Default Engineering Profile

This profile is the reusable engineering instruction pack for a Flotilla fleet. It bootstraps the shared coordination rules, agent-specific mandate files, starter memory folders, and placeholder configuration needed for a new multi-agent engineering workspace.

This README explains the pack itself. If you copy the profile directly into a new repository, replace this file with a project README after setup or move this content into onboarding docs.

## Contents

- `MISSION_CONTROL.md` - root project coordination template.
- `ARCHITECTURE.md` - starter architecture map required by the shared rules.
- `.gitignore` and `gitignore.template` - starter ignore rules. The template copy exists because npm packages omit `.gitignore`.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `MISTRAL.md`, `GEMMA.md` - runtime-specific mandate files.
- `AGENTS/RULES.md` - shared fleet heartbeat, task, review, reporting, and safety rules.
- `AGENTS/KEYVAULT.md` - vault usage rules without secrets.
- `AGENTS/CONFIG/*.json` - sanitized starter configuration files.
- `AGENTS/CONTEXT/*.md` - reusable coordination context.
- `AGENTS/MESSAGES/inbox.json` - starter inter-agent inbox.
- `AGENTS/LESSONS/ledger.json` - starter lessons ledger.
- `standups/` - starter daily-reporting files.

## How To Use

Copy the contents of this directory into a new repository root, then replace all `{{PLACEHOLDER}}` values with project-specific values. Keep private machine paths, deploy keys, secrets, and customer details out of the profile; put those in local config or vault-backed files after installation.

Agent-specific files should stay small. Shared coordination behavior belongs in `AGENTS/RULES.md`, and project memory belongs in `AGENTS/CONTEXT/`.
