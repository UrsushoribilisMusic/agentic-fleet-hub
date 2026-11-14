#!/usr/bin/env python3
"""
kanban_fetch.py — AgentFleet Kanban Bridge
Fetches GitHub Project v2 items and prints a status summary.

Usage:
    python scripts/kanban_fetch.py [--status STATUS] [--format json|table]

Requirements:
    - GITHUB_TOKEN env var (classic token with repo + project scopes)
    - KANBAN_ORG env var (GitHub org name or username)
    - KANBAN_PROJECT_NUMBER env var (GitHub Project v2 number, e.g. "1")

Example:
    export GITHUB_TOKEN=ghp_...
    export KANBAN_ORG=MyOrg
    export KANBAN_PROJECT_NUMBER=1
    python scripts/kanban_fetch.py --status "In Progress"
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

GITHUB_API = "https://api.github.com/graphql"


def gh_graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[kanban_fetch] ERROR: GITHUB_TOKEN not set.", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GITHUB_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[kanban_fetch] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


QUERY = """
query($org: String!, $number: Int!, $cursor: String) {
  organization(login: $org) {
    projectV2(number: $number) {
      title
      items(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2Field { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2Field { name } } }
            }
          }
          content {
            ... on Issue {
              number title url state
              assignees(first: 5) { nodes { login } }
              labels(first: 5) { nodes { name } }
            }
            ... on PullRequest {
              number title url state
              assignees(first: 5) { nodes { login } }
            }
          }
        }
      }
    }
  }
}
"""


def fetch_all_items(org: str, project_number: int) -> list[dict]:
    items = []
    cursor = None
    while True:
        data = gh_graphql(QUERY, {"org": org, "number": project_number, "cursor": cursor})
        project = data.get("data", {}).get("organization", {}).get("projectV2")
        if not project:
            errors = data.get("errors", [])
            print(f"[kanban_fetch] Could not load project: {errors}", file=sys.stderr)
            sys.exit(1)

        nodes = project["items"]["nodes"]
        for node in nodes:
            # Extract field values (Status, Priority, etc.)
            fields = {}
            for fv in node.get("fieldValues", {}).get("nodes", []):
                fname = fv.get("field", {}).get("name", "")
                val = fv.get("text") or fv.get("name") or (str(fv["number"]) if "number" in fv else None)
                if fname and val is not None:
                    fields[fname] = val

            content = node.get("content") or {}
            items.append({
                "id":        node["id"],
                "number":    content.get("number"),
                "title":     content.get("title", "(no title)"),
                "url":       content.get("url", ""),
                "state":     content.get("state", ""),
                "status":    fields.get("Status", ""),
                "priority":  fields.get("Priority", ""),
                "assignees": [a["login"] for a in content.get("assignees", {}).get("nodes", [])],
                "labels":    [l["name"] for l in content.get("labels", {}).get("nodes", [])],
                "fields":    fields,
            })

        page_info = project["items"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    return items


def print_table(items: list[dict]):
    print(f"{'#':<5} {'Status':<20} {'Priority':<12} {'Assignee':<20} {'Title'}")
    print("-" * 90)
    for item in items:
        num = f"#{item['number']}" if item["number"] else "-"
        assignee = ", ".join(item["assignees"]) or "-"
        print(f"{num:<5} {item['status']:<20} {item['priority']:<12} {assignee:<20} {item['title'][:50]}")


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub Project v2 Kanban items")
    parser.add_argument("--status", help="Filter by status (e.g. 'In Progress', 'Done')")
    parser.add_argument("--format", choices=["json", "table"], default="table")
    args = parser.parse_args()

    org = os.environ.get("KANBAN_ORG")
    project_number = os.environ.get("KANBAN_PROJECT_NUMBER")
    if not org or not project_number:
        print("[kanban_fetch] ERROR: Set KANBAN_ORG and KANBAN_PROJECT_NUMBER env vars.", file=sys.stderr)
        sys.exit(1)

    items = fetch_all_items(org, int(project_number))

    if args.status:
        items = [i for i in items if i["status"].lower() == args.status.lower()]

    if args.format == "json":
        print(json.dumps(items, indent=2))
    else:
        print_table(items)


if __name__ == "__main__":
    main()
