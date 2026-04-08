#!/usr/bin/env python3
"""
fleet/heartbeat_check.py
------------------------
Lightweight startup gate for fleet agents.

Run this immediately after `git pull`, before reading any context files.
Checks whether MISSION_CONTROL.md or inbox.json have changed since the
last wakeup, and whether those changes are relevant to this agent.

Also reads AGENTS/CONFIG/fleet_meta.json to find all active projects and
watches their MISSION_CONTROL.md files if they exist.

Exit codes:
  0  -- relevant changes detected, proceed with full startup
  1  -- nothing relevant, skip context loading and go idle

Usage:
    python fleet/heartbeat_check.py --agent clau
    python fleet/heartbeat_check.py --agent misty
    python fleet/heartbeat_check.py --agent gem
    python fleet/heartbeat_check.py --agent codi

Run from the repo root. Cache is stored in .fleet_cache/ (gitignored).
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

# Hub files always watched
HUB_WATCHED = [
    "MISSION_CONTROL.md",
    "AGENTS/MESSAGES/inbox.json",
    "AGENTS/CONFIG/fleet_meta.json",
]

FLEET_META = os.path.join("AGENTS", "CONFIG", "fleet_meta.json")

# Aliases used to match this agent in ticket tables and inbox messages
AGENT_ALIASES_DEFAULT = {
    "clau":  ["clau", "claude"],
    "misty": ["misty", "mistral"],
    "gem":   ["gem", "gemini"],
    "codi":  ["codi", "codex"],
}


# Force a full wakeup/heartbeat every N hours even if no files changed.
# This ensures the dashboard timeline shows activity and agents stay "alive".
FORCE_HEARTBEAT_INTERVAL_SEC = 4 * 3600  # 4 hours

# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_meta(repo: str) -> Optional[dict]:
    meta_path = os.path.join(repo, FLEET_META)
    try:
        with open(meta_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _get_agent_aliases(agent_key: str, meta: Optional[dict]) -> List[str]:
    """Derive aliases from fleet_meta.json or fall back to defaults."""
    if meta and "team" in meta:
        for member in meta["team"]:
            if member.get("heartbeatKey") == agent_key:
                aliases = [agent_key]
                name = member.get("name", "")
                if name and name.lower() != agent_key.lower():
                    aliases.append(name.lower())
                return aliases
    return AGENT_ALIASES_DEFAULT.get(agent_key, [agent_key])


def _checksum(path: str) -> Optional[str]:
    """SHA-256 of a file, or None if the file does not exist."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


def _active_project_mcs(repo: str, meta: Optional[dict]) -> List[str]:
    """
    Return absolute paths to all active projects' MISSION_CONTROL.md files.
    """
    if not meta:
        return []

    mcs = []
    for p in meta.get("projects", []):
        if not p.get("is_active"):
            continue
        rp = p.get("repo_path", ".").strip()
        if rp in (".", ""):
            continue  # hub itself — already in HUB_WATCHED
        candidate = os.path.normpath(os.path.join(repo, rp, "MISSION_CONTROL.md"))
        if os.path.exists(candidate):
            mcs.append(candidate)
    return mcs


def _load_cache(cache_path: str) -> dict:
    try:
        with open(cache_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache_path: str, data: dict):
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)


# ── Relevance checks (pure Python — zero LLM tokens) ──────────────────────────

def _ticket_for_agent(mc_path: str, aliases: list) -> bool:
    """Return True if MISSION_CONTROL.md has an OPEN ticket for this agent."""
    try:
        with open(mc_path) as f:
            content = f.read()
        # Extract only the OPEN section (stop at next ### or end of file)
        match = re.search(r"### OPEN.*?(?=\n###|\Z)", content, re.DOTALL | re.IGNORECASE)
        if not match:
            return False
        open_section = match.group()
        for alias in aliases:
            if alias.lower() in open_section.lower():
                return True
        return False
    except Exception:
        return True  # safe default: assume relevant if unreadable


def _inbox_for_agent(inbox_path: str, aliases: list) -> bool:
    """Return True if inbox.json has an unread message addressed to this agent."""
    try:
        with open(inbox_path) as f:
            messages = json.load(f)
        for msg in messages:
            if msg.get("status") == "unread":
                to_field = str(msg.get("to", "")).lower()
                for alias in aliases:
                    if alias.lower() in to_field:
                        return True
        return False
    except Exception:
        return True  # safe default


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fleet heartbeat startup gate")
    parser.add_argument("--agent", required=True, choices=AGENT_ALIASES_DEFAULT.keys(),
                        help="Agent identity (clau / misty / gem / codi)")
    parser.add_argument("--repo", default=".",
                        help="Repo root path (default: current directory)")
    args = parser.parse_args()

    repo    = os.path.abspath(args.repo)
    meta    = _load_meta(repo)
    aliases = _get_agent_aliases(args.agent, meta)
    cache_path = os.path.join(repo, ".fleet_cache", f"heartbeat_{args.agent}.json")

    # ── Build watched file list ────────────────────────────────────────────────
    # Always watch hub files; also watch all active projects' MCs
    watched = list(HUB_WATCHED)  # relative paths for hub files
    proj_mcs = _active_project_mcs(repo, meta)
    for mc in proj_mcs:
        watched.append(mc)

    # ── Step 1: calculate current checksums ───────────────────────────────────
    def _resolve(f):
        return f if os.path.isabs(f) else os.path.join(repo, f)

    current = {f: _checksum(_resolve(f)) for f in watched}

    # ── Step 2: compare to previous run ───────────────────────────────────────
    cache    = _load_cache(cache_path)
    previous = cache.get("checksums", {})
    changed  = [f for f in watched if current.get(f) != previous.get(f)]

    # Check for forced heartbeat based on time
    last_checked_str = cache.get("last_checked")
    force_wakeup = False
    if last_checked_str:
        try:
            last_checked = datetime.fromisoformat(last_checked_str)
            if last_checked.tzinfo is None:
                last_checked = last_checked.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last_checked).total_seconds()
            if age > FORCE_HEARTBEAT_INTERVAL_SEC:
                force_wakeup = True
        except:
            force_wakeup = True
    else:
        force_wakeup = True # First run

    if not changed and not force_wakeup:
        print(f"[heartbeat:{args.agent}] No changes. Going idle.")
        _save_cache(cache_path, {
            "checksums": current,
            "last_checked": last_checked_str if last_checked_str else datetime.now(timezone.utc).isoformat(),
            "last_result": "idle",
            "aliases": aliases,
        })
        sys.exit(1)

    if force_wakeup and not changed:
        print(f"[heartbeat:{args.agent}] Forced heartbeat wakeup (interval exceeded).")
    elif changed:
        print(f"[heartbeat:{args.agent}] Changed: {', '.join(changed)}")

    # ── Step 3: check relevance for this agent ────────────────────────────────
    reasons = []

    hub_mc_abs    = os.path.join(repo, "MISSION_CONTROL.md")
    hub_inbox_abs = os.path.join(repo, "AGENTS", "MESSAGES", "inbox.json")

    # If ANY watched file changed (even fleet_meta.json), check ALL active MCs and Inbox
    if os.path.exists(hub_mc_abs):
        if _ticket_for_agent(hub_mc_abs, aliases):
            reasons.append("open ticket assigned to you in hub MC")

    for mc_abs in proj_mcs:
        if os.path.exists(mc_abs):
            if _ticket_for_agent(mc_abs, aliases):
                # Get the project title if possible for the reason string
                proj_title = "active project"
                if meta:
                    for p in meta.get("projects", []):
                        rp = p.get("repo_path", ".").strip()
                        if rp and mc_abs.endswith(os.path.join(rp, "MISSION_CONTROL.md")):
                            proj_title = p.get("title", "active project")
                            break
                reasons.append(f"open ticket assigned to you in {proj_title} MC")

    if os.path.exists(hub_inbox_abs):
        if _inbox_for_agent(hub_inbox_abs, aliases):
            reasons.append("unread inbox message for you")

    # ── Step 4: save cache and exit ───────────────────────────────────────────
    _save_cache(cache_path, {
        "checksums": current,
        "last_checked": datetime.now(timezone.utc).isoformat(),
        "last_result": "proceed" if reasons else "idle",
        "changed_files": changed,
        "reasons": reasons,
        "watched_mcs": proj_mcs,
        "aliases": aliases,
    })

    if reasons:
        print(f"[heartbeat:{args.agent}] Action needed (aliases: {', '.join(aliases)}): {'; '.join(reasons)}")
        sys.exit(0)
    else:
        print(f"[heartbeat:{args.agent}] Changes detected but nothing for {args.agent} (aliases: {', '.join(aliases)}). Going idle.")
        sys.exit(1)


if __name__ == "__main__":
    main()
