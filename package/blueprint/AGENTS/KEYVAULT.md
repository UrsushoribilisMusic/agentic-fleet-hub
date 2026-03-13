# 🔐 KeyVault — Secrets Management

This fleet uses **Infisical** for secrets management. All API keys, tokens, and credentials are stored in the vault and fetched at runtime — never committed to source control.

---

## Setup

1. Create a project at [infisical.com](https://infisical.com) (EU region: `eu.infisical.com`).
2. Generate a **Service Token** for your project (Settings → Service Tokens).
3. Set the environment variable:
   ```bash
   export INFISICAL_TOKEN=st.your-token-here
   # For EU region (required):
   export INFISICAL_API_URL=https://eu.infisical.com/api
   ```
4. Add the secrets you need in the Infisical dashboard under the `dev` environment.

---

## Fetching Secrets

**Shell (Unix)**:
```bash
./vault/agent-fetch.sh SECRET_NAME_1 SECRET_NAME_2
```

**PowerShell (Windows)**:
```powershell
./vault/agent-fetch.ps1 SECRET_NAME_1 SECRET_NAME_2
```

**Python** (inside your app):
```python
import sys
sys.path.insert(0, "./vault")
from vault import load_secrets
load_secrets(["MY_API_KEY", "MY_DB_PASSWORD"])
# secrets are now in os.environ
```

---

## Secrets to Configure

| Secret Name | Description | Used By |
| :--- | :--- | :--- |
| `{{SECRET_1_NAME}}` | {{SECRET_1_DESC}} | {{SECRET_1_APP}} |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | fleet-server (auth) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | fleet-server (auth) |

> Replace `{{SECRET_*}}` rows with your project's actual secrets.

---

## Important Notes

- **EU region**: Always pass `--domain https://eu.infisical.com/api` to the Infisical CLI, or set `INFISICAL_API_URL`.
- **Fallback**: If `INFISICAL_TOKEN` is not set, `vault.py` falls back silently to existing `os.environ` values (safe for local dev with `.env` files that are gitignored).
- **Service token format**: Tokens start with `st.` — if yours doesn't, regenerate it.
