#!/usr/bin/env python3
"""Test script for fleet_api.py"""

import requests
import json
import time
import subprocess
import sys

def test_api():
    # Start the API server on port 5001
    print("Starting API server on port 5001...")
    proc = subprocess.Popen(
        [sys.executable, "fleet_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"FLASK_RUN_PORT": "5001"}
    )
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test switch-project endpoint
        print("Testing switch-project endpoint...")
        response = requests.post(
            "http://localhost:5001/fleet/api/switch-project",
            json={"repo_path": "/Users/miguelrodriguez/projects/agentic-fleet-hub"},
            timeout=5
        )
        print(f"Switch project response: {response.status_code}")
        print(response.text)
        
        # Test parse-mission-control endpoint
        print("\nTesting parse-mission-control endpoint...")
        response = requests.get(
            "http://localhost:5001/fleet/api/parse-mission-control",
            params={"repo_path": "/Users/miguelrodriguez/projects/agentic-fleet-hub"},
            timeout=5
        )
        print(f"Parse mission control response: {response.status_code}")
        print(response.text)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the server
        proc.terminate()
        proc.wait()
        print("\nAPI server stopped")

if __name__ == "__main__":
    test_api()
