"""
Agentic Fleet Hub — Vault Helper
Fetches secrets from Infisical (EU) and injects them into os.environ.
Falls back to .env / existing env vars if Infisical is unavailable.

Required env vars (put in .env):
    INFISICAL_TOKEN      Service token or machine-identity client secret
    INFISICAL_PROJECT_ID Project ID (required for machine-identity tokens;
                         find it under Project Settings → Project ID in the UI)

Usage:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'agentic-fleet-hub', 'vault'))
    from vault import load_secrets
    load_secrets(["RUNWAYML_API_SECRET", "ELEVENLABS_API_KEY"])
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

INFISICAL_DOMAIN = "https://eu.infisical.com/api"
INFISICAL_ENV    = "dev"


def get_secret(name: str, env: str = INFISICAL_ENV) -> str | None:
    """Fetch a single secret from Infisical. Returns None on failure."""
    token = os.environ.get("INFISICAL_TOKEN")
    if not token:
        return None

    cmd = [
        "infisical", "secrets", "get", name,
        "--domain", INFISICAL_DOMAIN,
        "--env",    env,
        "--plain",
    ]

    # Machine-identity tokens need --projectId; service tokens do not,
    # but passing it when present never hurts.
    project_id = os.environ.get("INFISICAL_PROJECT_ID")
    if project_id:
        cmd += ["--projectId", project_id]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        err = result.stderr.strip()
        if err:
            print(f"[Vault] WARNING: could not fetch '{name}': {err}")
    except FileNotFoundError:
        print("[Vault] WARNING: infisical CLI not found — install with `brew install infisical`")
    except Exception as e:
        print(f"[Vault] WARNING: infisical CLI error for '{name}': {e}")
    return None


def load_secrets(names: list[str], env: str = INFISICAL_ENV, overwrite: bool = False):
    """
    Fetch secrets from Infisical and inject into os.environ.
    Skips secrets already present in the environment unless overwrite=True.
    Prints a clear warning if INFISICAL_TOKEN is not configured.
    """
    token = os.environ.get("INFISICAL_TOKEN")
    if not token:
        missing = [n for n in names if not os.environ.get(n)]
        if missing:
            print(f"[Vault] WARNING: INFISICAL_TOKEN not set — "
                  f"these secrets will fall back to .env or fail: {missing}")
        return

    fetched, skipped, failed = 0, 0, []
    for name in names:
        if not overwrite and os.environ.get(name):
            skipped += 1
            continue
        value = get_secret(name, env)
        if value:
            os.environ[name] = value
            fetched += 1
        else:
            failed.append(name)

    parts = [f"loaded {fetched}"]
    if skipped:
        parts.append(f"skipped {skipped} (already set)")
    if failed:
        parts.append(f"FAILED to fetch: {failed}")
    print(f"[Vault] {', '.join(parts)}")
