#!/usr/bin/env python3
"""Debug regex pattern for parsing MISSION_CONTROL.md"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

# Find the OPEN section and print it with exact formatting
print("Looking for OPEN section...")
open_start = content.find("### OPEN")
if open_start != -1:
    # Print a larger context to see the exact formatting
    open_end = content.find("###", open_start + 1)
    if open_end == -1:
        open_end = len(content)
    
    open_section = content[open_start:open_end]
    print("OPEN section content:")
    print(repr(open_section[:500]))  # Show first 500 chars with escape sequences
    print("\n" + "="*50)
    print("OPEN section content (formatted):")
    print(open_section[:500])

# Test different regex patterns
print("\n" + "="*50)
print("Testing regex patterns...")

# Pattern 1: More flexible with whitespace
pattern1 = r"### OPEN\s*\n\|\s*Ticket\s*\|\s*Description\s*\|\s*Owner\s*\|\s*Status\s*\|\s*Notes\s*\|\s*\n\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*\n((?:\|\s*\*\*#\d+\*\*\s*\|\s*.+?\s*\n)+)"

match1 = re.search(pattern1, content)
if match1:
    print("Pattern 1 MATCHED!")
    print(f"Captured: {repr(match1.group(1)[:200])}")
else:
    print("Pattern 1 FAILED")

# Pattern 2: Even more flexible
pattern2 = r"### OPEN\s*\n\|\s*Ticket\s*\|\s*Description\s*\|\s*Owner\s*\|\s*Status\s*\|\s*Notes\s*\|\s*\n\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*\n([\s\S]*?)(?=\n###|\n\*\*Status|\Z)"

match2 = re.search(pattern2, content)
if match2:
    print("Pattern 2 MATCHED!")
    captured = match2.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
else:
    print("Pattern 2 FAILED")