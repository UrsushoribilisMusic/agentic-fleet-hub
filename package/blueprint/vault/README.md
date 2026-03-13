# 🔐 AgentFleet — Vault Setup

Secrets are managed via **Infisical** — no `.env` files committed to source control.

## Quick Setup

1. **Create an Infisical project** at [infisical.com](https://infisical.com) (or `eu.infisical.com` for EU-hosted).
2. **Generate a Service Token**: Settings → Service Tokens → Create Token.
3. **Set the env var** (your CI/CD, shell profile, or agent runtime):
   ```bash
   export INFISICAL_TOKEN=st.your-token-here

   # EU region (required if your project is on eu.infisical.com):
   export INFISICAL_API_URL=https://eu.infisical.com/api
   ```
4. **Add your secrets** in the Infisical dashboard under the `dev` environment.

## Usage

**From shell scripts / agents:**
```bash
# Fetch a single secret
./vault/agent-fetch.sh MY_API_KEY

# Fetch from a specific environment
./vault/agent-fetch.sh MY_API_KEY production
```

**From Python (inject into os.environ):**
```python
import sys
sys.path.insert(0, "./vault")
from vault import load_secrets

load_secrets(["MY_API_KEY", "MY_DB_PASSWORD"])
# Keys are now available in os.environ["MY_API_KEY"] etc.
```

## Lessons Learned

- **EU region**: Always set `INFISICAL_API_URL=https://eu.infisical.com/api` — the default CLI targets US. Without this, you'll get `404 service token not found` even with a valid token.
- **Token format**: Service tokens start with `st.` — if yours doesn't, it's the wrong type.
- **Fallback**: `vault.py` falls back silently if `INFISICAL_TOKEN` is unset (safe for local dev).
