#!/usr/bin/env python3
"""
Fleet Sync — bi-directional sync between MISSION_CONTROL.md and PocketBase.
Treats the Markdown table as a live interface.
"""

import os
import re
import requests
import json
from datetime import datetime

PB_URL = "http://127.0.0.1:8090/api"
MC_PATH = "/Users/miguelrodriguez/projects/agentic-fleet-hub/MISSION_CONTROL.md"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_pb_tasks():
    try:
        r = requests.get(f"{PB_URL}/collections/tasks/records", params={"perPage": 100})
        return r.json().get("items", [])
    except Exception as e:
        log(f"PB Fetch Error: {e}")
        return []

def delete_pb_task(task_id):
    try:
        requests.delete(f"{PB_URL}/collections/tasks/records/{task_id}")
    except Exception as e:
        log(f"PB Delete Error: {e}")

def create_pb_task(data):
    try:
        r = requests.post(f"{PB_URL}/collections/tasks/records", json=data)
        return r.json().get("id")
    except Exception as e:
        log(f"PB Create Error: {e}")
        return None

def parse_mc_table(content):
    """Extracts rows from the OPEN table in MISSION_CONTROL.md."""
    match = re.search(r"### OPEN\n\| Ticket \| Description \| Owner \| Status \| Notes \|\n\| :--- \| :--- \| :--- \| :--- \| :--- \|\n(.*?)(?=\n\n|\Z|\*\*)", content, re.DOTALL)
    if not match:
        return []
    
    rows = []
    table_content = match.group(1).strip()
    for line in table_content.split('\n'):
        if line.strip().startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 5:
                ticket_id_match = re.search(r"#(\d+)", parts[0])
                if ticket_id_match:
                    ticket_num = ticket_id_match.group(1)
                    rows.append({
                        "num": ticket_num,
                        "title": parts[1],
                        "owner": parts[2].lower(),
                        "status": parts[3],
                        "notes": parts[4],
                        "raw_line": line
                    })
    return rows

def sync():
    if not os.path.exists(MC_PATH):
        log(f"MC not found at {MC_PATH}")
        return

    with open(MC_PATH, 'r') as f:
        content = f.read()

    mc_tasks = parse_mc_table(content)
    pb_tasks = get_pb_tasks()
    
    pb_map = {}
    for t in pb_tasks:
        # Match "#84" anywhere in the title
        match = re.search(r"#(\d+)", t['title'])
        if match:
            num = match.group(1)
            # If duplicates exist, keep the one with the more advanced status or latest updated
            if num not in pb_map:
                pb_map[num] = t
            else:
                log(f"Found duplicate task for #{num} in PocketBase. Cleaning up...")
                delete_pb_task(t['id'])

    updated_content = content
    changes_made = False

    for mc in mc_tasks:
        pb = pb_map.get(mc['num'])
        
        if not pb:
            log(f"Creating Task #{mc['num']} in PocketBase")
            create_pb_task({
                "title": f"#{mc['num']}: {mc['title']}",
                "assigned_agent": mc['owner'],
                "status": mc['status'] if mc['status'] in ["todo", "in_progress", "peer_review", "backlog", "approved", "closed"] else "todo",
                "description": mc['notes']
            })
            changes_made = True
        else:
            # Sync PB -> MD (Status and Notes)
            if pb['status'] != mc['status'] or pb['description'] != mc['notes']:
                log(f"Syncing PB -> MC for Task #{mc['num']} (Status: {mc['status']} -> {pb['status']})")
                new_row = f"| **#{mc['num']}** | {mc['title']} | {mc['owner'].capitalize()} | {pb['status']} | {pb['description']} |"
                updated_content = updated_content.replace(mc['raw_line'], new_row)
                changes_made = True

    if changes_made:
        with open(MC_PATH, 'w') as f:
            f.write(updated_content)
        log("MISSION_CONTROL.md updated.")

if __name__ == "__main__":
    sync()
