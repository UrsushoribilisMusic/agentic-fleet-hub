#!/usr/bin/env python3
"""Test the fixed CLOSED tickets parsing"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

print("Testing fixed CLOSED tickets regex patterns...")

# Pattern: More flexible to handle ranges like #1-#6
pattern = r"### CLOSED\s*\n((?:- \*\*#[^\*]+\*\*: .+? \n)+)"
match = re.search(pattern, content)

if match:
    print("Pattern MATCHED!")
    captured = match.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 300 chars: {repr(captured[:300])}")
    
    # Parse the captured content
    print("\nParsing CLOSED tickets:")
    closed_tickets = []
    for line in captured.strip().split("\n"):
        if line.strip():
            print(f"Line: {repr(line)}")
            # Match patterns like "- **#1-#6**: description" or "- **#10**: description"
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

# Let's also try a simpler approach - just capture everything until the next section
print("\n" + "="*50)
print("Testing simpler approach...")

simple_pattern = r"### CLOSED[\s\S]*?\n((?:- .+\n)+?)(?=\n###)"
simple_match = re.search(simple_pattern, content)

if simple_match:
    print("Simple pattern MATCHED!")
    captured = simple_match.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 300 chars: {repr(captured[:300])}")
    
    # Parse the captured content
    print("\nParsing with simple pattern:")
    closed_tickets_simple = []
    for line in captured.strip().split("\n"):
        if line.strip():
            print(f"Line: {repr(line)}")
            # Match patterns like "- **#1-#6**: description" or "- **#10**: description"
            match = re.match(r"- \*\*([^\*]+)\*\*: (.+)", line)
            if match:
                ticket_id = match.group(1)
                description = match.group(2)
                closed_tickets_simple.append({
                    "id": ticket_id,
                    "description": description,
                    "status": "closed"
                })
                print(f"  Ticket {ticket_id}: {description[:50]}...")
    
    print(f"\nTotal parsed closed tickets with simple pattern: {len(closed_tickets_simple)}")
else:
    print("Simple pattern FAILED")