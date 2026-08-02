from __future__ import annotations

from datetime import datetime, timedelta, timezone

from manifest_schema import normalize_manifest
from flotilla_publisher.reddit_client import RedditClientBundle, RedditRateLimitGuard
from submission_executor import (
    AccountSnapshot,
    SubmittedPost,
    VERIFICATION_DELAYS,
    enqueue_verification_checks,
    isoformat_z,
    record_submission,
    run_once,
    select_next_pending,
    update_manifest_after_submit,
)


class FakePocketBase:
    def __init__(self) -> None:
        self.records = []

    def create_record(self, collection, payload):
        row = {"id": f"{collection}-{len(self.records) + 1}", **payload}
        self.records.append((collection, payload))
        return row


class FakeUser:
    def me(self):
        return "robotrossart"


class FakeRedditor:
    created_utc = datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp()
    link_karma = 100
    comment_karma = 25


class FakeSubmission:
    id = "abc123"
    permalink = "/r/LocalLLaMA/comments/abc123/running_apertus_locally/"


class FakeSubreddit:
    def __init__(self):
        self.submissions = []

    def submit(self, **kwargs):
        self.submissions.append(kwargs)
        return FakeSubmission()


class FakeAuthed:
    def __init__(self):
        self.user = FakeUser()
        self.target = FakeSubreddit()

    def redditor(self, username):
        assert username == "robotrossart"
        return FakeRedditor()

    def subreddit(self, name):
        assert name == "LocalLLaMA"
        return self.target


def sample_manifest():
    return normalize_manifest(
        [
            {
                "id": "apertus-m4-local-inference",
                "angle": "local inference on commodity Apple Silicon",
                "body_seed": "A concrete write-up of the Apertus 8B Mac Mini run.",
                "primary_sub": "r/LocalLLaMA",
                "fallback_subs": ["r/eutech"],
            }
        ],
        [
            {
                "name": "r/LocalLLaMA",
                "traction_tier": "A",
                "allows_link_posts": True,
                "allows_image_posts": True,
                "requires_flair": True,
                "flair_id": "Discussion",
                "min_account_age_days": 30,
                "min_karma": 50,
                "last_posted_ts": None,
                "cooldown_hours": 168,
                "bot_policy": "allowed",
            },
            {
                "name": "r/eutech",
                "traction_tier": "B",
                "allows_link_posts": True,
                "allows_image_posts": True,
                "requires_flair": True,
                "flair_id": "Technology",
                "min_account_age_days": 0,
                "min_karma": 0,
                "last_posted_ts": None,
                "cooldown_hours": 168,
                "bot_policy": "allowed",
            },
        ],
        generated_at="2026-08-02T20:00:00Z",
    )


def test_select_next_pending_requires_account_requirements():
    manifest = sample_manifest()
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)

    too_new = AccountSnapshot(username="robotrossart", age_days=4, karma=100)
    assert select_next_pending(manifest, too_new, now=now) is None

    eligible = AccountSnapshot(username="robotrossart", age_days=40, karma=100)
    selected = select_next_pending(manifest, eligible, now=now)
    assert selected is not None
    assert selected.post["id"] == "apertus-m4-local-inference"
    assert selected.subreddit["name"] == "r/LocalLLaMA"


def test_select_next_pending_respects_subreddit_cooldown():
    manifest = sample_manifest()
    now = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    manifest["subreddits"][0]["last_posted_ts"] = isoformat_z(now - timedelta(hours=12))

    account = AccountSnapshot(username="robotrossart", age_days=40, karma=100)
    assert select_next_pending(manifest, account, now=now) is None


def test_record_submission_uses_acceptance_fields():
    pb = FakePocketBase()
    manifest = sample_manifest()
    post = manifest["posts"][0]
    subreddit = manifest["subreddits"][0]
    draft = {"chosen_title": "Running Apertus locally", "body": "I tested it."}
    submitted = SubmittedPost("abc123", "https://reddit.com/r/LocalLLaMA/comments/abc123/x")
    ts = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)

    row = record_submission(pb, post, subreddit, draft, submitted, ts)

    assert row["post_id"] == post["id"]
    assert row["sub"] == "r/LocalLLaMA"
    assert row["submission_id"] == "abc123"
    assert row["permalink"].startswith("https://reddit.com/")
    assert row["ts"] == "2026-08-02T09:00:00Z"


def test_enqueue_verification_checks_at_required_offsets():
    pb = FakePocketBase()
    ts = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    submitted = SubmittedPost("abc123", "https://reddit.com/r/LocalLLaMA/comments/abc123/x")

    rows = enqueue_verification_checks(pb, "post-1", "r/LocalLLaMA", submitted, ts)

    assert len(rows) == 3
    assert [row["check_label"] for row in rows] == [label for label, _ in VERIFICATION_DELAYS]
    assert [row["due_at"] for row in rows] == [
        "2026-08-02T09:15:00Z",
        "2026-08-02T11:00:00Z",
        "2026-08-02T21:00:00Z",
    ]
    assert all(row["status"] == "queued" for row in rows)


def test_update_manifest_after_submit_marks_posted_and_cooldown():
    manifest = sample_manifest()
    ts = datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc)
    draft = {"chosen_title": "Running Apertus locally", "body": "I tested it."}
    submitted = SubmittedPost("abc123", "https://reddit.com/r/LocalLLaMA/comments/abc123/x")

    update_manifest_after_submit(manifest, "apertus-m4-local-inference", "r/LocalLLaMA", draft, submitted, ts)

    post = manifest["posts"][0]
    assert post["status"] == "posted"
    assert post["attempts"][0]["outcome"] == "submitted"
    assert post["attempts"][0]["submission_id"] == "abc123"
    assert manifest["subreddits"][0]["last_posted_ts"] == "2026-08-02T09:00:00Z"


def test_run_once_acceptance_path(tmp_path):
    manifest = sample_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(__import__("json").dumps(manifest))
    pb = FakePocketBase()
    authed = FakeAuthed()
    bundle = RedditClientBundle(
        authed=authed,
        readonly=None,
        guard=RedditRateLimitGuard(sleep=lambda _: None),
        credentials=type("Creds", (), {"username": "robotrossart"})(),
    )
    telegram_messages = []

    result = run_once(
        manifest_path=manifest_path,
        pb_client=pb,
        reddit_bundle=bundle,
        composer=lambda *args, **kwargs: {
            "r/LocalLLaMA": {
                "chosen_title": "Running Apertus locally",
                "body": "I tested it on a Mac Mini M4.",
                "lint_clean": True,
                "lint_failures": [],
            }
        },
        telegram_sender=lambda text: telegram_messages.append(text) is None or True,
        schema_migrator=lambda: None,
        now=datetime(2026, 8, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert result["submission_id"] == "abc123"
    assert result["permalink"].startswith("https://reddit.com/")
    assert [collection for collection, _ in pb.records] == [
        "publisher_submissions",
        "publisher_verification_queue",
        "publisher_verification_queue",
        "publisher_verification_queue",
    ]
    assert len(telegram_messages) == 1
    assert "https://reddit.com/" in telegram_messages[0]

    updated = __import__("json").loads(manifest_path.read_text())
    assert updated["posts"][0]["status"] == "posted"
    assert updated["posts"][0]["attempts"][0]["submission_id"] == "abc123"
