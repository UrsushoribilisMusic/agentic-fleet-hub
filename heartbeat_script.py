#!/usr/bin/env python3
"""
Optimized Heartbeat Script: Combines API calls and uses cached MISSION_CONTROL.md.
"""

import os
import sys
import requests
from fleet_utils import cache_mission_control, has_tasks_assigned


def post_heartbeat(agent: str, status: str) -> dict:
    """Post heartbeat status to PocketBase."""
    url = "http://localhost:8090/api/collections/heartbeats/records"
    payload = {"agent": agent, "status": status}
    response = requests.post(url, json=payload)
    return response.json()


def get_tasks(agent: str) -> list:
    """Get tasks assigned to the agent."""
    url = f"http://localhost:8090/api/collections/tasks/records?filter=assigned_agent=\"{agent}\"&status=\"todo\""
    response = requests.get(url)
    return response.json().get("items", [])


def get_lessons() -> list:
    """Get active lessons."""
    url = "http://localhost:8090/api/collections/lessons/records?filter=status=\"active\""
    response = requests.get(url)
    return response.json().get("items", [])


def optimized_heartbeat(agent: str = "misty"):
    """Run optimized heartbeat protocol."""
    print(f"Starting optimized heartbeat for {agent}...")

    # Step 1: Post working heartbeat
    post_heartbeat(agent, "working")

    # Step 2: Cache MISSION_CONTROL.md
    cache_result = cache_mission_control()
    if cache_result["cached"]:
        print("Using cached MISSION_CONTROL.md")
    else:
        print("MISSION_CONTROL.md updated, cached new version")

    # Step 3: Check for tasks
    tasks = get_tasks(agent)
    if tasks:
        print(f"Tasks assigned: {len(tasks)}")
        # If tasks exist, proceed with full protocol
        lessons = get_lessons()
        print(f"Active lessons: {len(lessons)}")
    else:
        print("No tasks assigned, skipping lessons")

    # Step 4: Post idle heartbeat
    post_heartbeat(agent, "idle")
    print("Heartbeat completed")


if __name__ == "__main__":
    optimized_heartbeat()
