param (
    [Parameter(Mandatory=$true)]
    [string]$SecretName,
    [string]$Environment = "dev"
)

# This script is used by AI Agents (Gemini CLI) to fetch secrets dynamically.
# It requires the Infisical CLI to be installed and authenticated.

if (-not (Get-Command "infisical" -ErrorAction SilentlyContinue)) {
    Write-Error "Infisical CLI is not installed. Please see agentic-fleet-hub/vault/README.md for setup instructions."
    exit 1
}

# Fetch the secret
$secret = infisical secrets get $SecretName --env=$Environment --plain 2>$null

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($secret)) {
    Write-Error "Failed to retrieve secret '$SecretName' from environment '$Environment'. Ensure you are logged in and the secret exists."
    exit 1
}

Write-Output $secret
