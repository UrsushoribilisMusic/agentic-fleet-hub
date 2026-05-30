#!/usr/bin/env python3
"""
QW-001: Standup Parser
Parse all standup markdown files into structured JSON dataset.

Input: ~/projects/agentic-fleet-hub/standups/*.md
Output: ~/fleet/analytics/standup_data.json
"""

import os
import re
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
STANDUPS_DIR = Path("/Users/miguelrodriguez/projects/agentic-fleet-hub/standups")
OUTPUT_FILE = Path("/Users/miguelrodriguez/fleet/analytics/standup_data.json")

# Agent names
AGENTS = ["clau", "codi", "gem", "misty", "gemma", "tcr_scout"]

# Project prefixes
PROJECT_PREFIXES = {
    "PC": "PrivateCore",
    "SC": "SiliconOracle", 
    "CR": "Classical Remix",
    "RT": "ReelTales",
    "fleet": "fleet",
    "QW": "QW Analytics",
}

def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from filename like '2026-03-10.md' or '2026-03-16-misty.md'"""
    match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def extract_agent_from_filename(filename: str) -> Optional[str]:
    """Extract agent name from filename like '2026-03-16-misty.md'"""
    # Handle hyphenated dates: 2026-05-17-clau-rt001.md
    match = re.match(r'^\d{4}-\d{2}-\d{2}-([a-z_]+)', filename)
    if match:
        agent = match.group(1)
        # Handle cases like "clau-rt001" - take first part
        agent = agent.split('-')[0]
        if agent in AGENTS:
            return agent
    return None

def extract_ticket_ids(text: str) -> List[str]:
    """Extract all ticket IDs from text"""
    # Pattern: [PC-001], PC-001, #123, SC-001, etc.
    patterns = [
        r'\[([A-Z]{2,3}-\d+)\]',      # [PC-001]
        r'(?<![\w-])([A-Z]{2,3}-\d+)(?![\w-])',  # PC-001 (not part of longer word)
        r'(?<!\/)(#\d+)(?!\/)',      # #123 (not in ### or #####)
    ]
    ticket_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match and match not in ticket_ids:
                ticket_ids.append(match)
    return ticket_ids

def extract_project_prefix(ticket_id: str) -> str:
    """Extract project prefix from ticket ID"""
    if ticket_id.startswith("#"):
        return "other"
    for prefix in PROJECT_PREFIXES.keys():
        if ticket_id.startswith(prefix):
            return prefix
    return "other"

def find_agent_name_in_content(content: str) -> Optional[str]:
    """Find agent name in content (e.g., '# Misty (Mistral Vibe) — 2026-05-30')"""
    # Pattern: # Agent Name
    match = re.search(r'^#\s*([A-Z][a-z]+)', content, re.MULTILINE)
    if match:
        agent = match.group(1).lower()
        if agent in AGENTS:
            return agent
    # Pattern: ## Agent Name
    match = re.search(r'^##\s*([A-Z][a-z]+)', content, re.MULTILINE)
    if match:
        agent = match.group(1).lower()
        if agent in AGENTS:
            return agent
    return None

def find_agent_name_from_header(content: str) -> Optional[str]:
    """Find agent name from various header patterns"""
    # Pattern: # Misty — 2026-05-30
    # Pattern: # Misty (Mistral Vibe) — 2026-05-30
    # Pattern: # Misty (Mistral Vibe) Standup — 2026-05-30
    match = re.search(r'^#\s*([A-Z][a-z]+)', content, re.MULTILINE)
    if match:
        agent = match.group(1).lower()
        if agent in AGENTS:
            return agent
    return None

def extract_tasks_from_section(content: str, section_pattern: str) -> List[Dict[str, str]]:
    """Extract tasks from a section like '## Done' or '## Accomplishments'"""
    tasks = []
    section_match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)
    if not section_match:
        return tasks
    
    section_content = section_match.group(1)
    
    for line in section_content.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip headers and separators
        if line.startswith('##') or line.startswith('---') or line.startswith('**') and ':' not in line:
            continue
        
        # Extract ticket IDs
        ticket_ids = extract_ticket_ids(line)
        
        # Extract title
        # Pattern: - **Ticket #1**: Description
        # Pattern: - [PC-001] Description
        # Pattern: - PC-001: Description
        # Pattern: *PC-001* Description
        
        title = line
        # Remove markdown bold/italic
        title = re.sub(r'\*\*([^\*]+)\*\*', r'\1', title)
        title = re.sub(r'\*([^\*]+)\*', r'\1', title)
        # Remove ticket IDs from beginning
        for tid in ticket_ids:
            title = title.replace(tid, '').replace(f'[{tid}]', '').strip()
        title = re.sub(r'^[\-\*\s]+', '', title).strip()
        
        for ticket_id in ticket_ids:
            project = extract_project_prefix(ticket_id)
            tasks.append({
                "id": ticket_id,
                "title": title if title else "",
                "project": project
            })
    
    return tasks

def extract_blockers(content: str) -> List[str]:
    """Extract blockers from content"""
    blockers = []
    
    # Find Blockers section
    section_pattern = r'##?\s*Blocker[s]?\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\Z)'
    section_match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)
    if section_match:
        section_content = section_match.group(1)
        for line in section_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*') and not line.startswith('**'):
                continue
            # Extract text after - or *
            line = re.sub(r'^[\-\*\s]+', '', line).strip()
            if line:
                blockers.append(line)
    
    # Also look for inline "Blockers:" mentions
    inline_pattern = r'Blocker[s]?\s*[:=]\s*(.+?)(?=\n\n|\n##|\Z)'
    inline_matches = re.findall(inline_pattern, content, re.DOTALL | re.IGNORECASE)
    for match in inline_matches:
        items = [item.strip() for item in match.split(',') if item.strip()]
        blockers.extend(items)
    
    return blockers

def extract_peer_reviews(content: str) -> List[Dict[str, str]]:
    """Extract peer reviews from content"""
    reviews = []
    
    # Find Peer Review section
    section_pattern = r'##?\s*Peer Review[s]?\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\Z)'
    section_match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)
    if section_match:
        section_content = section_match.group(1)
        for line in section_content.split('\n'):
            line = line.strip().lower()
            if 'approved' in line or 'reviewed' in line:
                ticket_ids = extract_ticket_ids(line)
                for ticket_id in ticket_ids:
                    reviews.append({
                        "ticket_id": ticket_id,
                        "verdict": "approved"
                    })
    
    return reviews

def extract_session_count(content: str) -> int:
    """Extract session count from content"""
    # Pattern: Sessions: 87
    # Pattern: session_count: 5
    # Pattern: Session: 1
    match = re.search(r'[Ss]ession[s]?\s*[:=]\s*(\d+)', content)
    if match:
        return int(match.group(1))
    return 0

def parse_file(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a single standup file and return entries"""
    date = extract_date_from_filename(filepath.name)
    if not date:
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine agent from filename
    agent = extract_agent_from_filename(filepath.name)
    
    # If no agent in filename, try to find from content
    if not agent:
        agent = find_agent_name_from_header(content)
    
    # If still no agent, this might be a multi-agent file
    if not agent:
        # Check if this is a multi-agent file with sections
        agent_sections = re.findall(r'^##\s+([A-Z][a-z]+)\s*$', content, re.MULTILINE)
        if agent_sections:
            # This is a multi-agent file, parse each section
            entries = []
            for agent_name in agent_sections:
                if agent_name.lower() in AGENTS:
                    # Extract content for this agent
                    agent_pattern = rf'##\s*{agent_name}\s*$\s*(.*?)(?=\n##|\n---|\Z)'
                    agent_match = re.search(agent_pattern, content, re.DOTALL | re.IGNORECASE)
                    if agent_match:
                        agent_content = agent_match.group(1)
                        entry = parse_agent_entry(date, agent_name.lower(), agent_content)
                        if entry:
                            entries.append(entry)
            return entries
        
        # No agent sections, treat as a general standup (skip or assign to all)
        return []
    
    # Single agent file
    entry = parse_agent_entry(date, agent, content)
    if entry:
        return [entry]
    return []

def parse_agent_entry(date: str, agent: str, content: str) -> Dict[str, Any]:
    """Parse content for a single agent"""
    entry = {
        "date": date,
        "agent": agent,
        "tasks_completed": [],
        "peer_reviews": [],
        "blockers": [],
        "notes_text": "",
        "session_count": 0
    }
    
    # Extract session count
    entry["session_count"] = extract_session_count(content)
    
    # Extract tasks from various sections
    sections = [
        r'##?\s*Done\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\n\n\Z)',
        r'##?\s*Accomplishment[s]?\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\n\n\Z)',
        r'##?\s*Done Today\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\n\n\Z)',
        r'##?\s*Completed\s*[:\-]*\s*$\s*(.*?)(?=\n##|\n---|\n\n\Z)',
    ]
    
    for section_pattern in sections:
        tasks = extract_tasks_from_section(content, section_pattern)
        entry["tasks_completed"].extend(tasks)
    
    # Also extract from bullet points anywhere in content
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('- ') or line.startswith('* ') or line.startswith('  - ') or line.startswith('  * '):
            # Check if it contains a ticket ID
            ticket_ids = extract_ticket_ids(line)
            if ticket_ids:
                # Check if already captured
                existing_ids = [t["id"] for t in entry["tasks_completed"]]
                for ticket_id in ticket_ids:
                    if ticket_id not in existing_ids:
                        project = extract_project_prefix(ticket_id)
                        # Extract title
                        title = re.sub(r'^[\-\*\s\[]+', '', line)
                        for tid in ticket_ids:
                            title = title.replace(tid, '').replace(f'[{tid}]', '').replace(f'({tid})', '')
                        title = title.strip()
                        entry["tasks_completed"].append({
                            "id": ticket_id,
                            "title": title[:200] if title else "",
                            "project": project
                        })
    
    # Extract peer reviews
    entry["peer_reviews"] = extract_peer_reviews(content)
    
    # Extract blockers
    entry["blockers"] = extract_blockers(content)
    
    # Extract notes - take first 10000 chars of content (excluding headers)
    notes_lines = []
    for line in content.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            notes_lines.append(line.strip())
    entry["notes_text"] = ' '.join(notes_lines)[:10000]
    
    return entry

def parse_all_standups() -> List[Dict[str, Any]]:
    """Parse all standup files"""
    all_entries = []
    
    md_files = list(STANDUPS_DIR.glob("*.md"))
    print(f"Found {len(md_files)} markdown files")
    
    for filepath in md_files:
        try:
            entries = parse_file(filepath)
            all_entries.extend(entries)
        except Exception as e:
            print(f"Error parsing {filepath.name}: {e}")
    
    return all_entries

def deduplicate_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate entries by (date, agent) and merge data"""
    seen = {}
    for entry in entries:
        key = (entry["date"], entry["agent"])
        if key in seen:
            # Merge
            existing = seen[key]
            existing["tasks_completed"].extend(entry["tasks_completed"])
            existing["peer_reviews"].extend(entry["peer_reviews"])
            existing["blockers"].extend(entry["blockers"])
            if entry["notes_text"]:
                existing["notes_text"] += " " + entry["notes_text"]
            existing["session_count"] += entry["session_count"]
        else:
            seen[key] = entry
    
    # Remove duplicates in tasks_completed
    for key, entry in seen.items():
        unique_tasks = []
        seen_ids = set()
        for task in entry["tasks_completed"]:
            if task["id"] not in seen_ids:
                seen_ids.add(task["id"])
                unique_tasks.append(task)
        entry["tasks_completed"] = unique_tasks
    
    return list(seen.values())

def fetch_pocketbase_timestamps() -> Dict[str, Dict[str, str]]:
    """Fetch ticket timestamps from PocketBase"""
    import requests
    
    timestamps = {}
    try:
        # Try to read from local snapshot first
        snapshot_path = Path("/Users/miguelrodriguez/fleet/codi/pb_snapshot.json")
        if snapshot_path.exists():
            with open(snapshot_path, 'r') as f:
                snapshot = json.load(f)
                for task in snapshot.get("items", []):
                    task_id = task.get("id")
                    if task_id:
                        timestamps[task_id] = {
                            "created": task.get("created", ""),
                            "updated": task.get("updated", ""),
                            "status": task.get("status", ""),
                            "title": task.get("title", "")
                        }
        else:
            # Fallback: query PocketBase directly
            response = requests.get(
                "http://localhost:8090/api/collections/tasks/records",
                params={"perPage": 500},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for task in data.get("items", []):
                    task_id = task.get("id")
                    if task_id:
                        timestamps[task_id] = {
                            "created": task.get("created", ""),
                            "updated": task.get("updated", ""),
                            "status": task.get("status", ""),
                            "title": task.get("title", "")
                        }
    except Exception as e:
        print(f"Warning: Could not fetch PocketBase timestamps: {e}")
    
    return timestamps

def enrich_entries(entries: List[Dict[str, Any]], timestamps: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """Add timestamp information to entries"""
    for entry in entries:
        for task in entry["tasks_completed"]:
            task_id = task["id"]
            if task_id in timestamps:
                task["created"] = timestamps[task_id].get("created", "")
                task["updated"] = timestamps[task_id].get("updated", "")
                task["status"] = timestamps[task_id].get("status", "")
                if not task.get("title"):
                    task["title"] = timestamps[task_id].get("title", "")
    return entries

def main():
    print("=" * 60)
    print("QW-001 Standup Parser")
    print("=" * 60)
    
    # Parse all standup files
    print("\n[1/4] Parsing standup files...")
    entries = parse_all_standups()
    print(f"    → Parsed {len(entries)} entries")
    
    # Deduplicate
    print("\n[2/4] Deduplicating entries...")
    entries = deduplicate_entries(entries)
    print(f"    → After deduplication: {len(entries)} entries")
    
    # Fetch PocketBase timestamps
    print("\n[3/4] Fetching PocketBase timestamps...")
    timestamps = fetch_pocketbase_timestamps()
    print(f"    → Retrieved timestamps for {len(timestamps)} tasks")
    
    # Enrich entries
    print("\n[4/4] Enriching entries with timestamps...")
    entries = enrich_entries(entries, timestamps)
    
    # Sort by date and agent
    entries.sort(key=lambda x: (x["date"], x["agent"]))
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Output written to {OUTPUT_FILE}")
    
    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    
    if not entries:
        print("ERROR: No entries found!")
        return
    
    print(f"Total entries: {len(entries)}")
    print(f"Date range: {entries[0]['date']} to {entries[-1]['date']}")
    
    agents_found = set(e["agent"] for e in entries)
    print(f"Agents: {', '.join(sorted(agents_found))}")
    
    total_tasks = sum(len(e["tasks_completed"]) for e in entries)
    print(f"Total tasks: {total_tasks}")
    
    total_peer_reviews = sum(len(e["peer_reviews"]) for e in entries)
    print(f"Total peer reviews: {total_peer_reviews}")
    
    total_blockers = sum(len(e["blockers"]) for e in entries)
    print(f"Total blockers: {total_blockers}")
    
    total_sessions = sum(e["session_count"] for e in entries)
    print(f"Total sessions: {total_sessions}")
    
    # Check for issues
    print("\n" + "-" * 60)
    print("POTENTIAL ISSUES")
    print("-" * 60)
    
    empty_task_count = sum(1 for e in entries if len(e["tasks_completed"]) == 0)
    print(f"Entries with no tasks: {empty_task_count}")
    
    empty_agent_count = sum(1 for e in entries if not e["agent"])
    print(f"Entries with no agent: {empty_agent_count}")
    
    print("\n" + "=" * 60)
    print("QW-001 COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
