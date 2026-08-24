#!/usr/bin/env python3
"""
Unit tests for tech-shorts intake engine & CLI.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add tech-shorts directory to sys.path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import intake


class TestIntakeEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_intake_test_")
        self.jobs_file = Path(self.test_dir) / "test_jobs.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_get_job(self):
        job = intake.create_job(
            title="Why Small Models Win On-Device",
            source_urls=["https://arxiv.org/abs/1234.5678", "https://notebook.google.com/notebook/abc-123"],
            idea_notes="Low latency and complete privacy.",
            tags=["mlx", "on-device", "canis"],
            jobs_file=self.jobs_file,
        )

        self.assertIsNotNone(job)
        self.assertEqual(job["title"], "Why Small Models Win On-Device")
        self.assertEqual(job["slug"], "why-small-models-win-on-device")
        self.assertEqual(job["status"], "queued")
        self.assertEqual(len(job["source_urls"]), 2)
        self.assertEqual(job["notebook_url"], "https://notebook.google.com/notebook/abc-123")
        self.assertIn("mlx", job["tags"])

        # Fetch by ID
        fetched = intake.get_job(job["id"], jobs_file=self.jobs_file)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], job["id"])

        # Fetch by slug
        fetched_by_slug = intake.get_job("why-small-models-win-on-device", jobs_file=self.jobs_file)
        self.assertIsNotNone(fetched_by_slug)
        self.assertEqual(fetched_by_slug["id"], job["id"])

    def test_list_and_filter_jobs(self):
        intake.create_job(
            title="Job Alpha",
            source_urls="https://example.com/alpha",
            tags="ai,safety",
            status="queued",
            jobs_file=self.jobs_file,
        )
        intake.create_job(
            title="Job Beta",
            source_urls="https://example.com/beta",
            tags="hardware,apple",
            status="in_progress",
            jobs_file=self.jobs_file,
        )
        intake.create_job(
            title="Job Gamma",
            source_urls="https://example.com/gamma",
            tags="ai,mlx",
            status="assembled",
            jobs_file=self.jobs_file,
        )

        all_jobs = intake.list_jobs(jobs_file=self.jobs_file)
        self.assertEqual(len(all_jobs), 3)

        queued_jobs = intake.list_jobs(status="queued", jobs_file=self.jobs_file)
        self.assertEqual(len(queued_jobs), 1)
        self.assertEqual(queued_jobs[0]["title"], "Job Alpha")

        ai_jobs = intake.list_jobs(tag="ai", jobs_file=self.jobs_file)
        self.assertEqual(len(ai_jobs), 2)

        search_jobs = intake.list_jobs(search="hardware", jobs_file=self.jobs_file)
        self.assertEqual(len(search_jobs), 1)
        self.assertEqual(search_jobs[0]["title"], "Job Beta")

    def test_update_job(self):
        job = intake.create_job(
            title="Draft Title",
            source_urls=["https://example.com/draft"],
            jobs_file=self.jobs_file,
        )

        updated = intake.update_job(
            job["id"],
            status="assembled",
            notebook_url="https://notebook.google.com/notebook/test-123",
            assets={"final_short_mp4": "output_short.mp4"},
            youtube={"short_url": "https://youtube.com/shorts/xyz123"},
            jobs_file=self.jobs_file,
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "assembled")
        self.assertEqual(updated["notebook_url"], "https://notebook.google.com/notebook/test-123")
        self.assertEqual(updated["assets"]["final_short_mp4"], "output_short.mp4")
        self.assertEqual(updated["youtube"]["short_url"], "https://youtube.com/shorts/xyz123")

    def test_claim_next_job(self):
        j1 = intake.create_job(title="First In Queue", source_urls="https://example.com/1", jobs_file=self.jobs_file)
        j2 = intake.create_job(title="Second In Queue", source_urls="https://example.com/2", jobs_file=self.jobs_file)

        claimed = intake.claim_next_job(jobs_file=self.jobs_file)
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["id"], j1["id"])
        self.assertEqual(claimed["status"], "in_progress")

        claimed2 = intake.claim_next_job(jobs_file=self.jobs_file)
        self.assertIsNotNone(claimed2)
        self.assertEqual(claimed2["id"], j2["id"])

        claimed3 = intake.claim_next_job(jobs_file=self.jobs_file)
        self.assertIsNone(claimed3)

    def test_delete_job(self):
        job = intake.create_job(title="To Delete", source_urls="https://example.com/del", jobs_file=self.jobs_file)
        self.assertEqual(len(intake.list_jobs(jobs_file=self.jobs_file)), 1)

        ok = intake.delete_job(job["id"], jobs_file=self.jobs_file)
        self.assertTrue(ok)
        self.assertEqual(len(intake.list_jobs(jobs_file=self.jobs_file)), 0)

    def test_cli_execution(self):
        # CLI add
        cmd_add = [
            sys.executable,
            str(HERE / "intake.py"),
            "--file",
            str(self.jobs_file),
            "add",
            "--title",
            "CLI Created Short",
            "--urls",
            "https://test.com/cli1, https://test.com/cli2",
            "--notes",
            "Notes from CLI test",
            "--tags",
            "cli,test",
            "--json",
        ]
        r = subprocess.run(cmd_add, capture_output=True, text=True, check=True)
        created_json = json.loads(r.stdout)
        self.assertEqual(created_json["title"], "CLI Created Short")
        self.assertEqual(len(created_json["source_urls"]), 2)

        # CLI list
        cmd_list = [
            sys.executable,
            str(HERE / "intake.py"),
            "--file",
            str(self.jobs_file),
            "list",
            "--json",
        ]
        r_list = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        jobs_list = json.loads(r_list.stdout)
        self.assertEqual(len(jobs_list), 1)

        # CLI claim
        cmd_claim = [
            sys.executable,
            str(HERE / "intake.py"),
            "--file",
            str(self.jobs_file),
            "claim",
            "--json",
        ]
        r_claim = subprocess.run(cmd_claim, capture_output=True, text=True, check=True)
        claimed_json = json.loads(r_claim.stdout)
        self.assertEqual(claimed_json["status"], "in_progress")


class TestSourceFileHandling(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ts_file_test_")
        self.jobs_file = Path(self.test_dir) / "test_jobs.json"
        self.uploads_root = Path(self.test_dir) / "uploads"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _store(self, job_id: str, content: bytes, name: str) -> dict:
        """Call store_source_file with a patched UPLOADS_DIR."""
        orig = intake.UPLOADS_DIR
        intake.UPLOADS_DIR = self.uploads_root
        try:
            return intake.store_source_file(job_id, content, name)
        finally:
            intake.UPLOADS_DIR = orig

    def test_validate_allowed_extensions(self):
        for name in ("doc.pdf", "notes.md", "essay.markdown", "source.txt"):
            intake.validate_source_file(name, 100)  # should not raise

    def test_validate_rejects_bad_extension(self):
        with self.assertRaises(ValueError) as ctx:
            intake.validate_source_file("doc.docx", 100)
        self.assertIn("not allowed", str(ctx.exception))

    def test_validate_rejects_oversized_file(self):
        limit = intake.MAX_SOURCE_FILE_BYTES + 1
        with self.assertRaises(ValueError) as ctx:
            intake.validate_source_file("big.pdf", limit)
        self.assertIn("too large", str(ctx.exception).lower())

    def test_store_source_file_writes_disk(self):
        content = b"%PDF-1.4 test content"
        meta = self._store("job-abc", content, "report.pdf")
        stored_path = Path(meta["path"])
        self.assertTrue(stored_path.exists())
        self.assertEqual(stored_path.read_bytes(), content)
        self.assertEqual(meta["original_name"], "report.pdf")
        self.assertEqual(meta["size_bytes"], len(content))
        self.assertIn("application/pdf", meta["mime_type"])

    def test_create_job_without_file(self):
        job = intake.create_job(
            title="No File Job",
            source_urls=["https://example.com"],
            jobs_file=self.jobs_file,
        )
        self.assertIn("source_file", job)
        self.assertEqual(job["source_file"], {})

    def test_create_job_with_file_meta(self):
        fake_meta = {
            "path": "uploads/job-x/notes.md",
            "original_name": "notes.md",
            "size_bytes": 512,
            "mime_type": "text/markdown",
        }
        job = intake.create_job(
            title="File Job",
            source_urls=["https://example.com"],
            jobs_file=self.jobs_file,
            source_file_meta=fake_meta,
        )
        self.assertEqual(job["source_file"]["original_name"], "notes.md")
        # Persists across reload
        reloaded = intake.get_job(job["id"], jobs_file=self.jobs_file)
        self.assertEqual(reloaded["source_file"]["original_name"], "notes.md")

    def test_update_job_source_file(self):
        job = intake.create_job(
            title="Update File Test",
            source_urls=["https://example.com"],
            jobs_file=self.jobs_file,
        )
        meta = {"path": "uploads/x/f.txt", "original_name": "f.txt", "size_bytes": 10, "mime_type": "text/plain"}
        updated = intake.update_job(job["id"], jobs_file=self.jobs_file, source_file=meta)
        self.assertEqual(updated["source_file"]["original_name"], "f.txt")

    def test_cli_add_with_source_file(self):
        tmp_file = Path(self.test_dir) / "source.txt"
        tmp_file.write_text("Hello, this is a source document.", encoding="utf-8")

        orig_uploads = intake.UPLOADS_DIR
        intake.UPLOADS_DIR = self.uploads_root
        try:
            cmd = [
                sys.executable,
                str(HERE / "intake.py"),
                "--file", str(self.jobs_file),
                "add",
                "--title", "CLI File Test",
                "--urls", "https://example.com",
                "--source-file", str(tmp_file),
                "--json",
            ]
            r = subprocess.run(cmd, capture_output=True, text=True,
                               env={**os.environ, "TS_UPLOADS_DIR": str(self.uploads_root)})
            self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
            created = json.loads(r.stdout)
            self.assertEqual(created["title"], "CLI File Test")
            self.assertEqual(created["source_file"]["original_name"], "source.txt")
        finally:
            intake.UPLOADS_DIR = orig_uploads


if __name__ == "__main__":
    unittest.main()
