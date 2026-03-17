#!/usr/bin/env python3
"""Debug the CLOSED section parsing"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

# Find the exact CLOSED section
closed_start = content.find("### CLOSED")
open_start = content.find("### OPEN", closed_start)

if closed_start != -1 and open_start != -1:
    closed_section = content[closed_start:open_start]
    print("CLOSED section:")
    print(repr(closed_section))
    print("\n" + "="*50)
    print("CLOSED section (formatted):")
    print(closed_section)
    
    # Test very simple pattern
    print("\n" + "="*50)
    print("Testing very simple pattern...")
    simple_pattern = r"### CLOSED"
    simple_match = re.search(simple_pattern, closed_section)
    if simple_match:
        print("Found '### CLOSED' in the section")
    else:
        print("'### CLOSED' NOT found in the section")
    
    # Test line by line pattern
    print("\n" + "="*50)
    print("Testing line by line...")
    lines = closed_section.split('\n')
    for i, line in enumerate(lines[:10]):  # First 10 lines
        print(f"Line {i}: {repr(line)}")
        
        # Test if it matches our expected pattern
        if line.startswith('-'):
            match = re.match(r"- \*\*([^\*]+)\*\*: (.+)", line)
            if match:
                print(f"  -> Matched! Ticket: {match.group(1)}, Desc: {match.group(2)[:30]}...")
            else:
                print("  -> No match")

# Test if there are any newlines after ### CLOSED
print("\n" + "="*50)
print("Checking for newlines after ### CLOSED...")
after_closed = content[closed_start + len("### CLOSED"):closed_start + len("### CLOSED") + 10]
print(f"Characters after '### CLOSED': {repr(after_closed)}")

# Test pattern that allows any whitespace after ### CLOSED
print("\n" + "="*50)
print("Testing pattern with flexible whitespace...")
flex_pattern = r"### CLOSED\s*\n(- .+)"
flex_match = re.search(flex_pattern, content)
if flex_match:
    print("Flex pattern MATCHED!")
    print(f"Captured: {repr(flex_match.group(1)[:100])}")
else:
    print("Flex pattern FAILED")