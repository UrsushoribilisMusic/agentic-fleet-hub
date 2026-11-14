param (
    [Parameter(Mandatory=$true)]
    [string]$SecretName,
    [string]$Environment = "dev"
)
# AgentFleet — Fetch a secret from Infisical (Windows PowerShell)
# Usage: .\vault\agent-fetch.ps1 -SecretName MY_API_KEY [-Environment dev]
# Requires: INFISICAL_TOKEN env var + infisical CLI

if (-not (Get-Command "infisical" -ErrorAction SilentlyContinue)) {
    Write-Error "Infisical CLI not found. See vault/README.md for install instructions."
    exit 1
}

$domain = if ($env:INFISICAL_API_URL) { $env:INFISICAL_API_URL } else { "https://app.infisical.com/api" }
$secret = infisical secrets get $SecretName --domain=$domain --env=$Environment --plain 2>$null

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($secret)) {
    Write-Error "Failed to retrieve '$SecretName' from env '$Environment'. Check INFISICAL_TOKEN and secret name."
    exit 1
}

Write-Output $secret
