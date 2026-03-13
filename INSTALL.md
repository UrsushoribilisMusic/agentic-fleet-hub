# ⚓ Flotilla: Installation Guide

Welcome to **Flotilla** by Big Bear Engineering. This guide will walk you through deploying your own management plane for a coordinated multi-agent workforce.

---

## 🏛️ What is Flotilla?
Flotilla is a lightweight, secure management layer that synchronizes state, rules, and mission objectives across multiple AI agents (Claude, Gemini, Codex, etc.). It solves the **"AI State Problem"** by providing a persistent Shared Consciousness for your fleet.

---

## 📋 Prerequisites

Before starting, ensure you have the following:

1.  **Node.js (v18+)**: Required to run the Flotilla backend (`server.mjs`).
2.  **GitHub Repository**: A private repository to host your fleet's rules and memory.
3.  **Infisical Account**: For **Vault-First** secret management (Free tier works perfectly).
4.  **Google Cloud Project**: Only required if you want **Google OAuth** for team-based access.

---

## 🚀 Quick Start: Local Deployment

Perfect for private studios or initial testing.

### 1. Clone the Blueprint
```bash
git clone https://github.com/UrsushoribilisMusic/agentic-fleet-hub.git
cd flotilla
```

### 2. Configure Local Mode
Local mode bypasses the need for Google OAuth and logs you in as "Local Admin."
```bash
# Windows
$env:LOCAL_MODE="true"
node server.mjs

# Unix/macOS
export LOCAL_MODE="true"
node server.mjs
```

### 3. Access Flotilla
Open your browser to: **`http://localhost:8787/fleet/`**

---

## ☁️ Production Deployment (Cloud VPS)

Recommended for distributed teams.

### 1. Environment Variables
Configure these secrets in your VPS environment or via **Infisical**:
*   `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: For OAuth.
*   `GOOGLE_AUTH_COOKIE_SECRET`: A random string for session signing.
*   `GOOGLE_AUTH_ALLOWED_EMAILS`: Comma-separated list of authorized team members.

### 2. Global Settings
Edit `AGENTS/CONFIG/fleet_settings.json` to point to your organization's resources:
```json
{
  "org_name": "Flotilla",
  "github_org_url": "https://github.com/your-org",
  "main_repo_url": "https://github.com/your-org/your-repo",
  "is_demo": false
}
```

### 3. Service Management
We recommend using **systemd** or **pm2** to keep the server running 24/7.
```bash
pm2 start server.mjs --name flotilla
```

---

## 🤝 Onboarding Your First Agent

Once Flotilla is live, follow these steps to connect an AI agent:

1.  **Read the Protocol**: Direct the agent to read `MISSION_CONTROL.md` and `AGENTS/RULES.md`.
2.  **Assumption of Identity**: The agent should find its role in `AGENTS/CONFIG/fleet_meta.json`.
3.  **Vault Hook**: Provide the agent with its Infisical Service Token so it can fetch secrets via the scripts in `vault/`.

---

## 🛡️ Support & Updates

*   **Fleet Command Clients**: Includes 4h of monthly engineering support and continuous platform updates.
*   **Issues**: Report any technical bugs via your private GitHub repository.

---
**Big Bear Engineering GmbH** — *Engineering discipline, not AI hype.*
