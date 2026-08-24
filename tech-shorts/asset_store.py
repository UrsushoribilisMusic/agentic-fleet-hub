#!/usr/bin/env python3
"""TS-12 — canonical asset store for tech-shorts jobs.

LOCAL layout:
  ~/flotilla/tech-shorts/assets/<YYYY-MM-DD-slug>/
    raw_cinematic.mp4   — NotebookLM Cinematic (16:9) video
    raw_short.mp4       — NotebookLM Short (9:16) video
    infographic.png     — NotebookLM infographic
    slidedeck.pdf       — NotebookLM slide deck (or .pptx)
    final_short.mp4     — assembled short with hook/outro
    final_long.mp4      — assembled long with hook/outro
    thumbnail.png       — optional thumbnail

DRIVE layout (shareable assets only):
  Tech Shorts/<YYYY-MM-DD-slug>/
    infographic.png
    slidedeck.pdf

YouTube URLs are the canonical video links and live in job.youtube.{short,long}_url.

The job record (jobs.json) is extended with:
  job.assets.store_dir        — absolute path to the date-slug directory
  job.assets.raw_cinematic_mp4
  job.assets.raw_short_mp4
  job.assets.infographic_png
  job.assets.slidedeck_pdf
  job.assets.final_short_mp4
  job.assets.final_long_mp4
  job.assets.thumbnail_png
  job.drive.folder_url
  job.drive.infographic_url
  job.drive.slidedeck_url

Usage:
  python3 asset_store.py store-raw <job_id> [--cinematic P] [--short P]
                                             [--infographic P] [--slidedeck P]
                                             [--from-downloads] [--from-raw-subdir PATH]
  python3 asset_store.py drive-upload <job_id>
  python3 asset_store.py store-finals <job_id> --short P --long P [--thumbnail P]
  python3 asset_store.py status <job_id>
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
JOBS_FILE = HERE / "jobs.json"
JOBS_LOCK = HERE / "jobs.lock"

ASSET_BASE = Path("~/flotilla/tech-shorts/assets").expanduser()
DOWNLOADS_DIR = Path("~/Downloads").expanduser()
DRIVE_TOKEN = Path("~/projects/music-video-tool/drive_token.pickle").expanduser()
DRIVE_ROOT_FOLDER = "Tech Shorts"


# ── Job I/O ───────────────────────────────────────────────────────────────────

def _load_jobs() -> dict:
    with open(JOBS_FILE) as f:
        return json.load(f)


def _save_jobs(data: dict) -> None:
    import datetime
    data["updated_at"] = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(JOBS_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            tmp = JOBS_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n")
            tmp.replace(JOBS_FILE)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _find_job(data: dict, job_id: str) -> Optional[dict]:
    for j in data["jobs"]:
        if j["id"] == job_id or j.get("slug") == job_id:
            return j
    return None


def _deep_set(target: dict, source: dict) -> None:
    for k, v in source.items():
        if isinstance(v, dict) and isinstance(target.get(k), dict):
            _deep_set(target[k], v)
        else:
            target[k] = v


def _update_job(data: dict, job: dict, updates: dict) -> None:
    import datetime
    _deep_set(job, updates)
    job["updated_at"] = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Slug / directory ──────────────────────────────────────────────────────────

def date_slug(job: dict) -> str:
    """Return YYYY-MM-DD-<slug> derived from job creation date + slug."""
    created = job.get("created_at", "")[:10]
    if not created:
        import datetime
        created = datetime.date.today().isoformat()
    slug = job.get("slug", job["id"])
    return f"{created}-{slug}"


def asset_dir(job: dict) -> Path:
    """Return canonical asset directory, honouring an existing store_dir in the job record."""
    existing = job.get("assets", {}).get("store_dir", "")
    if existing:
        d = Path(existing)
    else:
        d = ASSET_BASE / date_slug(job)
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Video probe ───────────────────────────────────────────────────────────────

def _find_ffprobe() -> Optional[str]:
    import shutil
    found = shutil.which("ffprobe")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe", "/usr/bin/ffprobe"):
        if os.path.isfile(candidate):
            return candidate
    return None


def _is_landscape(path: Path) -> bool:
    """True if video width >= height (Cinematic/landscape format)."""
    ffprobe_bin = _find_ffprobe()
    if not ffprobe_bin:
        # Fallback: larger file is usually the cinematic (landscape) version
        return True
    try:
        r = subprocess.run(
            [ffprobe_bin, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=15,
        )
        parts = r.stdout.strip().split(",")
        if len(parts) == 2:
            w, h = int(parts[0]), int(parts[1])
            return w >= h
    except Exception:
        pass
    return True  # assume landscape on failure


# ── Raw asset ingestion ───────────────────────────────────────────────────────

def store_raw_assets(
    job_id: str,
    cinematic_src: Optional[str | Path] = None,
    short_src: Optional[str | Path] = None,
    infographic_src: Optional[str | Path] = None,
    slidedeck_src: Optional[str | Path] = None,
    search_downloads: bool = False,
    downloads_dir: Path = DOWNLOADS_DIR,
    raw_subdir: Optional[Path] = None,
) -> dict:
    """Move raw NotebookLM downloads into the canonical asset store.

    Source resolution order for any unset source:
      1. Explicit argument (cinematic_src / short_src / etc.)
      2. --from-raw-subdir (raw_subdir arg, or <asset_dir>/raw/ if it exists)
      3. --from-downloads (newest matching files < 1h old in ~/Downloads)

    For mp4 files: ffprobe aspect ratio distinguishes Cinematic (16:9) from Short (9:16).
    Falls back to file-size ordering when both are the same orientation.

    Returns a dict {field: canonical_path_str} for every asset successfully stored.
    """
    data = _load_jobs()
    job = _find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    ad = asset_dir(job)

    # --- auto-detect from raw/ subdirectory ---
    raw_sub = raw_subdir or (ad / "raw")
    if raw_sub.exists():
        mp4s = sorted(raw_sub.glob("*.mp4"), key=lambda f: f.stat().st_size, reverse=True)
        if mp4s:
            landscape = [f for f in mp4s if _is_landscape(f)]
            portrait  = [f for f in mp4s if not _is_landscape(f)]
            if cinematic_src is None and landscape:
                cinematic_src = landscape[0]
            if short_src is None and portrait:
                short_src = portrait[0]
            # Both same orientation: bigger = cinematic
            if cinematic_src is None and mp4s:
                cinematic_src = mp4s[0]
            if short_src is None and len(mp4s) >= 2:
                short_src = mp4s[1]
        pngs = list(raw_sub.glob("*.png")) + list(raw_sub.glob("*.jpg")) + list(raw_sub.glob("*.jpeg"))
        if infographic_src is None and pngs:
            infographic_src = pngs[0]
        pdfs = list(raw_sub.glob("*.pdf")) + list(raw_sub.glob("*.pptx"))
        if slidedeck_src is None and pdfs:
            slidedeck_src = pdfs[0]

    # --- auto-detect from ~/Downloads (files < 1h old) ---
    if search_downloads and (cinematic_src is None or short_src is None
                              or infographic_src is None or slidedeck_src is None):
        import time
        cutoff = time.time() - 3600

        def _recent(exts: list[str]) -> list[Path]:
            found: list[Path] = []
            for ext in exts:
                found += [f for f in downloads_dir.glob(f"*{ext}") if f.stat().st_mtime > cutoff]
                found += [f for f in downloads_dir.glob(f"*{ext.upper()}") if f.stat().st_mtime > cutoff]
            return sorted(found, key=lambda f: f.stat().st_mtime, reverse=True)

        if cinematic_src is None or short_src is None:
            mp4s = _recent([".mp4"])
            landscape = [f for f in mp4s if _is_landscape(f)]
            portrait  = [f for f in mp4s if not _is_landscape(f)]
            if cinematic_src is None and landscape:
                cinematic_src = landscape[0]
            if short_src is None and portrait:
                short_src = portrait[0]
            # Same orientation fallback: bigger = cinematic
            if cinematic_src is None and mp4s:
                cinematic_src = mp4s[0]
            if short_src is None and len(mp4s) >= 2 and mp4s[1] != cinematic_src:
                short_src = mp4s[1]
        if infographic_src is None:
            pngs = _recent([".png", ".jpg", ".jpeg"])
            if pngs:
                infographic_src = pngs[0]
        if slidedeck_src is None:
            pdfs = _recent([".pdf", ".pptx"])
            if pdfs:
                slidedeck_src = pdfs[0]

    # --- move each asset to canonical destination ---
    def _ingest(src: Path, dest: Path) -> str:
        if not src.exists():
            print(f"  WARNING: source not found: {src}")
            return ""
        if dest.exists() and dest.stat().st_size == src.stat().st_size:
            print(f"  already stored: {dest.name}")
            return str(dest)
        print(f"  {src.name} -> {dest.name}")
        # Use copy+unlink so cross-device moves work (raw_sub is inside ad)
        shutil.copy2(str(src), str(dest))
        try:
            src.unlink()
        except OSError:
            pass
        return str(dest)

    slots = [
        ("raw_cinematic_mp4", cinematic_src,   ad / "raw_cinematic.mp4"),
        ("raw_short_mp4",     short_src,        ad / "raw_short.mp4"),
        ("infographic_png",   infographic_src,  ad / "infographic.png"),
        ("slidedeck_pdf",     slidedeck_src,    ad / "slidedeck.pdf"),
    ]

    paths: dict[str, str] = {}
    for field, src, dest in slots:
        if src is not None:
            p = _ingest(Path(src), dest)
            if p:
                paths[field] = p
        elif dest.exists():
            # Already in the store from a previous run
            paths[field] = str(dest)

    # Persist to job record
    data = _load_jobs()
    job = _find_job(data, job_id)
    _update_job(data, job, {"assets": {**job.get("assets", {}), **paths,
                                        "store_dir": str(ad)}})
    _save_jobs(data)
    print(f"  store: {ad}")
    return paths


# ── Drive upload ──────────────────────────────────────────────────────────────

def upload_drive(job_id: str) -> dict:
    """Upload infographic.png + slidedeck.pdf from the asset store to Google Drive.

    Creates Tech Shorts/<date-slug>/ in Drive, sets anyone-with-link viewer on each
    file, and returns {"folder_url", "infographic_url", "slidedeck_url"}.
    """
    try:
        import pickle
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.auth.transport.requests import Request
    except ImportError as e:
        raise RuntimeError(
            f"Drive deps missing: {e}\n  pip install google-api-python-client google-auth"
        ) from e

    if not DRIVE_TOKEN.exists():
        raise RuntimeError(f"Drive token not found: {DRIVE_TOKEN}")

    data = _load_jobs()
    job = _find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    ad = asset_dir(job)
    slug_name = date_slug(job)

    with open(DRIVE_TOKEN, "rb") as f:
        creds = pickle.load(f)
    if creds and getattr(creds, "expired", False) and creds.refresh_token:
        creds.refresh(Request())
    svc = build("drive", "v3", credentials=creds)

    def _find_or_create_folder(name: str, parent: Optional[str] = None) -> str:
        safe = name.replace("'", "\\'")
        q = (f"name = '{safe}' and mimeType = 'application/vnd.google-apps.folder' "
             f"and trashed = false")
        if parent:
            q += f" and '{parent}' in parents"
        r = svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
        if r.get("files"):
            return r["files"][0]["id"]
        meta: dict = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent:
            meta["parents"] = [parent]
        return svc.files().create(body=meta, fields="id").execute()["id"]

    def _upload_file(path: Path, parent: str) -> str:
        media = MediaFileUpload(str(path), resumable=True)
        f = svc.files().create(
            body={"name": path.name, "parents": [parent]},
            media_body=media, fields="id,webViewLink",
        ).execute()
        svc.permissions().create(
            fileId=f["id"], body={"type": "anyone", "role": "reader"}
        ).execute()
        return f["webViewLink"]

    root_id = _find_or_create_folder(DRIVE_ROOT_FOLDER)
    folder_id = _find_or_create_folder(slug_name, root_id)
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    drive_links: dict[str, str] = {"folder_url": folder_url}

    # Check for existing uploads in Drive folder to avoid duplicates
    existing_files = svc.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(name,webViewLink)", pageSize=20,
    ).execute().get("files", [])
    existing_names = {f["name"]: f["webViewLink"] for f in existing_files}

    for canonical, field in [
        ("infographic.png", "infographic_url"),
        ("slidedeck.pdf",   "slidedeck_url"),
    ]:
        local = ad / canonical
        if not local.exists() and canonical == "slidedeck.pdf":
            local = ad / "slidedeck.pptx"
        if local.exists():
            if local.name in existing_names:
                print(f"  {local.name} already in Drive")
                drive_links[field] = existing_names[local.name]
            else:
                print(f"  uploading {local.name} ...")
                drive_links[field] = _upload_file(local, folder_id)
                print(f"  -> {drive_links[field]}")
        else:
            print(f"  {canonical} not found in {ad}, skipping Drive upload")

    # Persist Drive links to job record
    data = _load_jobs()
    job = _find_job(data, job_id)
    _update_job(data, job, {"drive": {**job.get("drive", {}), **drive_links}})
    _save_jobs(data)
    return drive_links


# ── Finals storage ────────────────────────────────────────────────────────────

def store_finals(
    job_id: str,
    short_src: str | Path,
    long_src: str | Path,
    thumbnail_src: Optional[str | Path] = None,
) -> dict:
    """Move assembled finals into the canonical asset store.

    Called by pipeline.py after the build stage completes.
    Returns {field: canonical_path_str}.
    """
    data = _load_jobs()
    job = _find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    ad = asset_dir(job)
    paths: dict[str, str] = {}

    for src, dest_name, field in [
        (short_src,     "final_short.mp4", "final_short_mp4"),
        (long_src,      "final_long.mp4",  "final_long_mp4"),
    ]:
        src_path = Path(src)
        dest = ad / dest_name
        if src_path.exists():
            print(f"  {src_path.name} -> {dest.name}")
            shutil.move(str(src_path), str(dest))
            paths[field] = str(dest)
        else:
            print(f"  WARNING: {src_path} not found")

    if thumbnail_src:
        thumb = Path(thumbnail_src)
        if thumb.exists():
            dest = ad / "thumbnail.png"
            shutil.move(str(thumb), str(dest))
            paths["thumbnail_png"] = str(dest)

    # Persist to job record
    data = _load_jobs()
    job = _find_job(data, job_id)
    _update_job(data, job, {"assets": {**job.get("assets", {}), **paths}})
    _save_jobs(data)
    return paths


# ── Generic record sync ───────────────────────────────────────────────────────

def sync_record(job_id: str, **fields) -> None:
    """Deep-merge arbitrary fields into the job record (YouTube URLs, Drive links, etc.)."""
    data = _load_jobs()
    job = _find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")
    _update_job(data, job, fields)
    _save_jobs(data)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TS-12 asset store — move raw assets, upload to Drive, store finals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # store-raw
    p_raw = sub.add_parser("store-raw", help="Move raw NotebookLM downloads to canonical store")
    p_raw.add_argument("job_id")
    p_raw.add_argument("--cinematic", metavar="PATH", help="Path to Cinematic (16:9) mp4")
    p_raw.add_argument("--short",     metavar="PATH", help="Path to Short (9:16) mp4")
    p_raw.add_argument("--infographic", metavar="PATH", help="Path to infographic PNG/JPG")
    p_raw.add_argument("--slidedeck",   metavar="PATH", help="Path to slide deck PDF/PPTX")
    p_raw.add_argument("--from-downloads", action="store_true",
                       help="Auto-detect files downloaded to ~/Downloads in the last hour")
    p_raw.add_argument("--from-raw-subdir", metavar="PATH",
                       help="Scan this directory for raw NotebookLM files (default: <store>/<slug>/raw/)")

    # drive-upload
    p_drive = sub.add_parser("drive-upload", help="Upload infographic + slidedeck to Drive")
    p_drive.add_argument("job_id")

    # store-finals
    p_finals = sub.add_parser("store-finals", help="Move built finals into asset store")
    p_finals.add_argument("job_id")
    p_finals.add_argument("--short",     required=True, metavar="PATH", help="Final short mp4")
    p_finals.add_argument("--long",      required=True, metavar="PATH", help="Final long mp4")
    p_finals.add_argument("--thumbnail", metavar="PATH", help="Thumbnail PNG (optional)")

    # status
    p_status = sub.add_parser("status", help="Show asset store state for a job")
    p_status.add_argument("job_id")

    args = parser.parse_args()

    if args.command == "store-raw":
        raw_sub_arg = Path(args.from_raw_subdir) if getattr(args, "from_raw_subdir", None) else None
        paths = store_raw_assets(
            args.job_id,
            cinematic_src=args.cinematic,
            short_src=args.short,
            infographic_src=args.infographic,
            slidedeck_src=args.slidedeck,
            search_downloads=args.from_downloads,
            raw_subdir=raw_sub_arg,
        )
        for field, path in paths.items():
            print(f"  {field}: {path}")

    elif args.command == "drive-upload":
        links = upload_drive(args.job_id)
        for k, v in links.items():
            print(f"  {k}: {v}")

    elif args.command == "store-finals":
        paths = store_finals(
            args.job_id,
            short_src=args.short,
            long_src=args.long,
            thumbnail_src=getattr(args, "thumbnail", None),
        )
        for field, path in paths.items():
            print(f"  {field}: {path}")

    elif args.command == "status":
        data = _load_jobs()
        job = _find_job(data, args.job_id)
        if not job:
            sys.exit(f"Job not found: {args.job_id}")
        existing_store_dir = job.get("assets", {}).get("store_dir", "")
        ad = Path(existing_store_dir) if existing_store_dir else (ASSET_BASE / date_slug(job))
        print(f"Asset store: {ad}")
        print(f"  exists: {ad.exists()}")
        if ad.exists():
            for f in sorted(ad.rglob("*")):
                if f.is_file():
                    print(f"  {f.relative_to(ad)}  ({f.stat().st_size // 1024}KB)")
        drive = job.get("drive", {})
        if drive:
            print("\nDrive:")
            for k, v in drive.items():
                print(f"  {k}: {v}")
        yt = job.get("youtube", {})
        if yt.get("short_url") or yt.get("long_url"):
            print("\nYouTube:")
            if yt.get("short_url"):
                print(f"  short: {yt['short_url']}")
            if yt.get("long_url"):
                print(f"  long:  {yt['long_url']}")


if __name__ == "__main__":
    main()
