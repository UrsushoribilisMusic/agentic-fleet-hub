#!/usr/bin/env python3
"""Tech-shorts X poller.

For each job whose YouTube video is PUBLIC and not yet cross-posted, post it to X.
Flipping a video to Public is the "go-ahead" — this poller only fires on public
videos, so it never tweets a private link. Idempotent (skips jobs with an x_post).

Run 3x/day via cron, or once by hand.
  python3 x_poller.py [--dry-run] [--job=<id>] [--prefer=short|long]
"""
import os, sys, json, re
from pathlib import Path

# launchd/cron hands a minimal PATH without Homebrew; the infisical CLI needs it.
for _p in ("/opt/homebrew/bin", "/usr/local/bin"):
    if _p not in os.environ.get("PATH", "").split(":") and os.path.isdir(_p):
        os.environ["PATH"] = _p + ":" + os.environ.get("PATH", "")
# X keys live at the ROOT of the UrsusFleet Infisical project (dev env).
os.environ.setdefault("X_SECRET_PATH", "/")

HERE = Path(__file__).resolve().parent
JOBS = HERE / "jobs.json"
MVT = os.path.expanduser("~/projects/music-video-tool")
PUB = os.path.expanduser("~/flotilla/publisher")

DRY = "--dry-run" in sys.argv
ONE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--job=")), None)
PREFER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--prefer=")), "short")

_client = None


def yt_service():
    sys.path.insert(0, MVT)
    from youtube_uploader import get_authenticated_service  # type: ignore
    return get_authenticated_service(channel="main")


def privacy(yt, vid):
    r = yt.videos().list(part="status", id=vid).execute()
    items = r.get("items", [])
    return items[0]["status"]["privacyStatus"] if items else "not_found"


def caption(job, url):
    hook = (job.get("hook_copy", {}) or {}).get("vo_text") or job.get("title", "")
    hook = hook.strip()
    tags = job.get("tags") or []
    ht = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", t) for t in tags[:4]) if tags else "#AI"
    budget = 275 - len(url) - len(ht) - 3  # room for "\n\n" + space
    if len(hook) > budget:
        hook = hook[:budget - 1].rstrip() + "…"
    return f"{hook}\n\n{url} {ht}".strip()


def post_x(text):
    global _client
    if _client is None:
        os.chdir(PUB)
        sys.path.insert(0, PUB)
        from flotilla_publisher.x_client import build_client  # type: ignore
        _client = build_client()
    from flotilla_publisher.x_client import extract_tweet_id  # type: ignore
    resp = _client.create_post(text)
    tid = extract_tweet_id(resp)
    return tid, f"https://x.com/i/web/status/{tid}"


def vid_from_url(url):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def pick_video(ytd):
    order = ["short", "long"] if PREFER == "short" else ["long", "short"]
    for k in order:
        url = ytd.get(f"{k}_url")
        vid = ytd.get(f"{k}_id") or vid_from_url(url)
        if vid and url:
            yield k, vid, url


def main():
    data = json.load(open(JOBS))
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    yt = yt_service()
    changed = False
    for j in jobs:
        if ONE and j["id"] != ONE:
            continue
        if (j.get("x_post") or {}).get("post_url"):
            continue  # already cross-posted
        ytd = j.get("youtube", {}) or {}
        posted = False
        for kind, vid, url in pick_video(ytd):
            p = privacy(yt, vid)
            print(f"[{j['id']}] {kind} {vid} -> {p}")
            if p != "public":
                continue
            cap = caption(j, url)
            if DRY:
                print(f"  [dry-run] would post ({len(cap)} chars):\n  " + cap.replace("\n", "\n  "))
                posted = True
                break
            tid, purl = post_x(cap)
            print(f"  POSTED -> {purl}")
            j.setdefault("x_post", {}).update({"post_id": tid, "post_url": purl, "caption": cap})
            j["status"] = "published"
            changed = True
            posted = True
            break
        if not posted and not ONE:
            pass
    if changed and not DRY:
        tmp = JOBS.with_suffix(".json.tmp")
        json.dump(data, open(tmp, "w"), indent=2)
        tmp.replace(JOBS)
        print("jobs.json updated")


if __name__ == "__main__":
    main()
