#!/usr/bin/env python3
"""
Sync real YouTube and X metrics into each job's stats block.

Why this exists
---------------
intake.py creates a `stats` block on every job and nothing has ever written to
it. All six tech-shorts read views=0, likes=0, last_synced_at=NEVER. TS-6 is
marked closed in MISSION_CONTROL but no sync was ever wired, so "how did that
one do?" has only ever been answerable by opening the X app by hand.

What it records, per job:
  youtube.short / youtube.long  — views, likes, comments (Data API, quota only)
  x.post / x.reply              — impressions, likes, reposts, replies, quotes
  history[]                     — an append-only daily snapshot, so growth is
                                  visible rather than just the latest total

Costs: YouTube reads are quota-only (free). Each X post read is $0.005 through
the publisher's budget guard, so a full sync of 6 jobs with a reply is ~$0.035.
Use --no-x to skip the paid half.

Usage:
    python3 stats_sync.py [--job <id>] [--no-x] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE / "jobs.json"
MUSIC_VIDEO_TOOL = HERE.parent.parent / "music-video-tool"
FLOTILLA_PUBLISHER = Path("/Users/miguelrodriguez/flotilla/publisher")
YT_CHANNEL = "main"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def video_id(url: str) -> str:
    m = re.search(r"(?:watch\?v=|youtu\.be/|/shorts/)([\w-]+)", url or "")
    return m.group(1) if m else ""


def tweet_id(url: str) -> str:
    return (url or "").rstrip("/").split("/")[-1] if url else ""


def load() -> dict:
    return json.load(open(JOBS))


def save(d: dict) -> None:
    tmp = JOBS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=4, ensure_ascii=False) + "\n")
    tmp.replace(JOBS)


# ── YouTube ──────────────────────────────────────────────────────────────────

def fetch_youtube(ids: list) -> dict:
    """videos().list(part=statistics) for up to 50 ids. Quota only, no dollars."""
    if not ids:
        return {}
    sys.path.insert(0, str(MUSIC_VIDEO_TOOL))
    from youtube_uploader import get_authenticated_service, channel_token_path  # type: ignore
    svc = get_authenticated_service(token_path=channel_token_path(YT_CHANNEL))
    res = svc.videos().list(part="statistics,snippet", id=",".join(ids)).execute()
    out = {}
    for it in res.get("items", []):
        s = it.get("statistics", {})
        out[it["id"]] = {
            "views": int(s.get("viewCount", 0)),
            "likes": int(s.get("likeCount", 0)),
            "comments": int(s.get("commentCount", 0)),
            "title": it["snippet"]["title"],
        }
    return out


# ── X ────────────────────────────────────────────────────────────────────────

def build_x_client():
    sys.path.insert(0, str(FLOTILLA_PUBLISHER))
    for p in ("/opt/homebrew/bin", "/usr/local/bin"):
        if p not in os.environ.get("PATH", "").split(":") and os.path.isdir(p):
            os.environ["PATH"] = p + ":" + os.environ.get("PATH", "")
    os.environ.setdefault("X_SECRET_PATH", "/")
    from flotilla_publisher.x_client import build_client  # type: ignore
    cwd = os.getcwd()
    try:
        os.chdir(FLOTILLA_PUBLISHER)
        return build_client()
    finally:
        os.chdir(cwd)


def fetch_x(client, tid: str) -> dict:
    """Read one post's public metrics.

    x_client.read_post() does not forward tweet_fields, so public_metrics never
    comes back through it. Reserve the cost against the same budget guard, then
    call the underlying tweepy client with the fields we need — so the spend is
    still accounted for rather than sneaking past the guard.
    """
    client.budget_guard.reserve(
        "post.read",
        units=1,
        unit_cost_usd=client.rates.post_read,
        metadata={"tweet_id": tid, "purpose": "stats_sync"},
    )
    resp = client.client.get_tweet(tid, tweet_fields=["public_metrics"])
    data = getattr(resp, "data", None)
    if data is None:
        return {}
    pm = getattr(data, "public_metrics", None) or {}
    return {
        "impressions": pm.get("impression_count", 0),
        "likes": pm.get("like_count", 0),
        "reposts": pm.get("retweet_count", 0),
        "replies": pm.get("reply_count", 0),
        "quotes": pm.get("quote_count", 0),
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job")
    ap.add_argument("--no-x", action="store_true", help="skip the paid X reads")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    d = load()
    jobs = d if isinstance(d, list) else d["jobs"]
    if args.job:
        jobs = [j for j in jobs if j["id"] == args.job or j.get("slug") == args.job]
        if not jobs:
            raise SystemExit(f"job not found: {args.job}")

    # One batched YouTube call for every video across all jobs.
    wanted = []
    for j in jobs:
        yt = j.get("youtube") or {}
        for role in ("short", "long"):
            v = video_id(yt.get(f"{role}_url"))
            if v:
                wanted.append(v)
    ytstats = fetch_youtube(wanted) if wanted else {}

    xclient = None
    if not args.no_x and not args.dry_run:
        if any((j.get("x_post") or {}).get("post_url") for j in jobs):
            xclient = build_x_client()

    stamp = now_iso()
    total_yt_views = 0
    for j in jobs:
        yt = j.get("youtube") or {}
        xp = j.get("x_post") or {}
        entry = {"synced_at": stamp, "youtube": {}, "x": {}}

        for role in ("short", "long"):
            v = video_id(yt.get(f"{role}_url"))
            if v and v in ytstats:
                entry["youtube"][role] = ytstats[v]
                total_yt_views += ytstats[v]["views"]

        if xclient is not None:
            for key, url in (("post", xp.get("post_url")), ("reply", xp.get("reply_url"))):
                tid = tweet_id(url)
                if not tid:
                    continue
                try:
                    entry["x"][key] = fetch_x(xclient, tid)
                except Exception as exc:
                    entry["x"][key] = {"error": f"{type(exc).__name__}: {exc}"[:160]}

        yv = sum(v["views"] for v in entry["youtube"].values())
        yl = sum(v["likes"] for v in entry["youtube"].values())
        yc = sum(v["comments"] for v in entry["youtube"].values())
        print(f"{j['id'][:52]:<54} yt_views={yv:<7} yt_likes={yl:<5} "
              f"x_impr={entry['x'].get('post',{}).get('impressions','-')}")

        if args.dry_run:
            continue

        stats = j.setdefault("stats", {})
        stats.update({
            "views": yv, "likes": yl, "comments": yc,
            "last_synced_at": stamp,
            "detail": entry,
        })
        # Append-only daily snapshot: one row per calendar day, so a re-run the
        # same day corrects rather than duplicates.
        hist = stats.setdefault("history", [])
        today = stamp[:10]
        hist[:] = [h for h in hist if h.get("date") != today]
        hist.append({
            "date": today,
            "yt_views": yv, "yt_likes": yl, "yt_comments": yc,
            "x_impressions": entry["x"].get("post", {}).get("impressions"),
            "x_likes": entry["x"].get("post", {}).get("likes"),
        })

    if not args.dry_run:
        save(d)
        print(f"\nwritten to {JOBS}")
    print(f"total YouTube views across synced jobs: {total_yt_views}")


if __name__ == "__main__":
    main()
