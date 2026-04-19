#!/usr/bin/env python3
"""
GitHub Issues <-> PocketBase two-way sync.

OUTBOUND (PB -> GitHub):
  - On each cycle, find tasks with no gh_issue_id — create a GitHub Issue.
  - On each cycle, find tasks whose status changed — update Issue labels.
  - Close Issue when task status is 'approved'.

INBOUND (GitHub -> PB):
  - Poll GitHub for issues NOT labelled 'flotilla-managed' (human-written).
  - Create a matching PocketBase task, infer assigned_agent from issue labels.
  - Tag the issue 'flotilla-managed' to prevent re-import.

EXTRA-INBOUND (extra repos -> PB):
  - Repos listed in EXTRA_INBOUND_REPOS are polled for open issues.
  - Each issue is imported into PocketBase once (fingerprinted by repo+number in description).
  - Flotilla-managed label is applied in the source repo to mark as synced.

Runs every 5 minutes via launchd (fleet.github.plist).
Uses `gh` CLI (already auth'd) for all GitHub operations.
Stores last-synced state in ~/fleet/logs/gh_sync_offset.json.
"""

import subprocess
import json
import os
import time
import requests
from datetime import datetime

FLEET_DIR = "/Users/miguelrodriguez/projects/agentic-fleet-hub/fleet"
PB_URL = "http://127.0.0.1:8090/api"
GITHUB_REPO = "UrsushoribilisMusic/agentic-fleet-hub"
OFFSET_FILE = f"{FLEET_DIR}/logs/gh_sync_offset.json"
LOG_FILE = f"{FLEET_DIR}/logs/github_sync.log"
GH_BIN = "/opt/homebrew/bin/gh"

# Extra repos to pull issues FROM into PocketBase (inbound only — these have their own kanban)
EXTRA_INBOUND_REPOS = [
    {"repo": "UrsushoribilisMusic/privatecore-ios", "project": "PrivateCore iOS"},
]

# Map PocketBase task statuses to GitHub issue labels
STATUS_LABEL_MAP = {
    "todo":                   "flotilla:todo",
    "in_progress":            "flotilla:in-progress",
    "peer_review":            "flotilla:peer-review",
    "waiting_human":          "flotilla:waiting-human",
    "waiting_human_notified": "flotilla:waiting-human",
    "approved":               "flotilla:approved",
    "backlog":                "flotilla:backlog",
}

FLOTILLA_LABEL = "flotilla-managed"
ALL_STATUS_LABELS = list(STATUS_LABEL_MAP.values())

os.makedirs(f"{FLEET_DIR}/logs", exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line, end="")


def load_offset():
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE) as f:
                data = json.load(f)
                if "extra_repos" not in data:
                    data["extra_repos"] = {}
                return data
        except Exception:
            pass
    return {"last_gh_issue": 0, "last_pb_scan": "", "extra_repos": {}}


def save_offset(data):
    with open(OFFSET_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── PocketBase helpers ────────────────────────────────────────────────────────

def pb_get(path, params=None):
    try:
        r = requests.get(f"{PB_URL}/{path}", params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        log(f"PB GET error {path}: {e}")
        return None


def pb_patch(path, data):
    try:
        r = requests.patch(f"{PB_URL}/{path}", json=data, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        log(f"PB PATCH error {path}: {e}")
        return None


def pb_post(path, data):
    try:
        r = requests.post(f"{PB_URL}/{path}", json=data, timeout=10)
        return r.json() if r.status_code in (200, 201) else None
    except Exception as e:
        log(f"PB POST error {path}: {e}")
        return None


def get_all_tasks():
    result = pb_get("collections/tasks/records", {
        "perPage": 200,
        "sort": "created",
        "filter": 'status != "approved"',
    })
    return result.get("items", []) if result else []


def close_approved_issues(offset):
    """Close GitHub issues for tasks that have moved to 'approved'."""
    result = pb_get("collections/tasks/records", {
        "perPage": 200,
        "filter": 'status = "approved" && gh_issue_id > 0',
    })
    if not result:
        return
    closed_set = set(offset.get("closed_gh_issues", []))
    changed = False
    for task in result.get("items", []):
        n = task.get("gh_issue_id", 0)
        if n and n not in closed_set:
            close_github_issue(n)
            set_issue_labels(n, "approved")
            closed_set.add(n)
            changed = True
    if changed:
        offset["closed_gh_issues"] = list(closed_set)
        save_offset(offset)


# ── GitHub helpers (via gh CLI) ───────────────────────────────────────────────

def gh(*args, input_text=None, repo=None):
    """Run a gh CLI command against repo (defaults to GITHUB_REPO). Returns (stdout, returncode)."""
    cmd = [GH_BIN, "--repo", repo or GITHUB_REPO] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            input=input_text,
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        log(f"gh CLI error ({' '.join(args[:3])}): {e}")
        return "", 1


def ensure_labels(repo=None):
    """Create flotilla status labels and flotilla-managed label if missing."""
    labels_needed = {FLOTILLA_LABEL: "0075ca"} | {v: "e4e669" for v in ALL_STATUS_LABELS}
    out, _ = gh("label", "list", "--json", "name", "--limit", "100", repo=repo)
    try:
        existing = {item["name"] for item in json.loads(out)}
    except Exception:
        existing = set()
    for name, color in labels_needed.items():
        if name not in existing:
            gh("label", "create", name, "--color", color, "--force", repo=repo)
            log(f"Created GitHub label '{name}' in {repo or GITHUB_REPO}")


def create_github_issue(title, body):
    """Open a new GitHub issue in the main repo. Returns issue number or None."""
    out, rc = gh("issue", "create",
                 "--title", title,
                 "--body", body,
                 "--label", FLOTILLA_LABEL)
    if rc != 0:
        log(f"Failed to create issue: {out}")
        return None
    # gh returns URL like https://github.com/.../issues/42
    try:
        number = int(out.rstrip("/").split("/")[-1])
        return number
    except Exception:
        log(f"Could not parse issue number from: {out}")
        return None


def set_issue_labels(issue_number, status):
    """Replace status labels on an issue to reflect current PB status."""
    status_label = STATUS_LABEL_MAP.get(status)
    if not status_label:
        return

    # Remove all other status labels, add correct one
    out, _ = gh("issue", "view", str(issue_number), "--json", "labels")
    try:
        current_labels = [l["name"] for l in json.loads(out).get("labels", [])]
    except Exception:
        current_labels = []

    for old in current_labels:
        if old in ALL_STATUS_LABELS and old != status_label:
            gh("issue", "edit", str(issue_number), "--remove-label", old)

    if status_label not in current_labels:
        gh("issue", "edit", str(issue_number), "--add-label", status_label)


def close_github_issue(issue_number):
    gh("issue", "close", str(issue_number))
    log(f"Closed GitHub issue #{issue_number}")


def find_existing_issue_by_title(title):
    """Return issue number if a flotilla-managed issue with this title already exists (open or closed)."""
    out, rc = gh("issue", "list",
                 "--state", "all",
                 "--label", FLOTILLA_LABEL,
                 "--json", "number,title",
                 "--limit", "200")
    if rc != 0:
        return None
    try:
        for issue in json.loads(out):
            if issue["title"] == title:
                return issue["number"]
    except Exception:
        pass
    return None


def get_new_human_issues(last_seen_number):
    """Return GitHub issues from the main repo with no flotilla-managed label and number > last_seen."""
    out, rc = gh("issue", "list",
                 "--state", "all",
                 "--json", "number,title,body,labels,assignees",
                 "--limit", "50")
    if rc != 0:
        return []
    try:
        issues = json.loads(out)
    except Exception:
        return []

    new_issues = []
    for issue in issues:
        n = issue["number"]
        if n <= last_seen_number:
            continue
        label_names = [l["name"] for l in issue.get("labels", [])]
        if FLOTILLA_LABEL in label_names:
            continue  # already managed
        new_issues.append(issue)
    return new_issues


def get_all_open_issues_from_repo(repo):
    """Return all open issues from an extra repo."""
    out, rc = gh("issue", "list",
                 "--state", "open",
                 "--json", "number,title,body,labels,assignees",
                 "--limit", "200",
                 repo=repo)
    if rc != 0:
        log(f"Failed to list issues from {repo}: {out}")
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def infer_agent_from_labels(label_names):
    """Guess assigned_agent from issue labels. Defaults to 'clau'."""
    agents = ["clau", "gem", "codi", "misty", "gemma", "openclaw", "scout", "echo", "closer"]
    for label in label_names:
        for agent in agents:
            if agent in label.lower():
                return agent
    return "clau"


# ── Outbound: PB -> GitHub ────────────────────────────────────────────────────

EXTRA_REPO_PREFIXES = tuple(
    f"[{cfg['repo'].split('/')[-1].upper()}]" for cfg in EXTRA_INBOUND_REPOS
)


def is_extra_repo_task(title):
    """Return True if this task was imported from an extra repo (not the hub)."""
    return title.startswith(EXTRA_REPO_PREFIXES)


def sync_outbound(tasks, offset):
    changed = False
    for task in tasks:
        task_id = task["id"]
        gh_issue_id = task.get("gh_issue_id") or 0
        status = task.get("status", "todo")
        title = task.get("title", "(untitled)")
        description = task.get("description", "")

        # Extra-repo tasks (e.g. PC-*) live in a different GitHub repo.
        # Skip outbound label/issue management for them — their repo owns their labels.
        if is_extra_repo_task(title):
            continue

        if not gh_issue_id:
            # Check for existing issue with same title before creating to avoid duplicates
            existing = find_existing_issue_by_title(title)
            if existing:
                pb_patch(f"collections/tasks/records/{task_id}", {"gh_issue_id": existing})
                set_issue_labels(existing, status)
                log(f"OUTBOUND: Linked existing issue #{existing} to task '{title}' (dedup)")
                changed = True
            else:
                # Create a new GitHub issue for this task
                body = f"{description}\n\n---\n*PocketBase task ID: `{task_id}`*"
                number = create_github_issue(title, body)
                if number:
                    pb_patch(f"collections/tasks/records/{task_id}", {"gh_issue_id": number})
                    set_issue_labels(number, status)
                    log(f"OUTBOUND: Created issue #{number} for task '{title}'")
                    changed = True
        else:
            # Update labels to reflect current status
            set_issue_labels(gh_issue_id, status)
            if status == "approved":
                close_github_issue(gh_issue_id)
                log(f"OUTBOUND: Closed issue #{gh_issue_id} (task approved)")

    return changed


# ── Inbound: GitHub -> PB ─────────────────────────────────────────────────────

def sync_inbound(offset):
    last_seen = offset.get("last_gh_issue", 0)
    new_issues = get_new_human_issues(last_seen)
    if not new_issues:
        return False

    changed = False
    for issue in sorted(new_issues, key=lambda x: x["number"]):
        number = issue["number"]
        title = issue.get("title", f"GitHub issue #{number}")
        body = issue.get("body", "") or ""
        label_names = [l["name"] for l in issue.get("labels", [])]
        agent = infer_agent_from_labels(label_names)

        description = f"{body}\n\n---\n*Imported from GitHub issue #{number}*"
        task = pb_post("collections/tasks/records", {
            "title": title,
            "description": description,
            "status": "todo",
            "assigned_agent": agent,
            "gh_issue_id": number,
        })
        if task:
            # Tag the issue flotilla-managed to prevent re-import
            _, label_rc = gh("issue", "edit", str(number), "--add-label", FLOTILLA_LABEL)
            if label_rc != 0:
                log(f"INBOUND: WARNING — issue #{number} imported to PB but GitHub label failed.")
            else:
                log(f"INBOUND: Imported issue #{number} as PB task '{title}' -> {agent}")
            # Always advance offset regardless of label result to prevent duplicate PB task creation
            offset["last_gh_issue"] = max(offset.get("last_gh_issue", 0), number)
            changed = True

    return changed


def pb_task_exists_for_issue(repo_key, issue_number):
    """Check if a PB task already exists for this extra-repo issue by fingerprint in description."""
    fingerprint = f"[{repo_key}#{issue_number}]"
    result = pb_get("collections/tasks/records", {
        "filter": f'description ~ "{fingerprint}"',
        "perPage": 1,
    })
    return bool(result and result.get("items"))


def sync_extra_repo_inbound(repo_cfg):
    """Import open issues from an extra repo (e.g. privatecore-ios) into PocketBase."""
    repo = repo_cfg["repo"]
    project = repo_cfg["project"]
    repo_key = repo.split("/")[-1]
    label_to_status = {v: k for k, v in STATUS_LABEL_MAP.items()}

    issues = get_all_open_issues_from_repo(repo)
    if not issues:
        return False

    changed = False
    for issue in sorted(issues, key=lambda x: x["number"]):
        number = issue["number"]

        if pb_task_exists_for_issue(repo_key, number):
            continue  # already imported

        title = issue.get("title", f"{repo_key} issue #{number}")
        body = issue.get("body", "") or ""
        label_names = [l["name"] for l in issue.get("labels", [])]
        agent = infer_agent_from_labels(label_names)

        # Honour any flotilla status label already on the issue
        status = "todo"
        for lname in label_names:
            if lname in label_to_status:
                status = label_to_status[lname]
                break

        description = (
            f"**Project:** {project}\n\n"
            f"{body}\n\n"
            f"---\n*Synced from {repo} issue #{number} [{repo_key}#{number}]*"
        )
        task = pb_post("collections/tasks/records", {
            "title": f"[{repo_key.upper()}] {title}",
            "description": description,
            "status": status,
            "assigned_agent": agent,
            "gh_issue_id": number,
        })
        if task:
            gh("issue", "edit", str(number), "--add-label", FLOTILLA_LABEL, repo=repo)
            log(f"EXTRA-INBOUND [{repo_key}]: #{number} '{title}' -> agent:{agent} status:{status}")
            changed = True

    return changed


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    log("GitHub sync started")
    ensure_labels()
    for repo_cfg in EXTRA_INBOUND_REPOS:
        ensure_labels(repo=repo_cfg["repo"])

    while True:
        offset = load_offset()
        try:
            tasks = get_all_tasks()
            out_changed = sync_outbound(tasks, offset)
            in_changed = sync_inbound(offset)
            close_approved_issues(offset)

            for repo_cfg in EXTRA_INBOUND_REPOS:
                if sync_extra_repo_inbound(repo_cfg):
                    in_changed = True

            if out_changed or in_changed:
                save_offset(offset)
        except Exception as e:
            log(f"Sync cycle error: {e}")

        time.sleep(300)  # 5-minute interval


if __name__ == "__main__":
    main()
