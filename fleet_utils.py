#!/usr/bin/env python3
"""
Fleet Utilities: Checksum and caching logic for MISSION_CONTROL.md.
"""

import hashlib
import json
import os
from pathlib import Path


def calculate_checksum(file_path: str) -> str:
    """Calculate the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def cache_mission_control(repo_path: str = ".") -> dict:
    """Cache MISSION_CONTROL.md if checksum has changed."""
    mission_control_path = os.path.join(repo_path, "MISSION_CONTROL.md")
    cache_dir = os.path.join(repo_path, ".fleet_cache")
    cache_file = os.path.join(cache_dir, "mission_control_cache.json")

    # Ensure cache directory exists
    Path(cache_dir).mkdir(exist_ok=True)

    # Calculate current checksum
    current_checksum = calculate_checksum(mission_control_path)

    # Load or create cache
    cache = {"checksum": "", "content": ""}
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)

    # Update cache if checksum has changed
    if cache["checksum"] != current_checksum:
        with open(mission_control_path, "r") as f:
            cache["content"] = f.read()
        cache["checksum"] = current_checksum
        with open(cache_file, "w") as f:
            json.dump(cache, f)
        return {"cached": False, "content": cache["content"]}
    else:
        return {"cached": True, "content": cache["content"]}


def get_cached_mission_control(repo_path: str = ".") -> str:
    """Get cached MISSION_CONTROL.md content if available."""
    cache_dir = os.path.join(repo_path, ".fleet_cache")
    cache_file = os.path.join(cache_dir, "mission_control_cache.json")

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
        return cache["content"]
    return ""


def has_tasks_assigned(agent_name: str = "misty") -> bool:
    """Check if the agent has any tasks assigned."""
    # Placeholder: Replace with actual API call or logic
    # For now, return False to simulate no tasks
    return False
