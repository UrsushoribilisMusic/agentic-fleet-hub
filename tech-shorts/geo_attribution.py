#!/usr/bin/env python3
"""
Per-video geography + traffic-source attribution for the tech-shorts.

Answers "which post drove which viewers, from where, and via what surface"
by querying the YouTube Analytics API (already-authorised scopes on
music-video-tool/youtube_token.pickle: yt-analytics.readonly) and writing the
result into each job's stats block:

    job["stats"]["attribution"] = {
        "synced_at": "...Z",
        "short": {"video_id": "...", "since": "YYYY-MM-DD",
                   "top_countries": [["US", views, watch_min], ...],
                   "traffic_sources": [["SHORTS", views], ...]},
        "long":  { ... same shape ... },
    }

Then it scp's jobs.json to the droplet (same path stats_sync uses), so the
tracker/dashboard serves the attribution alongside the view counts. The droplet
holds no token; it only reads these precomputed numbers.

Usage:
    python3 geo_attribution.py                 # backfill all, then push
    python3 geo_attribution.py --job <id>      # one job
    python3 geo_attribution.py --no-push       # compute locally only
    python3 geo_attribution.py --top 8         # rows per country table
"""
import argparse
import os
import pickle
import sys
from datetime import date, datetime, timezone

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Reuse the plumbing stats_sync already defines (JOBS path, save, scp push).
from stats_sync import JOBS, load, save, push_to_droplet, video_id, now_iso

TOKEN = os.path.expanduser("~/projects/music-video-tool/youtube_token.pickle")


def services():
    creds = pickle.load(open(TOKEN, "rb"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    ya = build("youtubeAnalytics", "v2", credentials=creds)
    yt = build("youtube", "v3", credentials=creds)
    return ya, yt


def published_date(yt, vid: str) -> str:
    """Publish date (YYYY-MM-DD) so the lifetime window starts at go-live."""
    try:
        items = yt.videos().list(part="snippet", id=vid).execute().get("items", [])
        if items:
            return items[0]["snippet"]["publishedAt"][:10]
    except Exception:
        pass
    return "2026-08-01"  # safe floor: predates the first tech-short


def attribution_for(ya, yt, vid: str, top: int) -> dict:
    since = published_date(yt, vid)
    today = date.today().isoformat()

    def q(dimensions, extra_metric=""):
        metrics = "views" + ("," + extra_metric if extra_metric else "")
        try:
            return ya.reports().query(
                ids="channel==MINE", startDate=since, endDate=today,
                metrics=metrics, dimensions=dimensions,
                filters=f"video=={vid}", sort="-views", maxResults=25,
            ).execute().get("rows", [])
        except Exception as exc:
            print(f"    query error ({dimensions}): {str(exc)[:90]}", file=sys.stderr)
            return []

    countries = [[c, int(v), int(m)] for c, v, m in q("country", "estimatedMinutesWatched")][:top]
    sources = [[s, int(v)] for s, v in q("insightTrafficSourceType") if int(v) > 0]
    return {"video_id": vid, "since": since,
            "top_countries": countries, "traffic_sources": sources}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", help="only this job id")
    ap.add_argument("--no-push", action="store_true", help="skip scp to droplet")
    ap.add_argument("--top", type=int, default=8, help="rows in the country table")
    args = ap.parse_args()

    ya, yt = services()
    data = load()
    jobs = data["jobs"] if isinstance(data, dict) else data

    touched = 0
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if args.job and job.get("id") != args.job:
            continue
        ytb = job.get("youtube", {})
        short_id = ytb.get("short_id") or video_id(ytb.get("short_url", ""))
        long_id = ytb.get("long_id") or video_id(ytb.get("long_url", ""))
        if not (short_id or long_id):
            continue

        stats = job.setdefault("stats", {})
        attr = {"synced_at": now_iso()}
        label = job.get("id", "?")
        print(f"\n{label}")
        if short_id:
            attr["short"] = attribution_for(ya, yt, short_id, args.top)
            _print_attr("  short", attr["short"])
        if long_id:
            attr["long"] = attribution_for(ya, yt, long_id, args.top)
            _print_attr("  long ", attr["long"])
        stats["attribution"] = attr
        touched += 1

    if isinstance(data, dict):
        data["updated_at"] = now_iso()
    save(data)
    print(f"\nWrote attribution for {touched} job(s) -> {JOBS}")
    if not args.no_push:
        push_to_droplet()


def _print_attr(tag: str, a: dict) -> None:
    top = a.get("top_countries", [])
    if not top:
        print(f"{tag}: (no views yet)")
        return
    geo = "  ".join(f"{c}:{v}" for c, v, _m in top[:5])
    src = "  ".join(f"{s}:{v}" for s, v in a.get("traffic_sources", [])[:4])
    print(f"{tag}: {geo}   |   {src}")


if __name__ == "__main__":
    main()
