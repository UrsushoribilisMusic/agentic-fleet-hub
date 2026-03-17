#!/usr/bin/env python3
"""
Fleet API: Endpoint for project switching and MISSION_CONTROL.md parsing.
"""

from flask import Flask, request, jsonify
import json
import os
import subprocess
import re

app = Flask(__name__)


def update_fleet_meta(repo_path: str) -> bool:
    """Update fleet_meta.json with new repo_path."""
    fleet_meta_path = os.path.expanduser("~/fleet/fleet_meta.json")
    
    # Load existing fleet_meta.json
    if os.path.exists(fleet_meta_path):
        with open(fleet_meta_path, "r") as f:
            fleet_meta = json.load(f)
    else:
        fleet_meta = {"meta": {"installation": {}}}
    
    # Update repo_path
    fleet_meta["meta"]["installation"]["repo_path"] = repo_path
    
    # Save updated fleet_meta.json
    with open(fleet_meta_path, "w") as f:
        json.dump(fleet_meta, f, indent=2)
    
    return True


def restart_services() -> bool:
    """Restart fleet services."""
    try:
        # Restart PocketBase
        subprocess.run(["launchctl", "stop", "fleet.pocketbase"], check=True)
        subprocess.run(["launchctl", "start", "fleet.pocketbase"], check=True)
        
        # Restart dispatcher
        subprocess.run(["launchctl", "stop", "fleet.dispatcher"], check=True)
        subprocess.run(["launchctl", "start", "fleet.dispatcher"], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error restarting services: {e}")
        return False


def parse_mission_control(repo_path: str = ".") -> dict:
    """Parse MISSION_CONTROL.md for ticket status."""
    mission_control_path = os.path.join(repo_path, "MISSION_CONTROL.md")
    
    if not os.path.exists(mission_control_path):
        return {"error": "MISSION_CONTROL.md not found"}
    
    with open(mission_control_path, "r") as f:
        content = f.read()
    
    # Parse ticket status sections
    open_tickets = []
    closed_tickets = []
    
    # Extract OPEN tickets table
    open_section_match = re.search(r"### OPEN\s*\n\|\s*Ticket\s*\|\s*Description\s*\|\s*Owner\s*\|\s*Status\s*\|\s*Notes\s*\|\s*\n\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*\n((?:\|\s*\*\*#\d+\*\*\s*\|\s*.+?\s*\n)+)", content)
    
    if open_section_match:
        open_table = open_section_match.group(1)
        for line in open_table.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    ticket_id = parts[1].replace("**#", "").replace("**", "")
                    description = parts[2]
                    owner = parts[3]
                    status = parts[4]
                    open_tickets.append({
                        "id": ticket_id,
                        "description": description,
                        "owner": owner,
                        "status": status
                    })
    
    # Extract CLOSED tickets
    closed_section_match = re.search(r"### CLOSED\n([\s\S]*?)(?=\n###|\n\*\*Status:|$)", content)
    
    if closed_section_match:
        closed_list = closed_section_match.group(1)
        for line in closed_list.strip().split("\n"):
            if line.strip():
                # Handle both single tickets (#123) and ranges (#1-#6)
                match = re.match(r"- \*\*#(\d+(?:-\d+)?)\*\*\: (.+)", line)
                if match:
                    ticket_id = match.group(1)
                    description = match.group(2)
                    closed_tickets.append({
                        "id": ticket_id,
                        "description": description,
                        "status": "closed"
                    })
    
    return {
        "open": open_tickets,
        "closed": closed_tickets
    }


@app.route("/fleet/api/switch-project", methods=["POST"])
def switch_project():
    """Switch to a new project."""
    data = request.get_json()
    new_repo_path = data.get("repo_path")
    
    if not new_repo_path:
        return jsonify({"error": "repo_path is required"}), 400
    
    # Validate new project path
    if not os.path.exists(os.path.join(new_repo_path, "MISSION_CONTROL.md")):
        return jsonify({"error": "Invalid project path: MISSION_CONTROL.md not found"}), 400
    
    # Update fleet_meta.json
    if not update_fleet_meta(new_repo_path):
        return jsonify({"error": "Failed to update fleet_meta.json"}), 500
    
    # Restart services
    if not restart_services():
        return jsonify({"error": "Failed to restart services"}), 500
    
    return jsonify({"success": True, "message": "Project switched successfully"}), 200


@app.route("/fleet/api/parse-mission-control", methods=["GET"])
def get_parsed_mission_control():
    """Get parsed MISSION_CONTROL.md data."""
    repo_path = request.args.get("repo_path", ".")
    parsed_data = parse_mission_control(repo_path)
    
    if "error" in parsed_data:
        return jsonify({"error": parsed_data["error"]}), 404
    
    return jsonify(parsed_data), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
