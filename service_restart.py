#!/usr/bin/env python3
"""
Service Restart Logic: Restart fleet services after project switch.
"""

import subprocess


def restart_pocketbase() -> bool:
    """Restart PocketBase service."""
    try:
        subprocess.run(["launchctl", "stop", "fleet.pocketbase"], check=True)
        subprocess.run(["launchctl", "start", "fleet.pocketbase"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restarting PocketBase: {e}")
        return False


def restart_dispatcher() -> bool:
    """Restart dispatcher service."""
    try:
        subprocess.run(["launchctl", "stop", "fleet.dispatcher"], check=True)
        subprocess.run(["launchctl", "start", "fleet.dispatcher"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restarting dispatcher: {e}")
        return False


def restart_all_services() -> bool:
    """Restart all fleet services."""
    if not restart_pocketbase():
        return False
    if not restart_dispatcher():
        return False
    return True


if __name__ == "__main__":
    if restart_all_services():
        print("All services restarted successfully")
    else:
        print("Failed to restart services")
