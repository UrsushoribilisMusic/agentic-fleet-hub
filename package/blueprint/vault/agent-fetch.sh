#!/bin/bash
# AgentFleet — Fetch a secret from Infisical (Unix)
# Usage: ./vault/agent-fetch.sh SECRET_NAME [environment]
# Requires: INFISICAL_TOKEN env var + infisical CLI

SECRET_NAME=$1
ENV=${2:-dev}
DOMAIN=${INFISICAL_API_URL:-"https://app.infisical.com/api"}

if [ -z "$SECRET_NAME" ]; then
    echo "Usage: ./vault/agent-fetch.sh <SECRET_NAME> [environment]"
    exit 1
fi

if ! command -v infisical &> /dev/null; then
    echo "Error: Infisical CLI not found. See vault/README.md for install instructions."
    exit 1
fi

SECRET=$(infisical secrets get "$SECRET_NAME" --domain="$DOMAIN" --env="$ENV" --plain 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$SECRET" ]; then
    echo "Error: Failed to retrieve '$SECRET_NAME' from env '$ENV'. Check INFISICAL_TOKEN and secret name." >&2
    exit 1
fi

echo "$SECRET"
