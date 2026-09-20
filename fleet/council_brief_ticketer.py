#!/usr/bin/env python3
"""
council_brief_ticketer.py — Generate GitHub issues from approved Council decision briefs.

Run modes:
  (no args)         Process all decision_briefs with status='approved'.
  --brief <id>      Process a single brief by PocketBase ID.
  --dry-run         Print what would happen without touching GitHub or PocketBase.

Idempotency: Before creating an issue, checks for a flotilla-managed issue with the same
title. If one exists, writes its number back into the ticket_plan without creating a duplicate.

Miguel approval gate: Only processes briefs where approved_by is non-empty.

Ambiguity gate: If ticket_plan is null/empty/unparseable, or any ticket has no title,
moves the brief to waiting_human rather than guessing.

Issue links are written back into each ticket_plan item as gh_issue_id + gh_issue_url.
The brief status is set to 'ticketed' once all issues are created successfully.
"""

import argparse
import json
import os
import subprocess
import sys
import requests
from datetime import datetime

PB_URL = "http://127.0.0.1:8090/api"
GITHUB_REPO = "UrsushoribilisMusic/agentic-fleet-hub"
GH_BIN = "/opt/homebrew/bin/gh"

FLOTILLA_LABEL = "flotilla-managed"
TODO_LABEL = "flotilla:todo"
KNOWN_AGENTS = {"clau", "gem", "codi", "misty", "gemma", "openclaw", "scout", "echo", "closer"}

FLEET_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(FLEET_DIR, "logs", "council_brief_ticketer.log")
os.makedirs(os.path.join(FLEET_DIR, "logs"), exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)


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


# ── GitHub helpers ────────────────────────────────────────────────────────────

def gh(*args, repo=None):
    """Run a gh CLI command. Returns (stdout, returncode)."""
    cmd = [GH_BIN, "--repo", repo or GITHUB_REPO] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        log(f"gh CLI error ({' '.join(str(a) for a in args[:3])}): {e}")
        return "", 1


def ensure_labels():
    """Create flotilla labels if missing. Silently skips existing ones."""
    labels_needed = {
        FLOTILLA_LABEL: "e4e669",
        TODO_LABEL: "0075ca",
    }
    out, _ = gh("label", "list", "--json", "name", "--limit", "200")
    try:
        existing = {item["name"] for item in json.loads(out)}
    except Exception:
        existing = set()
    for name, color in labels_needed.items():
        if name not in existing:
            gh("label", "create", name, "--color", color, "--force")
            log(f"Created GitHub label '{name}'")


def find_existing_issue_by_title(title):
    """Return issue number if a flotilla-managed issue with this exact title exists."""
    out, rc = gh("issue", "list",
                 "--state", "all",
                 "--label", FLOTILLA_LABEL,
                 "--json", "number,title",
                 "--limit", "500")
    if rc != 0:
        return None
    try:
        for issue in json.loads(out):
            if issue["title"] == title:
                return issue["number"]
    except Exception:
        pass
    return None


def create_github_issue(title, body, labels):
    """Open a new GitHub issue. Returns issue number or None on failure."""
    label_args = []
    for label in labels:
        label_args += ["--label", label]
    out, rc = gh("issue", "create", "--title", title, "--body", body, *label_args)
    if rc != 0:
        log(f"  gh error creating issue {title!r}: {out}")
        return None
    try:
        return int(out.rstrip("/").split("/")[-1])
    except Exception:
        log(f"  Could not parse issue number from: {out}")
        return None


# ── Body builder ──────────────────────────────────────────────────────────────

def build_issue_body(ticket, brief, index, total):
    """Compose the GitHub issue body from brief context + per-ticket fields."""
    summary = brief.get("summary", "").strip()
    recommended_approach = brief.get("recommended_approach", "").strip()
    known_risks = brief.get("known_risks", "").strip()
    definition_of_done = brief.get("definition_of_done", "").strip()
    approved_by = brief.get("approved_by", "").strip()
    brief_id = brief.get("id", "")
    goal_id = brief.get("goal_id", "")
    estimate = ticket.get("estimate_hours", "?")
    agent = ticket.get("assigned_agent", "").strip()

    dep_note = ""
    if index > 0:
        ticket_plan = brief.get("ticket_plan") or []
        if index < len(ticket_plan):
            prev_title = (ticket_plan[index - 1].get("title") or "").strip()
            if prev_title:
                dep_note = f"\n**Depends on:** {prev_title}\n"

    body = f"""## Context

{summary}

### Recommended Approach

{recommended_approach}
{dep_note}
## Acceptance Criteria

{definition_of_done}

## Known Risks

{known_risks}

## Details

| Field | Value |
|---|---|
| Assigned agent | {agent or '(any)'} |
| Estimate | {estimate}h |
| Ticket | {index + 1} of {total} in brief |
| Decision brief | `{brief_id}` (goal: `{goal_id}`) |
| Approved by | {approved_by} |

---
*Generated from Council decision brief `{brief_id}` by `fleet/council_brief_ticketer.py`*
"""
    return body.strip()


# ── Core processing ───────────────────────────────────────────────────────────

def process_brief(brief, dry_run=False):
    brief_id = brief["id"]
    approved_by = (brief.get("approved_by") or "").strip()
    ticket_plan = brief.get("ticket_plan")
    summary = (brief.get("summary") or "(no summary)")[:80]

    log(f"Brief {brief_id}: {summary!r}")

    # Hard gate — Miguel must have approved
    if not approved_by:
        log(f"  SKIP: approved_by is empty — not yet approved by Miguel")
        return False

    # Ambiguity gate — ticket_plan must be a parseable non-empty list
    if not isinstance(ticket_plan, list) or not ticket_plan:
        log(f"  AMBIGUOUS: ticket_plan is null/empty — moving to waiting_human")
        if not dry_run:
            pb_patch(f"collections/decision_briefs/records/{brief_id}", {"status": "waiting_human"})
        return False

    total = len(ticket_plan)
    updated_plan = list(ticket_plan)  # copy; we mutate entries in place
    all_created = True

    for i, ticket in enumerate(ticket_plan):
        title = (ticket.get("title") or "").strip()
        if not title:
            log(f"  AMBIGUOUS: ticket #{i} has no title — moving brief to waiting_human")
            if not dry_run:
                pb_patch(f"collections/decision_briefs/records/{brief_id}", {"status": "waiting_human"})
            return False

        agent = (ticket.get("assigned_agent") or "").strip()

        # Idempotency: prefer cached gh_issue_id from a previous run, else search GitHub
        existing_number = ticket.get("gh_issue_id") or None
        if not existing_number:
            existing_number = find_existing_issue_by_title(title)

        if existing_number:
            log(f"  EXISTS #{existing_number}: {title!r} — skipping creation")
            updated_plan[i] = dict(ticket)
            updated_plan[i]["gh_issue_id"] = existing_number
            updated_plan[i]["gh_issue_url"] = f"https://github.com/{GITHUB_REPO}/issues/{existing_number}"
            continue

        # Build labels
        labels = [FLOTILLA_LABEL, TODO_LABEL]
        if agent and agent in KNOWN_AGENTS:
            labels.append(f"agent:{agent}")

        body = build_issue_body(ticket, brief, i, total)

        if dry_run:
            log(f"  [DRY RUN] Would create ({i+1}/{total}): {title!r} | labels: {labels}")
            updated_plan[i] = dict(ticket)
            updated_plan[i]["gh_issue_id"] = 0
            updated_plan[i]["gh_issue_url"] = f"https://github.com/{GITHUB_REPO}/issues/DRY_RUN"
            continue

        number = create_github_issue(title, body, labels)
        if number is None:
            log(f"  FAILED: could not create issue for {title!r}")
            all_created = False
            continue

        url = f"https://github.com/{GITHUB_REPO}/issues/{number}"
        log(f"  CREATED #{number} ({i+1}/{total}): {title!r}")
        updated_plan[i] = dict(ticket)
        updated_plan[i]["gh_issue_id"] = number
        updated_plan[i]["gh_issue_url"] = url

    # Write back updated ticket_plan with issue numbers
    if not dry_run:
        pb_patch(f"collections/decision_briefs/records/{brief_id}", {"ticket_plan": updated_plan})
        log(f"  Wrote issue links back to brief {brief_id}")

        if all_created:
            pb_patch(f"collections/decision_briefs/records/{brief_id}", {"status": "ticketed"})
            log(f"  Marked brief {brief_id} as ticketed")
        else:
            log(f"  Some issues failed — brief left in 'approved' for retry")
    else:
        log(f"  [DRY RUN] Would PATCH ticket_plan + status=ticketed on brief {brief_id}")

    return all_created


def main():
    parser = argparse.ArgumentParser(
        description="Generate GitHub issues from approved Council decision briefs"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making changes"
    )
    parser.add_argument(
        "--brief", metavar="ID",
        help="Process a single brief by PocketBase ID (any status, must have approved_by set)"
    )
    args = parser.parse_args()

    if args.dry_run:
        log("=== DRY RUN — no GitHub issues or PocketBase updates will be made ===")

    if not args.dry_run:
        ensure_labels()

    if args.brief:
        result = pb_get(f"collections/decision_briefs/records/{args.brief}")
        if not result or "id" not in result:
            log(f"ERROR: Could not fetch brief '{args.brief}' from PocketBase")
            sys.exit(1)
        briefs = [result]
    else:
        result = pb_get(
            "collections/decision_briefs/records",
            params={"filter": 'status="approved"', "perPage": 100}
        )
        if not result:
            log("ERROR: Could not fetch decision_briefs from PocketBase")
            sys.exit(1)
        briefs = result.get("items", [])
        log(f"Found {len(briefs)} approved decision_brief(s)")

    success = 0
    for brief in briefs:
        ok = process_brief(brief, dry_run=args.dry_run)
        if ok:
            success += 1

    log(f"Done: {success}/{len(briefs)} brief(s) fully ticketed.")


if __name__ == "__main__":
    main()
