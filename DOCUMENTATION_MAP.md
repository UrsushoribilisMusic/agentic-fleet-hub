# Fleet Documentation Map

This map documents the current state and structure of the project's documentation across the Ursushoribilis Agentic Workspace.

## 🗂️ Categorized Documentation

### 1. Core Fleet Mandates & Strategy
Primary entry points and strategic mandates for the fleet.
- `MISSION_CONTROL.md`: The Shared Context Hub and live execution table.
- `AGENTS.md`: High-level agent roles and responsibilities.
- `DUAL_SYSTEM.md`: Synchronization strategy (Markdown <=> PocketBase).
- `AGENTS/RULES.md`: Team protocols and shared memory rules.

### 2. Agent Handbooks & Mandates
Specific instructions and heartbeat protocols for each agent.
- `GEMINI.md`: Gem's core mandate and phase-based protocol.
- `CLAUDE.md`: Clau's core mandate.
- `MISTRAL.md`: Misty's core mandate.
- `AGENTS/TEMPLATE/GEMINI.md`: Bootstrap template for new agents.

### 3. Project Contexts (The Source of Truth)
Deep-dive architectural documentation for individual projects.
- `AGENTS/CONTEXT/crm_poc_context.md`: CRM System details.
- `AGENTS/CONTEXT/music_video_tool.md`: Music Video Tooling.
- `AGENTS/CONTEXT/robot_ross_artist.md`: Robot Ross (Painting).
- `AGENTS/CONTEXT/robot_ross_salesman.md`: Robot Ross (Salesman).
- `AGENTS/CONTEXT/big_bear_engineering_site.md`: Commercial presence details.
- `AGENTS/CONTEXT/kanban_format_spec.md`: Specification for the Markdown Kanban.
- `AGENTS/CONTEXT/fleet_steering_architecture.md`: High-level steering logic.

### 4. Operations & Deployment
Technical setup, installation, and environment management.
- `INSTALL.md`: Local environment setup.
- `MIGRATION.md`: Details on the Mac Mini migration (2026-03-14).
- `AGENTS/KEYVAULT.md`: Secrets management and Infisical integration.
- `vault/README.md`: KeyVault usage instructions.
- `package/INSTALL.md`: create-flotilla installation guide.

### 5. Release History & Progress
Change logs, standups, and historical records.
- `CHANGELOG.md`: High-level version history.
- `RELEASE_NOTES_v0.2.0.md`, `v0.3.0.md`, `v0.4.0.md`: Detailed release features.
- `standups/`: Daily logs (categorized by date).
- `PROGRESS.md`: Live session logs per agent.

### 6. Proposals & Drafts
Active brainstorming and upcoming feature drafts.
- `BLOG_POST_V0.4.0_DRAFT.md`: Outreach planning.
- `npm_naming_brainstorm.md`: Package naming discussion.

---

### 6. Communication, Goals & Domain Knowledge
Cross-cutting context that agents need to act consistently and strategically.
- `COMMUNICATION_STYLE.md`: Agent tone, format, and writing preferences. **Read before writing any output.**
- `GOALS.md`: What the fleet is optimizing for and what it deliberately ignores.
- `AGENTS/CONTEXT/domain_knowledge.md`: Swiss AI context, EU AI Act compliance notes, Innosuisse/Apertus angles, Classical Remix channel context.

---

## 🔧 Tools & Systems: Consolidation Proposal

The three technical reference docs (`ARCHITECTURE.md`, `DUAL_SYSTEM.md`, `INSTALL.md`) are complementary but fragmented. **Do not merge them** — they serve different audiences and scopes. Instead, cross-link them as follows:

| Document | Audience | Scope | Links to |
| :--- | :--- | :--- | :--- |
| `ARCHITECTURE.md` | All agents + new contributors | System overview, component diagram, data flow | → `DUAL_SYSTEM.md` for sync detail, → `INSTALL.md` for setup |
| `DUAL_SYSTEM.md` | Agents doing state management | How MISSION_CONTROL.md ↔ PocketBase sync works | → `ARCHITECTURE.md` for system context |
| `INSTALL.md` | New contributors / deployment | Step-by-step environment setup | → `ARCHITECTURE.md` for what they're setting up |

**Action for ticket #104 (Codi)**: Add cross-reference headers to each file pointing to the other two. No content merging needed — the separation is intentional.

---

## 🔍 Documentation Gap Analysis

### Filled Gaps (2026-04-07, #103):
- **Communication style**: `COMMUNICATION_STYLE.md` — created with tone, format, and output templates.
- **Goals & priorities**: `GOALS.md` — created with optimization targets, strategic priorities, and "done" definition.
- **Domain knowledge**: `AGENTS/CONTEXT/domain_knowledge.md` — created with EU AI Act, Swiss AI, Innosuisse, Apertus, and Classical Remix context.
- **Tools & systems**: Cross-linking proposal documented above. File-level changes deferred to #104.

### Remaining Gaps:
- **SECURITY.md**: Missing a dedicated security policy for secret handling and vault access patterns.
- **CONTRIBUTING.md**: While `RULES.md` exists, a specific guide for *extending* the fleet (adding new agents or bridges) is missing.
- **TROUBLESHOOTING.md**: No centralized guide for common agent failures (e.g., token exhaustion, API disconnects).
- **API_REFERENCE.md**: The PocketBase and Fleet Hub internal APIs are documented in fragments; a unified reference is needed.

### Documentation Health Assessment:
**Current Status**: **GOOD (Improving)**
The project now has content for all six categories. The `AGENTS/CONTEXT/` source of truth is strong. Next priority: cross-linking the tools docs (#104) and filling the remaining operational gaps (SECURITY, CONTRIBUTING, TROUBLESHOOTING).
