# 📦 Mac Mini Migration Guide (Windows -> macOS)

This guide documents the steps to recreate the **Agentic Fleet Hub** environment on your new Mac Mini.

## 🚀 1. Core Tooling
Install the following base tools:
- **Git**: `brew install git`
- **Node.js (v18+)**: `brew install node`
- **Python (3.12+)**: `brew install python@3.12`
- **Infisical CLI**: 
  ```bash
  curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.deb.sh' | sudo -E bash
  sudo apt-get update && sudo apt-get install -y infisical
  # Note: Use the macOS brew instructions if available:
  brew install infisical/tap/infisical
  ```

## 📂 2. Repositories
Clone all projects into a common directory (e.g., `~/Projects/`):
```bash
git clone https://github.com/UrsushoribilisMusic/agentic-fleet-hub.git
git clone https://github.com/UrsushoribilisMusic/crm-poc.git
git clone https://github.com/UrsushoribilisMusic/salesman-cloud-infra.git
git clone https://github.com/UrsushoribilisMusic/music-video-tool.git
git clone https://github.com/UrsushoribilisMusic/the-lost-coins.git
```

## 🔒 3. Secrets & Tokens (CRITICAL)
Most secrets are in **Infisical**. To authorize the Mac Mini:
1. Run `infisical login`.
2. Ensure you have the `INFISICAL_TOKEN` for each agent if using automated scripts.

**Manual Backup Required**: 
The following files are NOT in git and must be copied manually from the Windows machine to the Mac Mini:
- `music-video-tool/youtube_token.pickle`
- `music-video-tool/client_secrets.json`
- `music-video-tool/sheets_service_account.json`
- `~/.ssh/` (Your SSH keys for GitHub and VPS access)

## 🗄️ 4. Local Data
The local CRM development database should be backed up if you want to keep local history:
- Copy `customer-mgmt/data/crm.db` from Windows to the same path on Mac.

## 🛠️ 5. Agent Setup
Once the repos are cloned:
1. **Gemini CLI**: Set up your `.gemini` folder and ensure `MISSION_CONTROL.md` is correctly linked.
2. **Claude Code**: Ensure `CLAUDE.md` is present in the root.
3. **Misty**: Ensure `AGENTS.md` is present.

## 🏁 6. Verification
Run the following check:
- `node server.mjs` (in `salesman-cloud-infra/opt/salesman-api/`) should start locally.
- `infisical secrets` should list your workspace secrets.

---
**Status: READY FOR MOVE. ALL CODE SECURED.**
