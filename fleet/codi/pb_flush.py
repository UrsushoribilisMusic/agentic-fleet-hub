#!/usr/bin/env python3
"""Flush queued writes without dropping failures or repeating verified reviews.

Implementation progress needs a task-linked canonical commit. Approval needs a
current independent approval comment with real canonical commit references.
Older implementation commits and non-PC ticket names are supported.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.parse
import urllib.request

PENDING = Path('/Users/miguelrodriguez/fleet/codi/pb_pending_writes.json')
PB = 'http://127.0.0.1:8090/api/collections'
HUB = Path('/Users/miguelrodriguez/projects/agentic-fleet-hub')
PROGRESS_STATES = {'peer_review', 'approved', 'merged'}


def request(collection, record_id='', data=None, method='GET', params=None):
    url = f'{PB}/{collection}/records' + (f'/{record_id}' if record_id else '')
    if params:
        url += '?' + urllib.parse.urlencode(params)
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=payload, method=method,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read())


def canonical_repos():
    repos = [HUB]
    meta = json.loads((HUB/'AGENTS/CONFIG/fleet_meta.json').read_text())
    for project in meta.get('projects', []):
        if not project.get('is_active'):
            continue
        path = (HUB / project.get('repo_path', '.')).resolve()
        # SiliconOracle is the maintained fork; leave retired PrivateCore alone.
        if 'private-core' not in str(path) and (path/'.git').exists() and path not in repos:
            repos.append(path)
    return repos


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                           text=True, timeout=10)


def branches(repo):
    return [ref for ref in ['refs/heads/main', 'refs/heads/master']
            if git(repo, 'show-ref', '--verify', '--quiet', ref).returncode == 0]


def commit_verified(reference, repos):
    if not re.fullmatch(r'[0-9a-f]{7,40}', reference):
        return False
    for repo in repos:
        commit = git(repo, 'rev-parse', '--verify', reference+'^{commit}')
        if commit.returncode:
            continue
        if any(git(repo, 'merge-base', '--is-ancestor', commit.stdout.strip(), ref).returncode == 0
               for ref in branches(repo)):
            return True
    return False


def task_commit_exists(task, repos):
    match = re.match(r'([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b', task.get('title', ''))
    tokens = [task['id']] + ([match.group(1)] if match else [])
    for repo in repos:
        for ref in branches(repo):
            for token in tokens:
                result = git(repo, 'log', ref, '--format=%s', '--fixed-strings', '--grep='+token)
                if result.returncode == 0 and re.search(r'(?<![\w-])'+re.escape(token)+r'(?![\w-])', result.stdout):
                    return True
    return False


def timestamp(value):
    dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def validate_progress(op, task, repos, comments):
    target = op.get('data', {}).get('status')
    if target not in PROGRESS_STATES:
        return True, 'ordinary write'
    current = task.get('status')
    if target in {'approved', 'merged'}:
        if str(task.get('assigned_agent', '')).lower() in {'codi', 'codex'}:
            return False, 'self-approval is forbidden'
        if current == target:
            return True, 'already applied'
        if current not in ({'peer_review'} if target == 'approved' else {'approved'}):
            return False, f'cannot move {current} to {target}'
        for comment in comments:
            if comment.get('agent', '').lower() not in {'codi', 'codex'} or comment.get('type') != 'approval':
                continue
            if comment.get('task_id') != task['id']:
                continue
            if timestamp(comment['created']) < timestamp(task['updated']):
                continue
            references = re.findall(r'\b[0-9a-f]{7,40}\b', comment.get('content', ''))
            if references and all(commit_verified(ref, repos) for ref in references):
                return True, 'independent approval with verified canonical commits'
        return False, 'no current independent approval with verifiable commits'
    if current in {'approved', 'merged'}:
        return False, 'refusing to regress a completed task'
    if current == 'peer_review':
        return True, 'already applied'
    return (True, 'task-linked canonical commit') if task_commit_exists(task, repos) else (False, 'no task-linked canonical commit')


def flush(path=PENDING, api=request, repos=None, dry_run=False):
    path = Path(path)
    if not path.exists():
        print('[pb_flush] no pending writes')
        return 0
    repos = repos if repos is not None else canonical_repos()
    with path.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not path.exists():
            return 0
        ops = json.loads(path.read_text())
        retained = []
        for op in ops:
            method = op.get('method', 'POST').upper()
            collection = op['collection']
            record_id = op.get('id', '')
            try:
                if method == 'PATCH' and collection == 'tasks' and op.get('data', {}).get('status') in PROGRESS_STATES:
                    task = api('tasks', record_id)
                    comments = api('comments', params={'filter': f'task_id = "{record_id}" && type = "approval"',
                                                      'sort': '-created', 'perPage': 100}).get('items', [])
                    valid, reason = validate_progress(op, task, repos, comments)
                    if not valid:
                        raise ValueError(reason)
                    print(f'[pb_flush] verified {record_id}: {reason}')
                    if task.get('status') == op['data']['status']:
                        continue
                if not dry_run:
                    api(collection, record_id, data=op.get('data', {}), method=method)
                print(f'[pb_flush] {"WOULD " if dry_run else ""}{method} {collection}/{record_id}')
            except Exception as exc:
                print(f'[pb_flush] retained {method} {collection}/{record_id}: {exc}', file=sys.stderr)
                retained.append(dict(op, _attempts=int(op.get('_attempts', 0))+1, _last_error=str(exc)))
        if not dry_run:
            if retained:
                tmp = path.with_suffix('.tmp')
                tmp.write_text(json.dumps(retained, indent=2)+'\n')
                tmp.replace(path)
            else:
                path.unlink()
        print(f'[pb_flush] {len(ops)-len(retained)} verified/applied; {len(retained)} retained')
        return 1 if retained else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--pending', type=Path, default=PENDING)
    args = parser.parse_args()
    raise SystemExit(flush(args.pending, dry_run=args.dry_run))
