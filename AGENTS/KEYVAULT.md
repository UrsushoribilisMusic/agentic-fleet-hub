# 🔐 KeyVault Strategy (Infisical)

To ensure security and portability, we use **Infisical** for all secrets management. No secrets (API keys, tokens) should ever be stored in `.env` files or hardcoded.

---

## 🚀 How to Fetch Secrets

### 1. The "Guidance Package" Pattern
Every project includes a `get-secret.sh` (or `get-secret.ps1`) script. This script uses the Infisical CLI to pull secrets into the environment.

**Command**:
```bash
infisical export --format=dotenv > .env.local
```

### 2. Agent Usage (Service Tokens)
Agents are provided with an **Infisical Service Token** (stored in their local environment). They use this token to authenticate and fetch the latest keys for the project they are working on.

**Gemini/Claude Workflow**:
1. Check if the required secret exists in the environment.
2. If not, run the fetch command: `infisical get <SECRET_NAME>`.
3. Never log or print the output of these commands.

---

## 📂 Current Secret Scopes

| Project | Environment | Description |
| :--- | :--- | :--- |
| **Salesman API** | `Production` | Shopify API Keys, Bearer Tokens. |
| **Music Tool** | `Development` | RunwayML API, YouTube OAuth. |
| **CRM-POC** | `Demo` | Google OAuth Client ID/Secret. |

---

## 🛠️ Setup for Customers
1. Create a free account at [Infisical.com](https://infisical.com).
2. Create a Project and add your secrets.
3. Generate a Service Token for your agents.
4. Add the `INFISICAL_TOKEN` to your machine's environment variables.
