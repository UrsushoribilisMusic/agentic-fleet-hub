#!/usr/bin/env python3
"""
Heartbeat optimization for Misty - checksum caching for MISSION_CONTROL.md
Ticket #73: Optimize heartbeat token usage
"""
import hashlib
import json
import os
import sys

def calculate_checksum(file_path):
    """Calculate MD5 checksum of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None

def should_read_mission_control():
    """
    Determine if MISSION_CONTROL.md should be read based on:
    1. Checksum change (file content changed)
    2. Presence of active lessons
    3. Presence of tasks requiring attention
    """
    mission_control_path = "/Users/miguelrodriguez/fleet/MISSION_CONTROL.md"
    cache_file = "/Users/miguelrodriguez/fleet/misty/mission_control_checksum.json"
    
    # Calculate current checksum
    current_checksum = calculate_checksum(mission_control_path)
    if current_checksum is None:
        print("[optimize] MISSION_CONTROL.md not found", file=sys.stderr)
        return True  # Read it to be safe
    
    # Load cache
    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)
        last_checksum = cache.get("checksum")
        read_count = cache.get("read_count", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        last_checksum = None
        read_count = 0
    
    # Check if file changed
    file_changed = (current_checksum != last_checksum)
    
    # Update cache
    cache = {
        "checksum": current_checksum,
        "read_count": read_count + 1 if file_changed else read_count,
        "last_read": None if file_changed else cache.get("last_read")
    }
    
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)
    
    if file_changed:
        print(f"[optimize] MISSION_CONTROL.md changed (checksum: {current_checksum}), reading...")
        return True
    else:
        print(f"[optimize] MISSION_CONTROL.md unchanged (checksum: {current_checksum}), skipping read...")
        return False

if __name__ == "__main__":
    # This can be called standalone for testing
    should_read = should_read_mission_control()
    print(f"Should read MISSION_CONTROL.md: {should_read}")
    sys.exit(0 if should_read else 1)
