# KeyVault

Use this file to document how agents retrieve runtime secrets for this project. Do not store secrets here.

## Rules

1. Never commit API keys, tokens, private keys, `.env` files, or generated credential caches.
2. Fetch secrets at runtime from the configured vault provider.
3. Keep provider-specific project IDs, environment names, and regions in local configuration unless they are safe to share.
4. If a secret is missing, stop the operation that needs it and report the missing key in the task thread.

## Local Setup

Replace these placeholders during installation:

| Setting | Value |
| :--- | :--- |
| Vault provider | `{{VAULT_PROVIDER}}` |
| Vault region | `{{VAULT_REGION}}` |
| Project/environment | `{{VAULT_PROJECT_ENV}}` |
| Fetch command | `{{VAULT_FETCH_COMMAND}}` |

## Agent Usage

Agents should prefer a wrapper script such as:

```bash
{{VAULT_FETCH_COMMAND}} {{SECRET_NAME}}
```

If no vault is configured yet, ask the project owner to provide the expected provider and secret names. Do not invent placeholder credentials in production config.
