#!/usr/bin/env python3
"""
Mexico Log Parser

Parses raw Mexico wood-marking logs into normalized structured events.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any


def parse_mexico_log(log_file: Path) -> List[Dict[str, Any]]:
    """
    Parse a Mexico wood-marking log file into structured events.
    
    Args:
        log_file: Path to the log file
        
    Returns:
        List of structured event dictionaries
    """
    events = []
    
    # Define regex patterns for different event types
    patterns = {
        'PEN_DOWN': r'\[([^\]]+)\] PEN DOWN \� drawing line (\d+)/(\d+)',
        'DRAWING': r'\[([^\]]+)\] DRAWING  \� (\d+)/(\d+) moves (\(\d+%\)) \� X:([+-]?\d+\.?\d*) Y:([+-]?\d+\.?\d*)mm',
        'CHECK': r'\[([^\]]+)\] CHECK \� ([^\�]+) \� ([^\�]+)',
        'JOB_START': r'\[([^\]]+)\] JOB START \� action=([^\s]+) content=\'([^\']+)\'',
        'BUSY': r'\[([^\]]+)\] BUSY \� action=([^\s]+) content=\'([^\']+)\'',
        'OBS': r'\[([^\]]+)\] OBS \� ([^\�]+)',
        'CAFFEINATE': r'\[([^\]]+)\] CAFFEINATE \� ([^\�]+)',
        'NARRATION': r'\[([^\]]+)\] NARRATION \� ([^\�]+)',
        'WARNING_TONE': r'\[([^\]]+)\] WARNING TONE \� ([^\�]+)',
        'VOICE_INTRO': r'\[([^\]]+)\] VOICE INTRO \� (.+)',
        'DRAW_START': r'\[([^\]]+)\] DRAW START \� svg \'([^\']+)\'',
        'MARKERS': r'\[([^\]]+)\] MARKERS \� ([^\�]+)',
        'ERROR': r'\[([^\]]+)\] ERROR \� (.+)',
        'JOB_END': r'\[([^\]]+)\] JOB END \� status=([^\s]+) duration=([^\s]+)',
    }
    
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Try to match each pattern
            matched = False
            for event_type, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    event = {
                        'timestamp': match.group(1),
                        'event_type': event_type,
                        'details': match.groups()[1:],
                        'source_file': str(log_file),
                        'line_number': line_num
                    }
                    events.append(event)
                    matched = True
                    break
            
            if not matched:
                # Handle unmatched lines
                print(f"Warning: Unmatched line {line_num}: {line}")
    
    return events


def save_events(events: List[Dict[str, Any]], output_file: Path) -> None:
    """
    Save parsed events to a JSON file.
    
    Args:
        events: List of structured events
        output_file: Path to the output JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)


def main():
    """
    Main function to parse Mexico logs.
    """
    # Input and output paths
    input_dir = Path('vault/raw_sources/robotross/mexico_wood_marking')
    output_dir = Path('vault/derived/mexico_events')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all log files
    for log_file in input_dir.glob('*.log'):
        print(f"Processing {log_file}...")
        events = parse_mexico_log(log_file)
        
        # Create output filename
        output_file = output_dir / f"{log_file.stem}_events.json"
        save_events(events, output_file)
        print(f"Saved {len(events)} events to {output_file}")


if __name__ == '__main__':
    main()