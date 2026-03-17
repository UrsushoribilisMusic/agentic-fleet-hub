#!/usr/bin/env python3
"""Debug the final CLOSED section parsing"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

print("Testing CLOSED section parsing...")

# Test the pattern step by step
pattern = r"### CLOSED\s*\n((?:- \*\*[^\*]+\*\*: .+? \n)+)"
match = re.search(pattern, content)

if match:
    print("Pattern MATCHED!")
    captured = match.group(1)
    print(f"Captured length: {len(captured)}")
    print(f"First 200 chars: {repr(captured[:200])}")
else:
    print("Pattern FAILED")
    
    # Let's try to find what's wrong
    print("\nDebugging...")
    
    # Test if we can find ### CLOSED
    test1 = re.search(r"### CLOSED", content)
    if test1:
        print("Found '### CLOSED'")
        start_pos = test1.end()
        print(f"Next 100 chars after '### CLOSED': {repr(content[start_pos:start_pos+100])}")
    else:
        print("'### CLOSED' not found")
    
    # Test if we can find the first line after ### CLOSED
    test2 = re.search(r"### CLOSED\s*\n(-.+)", content)
    if test2:
        print("Found first line after ### CLOSED")
        print(f"First line: {repr(test2.group(1)[:100])}")
    else:
        print("First line not found")
    
    # Test a more permissive pattern
    test3 = re.search(r"### CLOSED[\s\S]*?\n((?:- .+\n)+?)(?=\n###)", content)
    if test3:
        print("Permissive pattern MATCHED!")
        captured = test3.group(1)
        print(f"Captured length: {len(captured)}")
        print(f"First 200 chars: {repr(captured[:200])}")
    else:
        print("Permissive pattern FAILED")