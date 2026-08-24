#!/usr/bin/env python3
"""
TS-10: Mac-side pipeline worker.

Pulls queued jobs from the DO intake API, runs the full pipeline on the Mac Mini,
and posts status back to DO after each stage.

End-to-end flow:
  DO queue (queued) → claim → NotebookLM (raw mp4s) → build (hook/outro/ffmpeg) →
  YouTube upload → X post → DO queue (published)

Usage:
    # One-shot: claim + run next queued job
    python3 mac_worker.py run [--tunnel] [--dry-run]

    # One-shot: run a specific job (must already be local or in DO)
    python3 mac_worker.py run --job ts-20260822-my-idea [--tunnel] [--stage notebooklm|build|upload|post]

    # Daemon: poll DO every N seconds (default 120)
    python3 mac_worker.py watch [--interval 120] [--tunnel]

    # Show DO queue + local pipeline state
    python3 mac_worker.py status [--tunnel]

Environment:
    DO_INTAKE_URL   Base URL of the intake API (default: http://localhost:8766)
                    Use --tunnel to SSH-tunnel to the droplet first.
    INTAKE_TOKEN    Optional bearer token for the intake API.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
PIPELINE_PY = HERE / "pipeline.py"
NLM_DRIVER_PY = HERE / "notebooklm_driver.py"

DEFAULT_INTAKE_URL = os.environ.get("DO_INTAKE_URL", "http://localhost:8766")
DEFAULT_POLL_INTERVAL = 120  # seconds


# ── Subprocess helpers ────────────────────────────────────────────────────────

def _run(cmd: list[str], dry_run: bool = False) -> int:
    """Run a subprocess; return exit code."""
    print(f"  $ {' '.join(cmd)}")
    if dry_run:
        print("  [dry-run] skipping")
        return 0
    result = subprocess.run(cmd)
    return result.returncode


def _python(script: Path, *args: str, dry_run: bool = False) -> int:
    return _run([sys.executable, str(script)] + list(args), dry_run=dry_run)


# ── Stage runners ─────────────────────────────────────────────────────────────

def stage_notebooklm(job_id: str, dry_run: bool = False) -> bool:
    """
    Run the NotebookLM browser driver (TS-2) to download raw mp4s.

    Returns True on success, False if steps are still stubs or an error occurs.
    """
    print("\n── stage: notebooklm ─────────────────────")
    rc = _python(NLM_DRIVER_PY, "run", job_id, *(["--dry-run"] if dry_run else []))
    if rc == 2:
        print(
            "\n  ⚠  NotebookLM steps are STUBS — see CLICK_PROTOCOL.md.\n"
            "  Fill in the Playwright selectors after Miguel's demo, then\n"
            "  re-run: mac_worker.py run --job " + job_id + " --stage notebooklm\n"
            "  OR manually download the mp4s and set-sources:\n"
            f"  python3 pipeline.py set-sources {job_id} --short PATH --long PATH\n"
        )
        return False
    if rc != 0:
        print(f"\n  ✗  notebooklm_driver exited {rc}")
        return False
    print(f"\n  ✓  raw mp4s ready for {job_id}")
    return True


def stage_store(job_id: str, dry_run: bool = False) -> bool:
    """Move raw NotebookLM downloads to the canonical asset store, then Drive-upload."""
    print("\n── stage: store ──────────────────────────")
    if dry_run:
        print("  [dry-run] would move raw assets to ~/flotilla/tech-shorts/assets/<slug>/")
        print("  [dry-run] would upload infographic.png + slidedeck.pdf to Drive")
        return True
    try:
        from asset_store import store_raw_assets, upload_drive
        paths = store_raw_assets(job_id, search_downloads=False)
        if not paths:
            print("  no raw assets found to store (raw/ subdir empty, --from-downloads not set)")
            print("  continuing — build stage will use job.assets paths as-is")
        else:
            print(f"\n  ✓  {len(paths)} assets stored")
        print("\n  uploading shareable assets to Drive ...")
        try:
            links = upload_drive(job_id)
            for k, v in links.items():
                print(f"  {k}: {v}")
        except Exception as e:
            print(f"  ⚠  Drive upload skipped: {e}")
            print("  continuing pipeline — Drive upload can be retried manually")
        print(f"\n  ✓  store stage done for {job_id}")
        return True
    except Exception as e:
        print(f"\n  ✗  store stage failed: {e}")
        return False


def stage_build(job_id: str, dry_run: bool = False) -> bool:
    print("\n── stage: build ──────────────────────────")
    rc = _python(PIPELINE_PY, "run", job_id, "--stage", "build", *(["--dry-run"] if dry_run else []))
    if rc != 0:
        print(f"\n  ✗  build stage exited {rc}")
        return False
    print(f"\n  ✓  build complete for {job_id}")
    return True


def stage_upload(job_id: str, dry_run: bool = False) -> bool:
    print("\n── stage: upload ─────────────────────────")
    rc = _python(PIPELINE_PY, "run", job_id, "--stage", "upload", *(["--dry-run"] if dry_run else []))
    if rc != 0:
        print(f"\n  ✗  upload stage exited {rc}")
        return False
    print(f"\n  ✓  uploaded to YouTube for {job_id}")
    return True


def stage_post(job_id: str, dry_run: bool = False) -> bool:
    print("\n── stage: post ───────────────────────────")
    rc = _python(PIPELINE_PY, "run", job_id, "--stage", "post", *(["--dry-run"] if dry_run else []))
    if rc != 0:
        print(f"\n  ✗  post stage exited {rc}")
        return False
    print(f"\n  ✓  cross-posted to X for {job_id}")
    return True


# ── Read local pipeline state ─────────────────────────────────────────────────

def _local_job_state(job_id: str) -> dict:
    """Read the local job record (pipeline.py writes updates here)."""
    jobs_file = HERE / "jobs.json"
    if not jobs_file.exists():
        return {}
    with open(jobs_file) as f:
        data = json.load(f)
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    for j in jobs:
        if j.get("id") == job_id or j.get("slug") == job_id:
            return j
    return {}


# ── Core: run one job ─────────────────────────────────────────────────────────

def run_job(
    job: dict,
    base_url: str,
    dry_run: bool = False,
    start_stage: Optional[str] = None,
) -> None:
    """
    Execute the full pipeline for a single job and post status back to DO.

    stage order: notebooklm → store → build → upload → post

    The 'store' stage (TS-12) moves raw NotebookLM downloads into
    ~/flotilla/tech-shorts/assets/<slug>/ and uploads shareable assets to Drive.

    If start_stage is given, skip all earlier stages (useful for resuming).
    The job must already be merged into local jobs.json before calling.
    """
    from do_sync import post_status, merge_job_local

    job_id = job["id"]
    print(f"\n{'='*60}")
    print(f"  Job: {job_id}")
    print(f"  Title: {job['title']}")
    print(f"  Stage start: {start_stage or 'notebooklm'}")
    print(f"{'='*60}\n")

    stages = ["notebooklm", "store", "build", "upload", "post"]
    if start_stage and start_stage in stages:
        stages = stages[stages.index(start_stage):]

    # Check if raw mp4s are already present (either canonical store or legacy paths)
    assets = job.get("assets", {})
    raw_candidates = [
        assets.get("raw_cinematic_mp4", ""),
        assets.get("raw_short_mp4", ""),
        assets.get("raw_long_mp4", ""),
    ]
    has_raws = any(p and Path(p).exists() for p in raw_candidates)

    for stage in stages:
        if stage == "notebooklm":
            if has_raws:
                print(f"\n  [skip notebooklm] raw mp4s already present")
                continue
            ok = stage_notebooklm(job_id, dry_run)
            if not ok:
                print(f"\n  Halting at notebooklm stage — manual intervention needed.")
                print(f"  Once raw mp4s are ready, resume with:")
                print(f"    python3 mac_worker.py run --job {job_id} --stage store\n")
                if not dry_run:
                    post_status(job_id, "failed", base_url)
                return
            if not dry_run:
                local = _local_job_state(job_id)
                ra = local.get("assets", {})
                post_status(
                    job_id, "raw_videos_ready", base_url,
                    assets={"raw_short_mp4": ra.get("raw_short_mp4", ""),
                            "raw_long_mp4": ra.get("raw_long_mp4", "")},
                )

        elif stage == "store":
            ok = stage_store(job_id, dry_run)
            if not ok:
                print(f"\n  Store stage failed — check asset_store.py logs.")
                if not dry_run:
                    post_status(job_id, "failed", base_url)
                return
            if not dry_run:
                local = _local_job_state(job_id)
                la = local.get("assets", {})
                drive = local.get("drive", {})
                post_status(
                    job_id, "assets_stored", base_url,
                    assets={k: la.get(k, "") for k in (
                        "store_dir", "raw_cinematic_mp4", "raw_short_mp4",
                        "infographic_png", "slidedeck_pdf",
                    )},
                    drive=drive,
                )

        elif stage == "build":
            ok = stage_build(job_id, dry_run)
            if not ok:
                print(f"\n  Build failed — check hook_copy and raw sources.")
                if not dry_run:
                    post_status(job_id, "failed", base_url)
                return
            if not dry_run:
                local = _local_job_state(job_id)
                la = local.get("assets", {})
                post_status(
                    job_id, "assembled", base_url,
                    assets={"final_short_mp4": la.get("final_short_mp4", ""),
                            "final_long_mp4": la.get("final_long_mp4", "")},
                )

        elif stage == "upload":
            ok = stage_upload(job_id, dry_run)
            if not ok:
                print(f"\n  Upload failed — check YouTube credentials.")
                if not dry_run:
                    post_status(job_id, "failed", base_url)
                return
            if not dry_run:
                local = _local_job_state(job_id)
                lyt = local.get("youtube", {})
                post_status(
                    job_id, "assembled", base_url,
                    youtube={
                        "short_id": lyt.get("short_id", ""),
                        "short_url": lyt.get("short_url", ""),
                        "long_id": lyt.get("long_id", ""),
                        "long_url": lyt.get("long_url", ""),
                    },
                )

        elif stage == "post":
            ok = stage_post(job_id, dry_run)
            if not ok:
                print(f"\n  X post failed — check credentials.")
                if not dry_run:
                    post_status(job_id, "failed", base_url)
                return
            if not dry_run:
                local = _local_job_state(job_id)
                lx = local.get("x_post", {})
                post_status(
                    job_id, "published", base_url,
                    x_post={
                        "post_id": lx.get("post_id", ""),
                        "post_url": lx.get("post_url", ""),
                        "caption": lx.get("caption", ""),
                    },
                )

    if dry_run:
        print(f"\n  [dry-run complete] no real changes made\n")
    else:
        print(f"\n  Pipeline complete for {job_id}  ✓\n")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> None:
    from do_sync import (
        open_tunnel, close_tunnel, claim_queued_job,
        get_job, merge_job_local, health_check,
    )

    base_url = args.base_url
    if args.tunnel:
        open_tunnel()

    try:
        if not health_check(base_url):
            sys.exit(
                f"✗  Intake API not reachable at {base_url}\n"
                "   Try --tunnel to SSH-forward, or set DO_INTAKE_URL."
            )

        if args.job:
            # Run a specific job (must be claimable or already local)
            job = get_job(args.job, base_url)
            if not job:
                # Try local
                job = _local_job_state(args.job)
                if not job:
                    sys.exit(f"Job not found on DO or locally: {args.job}")
            merge_job_local(job)
        else:
            # Claim next queued
            job = claim_queued_job(base_url)
            if not job:
                print("No queued jobs. Nothing to do.")
                return
            merge_job_local(job)

        run_job(
            job,
            base_url=base_url,
            dry_run=args.dry_run,
            start_stage=args.stage or None,
        )
    finally:
        if args.tunnel:
            close_tunnel()


def cmd_watch(args: argparse.Namespace) -> None:
    from do_sync import (
        open_tunnel, close_tunnel, claim_queued_job,
        merge_job_local, health_check,
    )

    base_url = args.base_url
    interval = args.interval

    if args.tunnel:
        open_tunnel()

    print(f"[worker] Watching DO queue every {interval}s  (Ctrl-C to stop)")
    try:
        while True:
            if health_check(base_url):
                job = claim_queued_job(base_url)
                if job:
                    merge_job_local(job)
                    run_job(job, base_url=base_url)
                else:
                    ts = time.strftime("%H:%M:%S")
                    print(f"[{ts}] queue empty — sleeping {interval}s")
            else:
                print(f"[worker] API not reachable — retrying in {interval}s")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[worker] stopped")
    finally:
        if args.tunnel:
            close_tunnel()


def cmd_status(args: argparse.Namespace) -> None:
    from do_sync import open_tunnel, close_tunnel, list_jobs, health_check

    base_url = args.base_url
    if args.tunnel:
        open_tunnel()

    try:
        if not health_check(base_url):
            print(f"✗  API not reachable at {base_url}")
        else:
            do_jobs = list_jobs(base_url=base_url)
            print(f"\n── DO Queue ({base_url}) ──")
            if not do_jobs:
                print("  (empty)")
            for j in do_jobs:
                print(f"  {j['status']:16} {j['id']}")

        # Local pipeline state
        jobs_file = HERE / "jobs.json"
        if jobs_file.exists():
            with open(jobs_file) as f:
                data = json.load(f)
            local_jobs = data.get("jobs", data) if isinstance(data, dict) else data
            print(f"\n── Local pipeline state ──")
            for j in local_jobs:
                yt = j.get("youtube", {})
                xp = j.get("x_post", {})
                print(f"  {j.get('status','?'):16} {j['id']}")
                ja = j.get("assets", {})
                print(f"    store:     {ja.get('store_dir') or '(not set)'}")
                print(f"    cinematic: {ja.get('raw_cinematic_mp4') or ja.get('raw_long_mp4') or '(not set)'}")
                print(f"    short_raw: {ja.get('raw_short_mp4') or '(not set)'}")
                print(f"    final:     {ja.get('final_short_mp4') or '(not built)'}")
                jd = j.get("drive", {})
                print(f"    drive:     {jd.get('folder_url') or '(not uploaded)'}")
                print(f"    yt_short:  {yt.get('short_url') or '(not uploaded)'}")
                print(f"    x_post:    {xp.get('post_url') or '(not posted)'}")
                print()
    finally:
        if args.tunnel:
            close_tunnel()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TS-10: Mac pipeline worker — pulls from DO, runs pipeline, reports back",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_INTAKE_URL,
        help=f"DO intake API base URL (default: {DEFAULT_INTAKE_URL})",
    )
    parser.add_argument(
        "--tunnel", action="store_true",
        help="Open SSH tunnel to robotsales before connecting",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Claim + run next queued job (or run a specific job)")
    p_run.add_argument("--job", metavar="JOB_ID", help="Run a specific job (skip claim)")
    p_run.add_argument(
        "--stage",
        choices=["notebooklm", "store", "build", "upload", "post"],
        help="Start from this stage (skip earlier stages)",
    )
    p_run.add_argument("--dry-run", action="store_true", help="Print plan, don't execute")

    # watch
    p_watch = sub.add_parser("watch", help="Daemon: poll DO and process jobs continuously")
    p_watch.add_argument(
        "--interval", type=int, default=DEFAULT_POLL_INTERVAL,
        help=f"Poll interval in seconds (default: {DEFAULT_POLL_INTERVAL})",
    )

    # status
    sub.add_parser("status", help="Show DO queue + local pipeline state")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "watch":
        cmd_watch(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
