import requests
import re
import os
from datetime import datetime

PB_URL = "http://localhost:8090/api"
MC_PATH = "/Users/miguelrodriguez/projects/agentic-fleet-hub/MISSION_CONTROL.md"

def fetch_pb_tasks():
    print("Fetching tasks from PocketBase...")
    tasks = []
    page = 1
    while True:
        try:
            r = requests.get(f"{PB_URL}/collections/tasks/records", params={
                "page": page,
                "perPage": 100,
                "sort": "-updated"
            }, timeout=10)
            if r.status_code != 200:
                print(f"Failed to fetch tasks: {r.status_code}")
                break
            data = r.json()
            items = data.get("items", [])
            tasks.extend(items)
            if len(items) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            break
    return tasks

def update_pb_task(task_id, data):
    print(f"Updating PocketBase task {task_id} with {data}...")
    try:
        r = requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}", json=data, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"Failed to update task {task_id}: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"Error updating task {task_id}: {e}")
    return False

def parse_mc_ticket_status(content):
    open_tickets = []
    closed_tickets = []
    
    # Extract OPEN tickets table
    # Matches the header and then all rows starting with |
    open_section_match = re.search(r"### OPEN\s*\n\|\s*Ticket\s*\|\s*Description\s*\|\s*Owner\s*\|\s*Status\s*\|\s*Notes\s*\|\s*\n\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*\n((?:\|\s*.+?\s*\n)+)", content)
    
    if open_section_match:
        open_table = open_section_match.group(1)
        for line in open_table.strip().split("\n"):
            if line.strip():
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    ticket_id_raw = parts[1].replace("**#", "").replace("**", "")
                    description = parts[2]
                    owner = parts[3].lower()
                    status_raw = parts[4].lower()
                    notes = parts[5]
                    
                    # Map status back to PB
                    status_map = {
                        'planned': 'todo',
                        'in_work': 'in_progress',
                        'merged': 'peer_review'
                    }
                    status = status_map.get(status_raw, 'todo')
                    
                    open_tickets.append({
                        "id_num": ticket_id_raw,
                        "title_desc": description,
                        "owner": owner,
                        "status": status,
                        "notes": notes
                    })
    
    # Extract CLOSED tickets
    closed_section_match = re.search(r"### CLOSED\n([\s\S]*?)(?=\n###|\n\*\*Status:|$)", content)
    
    if closed_section_match:
        closed_list = closed_section_match.group(1)
        for line in closed_list.strip().split("\n"):
            if line.strip():
                match = re.match(r"- \*\*#(\d+)\*\*\: (.+)", line)
                if match:
                    ticket_id = match.group(1)
                    desc_raw = match.group(2)
                    closed_tickets.append({
                        "id_num": ticket_id,
                        "desc_raw": desc_raw,
                        "status": "approved"
                    })
                else:
                    # Check for non-numeric IDs or other formats
                    match_alt = re.match(r"- \*\*([^\*]+)\*\*\: (.+)", line)
                    if match_alt:
                        ticket_id = match_alt.group(1)
                        desc_raw = match_alt.group(2)
                        closed_tickets.append({
                            "id_num": ticket_id,
                            "desc_raw": desc_raw,
                            "status": "approved"
                        })
                        
    return open_tickets, closed_tickets

def sync_mc_to_pb(content, pb_tasks):
    open_mc, closed_mc = parse_mc_ticket_status(content)
    
    # Create a mapping for easy lookup
    pb_map = {}
    pb_prefix_map = {} # Map 8-char prefixes to tasks
    
    for task in pb_tasks:
        # Extract #ID from title
        match = re.search(r"#(\d+)", task['title'])
        if match:
            pb_map[match.group(1)] = task
        # Also check gh_issue_id
        if task.get('gh_issue_id'):
            pb_map[str(task['gh_issue_id'])] = task
        
        # PB ID
        pb_map[task['id']] = task
        # PB ID prefix
        pb_prefix_map[task['id'][:8]] = task

    updates_made = 0
    
    # Combined list of MC tickets
    all_mc = open_mc
    
    for mc_t in all_mc:
        # Try finding by full ID, #ID, or prefix
        pb_t = pb_map.get(mc_t['id_num']) or pb_prefix_map.get(mc_t['id_num'])
        
        if pb_t:
            needs_update = False
            update_data = {}
            
            if pb_t['status'] != mc_t['status']:
                # Never downgrade from approved — PB agent writes are authoritative
                if pb_t['status'] == 'approved':
                    pass
                else:
                    needs_update = True
                    update_data['status'] = mc_t['status']
            
            # For open tickets, also check owner
            if 'owner' in mc_t and mc_t['owner'] != 'n/a':
                if pb_t.get('assigned_agent') != mc_t['owner']:
                    needs_update = True
                    update_data['assigned_agent'] = mc_t['owner']
            
            if needs_update:
                if update_pb_task(pb_t['id'], update_data):
                    updates_made += 1
                    pb_t.update(update_data)
        else:
            # Task not found, CREATE it
            print(f"Ticket #{mc_t['id_num']} not found in PocketBase. Creating...")
            title = mc_t.get('title_desc') or mc_t.get('desc_raw') or f"Task from MC: {mc_t['id_num']}"
            if mc_t['id_num'].isdigit():
                title = f"#{mc_t['id_num']}: {title}"
            
            new_task = {
                "title": title,
                "status": mc_t['status'],
                "assigned_agent": mc_t.get('owner', 'gem'),
                "description": mc_t.get('notes', 'Created from MISSION_CONTROL.md sync')
            }
            
            try:
                r = requests.post(f"{PB_URL}/collections/tasks/records", json=new_task, timeout=10)
                if r.status_code == 200:
                    print(f"Created task: {title}")
                    updates_made += 1
                else:
                    print(f"Failed to create task: {r.status_code}")
            except Exception as e:
                print(f"Error creating task: {e}")
            
    return updates_made

def format_open_table(tasks):
    # Only include tasks that are NOT approved/backlog
    open_tasks = [t for t in tasks if t['status'] in ['todo', 'in_progress', 'peer_review']]
    if not open_tasks:
        return "| Ticket | Description | Owner | Status | Notes |\n| :--- | :--- | :--- | :--- | :--- |\n"

    lines = ["| Ticket | Description | Owner | Status | Notes |", "| :--- | :--- | :--- | :--- | :--- |"]
    
    # Sort open tasks by ID if possible
    def get_id_num(t):
        match = re.search(r"#(\d+)", t['title'])
        if match: return int(match.group(1))
        if t.get('gh_issue_id'): return int(t['gh_issue_id'])
        return 99999
    
    open_tasks.sort(key=get_id_num)

    for t in open_tasks:
        title = t['title']
        match = re.search(r"#(\d+)", title)
        ticket_id = f"**#{match.group(1)}**" if match else f"**{t['id'][:8]}**"
        
        # Clean title for description column
        clean_title = re.sub(r"^#\d+:\s*", "", title)
        
        # Map status
        status_map = {
            'todo': 'planned',
            'in_progress': 'in_work',
            'peer_review': 'merged'
        }
        status = status_map.get(t['status'], 'planned')
        
        owner = t.get('assigned_agent', 'n/a').lower()
        notes = t.get('description', '').split('\n')[0][:50]
        if len(t.get('description', '')) > 50:
            notes += "..."
            
        lines.append(f"| {ticket_id} | {clean_title} | {owner} | {status} | {notes} |")
    
    return "\n".join(lines) + "\n"

def format_closed_list(tasks):
    closed_tasks = [t for t in tasks if t['status'] == 'approved']
    
    # Sort by ID descending
    def get_id_num(t):
        match = re.search(r"#(\d+)", t['title'])
        if match: return int(match.group(1))
        if t.get('gh_issue_id'): return int(t['gh_issue_id'])
        return 0
    
    closed_tasks.sort(key=get_id_num, reverse=True)
    
    lines = []
    for t in closed_tasks:
        title = t['title']
        match = re.search(r"#(\d+)", title)
        ticket_id = f"**#{match.group(1)}**" if match else f"**{t['id'][:8]}**"
        
        clean_title = re.sub(r"^#\d+:\s*", "", title)
        owner = t.get('assigned_agent', 'n/a').capitalize()
        
        desc = t.get('description', '').split('\n')[0]
        if desc:
            lines.append(f"- {ticket_id}: {clean_title} -- {desc} -- {owner}. Approved.")
        else:
            lines.append(f"- {ticket_id}: {clean_title} -- {owner}. Approved.")
            
    return "\n".join(lines) + "\n"

def main():
    # 1. Read current MISSION_CONTROL.md
    print(f"Reading {MC_PATH}...")
    try:
        with os.popen(f"cat {MC_PATH}") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {MC_PATH}: {e}")
        return

    # 2. Fetch PB tasks
    pb_tasks = fetch_pb_tasks()
    if not pb_tasks:
        print("No tasks found in PocketBase.")
        return

    # 3. Sync MC -> PB
    print("Syncing MISSION_CONTROL.md changes to PocketBase...")
    updates_to_pb = sync_mc_to_pb(content, pb_tasks)
    print(f"Updated {updates_to_pb} tasks in PocketBase.")

    # 4. Generate new MC content (PB -> MC)
    print("Re-generating MISSION_CONTROL.md from PocketBase state...")
    
    # Preserve everything above ## Ticket Status
    header_match = re.search(r"(.*?)## Ticket Status", content, re.DOTALL)
    if not header_match:
        print("## Ticket Status section not found in MISSION_CONTROL.md")
        return
    
    header = header_match.group(1)
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_ticket_status = f"## Ticket Status (as of {today})\n\n"
    
    # Preserve ENVIRONMENT NOTE
    env_note_match = re.search(r"### ENVIRONMENT NOTE.*?\n---", content, re.DOTALL)
    if env_note_match:
        new_ticket_status += env_note_match.group(0) + "\n\n"
    
    new_ticket_status += "### CLOSED\n"
    new_ticket_status += format_closed_list(pb_tasks)
    new_ticket_status += "\n### OPEN\n"
    new_ticket_status += format_open_table(pb_tasks)
    
    # Preserve footer
    footer_match = re.search(r"\*\*Status:.*", content)
    if footer_match:
        new_ticket_status += "\n" + footer_match.group(0) + "\n"

    new_content = header + new_ticket_status
    
    if new_content == content:
        print("No changes needed for MISSION_CONTROL.md")
        return

    # 5. Apply changes directly
    with open(MC_PATH, "w") as f:
        f.write(new_content)
    
    print(f"MISSION_CONTROL.md updated.")
    
    # 6. Commit and push
    try:
        repo_dir = os.path.dirname(MC_PATH)
        os.system(f"git -C {repo_dir} add MISSION_CONTROL.md")
        os.system(f"git -C {repo_dir} commit -m 'chore: auto-sync MISSION_CONTROL with PocketBase state'")
        os.system(f"git -C {repo_dir} push origin master")
        print("Changes pushed to GitHub.")
    except Exception as e:
        print(f"Failed to push changes: {e}")

if __name__ == "__main__":
    main()
