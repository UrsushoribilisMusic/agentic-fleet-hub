#!/usr/bin/env python3
import requests
import json

PB_URL = "http://localhost:8090/api"
DEFAULT_REPO = "UrsushoribilisMusic/agentic-fleet-hub"
PRIVATECORE_REPO = "UrsushoribilisMusic/privatecore-ios"

def get_tasks_to_backfill():
    url = f"{PB_URL}/collections/tasks/records"
    params = {
        "filter": 'gh_issue_id > 0 && github_repo = ""',
        "perPage": 200
    }
    tasks = []
    page = 1
    while True:
        params["page"] = page
        r = requests.get(url, params=params)
        if r.status_code != 200:
            break
        data = r.json()
        items = data.get("items", [])
        tasks.extend(items)
        if len(items) < 200:
            break
        page += 1
    return tasks

def backfill():
    tasks = get_tasks_to_backfill()
    print(f"Found {len(tasks)} tasks to backfill.")
    
    for task in tasks:
        task_id = task["id"]
        title = task["title"].upper()
        repo = DEFAULT_REPO
        
        if "[PRIVATECORE-IOS]" in title or "[PC-" in title or "PRIVATECORE" in title:
            repo = PRIVATECORE_REPO
            
        issue_id = task["gh_issue_id"]
        issue_url = f"https://github.com/{repo}/issues/{issue_id}"
        
        print(f"Updating task {task_id} ('{task['title']}') -> {repo} #{issue_id}")
        
        patch_data = {
            "github_repo": repo,
            "github_issue_url": issue_url
        }
        
        r = requests.patch(f"{PB_URL}/collections/tasks/records/{task_id}", json=patch_data)
        if r.status_code != 200:
            print(f"  Failed to update {task_id}: {r.status_code}")

if __name__ == "__main__":
    backfill()
