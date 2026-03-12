"""
Agentic Fleet Hub — Vault Helper
Fetches secrets from Infisical (EU) and injects them into os.environ.
Falls back silently to existing env vars / .env if INFISICAL_TOKEN is not set.

Usage (add to top of any project's main entry point):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agentic-fleet-hub', 'vault'))
    from vault import load_secrets
    load_secrets(["RUNWAYML_API_SECRET", "YOUTUBE_CLIENT_SECRETS_JSON"])
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

INFISICAL_DOMAIN = "https://eu.infisical.com/api"
INFISICAL_ENV = "dev"


def get_secret(name: str, env: str = INFISICAL_ENV) -> str | None:
    """Fetch a single secret from Infisical. Returns None on failure."""
    token = os.environ.get("INFISICAL_TOKEN")
    if not token:
        return None
    try:
        result = subprocess.run(
            ["infisical", "secrets", "get", name,
             "--domain", INFISICAL_DOMAIN,
             "--env", env,
             "--plain"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        logger.warning(f"[Vault] Could not fetch '{name}': {result.stderr.strip()}")
    except Exception as e:
        logger.warning(f"[Vault] Infisical CLI error for '{name}': {e}")
    return None


def load_secrets(names: list[str], env: str = INFISICAL_ENV, overwrite: bool = False):
    """
    Fetch secrets from Infisical and inject into os.environ.
    Skips secrets already present in the environment unless overwrite=True.
    """
    token = os.environ.get("INFISICAL_TOKEN")
    if not token:
        logger.debug("[Vault] INFISICAL_TOKEN not set — skipping vault, using local env.")
        return

    fetched, skipped = 0, 0
    for name in names:
        if not overwrite and os.environ.get(name):
            skipped += 1
            continue
        value = get_secret(name, env)
        if value:
            os.environ[name] = value
            fetched += 1
        else:
            logger.warning(f"[Vault] Secret '{name}' not found in vault or fetch failed.")

    logger.info(f"[Vault] Loaded {fetched} secret(s) from Infisical ({skipped} already set).")
