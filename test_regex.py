#!/usr/bin/env python3
"""Test regex pattern for parsing MISSION_CONTROL.md"""

import re

# Read the content
with open("MISSION_CONTROL.md", "r") as f:
    content = f.read()

# Test the OPEN tickets regex pattern
print("Testing OPEN tickets regex pattern...")
open_pattern = r"### OPEN\n\| Ticket \| Description \| Owner \| Status \| Notes \|\n\| :--- \| :--- \| :--- \| :--- \| :--- \|\n((?:\| \*\*#\d+\*\* \| .+ \n)+)"
open_section_match = re.search(open_pattern, content)

if open_section_match:
    print("OPEN section found!")
    open_table = open_section_match.group(1)
    print(f"Captured content:\n{open_table}")
else:
    print("OPEN section NOT found")
    
# Let's also test a simpler pattern to see what's happening
print("\n" + "="*50)
print("Testing simpler pattern...")
simple_pattern = r"### OPEN"
simple_match = re.search(simple_pattern, content)
if simple_match:
    print("Found '### OPEN' header")
    # Print some context around it
    start_pos = simple_match.start()
    print(f"Context around header:\n{content[start_pos:start_pos+500]}")
else:
    print("'### OPEN' header NOT found")

# Test if the table header exists
print("\n" + "="*50)
print("Testing table header pattern...")
table_header_pattern = r"\| Ticket \| Description \| Owner \| Status \| Notes \|"
table_header_match = re.search(table_header_pattern, content)
if table_header_match:
    print("Found table header")
    start_pos = table_header_match.start()
    print(f"Context around table header:\n{content[start_pos:start_pos+300]}")
else:
    print("Table header NOT found")