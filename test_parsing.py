#!/usr/bin/env python3
"""Test the complete parsing function"""

import re

def parse_mission_control_test():
    """Test parsing MISSION_CONTROL.md for ticket status."""
    mission_control_path = "MISSION_CONTROL.md"
    
    with open(mission_control_path, "r") as f:
        content = f.read()
    
    # Parse ticket status sections
    open_tickets = []
    closed_tickets = []
    
    # Extract OPEN tickets table - using the working pattern
    open_section_match = re.search(
        r"### OPEN\s*\n\|\s*Ticket\s*\|\s*Description\s*\|\s*Owner\s*\|\s*Status\s*\|\s*Notes\s*\|\s*\n\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*\n((?:\|\s*\*\*#\d+\*\*\s*\|\s*.+?\s*\n)+)",
        content
    )
    
    if open_section_match:
        open_table = open_section_match.group(1)
        print("OPEN tickets table found!")
        print(f"Table content:\n{open_table}")
        print("\n" + "="*50)
        
        for line in open_table.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split("|")]
                print(f"Parts: {parts}")
                if len(parts) >= 5:
                    ticket_id = parts[1].replace("**#", "").replace("**", "")
                    description = parts[2]
                    owner = parts[3]
                    status = parts[4]
                    open_tickets.append({
                        "id": ticket_id,
                        "description": description,
                        "owner": owner,
                        "status": status
                    })
    
    print(f"\nParsed {len(open_tickets)} open tickets:")
    for ticket in open_tickets:
        print(f"  Ticket #{ticket['id']}: {ticket['description'][:50]}... (Owner: {ticket['owner']}, Status: {ticket['status']})")
    
    # Extract CLOSED tickets
    closed_section_match = re.search(r"### CLOSED\n((?:- \*\*#\d+\*\*: .+ \n)+)", content)
    
    if closed_section_match:
        closed_list = closed_section_match.group(1)
        print(f"\nCLOSED tickets section found!")
        
        for line in closed_list.strip().split("\n"):
            if line.strip():
                match = re.match(r"- \*\*#(\d+)\*\*: (.+)", line)
                if match:
                    ticket_id = match.group(1)
                    description = match.group(2)
                    closed_tickets.append({
                        "id": ticket_id,
                        "description": description,
                        "status": "closed"
                    })
    
    print(f"\nParsed {len(closed_tickets)} closed tickets:")
    for ticket in closed_tickets[:5]:  # Show first 5
        print(f"  Ticket #{ticket['id']}: {ticket['description'][:50]}...")
    
    return {
        "open": open_tickets,
        "closed": closed_tickets
    }

if __name__ == "__main__":
    result = parse_mission_control_test()
    print(f"\nFinal result: {len(result['open'])} open, {len(result['closed'])} closed tickets")