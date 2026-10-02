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
import subprocess
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


# Droplet target for the tracker API (token-free: it only reads these stats).
REMOTE_JOBS = os.environ.get(
    "TECH_SHORTS_REMOTE_JOBS",
    "root@159.223.22.165:/opt/salesman-api/fleet/tech-shorts/jobs.json",
)


def push_to_droplet() -> bool:
    """scp jobs.json to the droplet so the tracker serves fresh view counts.

    The droplet holds no YouTube token; it just reads these precomputed stats.
    Mirrors tcr_scout._push_snapshot. Failure is non-fatal — the local write
    already succeeded and the next run retries.
    """
    import subprocess
    try:
        subprocess.run(
            ["scp", "-o", "StrictHostKeyChecking=accept-new", str(JOBS), REMOTE_JOBS],
            check=True, capture_output=True, timeout=60,
        )
        print(f"pushed jobs.json -> {REMOTE_JOBS}")
        return True
    except Exception as exc:
        print(f"WARNING: push to droplet failed: {exc}", file=sys.stderr)
        return False


# ── YouTube ──────────────────────────────────────────────────────────────────

def fetch_youtube(ids: list) -> dict:
    """videos().list(part=statistics) in chunks of 50 (the API's id cap). Quota only, no dollars."""
    if not ids:
        return {}
    sys.path.insert(0, str(MUSIC_VIDEO_TOOL))
    from youtube_uploader import get_authenticated_service, channel_token_path  # type: ignore
    svc = get_authenticated_service(token_path=channel_token_path(YT_CHANNEL))
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        res = svc.videos().list(part="statistics,snippet,status", id=",".join(chunk)).execute()
        for it in res.get("items", []):
            s = it.get("statistics", {})
            out[it["id"]] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "title": it["snippet"]["title"],
                "published_at": (it["snippet"].get("publishedAt") or "")[:10],
                "privacy": it.get("status", {}).get("privacyStatus"),
            }
    return out


# ── Ideas-console status reconcile ───────────────────────────────────────────
# The ideas console (tech-shorts-intake on the droplet) reads its own jobs.json.
# Keep its list honest: a job whose video is public -> published (drops off the
# "what's cooking" view into Insights); private/scheduled -> back to a ready state.
CONSOLE_SSH = os.environ.get("TECH_SHORTS_CONSOLE_SSH", "robotsales")
CONSOLE_JOBS = os.environ.get("TECH_SHORTS_CONSOLE_JOBS", "/opt/tech-shorts/jobs.json")


def reconcile_console_statuses() -> None:
    """scp the console's jobs.json, flip each job's status from the video's actual
    YouTube privacy, push back, and restart the console. Non-fatal on any error."""
    import tempfile
    try:
        tmp = Path(tempfile.mktemp(suffix="-console-jobs.json"))
        subprocess.run(["scp", "-o", "StrictHostKeyChecking=accept-new",
                        f"{CONSOLE_SSH}:{CONSOLE_JOBS}", str(tmp)], check=True)
        d = json.loads(tmp.read_text())
        ids = sorted({(j.get("youtube", {}) or {}).get("long_id")
                      for j in d.get("jobs", []) if (j.get("youtube", {}) or {}).get("long_id")})
        info = fetch_youtube(ids)
        changed = 0
        for j in d.get("jobs", []):
            vid = (j.get("youtube", {}) or {}).get("long_id")
            p = info.get(vid, {}).get("privacy") if vid else None
            if p == "public" and j.get("status") != "published":
                j["status"] = "published"; changed += 1
            elif p in ("private", "unlisted") and j.get("status") == "published":
                j["status"] = "assembled"; changed += 1  # ready / private
        if changed:
            tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2))
            subprocess.run(["scp", str(tmp), f"{CONSOLE_SSH}:{CONSOLE_JOBS}"], check=True)
            subprocess.run(["ssh", CONSOLE_SSH, "systemctl restart tech-shorts-intake"], check=True)
        print(f"console reconcile: {changed} status change(s)")
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: console reconcile failed: {exc}", file=sys.stderr)


# Per-video revenue overlay written by video_revenue_overlay.py (music-video-tool).
# The droplet holds no analytics token; we join the tech-short video ids to the
# already-computed per-video revenue here so the fleet dashboard reads it for free.
REVENUE_OVERLAY = os.path.expanduser("~/fleet/video_revenue_overlay.json")


def load_revenue_overlay() -> dict:
    try:
        return json.load(open(REVENUE_OVERLAY)).get("revenue", {})
    except Exception as exc:
        print(f"WARNING: revenue overlay unavailable: {exc}", file=sys.stderr)
        return {}


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
    ap.add_argument("--no-push", action="store_true", help="skip the scp to the droplet tracker")
    ap.add_argument("--no-reconcile", action="store_true",
                    help="skip reconciling the ideas-console job statuses from YouTube privacy")
    ap.add_argument("--set-tiktok", action="store_true",
                    help="manually set the TikTok stats on --job then save+push and exit (no API calls). "
                         "TikTok has no public per-account stats API, so these numbers are entered by hand; "
                         "the daily sync preserves them via merge.")
    ap.add_argument("--views", type=int, help="TikTok views (with --set-tiktok)")
    ap.add_argument("--likes", type=int, default=0, help="TikTok likes (with --set-tiktok)")
    args = ap.parse_args()

    d = load()
    jobs = d if isinstance(d, list) else d["jobs"]
    if args.job:
        jobs = [j for j in jobs if j["id"] == args.job or j.get("slug") == args.job]
        if not jobs:
            raise SystemExit(f"job not found: {args.job}")

    # Manual TikTok setter: TikTok exposes no per-account stats API, so views/likes
    # are entered by hand here. Goes through the same save+push path as the daily
    # sync, and the sync's stats.update() preserves the block on every later run.
    if args.set_tiktok:
        if not args.job:
            raise SystemExit("--set-tiktok requires --job")
        if args.views is None:
            raise SystemExit("--set-tiktok requires --views")
        day = now_iso()[:10]
        for j in jobs:
            tk = j.setdefault("stats", {}).setdefault("tiktok", {})
            tk.update({"views": args.views, "likes": args.likes, "synced_at": day})
            print(f"set tiktok on {j['id']}: views={args.views} likes={args.likes}")
        save(d)
        print(f"written to {JOBS}")
        if not args.no_push:
            push_to_droplet()
        return

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

    revenue_overlay = load_revenue_overlay()
    stamp = now_iso()
    total_yt_views = 0
    for j in jobs:
        yt = j.setdefault("youtube", {})
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
        short_v = entry["youtube"].get("short", {}).get("views", 0)
        long_v = entry["youtube"].get("long", {}).get("views", 0)

        # Publish date: earliest known across the video(s), persisted onto the job
        # so the token-free droplet can show and sort by it.
        pubs = [entry["youtube"][r].get("published_at") for r in ("short", "long")
                if entry["youtube"].get(r, {}).get("published_at")]
        published_at = min(pubs) if pubs else yt.get("published_at", "")
        if published_at:
            yt["published_at"] = published_at

        # Per-video revenue joined from the analytics overlay (sum short + long).
        rev_life = rev_30d = 0.0
        for role in ("short", "long"):
            r = revenue_overlay.get(video_id(yt.get(f"{role}_url")))
            if r:
                rev_life += float(r.get("revenue_lifetime") or 0)
                rev_30d += float(r.get("revenue_30d") or 0)

        print(f"{j['id'][:52]:<54} yt_views={yv:<7} yt_likes={yl:<5} "
              f"pub={published_at or '-'} rev=${rev_life:.3f}")

        if args.dry_run:
            continue

        # update() (not reassignment) so the hand-entered stats["tiktok"] block —
        # which has no API to refresh from — survives every daily sync.
        stats = j.setdefault("stats", {})
        stats.update({
            "views": yv, "likes": yl, "comments": yc,
            "short_views": short_v, "long_views": long_v, "total_views": yv,
            "published_at": published_at,
            "revenue_lifetime": round(rev_life, 4),
            "revenue_30d": round(rev_30d, 4),
            "last_synced_at": stamp,
            "detail": entry,
        })
        # Append-only daily snapshot: one row per calendar day, so a re-run the
        # same day corrects rather than duplicates.
        hist = stats.setdefault("history", [])
        today = stamp[:10]
        hist[:] = [h for h in hist if h.get("date") != today]
        tk = stats.get("tiktok") or {}
        hist.append({
            "date": today,
            "yt_views": yv, "yt_likes": yl, "yt_comments": yc,
            "x_impressions": entry["x"].get("post", {}).get("impressions"),
            "x_likes": entry["x"].get("post", {}).get("likes"),
            "tiktok_views": tk.get("views"),
            "tiktok_likes": tk.get("likes"),
        })

    if not args.dry_run:
        save(d)
        print(f"\nwritten to {JOBS}")
        if not args.no_push:
            push_to_droplet()
            if not args.no_reconcile:
                reconcile_console_statuses()
    print(f"total YouTube views across synced jobs: {total_yt_views}")


if __name__ == "__main__":
    main()
