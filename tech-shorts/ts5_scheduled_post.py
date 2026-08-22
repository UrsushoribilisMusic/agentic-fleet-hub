#!/usr/bin/env python3
"""TS-5 (scheduled): cross-post the Edge-Inference short to X — but ONLY if the
video is actually public. Safe to run headless. Exits non-zero if it declined.

Usage: python3 ts5_scheduled_post.py [--force] [--dry-run]
  --force    post even if privacyStatus != public (NOT recommended)
  --dry-run  print what would happen; do not post
"""
import os, sys

# launchd hands us a minimal PATH that omits Homebrew, so the `infisical` CLI
# (used by the X client to read keys from Infisical) isn't found. Restore it.
for _p in ("/opt/homebrew/bin", "/usr/local/bin"):
    if _p not in os.environ.get("PATH", "").split(":") and os.path.isdir(_p):
        os.environ["PATH"] = _p + ":" + os.environ.get("PATH", "")

VIDEO_ID = "oeJPAISjIjM"                       # Edge-Inference SHORT
YT_URL   = f"https://www.youtube.com/watch?v={VIDEO_ID}"
CAPTION  = (
    "Hundreds of billions are pouring into AI data centers. But inference is "
    "moving to the edge — and that could break the bet. The ghost of "
    "fiber-optic economics \U0001F43B\U0001F447 "
    f"{YT_URL} #AI #EdgeAI #DataCenter"
)
MVT = os.path.expanduser("~/projects/music-video-tool")
PUB = os.path.expanduser("~/flotilla/publisher")
# X keys live at the ROOT of the UrsusFleet Infisical project (dev env), not the
# x_client default /flotilla/x. Point the loader there unless already overridden.
os.environ.setdefault("X_SECRET_PATH", "/")
FORCE   = "--force"   in sys.argv
DRY_RUN = "--dry-run" in sys.argv


def video_privacy() -> str:
    sys.path.insert(0, MVT)
    from youtube_uploader import get_authenticated_service  # type: ignore
    yt = get_authenticated_service(channel="main")
    resp = yt.videos().list(part="status,snippet", id=VIDEO_ID).execute()
    items = resp.get("items", [])
    if not items:
        return "not_found"
    return items[0]["status"]["privacyStatus"]


def main() -> int:
    status = video_privacy()
    print(f"[TS-5] video {VIDEO_ID} privacyStatus = {status}")

    if status != "public" and not FORCE:
        print(f"[TS-5] DECLINED — video is '{status}', not 'public'. "
              f"Not posting to X. Flip it public then re-run.")
        return 2

    if DRY_RUN:
        print("[TS-5] [dry-run] would post:")
        print(f"  {CAPTION}")
        return 0

    # Run from the publisher dir so the infisical CLI resolves the project from
    # its .infisical.json (created via `infisical init`) — keeps keys in Infisical,
    # no secrets in env. INFISICAL_PROJECT_ID env still works as an override if set.
    os.chdir(PUB)
    sys.path.insert(0, PUB)
    from flotilla_publisher.x_client import build_client, extract_tweet_id  # type: ignore
    client = build_client()
    print(f"[TS-5] posting to X ({len(CAPTION)} chars)...")
    resp = client.create_post(CAPTION)
    tweet_id = extract_tweet_id(resp)
    post_url = f"https://x.com/i/web/status/{tweet_id}"
    print(f"[TS-5] POSTED: {post_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
