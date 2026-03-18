#!/usr/bin/env python3
"""
Test script for project switching functionality.
"""

import json
import os
import sys
sys.path.append('.')

from fleet_api import update_fleet_meta, parse_mission_control

def test_project_switching():
    """Test the project switching functionality."""
    print("=== Testing Project Switching ===")
    
    # Test 1: Switch to music-video-tool
    print("\n1. Testing switch to music-video-tool...")
    result = update_fleet_meta('/Users/miguelrodriguez/projects/music-video-tool')
    assert result == True, "Failed to update fleet meta"
    
    # Check active projects
    with open('AGENTS/CONFIG/fleet_meta.json', 'r') as f:
        fleet_meta = json.load(f)
    
    active_projects = [p['title'] for p in fleet_meta['projects'] if p.get('is_active')]
    print(f"   Active projects: {active_projects}")
    assert 'Music Video Tool' in active_projects, "Music Video Tool should be active"
    assert len(active_projects) == 1, "Only Music Video Tool should be active"
    
    # Test 2: Switch to agentic-fleet-hub
    print("\n2. Testing switch to agentic-fleet-hub...")
    result = update_fleet_meta('/Users/miguelrodriguez/projects/agentic-fleet-hub')
    assert result == True, "Failed to update fleet meta"
    
    # Check active projects
    with open('AGENTS/CONFIG/fleet_meta.json', 'r') as f:
        fleet_meta = json.load(f)
    
    active_projects = [p['title'] for p in fleet_meta['projects'] if p.get('is_active')]
    print(f"   Active projects: {active_projects}")
    assert 'Agentic Fleet Hub (Flotilla)' in active_projects, "Agentic Fleet Hub should be active"
    assert 'Robot Ross' in active_projects, "Robot Ross should be active"
    assert len(active_projects) == 2, "Both Robot Ross and Agentic Fleet Hub should be active"
    
    # Test 3: Parse MISSION_CONTROL.md
    print("\n3. Testing MISSION_CONTROL.md parsing...")
    result = parse_mission_control()
    assert 'open' in result, "Parse result should contain 'open' key"
    assert 'closed' in result, "Parse result should contain 'closed' key"
    assert len(result['open']) > 0, "Should have open tickets"
    assert len(result['closed']) > 0, "Should have closed tickets"
    print(f"   Open tickets: {len(result['open'])}")
    print(f"   Closed tickets: {len(result['closed'])}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_project_switching()