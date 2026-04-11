#!/usr/bin/env python3
"""
Mexico Log Parser for RobotRoss Wood-Marking Logs

Parses the raw log files from vault/raw_sources/robotross/mexico_wood_marking/
and extracts normalized events according to the schema defined in schema.json.

Usage:
    python3 parser.py <log_file> [--output output.jsonl]
    python3 parser.py --directory <log_dir> [--output output.jsonl]
    python3 parser.py --test  # Run self-test on sample data
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# Normalized event type mapping
EVENT_TYPE_MAP = {
    "PEN DOWN": "PEN_DOWN",
    "DRAWING": "DRAWING",
    "JOB START": "JOB_START",
    "JOB END": "JOB_END",
    "DRAW START": "DRAW_START",
    "DRAW END": "DRAW_END",
    "CHECK": "CHECK",
    "BUSY": "BUSY",
    "SKETCH": "SKETCH",
    "APPROVE": "APPROVE",
    "OBS": "OBS",
    "CAFFEINATE": "CAFFEINATE",
    "NARRATION": "NARRATION",
    "WARNING TONE": "WARNING",
    "WARNING": "WARNING",
    "VOICE INTRO": "VOICE_INTRO",
    "VOICE OUTRO": "VOICE_OUTRO",
    "ERROR": "ERROR",
    "MARKERS": "MARKERS",
    "STOP": "STOP",
    "AI TOKENS": "AI_TOKENS",
    "SKETCH PREVIEW": "SKETCH_PREVIEW",
    "GCODE": "GCODE",
    "PORT": "PORT",
    "C": "GCODE_COMMENT",
    "SUBPROCESS_ERROR_T": "ERROR",
    "LOCK": "SYSTEM_LOCK",
    "DRY_RUN": "DRY_RUN",
}


def normalize_event_type(raw_type: str) -> str:
    """Normalize the event type from raw log to schema enum."""
    # Handle multi-word types
    upper_raw = raw_type.upper()
    if upper_raw in EVENT_TYPE_MAP:
        return EVENT_TYPE_MAP[upper_raw]
    
    # Try partial match for types with extra characters
    for key, value in EVENT_TYPE_MAP.items():
        if upper_raw.startswith(key.upper()):
            return value
    
    return upper_raw.replace(" ", "_")


def parse_timestamp(ts_str: str) -> str:
    """Convert log timestamp to ISO 8601 format."""
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return ts_str


def extract_details(event_type: str, message: str) -> Dict[str, Any]:
    """Extract structured details from the message based on event type."""
    details = {}
    
    # Common patterns
    # PEN DOWN: "drawing line 1/2628"
    if event_type == "PEN_DOWN":
        match = re.search(r'drawing line\s+(\d+)/(\d+)', message, re.IGNORECASE)
        if match:
            details["line_number"] = int(match.group(1))
            details["total_lines"] = int(match.group(2))
            details["subtype"] = "line"
    
    # DRAWING: "50/2628 moves (2%) X:+3.9 Y:+16.7mm" or "3750/6997 (54%) X:-24.1 Y:-18.2 Z:-0.637mm"
    elif event_type == "DRAWING":
        # Try with 'moves' first
        move_match = re.search(r'(\d+)/(\d+)\s+moves\s*\(\s*(\d+)%', message)
        # Try without 'moves' for later format
        simple_match = re.search(r'(\d+)/(\d+)\s*\(\s*(\d+)%', message)
        
        if move_match:
            details["move_number"] = int(move_match.group(1))
            details["total_moves"] = int(move_match.group(2))
            details["percentage"] = int(move_match.group(3))
            details["subtype"] = "moves"
        elif simple_match:
            details["move_number"] = int(simple_match.group(1))
            details["total_moves"] = int(simple_match.group(2))
            details["percentage"] = int(simple_match.group(3))
            details["subtype"] = "moves"
        
        coord_match = re.search(r'X:([+-]?[\d.]+)\s+Y:([+-]?[\d.]+)mm', message)
        if coord_match:
            details["x_mm"] = float(coord_match.group(1))
            details["y_mm"] = float(coord_match.group(2))
        
        coord_z_match = re.search(r'X:([+-]?[\d.]+)\s+Y:([+-]?[\d.]+)\s+Z:([+-]?[\d.]+)mm', message)
        if coord_z_match:
            details["x_mm"] = float(coord_z_match.group(1))
            details["y_mm"] = float(coord_z_match.group(2))
            details["z_mm"] = float(coord_z_match.group(3))
    
    # JOB START: "action=svg content='...' size=80.0"
    elif event_type == "JOB_START":
        action_match = re.search(r'action=(\S+)', message)
        if action_match:
            details["action"] = action_match.group(1)
        
        content_match = re.search(r"content=['\"]([^'\"]+)['\"]", message)
        if content_match:
            details["content"] = content_match.group(1)
        
        size_match = re.search(r'size=([\d.]+)', message)
        if size_match:
            details["size"] = float(size_match.group(1))
        
        details["subtype"] = "start"
    
    # JOB END: "status=success duration=15.4s"
    elif event_type == "JOB_END":
        status_match = re.search(r'status=(\S+)', message)
        if status_match:
            details["status"] = status_match.group(1)
        
        duration_match = re.search(r'duration=([\d.]+)s', message)
        if duration_match:
            details["duration"] = float(duration_match.group(1))
        
        details["subtype"] = "end"
    
    # CHECK: "not ready" or "all systems ready"
    elif event_type == "CHECK":
        if "not ready" in message.lower():
            details["status"] = "not_ready"
            details["subtype"] = "status"
        elif "all systems ready" in message.lower():
            details["status"] = "ready"
            details["subtype"] = "status"
    
    # ERROR: "could not add markers: [Errno 2] No such file..."
    elif event_type == "ERROR":
        details["subtype"] = "error"
        if "No such file or directory" in message:
            details["error_type"] = "file_not_found"
    
    # WARNING: "playing stand clear"
    elif event_type == "WARNING":
        details["subtype"] = "alert"
    
    # AI TOKENS: "TOKENS — input=224 output=1029 total=1253"
    elif event_type == "AI_TOKENS":
        input_match = re.search(r'input=(\d+)', message)
        output_match = re.search(r'output=(\d+)', message)
        total_match = re.search(r'total=(\d+)', message)
        if input_match:
            details["input_tokens"] = int(input_match.group(1))
        if output_match:
            details["output_tokens"] = int(output_match.group(1))
        if total_match:
            details["total_tokens"] = int(total_match.group(1))
        details["subtype"] = "tokens"
    
    # SKETCH: "prompt='a rocket'"
    elif event_type == "SKETCH":
        prompt_match = re.search(r"prompt=['\"]([^'\"]+)['\"]", message)
        if prompt_match:
            details["prompt"] = prompt_match.group(1)
        details["subtype"] = "generated"
    
    # VOICE: "We got a lovely request..."
    elif event_type in ["VOICE_INTRO", "VOICE_OUTRO"]:
        details["subtype"] = "voice"
    
    # NARRATION: "requesting from Apertus" or "ready"
    elif event_type == "NARRATION":
        if "requesting" in message.lower():
            details["status"] = "requesting"
        elif "ready" in message.lower():
            details["status"] = "ready"
        details["subtype"] = "status"
    
    # BUSY: "action=svg content='...'"
    elif event_type == "BUSY":
        action_match = re.search(r'action=(\S+)', message)
        if action_match:
            details["action"] = action_match.group(1)
        content_match = re.search(r"content=['\"]([^'\"]+)['\"]", message)
        if content_match:
            details["content"] = content_match.group(1)
        details["subtype"] = "busy"
    
    # APPROVE: "drawing C:\path\to\file.svg"
    elif event_type == "APPROVE":
        content_match = re.search(r"drawing\s+(['\"])(.+)\1", message)
        if content_match:
            details["content"] = content_match.group(2)
        details["subtype"] = "approved"
    
    # OBS/CAFFEINATE: "skipped (Windows / --no-obs)"
    elif event_type in ["OBS", "CAFFEINATE"]:
        if "skipped" in message.lower():
            details["status"] = "skipped"
            reason_match = re.search(r'\(([^)]+)\)', message)
            if reason_match:
                details["reason"] = reason_match.group(1)
        elif "stop" in message.lower():
            details["status"] = "stopped"
        else:
            details["status"] = "active"
        details["subtype"] = "system"
    
    # MARKERS: "corner marks + signature added" or error
    elif event_type == "MARKERS":
        if "added" in message.lower():
            details["status"] = "success"
        elif "could not" in message.lower() or "error" in message.lower():
            details["status"] = "error"
        details["subtype"] = "markers"
    
    # STOP: "skipped"
    elif event_type == "STOP":
        details["subtype"] = "stop"
    
    return details


def clean_text(text: str) -> str:
    """Clean text by removing problematic characters that appear in the logs."""
    # Use a broader approach - keep only printable ASCII (32-126) and newline/tab
    # This handles the 0x97 control character and other special chars found in logs
    cleaned = re.sub(r'[^\x20-\x7E\r\n\t]', ' ', text)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def parse_log_line(line: str, line_number: int, source_file: str) -> Optional[Dict[str, Any]]:
    """Parse a single log line into a normalized event."""
    # Clean the line first to remove problematic Unicode characters
    clean_line = clean_text(line)
    
    # Pattern: [YYYY-MM-DD HH:MM:SS] EventType message
    pattern = r'^\[([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\]\s+([A-Z][A-Z_ ]*)\s*(.*)'
    
    match = re.match(pattern, clean_line)
    if not match:
        return None
    
    timestamp_str = match.group(1)
    raw_event_type = match.group(2).strip()
    message = match.group(3).strip()
    
    event = {
        "timestamp": parse_timestamp(timestamp_str),
        "event_type": normalize_event_type(raw_event_type),
        "message": message,
        "source_file": source_file,
        "source_line": line_number,
        "details": extract_details(normalize_event_type(raw_event_type), message)
    }
    
    # Add subtype from details to top level if present
    if "subtype" in event["details"]:
        event["subtype"] = event["details"].pop("subtype")
    
    return event


def parse_log_file(file_path: str, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse a log file and return list of normalized events."""
    events = []
    source_file = Path(file_path).name
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                event = parse_log_line(line, line_number, source_file)
                if event:
                    events.append(event)
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    # Optionally write to output
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    return events


def parse_directory(directory: str, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse all log files in a directory."""
    all_events = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        print(f"Directory not found: {directory}", file=sys.stderr)
        return all_events
    
    for log_file in sorted(dir_path.glob("*.log")):
        print(f"Parsing {log_file.name}...")
        events = parse_log_file(str(log_file))
        all_events.extend(events)
        print(f"  Extracted {len(events)} events")
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            for event in all_events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    return all_events


def self_test():
    """Run self-test on sample data from the first 100 lines of bob_ross.log."""
    test_file = Path("vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log")
    
    if not test_file.exists():
        print("Test file not found: vault/raw_sources/robotross/mexico_wood_marking/bob_ross.log")
        print("Run from the agentic-fleet-hub directory.")
        sys.exit(1)
    
    print("Running self-test on first 100 non-empty lines...")
    
    events = []
    with open(test_file, 'r', encoding='utf-8', errors='replace') as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            if line_number > 100:
                break
            
            event = parse_log_line(line, line_number, test_file.name)
            if event:
                events.append(event)
    
    print(f"\nParsed {len(events)} events from first 100 lines")
    print("\nSample events:")
    for i, event in enumerate(events[:5]):
        print(f"\nEvent {i+1}:")
        print(json.dumps(event, indent=2, ensure_ascii=False))
    
    # Validate against schema
    with open("scripts/mexico_logs/schema.json", 'r') as f:
        schema = json.load(f)
    
    print(f"\nValidating against schema...")
    # Simple validation - check required fields
    required_fields = schema.get("required", [])
    for event in events:
        for field in required_fields:
            if field not in event:
                print(f"ERROR: Missing required field '{field}' in event")
                return False
    
    print("All events have required fields!")
    print(f"\nEvent types found: {sorted(set(e['event_type'] for e in events))}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Parse Mexico wood-marking logs into normalized events"
    )
    parser.add_argument(
        "file_or_dir",
        nargs="?",
        help="Log file or directory containing logs to parse"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (JSONL format)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-test on sample data"
    )
    parser.add_argument(
        "--directory", "-d",
        type=str,
        help="Directory containing log files to parse"
    )
    
    args = parser.parse_args()
    
    if args.test:
        success = self_test()
        sys.exit(0 if success else 1)
    
    if args.directory:
        events = parse_directory(args.directory, args.output)
        print(f"\nTotal events: {len(events)}")
    elif args.file_or_dir:
        if Path(args.file_or_dir).is_dir():
            events = parse_directory(args.file_or_dir, args.output)
        else:
            events = parse_log_file(args.file_or_dir, args.output)
        print(f"\nTotal events: {len(events)}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
