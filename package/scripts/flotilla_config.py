"""flotilla_config.py: one place for every deployment-specific setting.

All engine scripts import their paths, URLs and identities from here, so a
fresh install works without editing code. Everything can be overridden with
environment variables (set them in your shell, your launchd plists, or your
secrets manager).

Layout produced by `npx create-flotilla my-fleet`:

    my-fleet/                  <- FLOTILLA_WORKSPACE (MISSION_CONTROL.md, AGENTS/, standups/)
    my-fleet/scripts/          <- FLOTILLA_RUNTIME_DIR (this file, dispatcher.py, ...)
    my-fleet/scripts/logs/     <- runtime logs and caches
    my-fleet/pocketbase/       <- PocketBase binary, pb_migrations/, pb_data/
"""

import json
import os
import shutil
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_env_file(path):
    """Load KEY=VALUE lines from scripts/flotilla.env without overriding the real environment."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(_HERE / "flotilla.env")


def _env_path(name, default):
    value = os.environ.get(name)
    return Path(os.path.expanduser(value)).resolve() if value else Path(default)


# ── Directories ──────────────────────────────────────────────────────────────
RUNTIME_DIR = _env_path("FLOTILLA_RUNTIME_DIR", _HERE)
WORKSPACE_DIR = _env_path("FLOTILLA_WORKSPACE", _HERE.parent)
# Logs, caches and per-agent working folders (scout/, gemma/, ...).
FLEET_DIR = _env_path("FLOTILLA_FLEET_DIR", RUNTIME_DIR)
LOG_DIR = FLEET_DIR / "logs"
CACHE_DIR = _env_path("FLOTILLA_CACHE_DIR", WORKSPACE_DIR / ".fleet_cache")

MISSION_CONTROL_PATH = WORKSPACE_DIR / "MISSION_CONTROL.md"
FLEET_META_PATH = WORKSPACE_DIR / "AGENTS" / "CONFIG" / "fleet_meta.json"
AGENT_COMMANDS_PATH = _env_path(
    "FLOTILLA_AGENT_COMMANDS", WORKSPACE_DIR / "AGENTS" / "CONFIG" / "agent_commands.json"
)
STANDUPS_DIR = WORKSPACE_DIR / "standups"

# ── Services ─────────────────────────────────────────────────────────────────
PB_URL = os.environ.get("FLOTILLA_PB_URL", "http://127.0.0.1:8090/api")

# GitHub mirror of the task board. Empty = GitHub sync disabled.
# Use a PRIVATE repo: issue bodies can contain task details.
GITHUB_REPO = os.environ.get("FLOTILLA_GITHUB_REPO", "")
GH_BIN = os.environ.get("FLOTILLA_GH_BIN") or shutil.which("gh") or "gh"

# Optional extra repos whose issues are imported into the board, as JSON:
#   [{"repo": "owner/name", "project": "Display name"}]
try:
    EXTRA_INBOUND_REPOS = json.loads(os.environ.get("FLOTILLA_EXTRA_INBOUND_REPOS", "[]"))
except ValueError:
    EXTRA_INBOUND_REPOS = []

# Optional cloud dashboard that receives fleet snapshots (fleet_push.py).
FLEET_SYNC_URL = os.environ.get("FLEET_SYNC_URL", "")

# Telegram bridge to the human manager. Token and chat id come from your vault.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# How agents and prompts refer to the human who approves work.
HUMAN_NAME = os.environ.get("FLOTILLA_HUMAN_NAME", "the human manager")

# ── Agents ───────────────────────────────────────────────────────────────────
HEARTBEAT_PROMPT = os.environ.get(
    "FLOTILLA_HEARTBEAT_PROMPT",
    "Run your heartbeat protocol. Read MISSION_CONTROL.md first, then follow AGENTS/RULES.md.",
)


def _which(*names):
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return names[0]


def default_agent_commands():
    """Built-in commands for the common agent CLIs. Override any of them in
    AGENTS/CONFIG/agent_commands.json (see the example in that folder)."""
    ws = str(WORKSPACE_DIR)
    prompt = HEARTBEAT_PROMPT
    return {
        "clau": [_which("claude"), "--dangerously-skip-permissions", "-p", prompt],
        "gem": [_which("gemini"), "--yolo", "-p", prompt],
        "codi": [_which("codex"), "exec", "--dangerously-bypass-approvals-and-sandbox",
                 "--skip-git-repo-check", "-C", ws, "--add-dir", str(FLEET_DIR), prompt],
        "misty": [_which("vibe"), "--workdir", ws, "--trust", "-p", prompt],
        "gemma": ["/bin/bash", str(FLEET_DIR / "gemma" / "run_heartbeat.sh")],
    }


def _expand(arg):
    return (str(arg)
            .replace("{workspace}", str(WORKSPACE_DIR))
            .replace("{fleet_dir}", str(FLEET_DIR))
            .replace("{runtime_dir}", str(RUNTIME_DIR))
            .replace("{cache_dir}", str(CACHE_DIR))
            .replace("{prompt}", HEARTBEAT_PROMPT)
            .replace("~", os.path.expanduser("~")))


def load_agent_commands():
    """Defaults merged with AGENTS/CONFIG/agent_commands.json.

    The JSON maps an agent name to its argv list. Placeholders {workspace},
    {fleet_dir}, {runtime_dir}, {cache_dir} and {prompt} are expanded. A value
    of null removes a default agent.
    """
    commands = default_agent_commands()
    if AGENT_COMMANDS_PATH.exists():
        try:
            custom = json.loads(AGENT_COMMANDS_PATH.read_text())
        except ValueError:
            custom = {}
        for name, argv in custom.items():
            if name.startswith("_"):
                continue
            if argv is None:
                commands.pop(name, None)
            else:
                commands[name] = [_expand(a) for a in argv]
    return commands


def github_repo_url(path=""):
    if not GITHUB_REPO:
        return ""
    return f"https://github.com/{GITHUB_REPO}{path}"
