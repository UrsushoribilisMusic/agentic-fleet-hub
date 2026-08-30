#!/usr/bin/env python3
"""
Push a job's title/description/tags to its ALREADY-UPLOADED YouTube videos.

pipeline.py sets metadata at upload time only. When copy is corrected afterwards
(a wrong source URL, a fact cleared for publication, a description rewrite), the
job record and the live videos silently diverge. This resyncs them.

Reads the same job copy that stage_upload reads, so there is one source of truth.

Usage:
    python3 sync_yt_metadata.py <job_id> [--dry-run]

Only touches videos whose IDs are already recorded on the job. It never uploads,
never changes privacy status, and never publishes.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUSIC_VIDEO_TOOL = Path("~/projects/music-video-tool").expanduser()
JOBS = HERE / "jobs.json"
YT_CHANNEL = "main"


def load_job(job_id: str) -> dict:
    d = json.load(open(JOBS))
    jobs = d if isinstance(d, list) else d["jobs"]
    for j in jobs:
        if j["id"] == job_id or j.get("slug") == job_id:
            return j
    raise SystemExit(f"job not found: {job_id}")


def video_ids(job: dict) -> dict:
    """Recorded video ids, keyed by role. Falls back to parsing the url."""
    yt = job.get("youtube", {}) or {}
    out = {}
    for role in ("short", "long"):
        vid = yt.get(f"{role}_id") or ""
        if not vid:
            url = yt.get(f"{role}_url") or ""
            if "watch?v=" in url:
                vid = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                vid = url.split("youtu.be/")[1].split("?")[0]
        if vid:
            out[role] = vid
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    job = load_job(args.job_id)
    yt = job.get("youtube", {}) or {}
    desc = yt.get("description", "")
    tags = yt.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    titles = {"short": yt.get("title_short", ""), "long": yt.get("title_long", "")}

    ids = video_ids(job)
    if not ids:
        raise SystemExit("no uploaded video ids on this job — nothing to sync")
    if not desc:
        raise SystemExit("job has no youtube.description — refusing to blank the live one")

    print(f"job: {job['id']}")
    for role, vid in ids.items():
        print(f"  {role}: {vid}  title={titles.get(role,'')!r}  desc={len(desc)} chars  tags={len(tags)}")
    if args.dry_run:
        print("\n(dry run — nothing sent)")
        return

    sys.path.insert(0, str(MUSIC_VIDEO_TOOL))
    from youtube_uploader import get_authenticated_service, channel_token_path  # type: ignore

    svc = get_authenticated_service(token_path=channel_token_path(YT_CHANNEL))

    for role, vid in ids.items():
        # category must be carried through: videos.update replaces the whole
        # snippet, so omitting it would clear the category on the live video.
        cur = svc.videos().list(part="snippet", id=vid).execute()
        items = cur.get("items", [])
        if not items:
            print(f"  {role} {vid}: NOT FOUND — skipping")
            continue
        snip = items[0]["snippet"]
        snip["title"] = titles.get(role) or snip["title"]
        snip["description"] = desc
        snip["tags"] = tags or snip.get("tags", [])
        svc.videos().update(part="snippet", body={"id": vid, "snippet": snip}).execute()
        print(f"  {role} {vid}: updated")

    print("done — privacy status untouched")


if __name__ == "__main__":
    main()
