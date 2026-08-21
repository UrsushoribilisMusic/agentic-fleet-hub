#!/usr/bin/env python3
"""
TS-2: NotebookLM browser automation harness.

Drives Chrome via Playwright to:
  1. Open or create a NotebookLM notebook
  2. Add source URL(s)
  3. Trigger Video Overview generation (short 9:16 + long 16:9)
  4. Wait for both videos to be ready
  5. Download both mp4s to a working directory

Browser interaction steps (1-5) are STUBS pending Miguel's demo walkthrough.
See CLICK_PROTOCOL.md for the template; fill in selectors after the demo.

Usage:
    python3 notebooklm_driver.py run <job_id> [--workdir DIR] [--dry-run]
    python3 notebooklm_driver.py status <job_id>

Deps:
    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
JOBS_FILE = HERE / "jobs.json"
NOTEBOOKLM_URL = "https://notebooklm.google.com/"
COOKIE_JAR = Path.home() / ".ts_notebooklm_cookies.json"

# Generation timeout (seconds) — NotebookLM can take 5–15 min per video
VIDEO_READY_TIMEOUT = 900
VIDEO_POLL_INTERVAL = 15


# ── Job I/O (thin wrappers over intake.py) ────────────────────────────────────

def _load_jobs() -> dict:
    with open(JOBS_FILE) as f:
        return json.load(f)


def _save_jobs(data: dict) -> None:
    import fcntl, os, datetime
    data["updated_at"] = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    lock_path = HERE / "jobs.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            tmp = JOBS_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            tmp.replace(JOBS_FILE)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _find_job(data: dict, job_id: str) -> Optional[dict]:
    for j in data["jobs"]:
        if j["id"] == job_id or j.get("slug") == job_id:
            return j
    return None


def _update_job(job_id: str, **fields) -> None:
    data = _load_jobs()
    job = _find_job(data, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    def _deep_set(target, source):
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                _deep_set(target[k], v)
            else:
                target[k] = v

    _deep_set(job, fields)
    import datetime
    job["updated_at"] = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_jobs(data)


# ── NotebookLM driver ─────────────────────────────────────────────────────────

class NotebookLMDriver:
    """
    Browser automation harness for NotebookLM Video Overview generation.

    Browser steps are STUBS. Fill in CLICK_PROTOCOL.md after Miguel's demo,
    then replace each `raise NotImplementedError(...)` with real Playwright calls.
    """

    def __init__(
        self,
        source_urls: list[str],
        workdir: Path,
        existing_notebook_url: str = "",
        headless: bool = False,
    ):
        self.source_urls = source_urls
        self.workdir = workdir
        self.existing_notebook_url = existing_notebook_url
        self.headless = headless
        self._browser = None
        self._context = None
        self._page = None

    # ── Browser lifecycle ──────────────────────────────────────────────────

    def _launch(self) -> None:
        """Start Playwright + persistent Chrome profile (keeps Google session)."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "playwright not installed — run: pip install playwright && playwright install chromium"
            )

        self._pw = sync_playwright().__enter__()

        # Persistent context so Google cookies survive between runs
        user_data_dir = Path.home() / ".ts_notebooklm_profile"
        user_data_dir.mkdir(exist_ok=True)

        self._context = self._pw.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=self.headless,
            channel="chromium",
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._page = self._context.new_page()
        print(f"  browser launched (headless={self.headless})")

    def _close(self) -> None:
        if self._context:
            self._context.close()
        if self._pw:
            self._pw.__exit__(None, None, None)

    # ── Step 1 ─────────────────────────────────────────────────────────────

    def open_or_create_notebook(self) -> str:
        """
        Navigate to NotebookLM and open an existing notebook or create a new one.

        Returns the notebook URL (persisted to job["notebook_url"]).

        TODO(after-demo): fill in Playwright selectors from CLICK_PROTOCOL.md §Step 1.
        """
        raise NotImplementedError(
            "Step 1 not yet wired — see CLICK_PROTOCOL.md §Step 1.\n"
            "Wire after Miguel's demo walkthrough."
        )

    # ── Step 2 ─────────────────────────────────────────────────────────────

    def add_sources(self) -> None:
        """
        Add each source URL from self.source_urls to the open notebook.

        Skips URLs already present in the source list.

        TODO(after-demo): fill in Playwright selectors from CLICK_PROTOCOL.md §Step 2.
        """
        raise NotImplementedError(
            "Step 2 not yet wired — see CLICK_PROTOCOL.md §Step 2.\n"
            "Wire after Miguel's demo walkthrough."
        )

    # ── Step 3 ─────────────────────────────────────────────────────────────

    def trigger_video_overview(self) -> None:
        """
        Open the Video Overview panel and trigger generation for both formats:
          - Short (9:16 vertical)
          - Long  (16:9 landscape)

        TODO(after-demo): fill in Playwright selectors from CLICK_PROTOCOL.md §Step 3.
        """
        raise NotImplementedError(
            "Step 3 not yet wired — see CLICK_PROTOCOL.md §Step 3.\n"
            "Wire after Miguel's demo walkthrough."
        )

    # ── Step 4 ─────────────────────────────────────────────────────────────

    def wait_for_video_ready(self, timeout_s: int = VIDEO_READY_TIMEOUT) -> None:
        """
        Poll until both Short and Long video download buttons are visible/enabled.

        Raises RuntimeError on timeout or generation failure.

        TODO(after-demo): fill in Playwright selectors from CLICK_PROTOCOL.md §Step 4.
        """
        raise NotImplementedError(
            "Step 4 not yet wired — see CLICK_PROTOCOL.md §Step 4.\n"
            "Wire after Miguel's demo walkthrough."
        )

    # ── Step 5 ─────────────────────────────────────────────────────────────

    def download_mp4s(self, job_id: str) -> tuple[Path, Path]:
        """
        Download both mp4s using Playwright's download interception.

        Returns (short_path, long_path) as absolute Paths.

        File naming:
          workdir/{job_id}_short.mp4   ← 9:16 vertical
          workdir/{job_id}_long.mp4    ← 16:9 landscape

        TODO(after-demo): fill in Playwright selectors from CLICK_PROTOCOL.md §Step 5.
        """
        # Playwright download interception pattern (ready to use):
        #
        #   with self._page.expect_download() as dl_info:
        #       self._page.click(SHORT_DOWNLOAD_SELECTOR)
        #   download = dl_info.value
        #   short_path = self.workdir / f"{job_id}_short.mp4"
        #   download.save_as(short_path)
        #
        # Repeat for long format.

        raise NotImplementedError(
            "Step 5 not yet wired — see CLICK_PROTOCOL.md §Step 5.\n"
            "Wire after Miguel's demo walkthrough."
        )

    # ── Orchestrator ───────────────────────────────────────────────────────

    def run(self, job_id: str) -> tuple[Path, Path]:
        """
        Run all 5 steps end-to-end.

        Returns (short_path, long_path) once both mp4s are downloaded.
        On any stub NotImplementedError, re-raises with guidance.
        """
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._launch()
        try:
            print("  [1/5] open/create notebook")
            notebook_url = self.open_or_create_notebook()
            _update_job(job_id, notebook_url=notebook_url)

            print("  [2/5] add sources")
            self.add_sources()

            print("  [3/5] trigger video overview")
            self.trigger_video_overview()

            print(f"  [4/5] waiting for videos (up to {VIDEO_READY_TIMEOUT}s)...")
            self.wait_for_video_ready()

            print("  [5/5] downloading mp4s")
            short_path, long_path = self.download_mp4s(job_id)
        finally:
            self._close()

        return short_path, long_path


# ── Dry-run mode ──────────────────────────────────────────────────────────────

def dry_run_report(job: dict, workdir: Path) -> None:
    """Print what the driver would do without opening a browser."""
    print("\n[dry-run] NotebookLM driver plan:")
    print(f"  job_id:      {job['id']}")
    print(f"  title:       {job['title']}")
    print(f"  source_urls: {', '.join(job.get('source_urls', []))}")
    print(f"  notebook:    {job.get('notebook_url') or '(will create new)'}")
    print(f"  workdir:     {workdir}")
    short_out = workdir / f"{job['id']}_short.mp4"
    long_out  = workdir / f"{job['id']}_long.mp4"
    print(f"\n  Step 1 — open/create notebook at {NOTEBOOKLM_URL}")
    print(f"  Step 2 — add {len(job.get('source_urls', []))} source URL(s)")
    print(f"  Step 3 — trigger Video Overview (short + long)")
    print(f"  Step 4 — wait up to {VIDEO_READY_TIMEOUT}s for both videos")
    print(f"  Step 5 — download:")
    print(f"           {short_out}   ← 9:16 short")
    print(f"           {long_out}    ← 16:9 long")
    print(f"\n  On success: job status → raw_videos_ready")
    print(f"\n  NOTE: Steps 1-5 are STUBS — see CLICK_PROTOCOL.md to wire them.\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> None:
    data = _load_jobs()
    job = _find_job(data, args.job_id)
    if job is None:
        sys.exit(f"Job not found: {args.job_id}")

    workdir = Path(args.workdir) if args.workdir else HERE / "raw" / job["id"]

    if args.dry_run:
        dry_run_report(job, workdir)
        return

    print(f"\n── TS-2: NotebookLM driver for {job['id']} ──")
    driver = NotebookLMDriver(
        source_urls=job.get("source_urls", []),
        workdir=workdir,
        existing_notebook_url=job.get("notebook_url", ""),
        headless=args.headless,
    )

    try:
        short_path, long_path = driver.run(job["id"])
    except NotImplementedError as e:
        print(f"\n  BLOCKED: {e}", file=sys.stderr)
        print(
            "\n  This step is not yet wired. See CLICK_PROTOCOL.md for the template.\n"
            "  After Miguel's demo, fill in the selectors and replace the NotImplementedError.\n",
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        print(f"\n  ERROR: {e}", file=sys.stderr)
        _update_job(args.job_id, status="failed")
        sys.exit(1)

    # Success — record paths and advance status
    _update_job(
        args.job_id,
        status="raw_videos_ready",
        assets={
            **job.get("assets", {}),
            "raw_short_mp4": str(short_path),
            "raw_long_mp4": str(long_path),
        },
    )
    print(f"\n  Done.")
    print(f"  short: {short_path}")
    print(f"  long:  {long_path}")
    print(f"  job status → raw_videos_ready\n")
    print("  Next step: run pipeline.py set-copy <job_id> ..., then pipeline.py run <job_id> --stage build")


def cmd_status(args: argparse.Namespace) -> None:
    data = _load_jobs()
    job = _find_job(data, args.job_id)
    if job is None:
        sys.exit(f"Job not found: {args.job_id}")

    print(f"\n── TS-2 status for {job['id']} ──")
    print(f"  title:       {job['title']}")
    print(f"  status:      {job['status']}")
    print(f"  notebook:    {job.get('notebook_url') or '(none)'}")
    assets = job.get("assets", {})
    print(f"  raw_short:   {assets.get('raw_short_mp4') or '(not downloaded)'}")
    print(f"  raw_long:    {assets.get('raw_long_mp4') or '(not downloaded)'}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TS-2: NotebookLM browser automation harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Browser steps are STUBS until wired after Miguel's demo.\n"
            "Use --dry-run to see the plan without opening a browser.\n"
            "See CLICK_PROTOCOL.md for the selector template.\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Run the NotebookLM browser automation for a job")
    p_run.add_argument("job_id", help="Job ID or slug from jobs.json")
    p_run.add_argument(
        "--workdir", metavar="DIR",
        help="Directory to download mp4s into (default: tech-shorts/raw/<job_id>/)"
    )
    p_run.add_argument(
        "--headless", action="store_true",
        help="Run Chrome headless (not recommended — login required on first run)"
    )
    p_run.add_argument(
        "--dry-run", action="store_true",
        help="Print the plan without opening a browser"
    )

    # status
    p_status = sub.add_parser("status", help="Show NotebookLM + asset status for a job")
    p_status.add_argument("job_id", help="Job ID or slug from jobs.json")

    args = parser.parse_args()
    if args.command == "run":
        cmd_run(args)
    elif args.command == "status":
        cmd_status(args)


if __name__ == "__main__":
    main()
