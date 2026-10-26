"""Deterministic availability shared by dispatcher and autonomous wrappers."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

REPO = Path('/Users/miguelrodriguez/projects/agentic-fleet-hub')
META = REPO / 'AGENTS/CONFIG/fleet_meta.json'
FAILURES = REPO / 'fleet/logs/agent_failures.json'


def canonical_agent(agent):
    return {'qwen': 'gemma', 'gemini': 'gem', 'codex': 'codi'}.get(agent, agent)


def utc(value):
    if not value:
        return None
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def availability(agent, meta=None, failures=None, now=None):
    agent = canonical_agent(agent)
    try:
        if meta is None:
            meta = json.loads(META.read_text())
        if failures is None:
            failures = json.loads(FAILURES.read_text()) if FAILURES.exists() else {}
        member = next((a for a in meta.get('team', []) if a.get('heartbeatKey') == agent), {})
        if member.get('available') is False:
            return False, member.get('availabilityReason', 'paused in fleet configuration')
        now = now or datetime.now(timezone.utc)
        failure = failures.get(agent, failures.get('qwen', {}) if agent == 'gemma' else {})
        for value in [member.get('unavailableUntil') or member.get('blocked_until'), failure.get('blocked_until')]:
            until = utc(value)
            if until and until > now:
                return False, f'{failure.get("reason", "unavailable")}; retry after {until.isoformat()}'
        return True, ''
    except (OSError, ValueError, TypeError) as exc:
        return False, f'cannot verify scheduler availability: {type(exc).__name__}'


def quota_retry_seconds(output, default=12 * 3600):
    """Honor the provider's relative reset hint, plus two minutes of clock margin."""
    match = re.search(r'resets?\s+in\s+((?:\d+(?:\.\d+)?\s*[dhms]\s*)+)', output or '', re.I)
    if not match:
        return default
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    seconds = sum(float(n) * units[u.lower()] for n, u in re.findall(r'(\d+(?:\.\d+)?)\s*([dhms])', match.group(1), re.I))
    return max(120, int(seconds) + 120)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', required=True)
    args = parser.parse_args()
    allowed, reason = availability(args.agent)
    if not allowed:
        print(f'[scheduler:{args.agent}] {reason}')
    raise SystemExit(0 if allowed else 1)
