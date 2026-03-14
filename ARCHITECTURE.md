# Flotilla Architecture (v0.1.0)

## Overview
**Flotilla** is an autonomous multi-agent management plane designed to run persistently on a local environment (e.g., Mac Mini). It orchestrates a fleet of specialized AI agents (Clau, Gem, Codi, Misty) using a combination of a shared filesystem, a real-time database, and a staggered heartbeat system.

## System Architecture

```mermaid
graph TD
    subgraph Mac_Mini [Mac Mini / Host Environment]
        launchd[launchd Service Manager]
        PB[PocketBase / Port 8090]
        Disp[Dispatcher.py / Polls every 60s]
        
        subgraph Agents [Active Agent Roster]
            Clau[Clau / Claude Code]
            Gem[Gem / Gemini CLI]
            Codi[Codi / Codex]
            Misty[Misty / Mistral Vibe]
        end
        
        subgraph Filesystem [Shared Filesystem / ~/fleet]
            MC[MISSION_CONTROL.md]
            Lessons[Lessons Ledger / lessons/]
            Inbox[IAP Inbox / inbox.json]
            Workspaces[Isolated Workspaces / agent/workspace/]
        end
    end

    subgraph Network [Network & External]
        Hub[Fleet Hub Dashboard / api.robotross.art]
        TG[Telegram Notifications]
        Inf[Infisical / KeyVault]
    end

    %% Orchestration Flow
    launchd --> PB
    launchd --> Disp
    launchd -. Heartbeat (Staggered) .-> Agents

    %% Data Flow
    Agents -->|Read/Write| MC
    Agents -->|Read/Write| Inbox
    Agents -->|POST/GET| PB
    
    Disp -->|Polls Tasks| PB
    Disp -->|Triggers| Agents
    Disp -->|Alerts| TG

    %% External Connections
    Hub -->|Read-only REST| PB
    Agents -->|Fetch Secrets| Inf
    
    %% Relationships
    MC -. Cognitive Layer .-> Agents
    PB -. Task State & Persistence .-> Hub
```

## Core Components

### 1. The Cognitive Layer (`MISSION_CONTROL.md`)
The "soul" of the fleet. A single Markdown file that serves as the shared memory and high-level project roadmap. Every agent reads this file first to understand the current priority and ticket status.

### 2. The Data Layer (PocketBase)
A single-binary database and REST API that handles:
- **Tasks**: Granular execution state (Todo, In Progress, Peer Review).
- **Comments**: Real-time activity feed from agents.
- **Heartbeats**: Health monitoring and status (Working, Idle, Blocked).
- **Lessons**: Structured evolutionary memory.

### 3. The Orchestrator (Dispatcher & Heartbeats)
- **Dispatcher**: A lightweight Python script that routes pending tasks from PocketBase to the correct agent binary.
- **Heartbeats**: `launchd` services that wake agents on a staggered schedule (e.g., Gem at :00, Codi at :02) to perform autonomous maintenance and review others' work.

### 4. Inter-Agent Protocol (IAP)
A push-messaging layer (`inbox.json`) for high-priority alerts, questions, and handoffs between agents. Complementary to the "pull-based" PocketBase task model.

### 5. Fleet Hub Dashboard
A web-based UI that provides a "God view" of the fleet:
- **Task Board**: Live Kanban view of PocketBase tasks.
- **Activity Feed**: Real-time stream of agent thoughts and outputs.
- **Heartbeat Dots**: Green/Amber/Red indicators for agent health.

## Task Lifecycle (Sequence Diagram)

```mermaid
sequenceDiagram
    participant H as Human / Scheduler
    participant PB as PocketBase
    participant D as Dispatcher
    participant A as Agent (e.g., Gem)
    participant C as Peer Agent (e.g., Clau)

    H->>PB: Create Task (Status: Todo)
    loop Every 60s
        D->>PB: Get Pending Tasks
    end
    D->>A: Trigger Heartbeat / Task Run
    A->>PB: Update Status: In Progress
    A->>A: Perform Work
    A->>PB: Post Output (Comment)
    A->>PB: Update Status: Peer Review
    Note over A,C: Cross-Model Peer Review
    C->>PB: Read Task Output
    C->>PB: Post Feedback / Approval
    C->>PB: Update Status: Approved
```

## Security & Compliance
- **Zero-Disk Secrets**: All API keys and credentials are fetched at runtime via **Infisical**.
- **Audit Logs**: All agent decisions and outputs are persisted in PocketBase with timestamps and agent IDs.
- **Human-in-the-Loop**: Tasks requiring sensitive decisions are moved to `waiting_human` status, triggering a Telegram alert to Miguel.
