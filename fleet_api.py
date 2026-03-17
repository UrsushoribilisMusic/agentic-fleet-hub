#!/usr/bin/env python3
"""
Fleet API: Endpoint for project switching.
"""

from flask import Flask, request, jsonify
import json
import os
import subprocess

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
