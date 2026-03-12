#!/bin/bash

# This script is used by AI Agents (Claude/Codi) to fetch secrets dynamically.
# It requires the Infisical CLI to be installed and authenticated.

SECRET_NAME=$1
ENV=${2:-dev}

if [ -z "$SECRET_NAME" ]; then
    echo "Usage: ./agent-fetch.sh <SECRET_NAME> [environment]"
    exit 1
fi

if ! command -v infisical &> /dev/null; then
    echo "Error: Infisical CLI is not installed. Please see agentic-fleet-hub/vault/README.md for setup instructions."
    exit 1
fi

# Fetch the secret
SECRET=$(infisical secrets get "$SECRET_NAME" --env="$ENV" --plain 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$SECRET" ]; then
    echo "Error: Failed to retrieve secret '$SECRET_NAME' from environment '$ENV'. Ensure you are logged in and the secret exists."
    exit 1
fi

echo "$SECRET"
