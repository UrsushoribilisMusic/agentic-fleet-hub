#!/usr/bin/env python3

# Read the file
with open('fleet_api.py', 'r') as f:
    content = f.read()

# Replace the logic
old_logic = '''        # Set is_active to True for the project matching the repo_path
        for project in agents_fleet_meta.get("projects", []):
            # Check if the repo_path matches the project's kanban or docs URL
            kanban_url = project.get("kanban", "")
            docs_url = project.get("docs", [])
            if isinstance(docs_url, list) and len(docs_url) > 0:
                docs_url = docs_url[0]
            
            if repo_path in kanban_url or repo_path in docs_url:
                project["is_active"] = True
            else:
                project["is_active"] = False'''

new_logic = '''        # Set is_active to True for the project matching the repo_path
        repo_name = os.path.basename(new_repo_path)
        for project in agents_fleet_meta.get("projects", []):
            # Check if the repo_name matches the project's title or is in the docs URL
            docs_url = project.get("docs", [])
            if isinstance(docs_url, list) and len(docs_url) > 0:
                docs_url = docs_url[0]
            
            if repo_name.lower() in project.get("title", "").lower() or repo_name in docs_url:
                project["is_active"] = True
            else:
                project["is_active"] = False'''

# Replace
content = content.replace(old_logic, new_logic)

# Write back
with open('fleet_api.py', 'w') as f:
    f.write(content)

print('Updated successfully')
