#!/usr/bin/env python3
"""Test the CLOSED tickets parsing"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

# Find the CLOSED section
print("Looking for CLOSED section...")
closed_start = content.find("### CLOSED")
if closed_start != -1:
    # Print the CLOSED section
    open_start = content.find("### OPEN", closed_start)
    if open_start == -1:
        open_start = len(content)
    
    closed_section = content[closed_start:open_start]
    print("CLOSED section content:")
    print(repr(closed_section[:500]))  # Show first 500 chars with escape sequences
    print("\n" + "="*50)
    print("CLOSED section content (formatted):")
    print(closed_section[:500])

# Test different regex patterns for CLOSED tickets
print("\n" + "="*50)
print("Testing CLOSED tickets regex patterns...")

# Pattern 1: Original pattern
pattern1 = r"### CLOSED\n((?:- \*\*#\d+\*\*: .+ \n)+)"
match1 = re.search(pattern1, content)
if match1:
    print("Pattern 1 MATCHED!")
    print(f"Captured: {repr(match1.group(1)[:200])}")
else:
    print("Pattern 1 FAILED")

# Pattern 2: More flexible with whitespace
pattern2 = r"### CLOSED\s*\n((?:- \*\*#\d+\*\*: .+? \n)+)"
match2 = re.search(pattern2, content)
if match2:
    print("Pattern 2 MATCHED!")
    captured = match2.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
    
    # Parse the captured content
    print("\nParsing CLOSED tickets:")
    for line in captured.strip().split("\n"):
        if line.strip():
            print(f"Line: {repr(line)}")
            match = re.match(r"- \*\*#(\d+)\*\*: (.+)", line)
            if match:
                ticket_id = match.group(1)
                description = match.group(2)
                print(f"  Ticket #{ticket_id}: {description[:50]}...")
else:
    print("Pattern 2 FAILED")

# Pattern 3: Even more flexible
pattern3 = r"### CLOSED[\s\S]*?\n((?:- \*\*#\d+\*\*: .+? \n)+?)(?=\n###)"
match3 = re.search(pattern3, content)
if match3:
    print("Pattern 3 MATCHED!")
    captured = match3.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
else:
    print("Pattern 3 FAILED")