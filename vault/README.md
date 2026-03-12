# 🔐 Agentic Fleet Hub — Vault Setup

To maintain a secure, `.env`-free environment, the Ursushoribilis Agentic Fleet utilizes **Infisical** as a centralized secrets manager.

Instead of hardcoding API keys or relying on local `.env` files, agents (Gemini, Claude, Codi) are instructed to dynamically fetch the secrets they need using the wrapper scripts provided in this folder.

## 🚀 Setup for Human Managers (Customers)

1. **Install the CLI**: 
   - macOS/Linux: `curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash`
   - Windows: `scoop install infisical` (or download the binary from their GitHub releases).
2. **Login**: Run `infisical login` and authenticate via your browser.
3. **Select Project**: Run `infisical init` inside your project root to link the directory to your Infisical workspace.

## 🤖 Setup for Agents (Unattended Environments)

If your agent is running in a headless environment (like a cloud runner or Docker container), you must provide it with an **Infisical Machine Identity Token**.

1. Generate a **Machine Identity** in your Infisical Dashboard.
2. Set the `INFISICAL_TOKEN` environment variable in the agent's runtime.
3. The agent will automatically use this token when running `./vault/agent-fetch.sh`.

## 🛠️ How Agents Use This

When an agent is tasked with a job that requires an API key (e.g., `RUNWAYML_API_SECRET`), it will run the following command:

**Windows (Gemini CLI)**:
```powershell
.\agentic-fleet-hub\vault\agent-fetch.ps1 -SecretName RUNWAYML_API_SECRET -Environment dev
```

**Linux/macOS (Claude/Codi)**:
```bash
./agentic-fleet-hub/vault/agent-fetch.sh RUNWAYML_API_SECRET dev
```

The script will securely fetch the secret directly into the agent's memory for that session, leaving no trace on the disk.
