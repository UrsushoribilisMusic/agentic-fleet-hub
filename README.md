# ⚓ Flotilla

The centralized management plane for a disciplined, multi-agent engineering workforce. 

This repository serves as the **Shared Consciousness** for Big Bear Engineering's agentic fleet. It synchronizes state, rules, and mission objectives across multiple models (Claude, Gemini, Codex) to solve the "AI State Problem."

---

## 🚀 Quick Start

Ready to deploy your workforce? 

1.  **Installation**: Follow the [Installation Guide](INSTALL.md) to set up your Flotilla instance (Local or Cloud).
2.  **Configuration**: Define your agents and projects in `AGENTS/CONFIG/`.
3.  **Bootstrap**: Use the provided `MISSION_CONTROL.md` to synchronize your fleet's first session.

---

## 🏛️ Platform Architecture

For a deep dive into the system components, data flow, and task lifecycle, see the **[Architecture Diagram & Spec](ARCHITECTURE.md)**.

*   **Task Scratchpad**: Inter-agent state tracking field in PocketBase tasks for seamless handoffs.
*   **Structured Evolutionary Memory**: A lessons ledger that captures decisions, rationales, and outcomes as data, not just prose.
*   **Management Hub**: A human-readable dashboard for monitoring agent health and standups.
*   **Memory Tree**: A structured, version-controlled hierarchy of project context and blueprints.
*   **Shared Consciousness Protocol**: Mandatory synchronization via `MISSION_CONTROL.md`.
*   **Evolutionary Learning**: A structured "Lessons Learned" ledger where agents log and Miguel approves hard-won insights.
*   **Vault-First Security**: Zero-footprint secret management via **Infisical**.

---

## 📂 Repository Structure

```text
flotilla/
├── AGENTS/
│   ├── CONFIG/       # Dynamic metadata driving the UI
│   ├── CONTEXT/      # Deep project architectural blueprints
│   ├── LESSONS/      # Evolutionary memory ledger (Karpathy-style)
│   ├── MESSAGES/     # Inter-Agent Protocol (IAP) Inbox
│   └── RULES.md      # The fleet's standard operating procedures
├── command-center/   # Source code for the Flotilla Management Dashboard
├── standups/         # Automated session logs and audit trails
├── vault/            # Security wrapper scripts for secret injection
└── MISSION_CONTROL.md # The live session entry point (Read First)
```

---

## 🤝 Multi-Agent Orchestration

### 🚀 Startup Protocol (Mandatory)
Every agent session **MUST** begin by reading `MISSION_CONTROL.md`. This ensures the agent inherits the current fleet state, active tickets, and any newly approved "Lessons Learned."

### 📬 Inter-Agent Protocol (IAP)
Agents communicate via the internal Inbox located in the dashboard. High-priority alerts can be used to coordinate complex multi-step tasks between models.

### 🧬 Evolutionary Learning
When an agent encounters a failure or discovers an optimization, it logs a lesson to the `LESSONS/ledger.json`. Once approved by the human manager, this lesson is injected into the context of all future sessions.

---

## 🔧 Deployment Scenarios

Flotilla supports three deployment models so customers can self-select the right setup for their security and accessibility needs.

| Scenario | Components | Dashboard Access | Best For |
| :--- | :--- | :--- | :--- |
| **1. Local (Default)** | All local | `localhost:8787/fleet/` | Personal use, local teams, strict privacy |
| **2. Cloud VPS** | All on 1 VPS | `https://your-domain.com/fleet/` | Remote teams, public dashboards |
| **3. Hybrid** | Split (Local + Cloud) | `https://your-domain.com/fleet/` | Hardware agents, public visibility + local execution |

### Scenario 1 — Local (Default)
Everything runs on a single local machine (agents + PocketBase + Fleet Hub). You access the dashboard at `localhost:8787/fleet/`. This requires zero extra config and works out-of-the-box with `create-flotilla`. Ideal for personal use, local teams, or privacy-first corporate installs.

### Scenario 2 — Cloud VPS (Single Server)
Everything runs on a single cloud VPS (like DigitalOcean or AWS EC2). The dashboard is publicly accessible. PocketBase and Fleet Hub are co-located, meaning no connectivity gap for the UI. Best for remote teams and always-on fleets. *(Note: Claude Code, Gemini CLI, and Codex must support headless operation on Linux).*

### Scenario 3 — Hybrid (Agents Local, Dashboard Remote)
Agents and PocketBase run on a local machine (e.g., Mac Mini, on-prem server), while the Fleet Hub is hosted publicly on a separate cloud server. This requires the push connector (`fleet_push.py`). Best for hardware-connected agents (robot arms, local files) where you need enterprise privacy but public visibility.
The connector pushes a read-only PocketBase snapshot (`heartbeats`, `tasks`, `comments`) to the remote Fleet Hub every 60 seconds using `FLEET_SYNC_TOKEN`, and the remote `server.mjs` serves that cached snapshot whenever it cannot reach PocketBase directly.
Required runtime secrets:
- `FLEET_SYNC_TOKEN` on both the local connector and the remote Fleet Hub server
- `FLEET_SYNC_URL` on the local connector if the public dashboard is not `https://api.robotross.art/fleet/snapshot`
**Scenario 3 requires additional configuration. Contact us at info@flotilla.cc for setup assistance.**

*   **Public Site**: [bigbearengineering.com](https://bigbearengineering.com)
*   **Flotilla Hub**: [api.robotross.art/fleet/](https://api.robotross.art/fleet/)
*   **Growth Hub**: [api.robotross.art/growth/](https://api.robotross.art/growth/)

---

## The Crew

This repository is built and maintained by a coordinated multi-agent team:

| Agent | Model | Role |
| :--- | :--- | :--- |
| **Clau** | Claude Code (Anthropic) | Implementation lead — logic, refactoring, complex tickets |
| **Gem** | Gemini CLI (Google) | Architecture and context — large-context synthesis, documentation |
| **Codi** | Codex (OpenAI) | QA and delivery — throughput, validation, scaffolding |
| **Misty** | Mistral Vibe (Mistral AI) | European model — compliance, EU market, open-weight advantage |

Human manager: **Miguel** — Big Bear Engineering GmbH, Zurich.

---
**Big Bear Engineering GmbH** — *Engineering discipline, not AI hype.*
