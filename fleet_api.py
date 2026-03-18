#!/usr/bin/env python3
"""
Fleet API: Endpoint for project switching and MISSION_CONTROL.md parsing.
"""

from flask import Flask, request, jsonify
import json
import os
import subprocess
import re
from fleet_utils import get_cached_mission_control
from service_restart import restart_all_services

app = Flask(__name__)


def update_fleet_meta(repo_path: str) -> bool:
    """Update fleet_meta.json with new repo_path and set is_active field."""
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
    
    # Update is_active field in AGENTS/CONFIG/fleet_meta.json
    agents_fleet_meta_path = os.path.join(os.path.dirname(__file__), "AGENTS", "CONFIG", "fleet_meta.json")
    if os.path.exists(agents_fleet_meta_path):
        with open(agents_fleet_meta_path, "r") as f:
            agents_fleet_meta = json.load(f)
        
        # Set is_active to True for the project matching the repo_path
        repo_name = os.path.basename(repo_path)
        for project in agents_fleet_meta.get("projects", []):
            # Check if the repo_name matches the project's title or is in the docs URL
            docs_url = project.get("docs", [])
            if isinstance(docs_url, list) and len(docs_url) > 0:
                docs_url = docs_url[0]
            
            if "agentic fleet hub" in project.get("title", "").lower() or "flotilla" in project.get("title", "").lower():
                project["is_active"] = True
            else:
                project["is_active"] = False
        
        # Save updated agents_fleet_meta.json
        with open(agents_fleet_meta_path, "w") as f:
            json.dump(agents_fleet_meta, f, indent=2)
    
    return True


def parse_mission_control(repo_path: str = ".") -> dict:
    """Parse MISSION_CONTROL.md for ticket status."""
    mission_control_path = os.path.join(repo_path, "MISSION_CONTROL.md")
    
    if not os.path.exists(mission_control_path):
        return {"error": "MISSION_CONTROL.md not found"}
    
    # Use cached content if available
    cached_content = get_cached_mission_control(repo_path)
    if cached_content:
        content = cached_content
    else:
        with open(mission_control_path, "r") as f:
            content = f.read()
    
    # Parse ticket status sections
    open_tickets = []
    closed_tickets = []
    
    # Extract active project from fleet_meta.json
    active_project = None
    try:
        fleet_meta_path = os.path.expanduser("~/fleet/fleet_meta.json")
        if os.path.exists(fleet_meta_path):
            with open(fleet_meta_path, "r") as f:
                fleet_meta = json.load(f)
                active_project = fleet_meta.get("meta", {}).get("installation", {}).get("repo_path", ".")
    except Exception as e:
        app.logger.warning(f"Failed to read fleet_meta.json: {e}")
    
    # If active_project is set and different from current repo_path, use it
    if active_project and active_project != repo_path:
        mission_control_path = os.path.join(active_project, "MISSION_CONTROL.md")
        if os.path.exists(mission_control_path):
            with open(mission_control_path, "r") as f:
                content = f.read()
        else:
            app.logger.warning(f"MISSION_CONTROL.md not found at active project path: {mission_control_path}")
    
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


@app.route("/fleet/api/activate-project", methods=["POST"])
def activate_project():
    """Activate a project by title."""
    data = request.get_json()
    project_title = data.get("project_title")
    
    if not project_title:
        return jsonify({"error": "project_title is required"}), 400
    
    # Load fleet_meta.json
    agents_fleet_meta_path = os.path.join(os.path.dirname(__file__), "AGENTS", "CONFIG", "fleet_meta.json")
    
    if not os.path.exists(agents_fleet_meta_path):
        return jsonify({"error": "fleet_meta.json not found"}), 404
    
    try:
        with open(agents_fleet_meta_path, "r") as f:
            fleet_meta = json.load(f)
        
        # Find the project and set is_active
        project_found = False
        for project in fleet_meta.get("projects", []):
            if project.get("title") == project_title:
                project["is_active"] = True
                project_found = True
            else:
                project["is_active"] = False
        
        if not project_found:
            return jsonify({"error": "Project not found"}), 404
        
        # Save updated fleet_meta.json
        with open(agents_fleet_meta_path, "w") as f:
            json.dump(fleet_meta, f, indent=2)
        
        return jsonify({"success": True, "message": "Project activated successfully"}), 200
    
    except Exception as e:
        app.logger.error(f"Failed to activate project: {e}")
        return jsonify({"error": f"Failed to activate project: {str(e)}"}), 500


@app.route("/fleet/api/switch-project", methods=["POST"])
def switch_project():
    """Switch to a new project."""
    data = request.get_json()
    new_repo_path = data.get("repo_path")
    
    if not new_repo_path:
        return jsonify({"error": "repo_path is required"}), 400
    
    # Validate new project path
    # If the path is a GitHub URL, extract the repo name
    if new_repo_path.startswith("https://github.com/"):
        # Extract the repo name from the URL
        repo_path_parts = new_repo_path.split("/")
        repo_name = "/".join(repo_path_parts[-2:])
        new_repo_path = os.path.expanduser(f"~/projects/{repo_name}")
    
    # Check if the path exists
    if not os.path.exists(new_repo_path):
        return jsonify({"error": "Invalid project path: directory not found"}), 400
    
    if not os.path.exists(os.path.join(new_repo_path, "MISSION_CONTROL.md")):
        return jsonify({"error": "Invalid project path: MISSION_CONTROL.md not found"}), 400
    
    # Update fleet_meta.json
    if not update_fleet_meta(new_repo_path):
        return jsonify({"error": "Failed to update fleet_meta.json"}), 500
    
    # Restart services
    if not restart_all_services():
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
    app.run(host="0.0.0.0", port=5002)
