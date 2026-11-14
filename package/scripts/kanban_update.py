#!/usr/bin/env python3
"""
kanban_update.py — AgentFleet Kanban Bridge
Updates the Status field of a GitHub Project v2 item.

Usage:
    python scripts/kanban_update.py --item ITEM_ID --status "In Progress"
    python scripts/kanban_update.py --ticket 14 --status Done

Requirements:
    - GITHUB_TOKEN env var (classic token with repo + project scopes)
    - KANBAN_ORG env var
    - KANBAN_PROJECT_NUMBER env var

The script automatically resolves the project node ID and the Status field's
single-select option ID before applying the mutation.
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
        print("[kanban_update] ERROR: GITHUB_TOKEN not set.", file=sys.stderr)
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
        print(f"[kanban_update] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


FETCH_PROJECT_QUERY = """
query($org: String!, $number: Int!) {
  organization(login: $org) {
    projectV2(number: $number) {
      id
      fields(first: 20) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id name
            options { id name }
          }
        }
      }
      items(first: 100) {
        nodes {
          id
          content {
            ... on Issue { number }
            ... on PullRequest { number }
          }
        }
      }
    }
  }
}
"""

UPDATE_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId
    itemId: $itemId
    fieldId: $fieldId
    value: { singleSelectOptionId: $optionId }
  }) {
    projectV2Item { id }
  }
}
"""


def main():
    parser = argparse.ArgumentParser(description="Update GitHub Project v2 item status")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--item", help="Project item node ID (starts with PVTI_)")
    group.add_argument("--ticket", type=int, help="Issue/PR number (e.g. 14)")
    parser.add_argument("--status", required=True, help="New status value (e.g. 'In Progress', 'Done')")
    args = parser.parse_args()

    org = os.environ.get("KANBAN_ORG")
    project_number = os.environ.get("KANBAN_PROJECT_NUMBER")
    if not org or not project_number:
        print("[kanban_update] ERROR: Set KANBAN_ORG and KANBAN_PROJECT_NUMBER env vars.", file=sys.stderr)
        sys.exit(1)

    # Fetch project metadata
    data = gh_graphql(FETCH_PROJECT_QUERY, {"org": org, "number": int(project_number)})
    project = data.get("data", {}).get("organization", {}).get("projectV2")
    if not project:
        print(f"[kanban_update] Could not load project: {data.get('errors')}", file=sys.stderr)
        sys.exit(1)

    project_id = project["id"]

    # Resolve Status field and option ID
    status_field = None
    status_option_id = None
    for field in project["fields"]["nodes"]:
        if field.get("name", "").lower() == "status":
            status_field = field
            for opt in field.get("options", []):
                if opt["name"].lower() == args.status.lower():
                    status_option_id = opt["id"]
                    break
            break

    if not status_field:
        print("[kanban_update] ERROR: 'Status' field not found in project.", file=sys.stderr)
        sys.exit(1)
    if not status_option_id:
        available = [o["name"] for o in status_field.get("options", [])]
        print(f"[kanban_update] ERROR: Status '{args.status}' not found. Available: {available}", file=sys.stderr)
        sys.exit(1)

    # Resolve item ID
    item_id = args.item
    if args.ticket:
        for item in project["items"]["nodes"]:
            content = item.get("content") or {}
            if content.get("number") == args.ticket:
                item_id = item["id"]
                break
        if not item_id:
            print(f"[kanban_update] ERROR: Ticket #{args.ticket} not found in project.", file=sys.stderr)
            sys.exit(1)

    # Apply mutation
    result = gh_graphql(UPDATE_MUTATION, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": status_field["id"],
        "optionId": status_option_id,
    })

    if result.get("errors"):
        print(f"[kanban_update] Mutation failed: {result['errors']}", file=sys.stderr)
        sys.exit(1)

    print(f"[kanban_update] Ticket #{args.ticket or item_id} → '{args.status}' ✓")


if __name__ == "__main__":
    main()
