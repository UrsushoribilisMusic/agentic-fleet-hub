#!/usr/bin/env python3
"""
QW-001: Standup Parser - FIXED VERSION
Parse all standup markdown files into structured JSON dataset.

Input: ~/projects/agentic-fleet-hub/standups/*.md
Output: ~/fleet/analytics/standup_data.json

Fixes:
- Handles multi-agent files with complex section headers (e.g., "## Clau (Claude Code)")
- Handles all filename patterns (2026-03-16.md, 2026-03-16-misty.md, 2026-05-17-clau-rt001.md, etc.)
- Better ticket ID extraction from content
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

# Agent display names for matching
AGENT_DISPLAY_NAMES = {
    "clau": ["Clau", "Claude Code"],
    "codi": ["Codi", "Codex"],
    "gem": ["Gem", "Gemini CLI"],
    "misty": ["Misty", "Mistral Vibe"],
    "gemma": ["Gemma", "gemma"],
    "tcr_scout": ["tcr_scout", "TCR-Scout", "TCR Scout"],
}

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
    """Extract date from filename like '2026-03-10.md' or '2026-03-16-misty.md' or '2026-05-17-clau-rt001.md'"""
    # Match date at the beginning: 2026-03-16
    match = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def extract_agent_from_filename(filename: str) -> Optional[str]:
    """Extract agent name from filename like '2026-03-16-misty.md' or '2026-05-17-clau-rt001.md'"""
    # Handle hyphenated patterns: 2026-05-17-clau-rt001.md
    match = re.match(r'^\d{4}-\d{2}-\d{2}-([a-z_]+)', filename)
    if match:
        agent_part = match.group(1)
        # Take first part before any additional hyphens
        agent = agent_part.split('-')[0]
        if agent in AGENTS:
            return agent
    return None

def match_agent_in_text(text: str) -> Optional[str]:
    """Match agent name in text, handling display names"""
    text_lower = text.lower()
    for agent, display_names in AGENT_DISPLAY_NAMES.items():
        for display_name in display_names:
            if display_name.lower() in text_lower:
                return agent
    return None

def extract_ticket_ids(text: str) -> List[str]:
    """Extract all ticket IDs from text"""
    ticket_ids = []
    
    # Pattern 1: [PC-001], [SC-001], etc.
    matches = re.findall(r'\[([A-Z]{2,3}-\d+)\]', text)
    ticket_ids.extend(matches)
    
    # Pattern 2: PC-001, SC-001, etc. (not in brackets)
    # Use word boundaries to avoid matching partial words
    matches = re.findall(r'(?<![\w-])([A-Z]{2,3}-\d+)(?![\w-])', text)
    ticket_ids.extend(matches)
    
    # Pattern 3: #123 (GitHub issue numbers)
    # Exclude markdown headers (###, ####, etc.)
    matches = re.findall(r'(?<!\/#)(#\d+)(?!\/#)', text)
    ticket_ids.extend(matches)
    
    # Deduplicate while preserving order
    seen = set()
    unique_tickets = []
    for tid in ticket_ids:
        if tid not in seen:
            seen.add(tid)
            unique_tickets.append(tid)
    
    return unique_tickets

def extract_project_prefix(ticket_id: str) -> str:
    """Extract project prefix from ticket ID"""
    if ticket_id.startswith("#"):
        return "other"
    for prefix in PROJECT_PREFIXES.keys():
        if ticket_id.startswith(prefix):
            return prefix
    return "other"

def extract_session_count(content: str) -> int:
    """Extract session count from content"""
    # Pattern: Sessions: 87
    # Pattern: session_count: 5
    # Pattern: Session: 1
    match = re.search(r'[Ss]ession[s]?\s*[:=]\s*(\d+)', content)
    if match:
        return int(match.group(1))
    return 0

def find_agent_sections(content: str) -> List[Dict[str, str]]:
    """Find all agent sections in a multi-agent standup file"""
    sections = []
    
    lines = content.split('\n')
    current_section = None
    current_agent = None
    section_start = 0
    
    for i, line in enumerate(lines):
        # Check if this line is a ## header
        if line.strip().startswith('##'):
            # Extract the header text
            header_match = re.match(r'^##\s+(.+?)\s*$', line.strip())
            if header_match:
                header_text = header_match.group(1)
                
                # Check if this header contains an agent name
                agent = extract_agent_from_section_header(header_text)
                
                if agent:
                    # This is an agent section
                    if current_section is not None:
                        # Save previous section
                        section_content = '\n'.join(lines[section_start:i])
                        sections.append({
                            'header': current_section,
                            'agent': current_agent,
                            'content': section_content
                        })
                    
                    current_section = header_text
                    current_agent = agent
                    section_start = i + 1
                else:
                    # This is a non-agent section (like "## Blockers")
                    # If we're in an agent section, continue it
                    if current_section is not None:
                        pass  # Continue the current section
                    # Otherwise, skip
            else:
                # Not a valid header format, skip
                pass
        else:
            # Regular line, continue current section
            pass
    
    # Save last section
    if current_section is not None:
        section_content = '\n'.join(lines[section_start:])
        sections.append({
            'header': current_section,
            'agent': current_agent,
            'content': section_content
        })
    
    return sections

def extract_agent_from_section_header(header: str) -> Optional[str]:
    """Extract agent name from section header like 'Clau (Claude Code)' or 'Misty (Mistral Vibe)'"""
    # Extract first word
    first_word = header.split()[0] if header.split() else ""
    first_word_lower = first_word.lower()
    
    if first_word_lower in AGENTS:
        return first_word_lower
    
    # Try display names
    for agent, display_names in AGENT_DISPLAY_NAMES.items():
        for display_name in display_names:
            if display_name.lower() == first_word_lower:
                return agent
    
    # Check if header contains a known agent name
    header_lower = header.lower()
    for agent, display_names in AGENT_DISPLAY_NAMES.items():
        for display_name in display_names:
            if display_name.lower() in header_lower:
                return agent
    
    return None

def extract_tasks_from_text(text: str) -> List[Dict[str, str]]:
    """Extract tasks from text, handling various formats"""
    tasks = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip headers
        if line.startswith('#') or line.startswith('---'):
            continue
        
        # Extract ticket IDs
        ticket_ids = extract_ticket_ids(line)
        
        if not ticket_ids:
            continue
        
        # Extract title - remove ticket IDs and markdown formatting
        title = line
        # Remove markdown bold: **text**
        title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
        # Remove markdown italic: *text*
        title = re.sub(r'\*(.+?)\*', r'\1', title)
        # Remove markdown bold italic: ***text***
        title = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', title)
        
        # Remove bullet points and numbering
        title = re.sub(r'^[-*\d.\s]+', '', title)
        
        # Remove ticket IDs
        for tid in ticket_ids:
            title = title.replace(tid, '').replace(f'[{tid}]', '').replace(f'({tid})', '').replace(f'#{tid}', '')
        
        title = title.strip()
        
        for ticket_id in ticket_ids:
            project = extract_project_prefix(ticket_id)
            tasks.append({
                "id": ticket_id,
                "title": title[:200] if title else "",
                "project": project
            })
    
    return tasks

def extract_blockers_from_text(text: str) -> List[str]:
    """Extract blockers from text"""
    blockers = []
    
    # Find Blockers section
    pattern = r'##?\s*Blocker[s]?\s*[:\-]*\s*$'
    section_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    
    if section_match:
        # Get content after the section header
        start_idx = section_match.end()
        # Find next section or end of content
        next_section = re.search(r'\n##', text[start_idx:])
        if next_section:
            section_content = text[start_idx:start_idx + next_section.start()]
        else:
            section_content = text[start_idx:]
        
        for line in section_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*') and not line.startswith('**'):
                continue
            # Extract text after bullet
            line = re.sub(r'^[-*\s]+', '', line).strip()
            if line:
                blockers.append(line)
    
    # Also look for inline "Blockers:" mentions
    inline_pattern = r'Blocker[s]?\s*[:=]\s*(.+?)(?=\n\n|\n##|\Z)'
    inline_matches = re.findall(inline_pattern, text, re.DOTALL | re.IGNORECASE)
    for match in inline_matches:
        items = [item.strip() for item in match.split(',') if item.strip()]
        blockers.extend(items)
    
    return blockers

def extract_peer_reviews_from_text(text: str) -> List[Dict[str, str]]:
    """Extract peer reviews from text"""
    reviews = []
    
    # Find Peer Review section
    pattern = r'##?\s*Peer Review[s]?\s*[:\-]*\s*$'
    section_match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    
    if section_match:
        start_idx = section_match.end()
        next_section = re.search(r'\n##', text[start_idx:])
        if next_section:
            section_content = text[start_idx:start_idx + next_section.start()]
        else:
            section_content = text[start_idx:]
        
        for line in section_content.split('\n'):
            line_lower = line.strip().lower()
            if 'approved' in line_lower or 'reviewed' in line_lower:
                ticket_ids = extract_ticket_ids(line)
                for ticket_id in ticket_ids:
                    reviews.append({
                        "ticket_id": ticket_id,
                        "verdict": "approved"
                    })
    
    return reviews

def parse_single_agent_file(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a file that contains standup for a single agent"""
    date = extract_date_from_filename(filepath.name)
    if not date:
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to determine agent from filename
    agent = extract_agent_from_filename(filepath.name)
    
    # If no agent in filename, try to find from content header
    if not agent:
        # Look for # Agent Name pattern
        match = re.search(r'^#\s+([A-Z][a-zA-Z\s\(\)]+)', content, re.MULTILINE)
        if match:
            header = match.group(1)
            agent = extract_agent_from_section_header(header)
    
    if not agent:
        # Try to find agent name in content
        agent = match_agent_in_text(content)
    
    if not agent:
        print(f"  WARNING: Could not determine agent for {filepath.name}")
        return []
    
    entry = create_entry(date, agent, content)
    return [entry] if entry else []

def parse_multi_agent_file(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a file that contains standups for multiple agents"""
    date = extract_date_from_filename(filepath.name)
    if not date:
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all agent sections
    sections = find_agent_sections(content)
    
    if not sections:
        # No clear sections, treat as single agent
        return parse_single_agent_file(filepath)
    
    entries = []
    for section in sections:
        # Use pre-extracted agent if available
        agent = section.get('agent')
        if not agent:
            agent = extract_agent_from_section_header(section['header'])
        if not agent:
            # Try to match agent from section content
            agent = match_agent_in_text(section['content'])
        
        if not agent:
            print(f"  WARNING: Could not determine agent for section: {section['header']}")
            continue
        
        entry = create_entry(date, agent, section['content'])
        if entry:
            entries.append(entry)
    
    return entries

def create_entry(date: str, agent: str, content: str) -> Dict[str, Any]:
    """Create a standup entry from date, agent, and content"""
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
    
    # Extract tasks
    entry["tasks_completed"] = extract_tasks_from_text(content)
    
    # Extract peer reviews
    entry["peer_reviews"] = extract_peer_reviews_from_text(content)
    
    # Extract blockers
    entry["blockers"] = extract_blockers_from_text(content)
    
    # Extract notes text (content without headers, first 10000 chars)
    notes_lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('---'):
            notes_lines.append(stripped)
    entry["notes_text"] = ' '.join(notes_lines)[:10000]
    
    return entry

def parse_file(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a standup file and return entries"""
    # Check if this is a special file (like MEMOIR)
    if 'MEMOIR' in filepath.name.upper() or 'SPEC' in filepath.name.upper():
        return []
    
    # Try multi-agent parsing first
    entries = parse_multi_agent_file(filepath)
    
    if entries:
        return entries
    
    # Fall back to single agent
    return parse_single_agent_file(filepath)

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
            existing["session_count"] = max(existing["session_count"], entry["session_count"])
        else:
            seen[key] = dict(entry)  # Make a copy
    
    # Remove duplicates in tasks_completed
    for key, entry in seen.items():
        seen_ids = set()
        unique_tasks = []
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
        print(f"  Warning: Could not fetch PocketBase timestamps: {e}")
    
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
    print("QW-001 Standup Parser - FIXED VERSION")
    print("=" * 60)
    
    # Parse all standup files
    print("\n[1/4] Parsing standup files...")
    md_files = list(STANDUPS_DIR.glob("*.md"))
    print(f"    Found {len(md_files)} markdown files")
    
    all_entries = []
    parsed_count = 0
    for filepath in sorted(md_files):
        try:
            entries = parse_file(filepath)
            all_entries.extend(entries)
            if entries:
                parsed_count += 1
        except Exception as e:
            print(f"  ERROR parsing {filepath.name}: {e}")
    
    print(f"    → Parsed {len(all_entries)} entries from {parsed_count} files")
    
    # Deduplicate
    print("\n[2/4] Deduplicating entries...")
    all_entries = deduplicate_entries(all_entries)
    print(f"    → After deduplication: {len(all_entries)} entries")
    
    # Fetch PocketBase timestamps
    print("\n[3/4] Fetching PocketBase timestamps...")
    timestamps = fetch_pocketbase_timestamps()
    print(f"    → Retrieved timestamps for {len(timestamps)} tasks")
    
    # Enrich entries
    print("\n[4/4] Enriching entries with timestamps...")
    all_entries = enrich_entries(all_entries, timestamps)
    
    # Sort by date and agent
    all_entries.sort(key=lambda x: (x["date"], x["agent"]))
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Output written to {OUTPUT_FILE}")
    
    # Validation
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    
    if not all_entries:
        print("ERROR: No entries found!")
        return
    
    print(f"Total entries: {len(all_entries)}")
    
    dates = [e["date"] for e in all_entries]
    print(f"Date range: {min(dates)} to {max(dates)}")
    
    agents_found = sorted(set(e["agent"] for e in all_entries))
    print(f"Agents: {', '.join(agents_found)}")
    
    total_tasks = sum(len(e["tasks_completed"]) for e in all_entries)
    print(f"Total tasks: {total_tasks}")
    
    total_peer_reviews = sum(len(e["peer_reviews"]) for e in all_entries)
    print(f"Total peer reviews: {total_peer_reviews}")
    
    total_blockers = sum(len(e["blockers"]) for e in all_entries)
    print(f"Total blockers: {total_blockers}")
    
    total_sessions = sum(e["session_count"] for e in all_entries)
    print(f"Total sessions: {total_sessions}")
    
    # Check for issues
    print("\n" + "-" * 60)
    print("POTENTIAL ISSUES")
    print("-" * 60)
    
    empty_task_count = sum(1 for e in all_entries if len(e["tasks_completed"]) == 0)
    print(f"Entries with no tasks: {empty_task_count}")
    
    empty_agent_count = sum(1 for e in all_entries if not e["agent"])
    print(f"Entries with no agent: {empty_agent_count}")
    
    print("\n" + "=" * 60)
    print("QW-001 COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
