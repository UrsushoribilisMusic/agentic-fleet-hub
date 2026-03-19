#!/usr/bin/env python3
"""
kanban_standup.py — AgentFleet Kanban Bridge
Generates a standup markdown report from:
  - GitHub Project v2 items changed today (via recent commits)
  - In-progress and recently-closed tickets

Usage:
    python scripts/kanban_standup.py [--repo OWNER/REPO] [--days N] [--output FILE]

Requirements:
    - GITHUB_TOKEN env var
    - KANBAN_ORG env var
    - KANBAN_PROJECT_NUMBER env var

Output format matches standups/YYYY-MM-DD.md convention.
"""

import os
import sys
import json
import argparse
import datetime
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com/graphql"
GITHUB_REST = "https://api.github.com"


def gh_graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[kanban_standup] ERROR: GITHUB_TOKEN not set.", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GITHUB_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[kanban_standup] HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def gh_rest(path: str) -> list | dict:
    token = os.environ.get("GITHUB_TOKEN")
    req = urllib.request.Request(
        f"{GITHUB_REST}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return []


PROJECT_QUERY = """
query($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      title
      items(first: 100) {
        nodes {
          updatedAt
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
            }
          }
          content {
            ... on Issue { number title url state }
            ... on PullRequest { number title url state }
          }
        }
      }
    }
  }
}
"""


def fetch_project_items(org: str, number: int) -> tuple[str, list[dict]]:
    data = gh_graphql(PROJECT_QUERY, {"org": org, "number": number})
    project = data.get("data", {}).get("organization", {}).get("projectV2", {})
    title = project.get("title", "Project")
    items = []
    for node in project.get("items", {}).get("nodes", []):
        fields = {}
        for fv in node.get("fieldValues", {}).get("nodes", []):
            fname = fv.get("field", {}).get("name", "")
            if fname:
                fields[fname] = fv.get("name", "")
        content = node.get("content") or {}
        items.append({
            "number":     content.get("number"),
            "title":      content.get("title", "(no title)"),
            "url":        content.get("url", ""),
            "state":      content.get("state", ""),
            "status":     fields.get("Status", ""),
            "updated_at": node.get("updatedAt", ""),
        })
    return title, items


def fetch_recent_commits(repo: str, days: int) -> list[str]:
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
    commits = gh_rest(f"/repos/{repo}/commits?since={since}&per_page=20")
    if not isinstance(commits, list):
        return []
    return [c.get("commit", {}).get("message", "").split("\n")[0] for c in commits]


def generate_standup(project_title: str, items: list[dict], commits: list[str], agent: str, days: int) -> str:
    today = datetime.date.today().isoformat()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    done = [i for i in items if i["status"].lower() == "done" and i["updated_at"] >= cutoff.isoformat()]
    in_progress = [i for i in items if i["status"].lower() in ("in progress", "in-progress")]
    todo = [i for i in items if i["status"].lower() in ("todo", "backlog", "to do")]

    lines = [f"# Standup {today}", "", f"## {agent}", "", "### Done"]
    if done:
        for i in done:
            lines.append(f"- **#{i['number']} {i['title']}** [{i['status']}]({i['url']})")
    else:
        lines.append("- (no items closed today)")

    lines += ["", "### In Progress"]
    if in_progress:
        for i in in_progress:
            lines.append(f"- **#{i['number']} {i['title']}** — {i['url']}")
    else:
        lines.append("- (nothing in progress)")

    lines += ["", "### Today / Up Next"]
    if todo:
        for i in todo[:5]:
            lines.append(f"- #{i['number']} {i['title']}")
    else:
        lines.append("- (backlog empty — check project board)")

    if commits:
        lines += ["", "### Recent Commits"]
        for msg in commits[:10]:
            lines.append(f"- `{msg}`")

    lines += ["", "### Blockers", "- None", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate standup from GitHub Project Kanban")
    parser.add_argument("--repo", help="GitHub repo (owner/name) for commit history", default="")
    parser.add_argument("--days", type=int, default=1, help="Look-back window in days (default: 1)")
    parser.add_argument("--agent", default="Agent", help="Agent name for standup header")
    parser.add_argument("--output", help="Write to file instead of stdout")
    args = parser.parse_args()

    org = os.environ.get("KANBAN_ORG")
    project_number = os.environ.get("KANBAN_PROJECT_NUMBER")
    if not org or not project_number:
        print("[kanban_standup] ERROR: Set KANBAN_ORG and KANBAN_PROJECT_NUMBER.", file=sys.stderr)
        sys.exit(1)

    title, items = fetch_project_items(org, int(project_number))
    commits = fetch_recent_commits(args.repo, args.days) if args.repo else []

    md = generate_standup(title, items, commits, args.agent, args.days)

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
        with open(args.output, "w") as f:
            f.write(md)
        print(f"[kanban_standup] Written to {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
