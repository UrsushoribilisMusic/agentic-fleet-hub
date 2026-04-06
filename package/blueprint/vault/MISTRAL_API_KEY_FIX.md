# Mistral API Key Fix - April 5, 2026

## 🔴 Issue
Mistral API key is returning "Invalid API key" errors. The key has either:
- Expired
- Been revoked
- Changed on the Mistral platform

## 🔧 Solution

### Step 1: Regenerate API Key
1. Go to [Mistral Console](https://console.mistral.ai/)
2. Navigate to **API Keys** section
3. Generate a new API key
4. Copy the new key

### Step 2: Update in Infisical
```bash
# Set your Infisical token
export INFISICAL_TOKEN="your-infisical-token-here"

# Update the Mistral API key
infisical secrets set MISTRAL_API_KEY \
  --value="your-new-api-key-here" \
  --domain="https://app.infisical.com/api" \
  --env="dev" \
  --projectId="3233b7c1-8309-447d-af5a-6541e38dc1b3"
```

### Step 3: Verify the Update
```bash
# Fetch the updated key to verify
./vault/agent-fetch.sh MISTRAL_API_KEY dev
```

### Step 4: Restart Misty Agent
```bash
# Unload and reload the plist
launchctl unload /Users/miguelrodriguez/Library/LaunchAgents/fleet.misty.plist
launchctl load /Users/miguelrodriguez/Library/LaunchAgents/fleet.misty.plist

# Check logs
 tail -f /Users/miguelrodriguez/fleet/logs/misty.log
```

## 📋 Additional Checks

### Verify Mistral-Vibe Installation
```bash
# Check installed version
ls /opt/homebrew/Cellar/mistral-vibe/

# Test mistral-vibe CLI
/opt/homebrew/bin/vibe --version
```

### Test API Key Directly
```bash
# Test with curl
curl https://api.mistral.ai/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## ✅ Verification

After completing these steps:
- Misty should be able to authenticate with Mistral API
- No more "Invalid API key" errors
- Heartbeat protocol should complete successfully

## 📝 Notes

- The plist has been updated to use mistral-vibe 2.7.3
- Remember to update the API key in all environments (dev, staging, prod)
- If issues persist, check Mistral's status page for outages

**Last Updated**: April 5, 2026