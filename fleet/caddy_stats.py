#!/usr/bin/env python3
"""
Caddy access-log -> persistent daily traffic store.

Why this exists
---------------
Caddy logs every request across all 12 hosts to /var/log/caddy/access.log with
`roll_size 20mb, roll_keep 5`. At current volume that window is roughly two
weeks. Once a file rotates out, the traffic it recorded is gone — so "how did
that paper do" becomes unanswerable shortly after it stops mattering.

This reads the live log plus every surviving rotated archive, aggregates to
UTC day x host x path, and merges the result into a persistent JSON store that
outlives rotation.

Merge semantics
---------------
Logs only ever LOSE data (rotation truncates the past); they never gain it. So a
recount of an older day can only come back equal or smaller. The merge therefore
takes max() per counter rather than overwriting — a re-run after rotation cannot
silently shrink history. New days are inserted, existing days are lifted, nothing
is ever deleted.

That makes the script idempotent and safe to run as often as you like.

Usage:
    caddy_stats.py [--store PATH] [--emit PATH] [--days N] [--dry-run]
"""

import argparse
import glob
import gzip
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta

LOG_GLOB = "/var/log/caddy/access*.log*"
STORE = "/var/lib/caddy-stats/daily.json"
# NOT under the web root: /stats/* is served statically, so a file there is
# public regardless of the page's client-side auth. server.mjs exposes this
# via the cookie-gated GET /stats/caddy-traffic route instead.
EMIT = "/var/lib/caddy-stats/page.json"

# Requests that are not a human reading a page.
BOT_RE = re.compile(
    r"bot|spider|crawl|curl|wget|python-requests|headlesschrome|"
    r"facebookexternalhit|slackbot|discordbot|preview|monitor|uptime|"
    r"scanner|nmap|zgrab|censys|semrush|ahrefs|dataprovider|expanse",
    re.I,
)
# Assets are noise for a "what did people read" view.
ASSET_RE = re.compile(r"\.(css|js|map|png|jpe?g|gif|svg|ico|woff2?|ttf|webp|avif)$", re.I)


def day_of(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def iter_log_lines():
    for path in sorted(glob.glob(LOG_GLOB)):
        opener = gzip.open if path.endswith(".gz") else open
        try:
            with opener(path, "rt", errors="ignore") as fh:
                for line in fh:
                    if '"handled request"' not in line:
                        continue
                    yield line
        except OSError as exc:
            print(f"WARNING: could not read {path}: {exc}", file=sys.stderr)


def scan(cutoff_day: str):
    """Aggregate the logs into {day: {host: {path: {...}}}} plus referrers."""
    hits = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    ips = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    refs = defaultdict(lambda: defaultdict(int))
    bots = defaultdict(int)

    for line in iter_log_lines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("ts")
        if not ts:
            continue
        day = day_of(ts)
        if day < cutoff_day:
            continue

        req = d.get("request", {})
        headers = req.get("headers", {}) or {}
        ua = (headers.get("User-Agent") or [""])[0]
        host = (req.get("host") or "").lower().replace("www.", "")
        uri = (req.get("uri") or "/").split("?")[0]
        method = req.get("method")
        status = d.get("status", 0)

        if method not in ("GET",) or status >= 400:
            continue
        if BOT_RE.search(ua):
            bots[day] += 1
            continue
        if ASSET_RE.search(uri):
            continue

        hits[day][host][uri] += 1
        ip = req.get("client_ip") or req.get("remote_ip") or ""
        if ip:
            ips[day][host][uri].add(ip)

        ref = (headers.get("Referer") or [""])[0]
        if ref:
            # Group by referring host; the full URL is high-cardinality noise.
            m = re.match(r"https?://([^/]+)", ref)
            rhost = (m.group(1) if m else ref).lower().replace("www.", "")
            if rhost != host:
                refs[day][rhost] += 1
        else:
            refs[day]["(direct)"] += 1

    out = {}
    for day, hostmap in hits.items():
        out[day] = {
            "hosts": {
                host: {
                    "paths": {
                        p: {"views": c, "uniques": len(ips[day][host][p])}
                        for p, c in pathmap.items()
                    },
                    "views": sum(pathmap.values()),
                    "uniques": len(set().union(*ips[day][host].values())) if ips[day][host] else 0,
                }
                for host, pathmap in hostmap.items()
            },
            "referrers": dict(refs[day]),
            "bot_hits": bots.get(day, 0),
        }
    return out


def merge(store: dict, fresh: dict) -> dict:
    """max()-merge. A recount after rotation must never shrink history."""
    for day, data in fresh.items():
        cur = store.setdefault(day, {"hosts": {}, "referrers": {}, "bot_hits": 0})
        cur["bot_hits"] = max(cur.get("bot_hits", 0), data.get("bot_hits", 0))
        for host, hd in data["hosts"].items():
            ch = cur["hosts"].setdefault(host, {"paths": {}, "views": 0, "uniques": 0})
            ch["views"] = max(ch.get("views", 0), hd["views"])
            ch["uniques"] = max(ch.get("uniques", 0), hd["uniques"])
            for p, pd in hd["paths"].items():
                cp = ch["paths"].setdefault(p, {"views": 0, "uniques": 0})
                cp["views"] = max(cp.get("views", 0), pd["views"])
                cp["uniques"] = max(cp.get("uniques", 0), pd["uniques"])
        for r, c in data["referrers"].items():
            cur["referrers"][r] = max(cur["referrers"].get(r, 0), c)
    return store


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default=STORE)
    ap.add_argument("--emit", default=EMIT)
    ap.add_argument("--days", type=int, default=400, help="ignore log entries older than N days")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")
    fresh = scan(cutoff)

    store = {}
    if os.path.exists(args.store):
        try:
            store = json.load(open(args.store))
        except ValueError:
            # Never clobber a corrupt store silently — keep it for inspection.
            os.rename(args.store, args.store + ".corrupt")
            print(f"WARNING: store was unparseable, kept as {args.store}.corrupt", file=sys.stderr)

    before_days = len(store)
    store = merge(store, fresh)

    print(f"days in logs: {len(fresh)}  days in store: {before_days} -> {len(store)}")
    for day in sorted(fresh)[-5:]:
        tv = sum(h["views"] for h in store[day]["hosts"].values())
        print(f"  {day}  views={tv}  hosts={len(store[day]['hosts'])}  bots_skipped={store[day]['bot_hits']}")

    if args.dry_run:
        print("(dry run — nothing written)")
        return

    os.makedirs(os.path.dirname(args.store), exist_ok=True)
    tmp = args.store + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(store, fh, separators=(",", ":"), sort_keys=True)
    os.replace(tmp, args.store)
    print(f"store -> {args.store}")

    # The page reads a trimmed view: it does not need every path ever served.
    view = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "days": {}}
    for day, d in store.items():
        paths = []
        for host, hd in d["hosts"].items():
            for p, pd in hd["paths"].items():
                paths.append({"host": host, "path": p, "views": pd["views"], "uniques": pd["uniques"]})
        paths.sort(key=lambda x: -x["views"])
        view["days"][day] = {
            "hosts": {h: {"views": hd["views"], "uniques": hd["uniques"]} for h, hd in d["hosts"].items()},
            "top_paths": paths[:40],
            "referrers": dict(sorted(d["referrers"].items(), key=lambda kv: -kv[1])[:20]),
        }
    if args.emit:
        os.makedirs(os.path.dirname(args.emit), exist_ok=True)
        tmp = args.emit + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(view, fh, separators=(",", ":"), sort_keys=True)
        os.replace(tmp, args.emit)
        print(f"page data -> {args.emit}")


if __name__ == "__main__":
    main()
