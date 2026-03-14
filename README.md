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

## 🔧 Deployment

The Hub is deployed to a private cloud VPS using a surgical-push model. 

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
