#!/usr/bin/env python3
"""Test CLOSED section parsing with end of file"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

print("Testing CLOSED section parsing with end of file...")

# Test pattern that allows end of file
pattern = r"### CLOSED\s*\n((?:- \*\*[^\*]+\*\*: .+? \n)+)"
match = re.search(pattern, content)

if match:
    print("Pattern MATCHED!")
    captured = match.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
    
    # Parse the captured content
    print("\nParsing CLOSED tickets:")
    closed_tickets = []
    for line in captured.strip().split("\n"):
        if line.strip():
            match = re.match(r"- \*\*([^\*]+)\*\*: (.+)", line)
            if match:
                ticket_id = match.group(1)
                description = match.group(2)
                closed_tickets.append({
                    "id": ticket_id,
                    "description": description,
                    "status": "closed"
                })
                print(f"  Ticket {ticket_id}: {description[:50]}...")
    
    print(f"\nTotal parsed closed tickets: {len(closed_tickets)}")
else:
    print("Pattern FAILED")

# Test a pattern that goes until end of file
print("\n" + "="*50)
print("Testing pattern until end of file...")
pattern_eof = r"### CLOSED\s*\n([\s\S]+?)(?=\Z|\n###)"
match_eof = re.search(pattern_eof, content)

if match_eof:
    print("EOF pattern MATCHED!")
    captured = match_eof.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
    
    # Parse the captured content
    print("\nParsing CLOSED tickets from EOF pattern:")
    closed_tickets_eof = []
    for line in captured.strip().split("\n"):
        if line.strip() and line.startswith('-'):
            match = re.match(r"- \*\*([^\*]+)\*\*: (.+)", line)
            if match:
                ticket_id = match.group(1)
                description = match.group(2)
                closed_tickets_eof.append({
                    "id": ticket_id,
                    "description": description,
                    "status": "closed"
                })
                print(f"  Ticket {ticket_id}: {description[:50]}...")
    
    print(f"\nTotal parsed closed tickets with EOF pattern: {len(closed_tickets_eof)}")
else:
    print("EOF pattern FAILED")