# Mac Mini Migration Guide

This document covers moving the full Ursushoribilis development environment
from Windows 11 (MiguelWindows) to Mac Mini. Written by Clau on 2026-03-14.

---

## 1. System Prerequisites (install first)

```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.12
brew install python@3.12

# Node.js 20+
brew install node

# Git (usually pre-installed on Mac, verify)
git --version

# ffmpeg (required by moviepy for video assembly)
brew install ffmpeg

# espeak-ng (required by Kokoro TTS)
brew install espeak-ng
```

---

## 2. Clone All Repos

```bash
mkdir ~/projects && cd ~/projects

git clone https://github.com/UrsushoribilisMusic/agentic-fleet-hub.git
git clone https://github.com/UrsushoribilisMusic/music-video-tool.git
git clone https://github.com/UrsushoribilisMusic/crm-poc.git
git clone https://github.com/UrsushoribilisMusic/the-lost-coins.git
git clone https://github.com/UrsushoribilisMusic/salesman-cloud-infra.git  # private
```

---

## 3. Python Virtual Environment

The Windows venv (`.venv312`) does NOT transfer -- recreate it:

```bash
cd ~/projects/music-video-tool
python3.12 -m venv .venv312
source .venv312/bin/activate

pip install gradio anthropic beautifulsoup4 python-dotenv runwayml openpyxl \
  pillow requests "moviepy<2.0" "numpy<2.0" librosa kokoro soundfile \
  espeakng-loader google-api-python-client google-auth-httplib2 \
  google-auth-oauthlib gspread
```

Key version constraints (learned the hard way):
- `moviepy<2.0` — v2 removed the `.editor` submodule
- `numpy<2.0` — v2 breaks moviepy (int64 frame dtype issue)
- Kokoro first run downloads ~300MB model -- appears to hang, just wait

---

## 4. Credential Files (Manual Transfer -- NOT in git)

These files are gitignored and must be copied manually from the Windows machine
(or re-downloaded from their respective services):

| File | Location | Source |
| :--- | :--- | :--- |
| `.env` | `music-video-tool/.env` | Copy from Windows or recreate |
| `client_secrets.json` | `music-video-tool/client_secrets.json` | Google Cloud Console |
| `sheets_service_account.json` | `music-video-tool/sheets_service_account.json` | Google Cloud Console |
| `youtube_token.pickle` | `music-video-tool/youtube_token.pickle` | Copy from Windows (or re-auth) |

### .env contents needed:
```
RUNWAYML_API_SECRET=<from Infisical or RunwayML dashboard>
```

### Re-authenticate YouTube (if not copying token):
```bash
# Run the tool once -- it will open a browser for OAuth
python app.py
# Click YouTube upload -- it will trigger the auth flow
```

---

## 5. Large Files / Media (Manual Transfer)

These live outside git repos. Transfer via USB, AirDrop, or external drive:

| Source (Windows) | Destination (Mac) |
| :--- | :--- |
| `C:\Users\migue\Videos\MusicVideoOutput\video_tracker.xlsx` | `~/Videos/MusicVideoOutput/video_tracker.xlsx` |
| `C:\Users\migue\Videos\StoryVideos\` | `~/Videos/StoryVideos/` |
| `C:\Users\migue\Videos\StoryCharacters\` | `~/Videos/StoryCharacters/` |
| `C:\Users\migue\Videos\MusicVideoOutput\` (video files) | `~/Videos/MusicVideoOutput/` |

---

## 6. Claude Memory

Claude Code stores memory at `~/.claude/projects/`. This may auto-sync if you
use the same Anthropic account, or copy manually:

```bash
# From Windows, zip and transfer:
# C:\Users\migue\.claude\projects\C--Users-migue\memory\
# Destination on Mac: ~/.claude/projects/<project-hash>/memory/
```

The memory system will rebuild itself over time if not transferred.

---

## 7. Launch Scripts (Mac equivalents)

The Windows `.bat` files do not work on Mac. Use these instead:

### Music Video Tool
```bash
cd ~/projects/music-video-tool
source .venv312/bin/activate
python app.py
# Opens at http://localhost:7860
```

### Story Tool
```bash
cd ~/projects/music-video-tool
source .venv312/bin/activate
python story_tool.py
# Opens at http://localhost:7861
```

### Create a launch script (optional):
```bash
cat > ~/launch_music.sh << 'EOF'
#!/bin/bash
cd ~/projects/music-video-tool
source .venv312/bin/activate
python app.py
EOF
chmod +x ~/launch_music.sh
```

---

## 8. Fleet Hub (agentic-fleet-hub)

```bash
cd ~/projects/agentic-fleet-hub

# No Python venv needed -- pure Node.js
# Run local fleet server (optional, for testing)
cd package/server
npm start
# Opens at http://localhost:8787/setup/
```

Set GITHUB_REPO env var for live standup sync:
```bash
export GITHUB_REPO=UrsushoribilisMusic/agentic-fleet-hub
```

---

## 9. CRM POC

```bash
cd ~/projects/crm-poc
pip install fastapi uvicorn sqlalchemy google-auth google-auth-oauthlib
uvicorn main:app --reload
# Opens at http://localhost:8000
```

---

## 10. SSH Key Setup (for GitHub and DigitalOcean server)

```bash
# Generate a new key
ssh-keygen -t ed25519 -C "mac-mini" -f ~/.ssh/id_ed25519_mac

# Add to GitHub: Settings > SSH Keys
cat ~/.ssh/id_ed25519_mac.pub

# Add to DigitalOcean server (159.223.22.165):
ssh-copy-id -i ~/.ssh/id_ed25519_mac.pub root@159.223.22.165
```

---

## 11. Claude Code Setup

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Run Claude Code
claude
# It will prompt for your Anthropic API key on first run
```

Clau (Claude Code) reads `CLAUDE.md` automatically from the project root.
Start any session from the `agentic-fleet-hub/` directory for fleet context.

---

## 12. Path Changes (Windows -> Mac)

Key paths that appear in config files and scripts:

| Windows | Mac |
| :--- | :--- |
| `C:\Users\migue\` | `~/` or `/Users/migue/` |
| `C:\Users\migue\Videos\` | `~/Videos/` |
| `C:\Users\migue\.venv312\Scripts\activate` | `~/.venv312/bin/activate` or `~/projects/music-video-tool/.venv312/bin/activate` |
| `C:\Users\migue\music-video-tool\` | `~/projects/music-video-tool/` |
| Backslashes in paths | Forward slashes |

Check and update:
- `story_tool.py` — any hardcoded Windows paths
- `app.py` — any hardcoded Windows paths
- `config.py` — video extensions, output directories
- `tracker.py` — Excel file path

---

## 13. Verification Checklist

- [ ] All repos cloned
- [ ] Python venv created and packages installed
- [ ] `python app.py` starts without errors
- [ ] `python story_tool.py` starts without errors
- [ ] YouTube OAuth working (upload test)
- [ ] Google Sheets read/write working
- [ ] Kokoro TTS working (narration test)
- [ ] Excel tracker loads correctly
- [ ] Claude Code (`claude`) starts and reads CLAUDE.md
- [ ] Fleet server starts (`npm start` in package/server)
- [ ] SSH access to 159.223.22.165 working

---

## 14. Infisical Vault Setup (recommended)

Instead of copying .env files, set up Infisical on the Mac:

```bash
brew install infisical/get-cli/infisical
infisical login
# Then use vault/agent-fetch.sh to inject secrets at runtime
```

Secrets already stored in Infisical EU:
- `RUNWAYML_API_SECRET`
- `YOUTUBE_CLIENT_SECRETS_JSON`

---

*Migration prepared by Clau -- 2026-03-14. Good luck on the other side.*
