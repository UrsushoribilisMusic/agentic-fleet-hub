"""FLOT-110 unattended Reddit submission executor.

One fire:
1. select the next eligible pending manifest post
2. compose a per-sub draft using FLOT-109
3. submit self/link/image post with required flair
4. write PocketBase publisher_submissions row
5. enqueue FLOT-111 verification checks at T+15m/T+2h/T+12h
6. Telegram the permalink
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import string
import random
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from manifest_schema import (
    DEFAULT_MANIFEST_PATH,
    ManifestValidationError,
    load_manifest,
    validate_manifest,
    write_manifest,
)

from flotilla_publisher.reddit_client import (
    RedditClientBundle,
    RedditCredentialError,
    build_reddit_clients,
    ensure_authenticated,
    load_reddit_credentials_from_infisical,
)

PB_BASE_URL = os.environ.get("POCKETBASE_URL", "http://localhost:8090")
PB_DB_PATH = Path(os.environ.get("POCKETBASE_DB_PATH", "/Users/miguelrodriguez/fleet/pocketbase/pb_data/data.db"))
INFISICAL_DOMAIN = "https://eu.infisical.com"
VERIFICATION_DELAYS = (
    ("t_plus_15m", timedelta(minutes=15)),
    ("t_plus_2h", timedelta(hours=2)),
    ("t_plus_12h", timedelta(hours=12)),
)


class SubmissionExecutorError(RuntimeError):
    """Raised when an unattended fire cannot complete."""


@dataclass(frozen=True)
class AccountSnapshot:
    username: str
    age_days: int
    karma: int


@dataclass(frozen=True)
class SelectedPost:
    post: dict[str, Any]
    subreddit: dict[str, Any]


@dataclass(frozen=True)
class SubmittedPost:
    submission_id: str
    permalink: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


class PocketBaseClient:
    def __init__(self, base_url: str = PB_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def create_record(self, collection: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/collections/{collection}/records"
        req = urllib.request.Request(
            url,
            data=json.dumps(dict(payload)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise SubmissionExecutorError(f"PocketBase create failed for {collection}: {exc.code} {detail}") from exc


def ensure_publisher_runtime_schema(db_path: Path = PB_DB_PATH) -> None:
    """Ensure FLOT-110/FLOT-111 runtime collections exist in local PB SQLite."""

    if not db_path.exists():
        raise SubmissionExecutorError(f"PocketBase data.db not found at {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        _ensure_submission_columns(conn)
        _ensure_verification_queue(conn)
        conn.commit()
    finally:
        conn.close()


def select_next_pending(
    manifest: dict[str, Any],
    account: AccountSnapshot,
    *,
    now: Optional[datetime] = None,
) -> Optional[SelectedPost]:
    validate_manifest(manifest)
    current = now or utc_now()
    subreddits = {sub["name"]: sub for sub in manifest["subreddits"]}

    for post in manifest["posts"]:
        if post.get("status") != "pending":
            continue
        sub = subreddits.get(post.get("primary_sub"))
        if sub is None:
            continue
        if not subreddit_is_eligible(sub, account, current):
            continue
        if not post_gap_is_clear(post, current):
            continue
        return SelectedPost(post=post, subreddit=sub)
    return None


def subreddit_is_eligible(subreddit: Mapping[str, Any], account: AccountSnapshot, now: datetime) -> bool:
    if subreddit.get("bot_policy") == "banned":
        return False
    if account.age_days < int(subreddit.get("min_account_age_days", 0)):
        return False
    if account.karma < int(subreddit.get("min_karma", 0)):
        return False

    last_posted = parse_ts(subreddit.get("last_posted_ts"))
    if last_posted is None:
        return True
    cooldown = timedelta(hours=int(subreddit.get("cooldown_hours", 168)))
    return now - last_posted >= cooldown


def post_gap_is_clear(post: Mapping[str, Any], now: datetime) -> bool:
    attempts = post.get("attempts") or []
    if not attempts:
        return True
    latest = max((parse_ts(attempt.get("ts")) for attempt in attempts), default=None)
    if latest is None:
        return True
    return now - latest >= timedelta(hours=int(post.get("min_gap_hours", 48)))


def submit_to_reddit(
    bundle: RedditClientBundle,
    post: Mapping[str, Any],
    subreddit: Mapping[str, Any],
    draft: Mapping[str, Any],
) -> SubmittedPost:
    title = str(draft["chosen_title"])
    body = str(draft.get("body") or "")
    sub_name = str(subreddit["name"]).removeprefix("r/")
    flair_id = str(subreddit.get("flair_id") or "")
    flair_kw = {"flair_id": flair_id} if subreddit.get("requires_flair") else {}

    target = bundle.authed.subreddit(sub_name)
    artwork = post.get("artwork")
    link = post.get("link")

    if artwork:
        if not subreddit.get("allows_image_posts"):
            raise SubmissionExecutorError(f"{subreddit['name']} does not allow image posts")
        path = Path(str(artwork)).expanduser()
        if not path.exists():
            raise SubmissionExecutorError(f"Artwork not found: {path}")
        submission = bundle.guard.call(
            lambda: target.submit_image(title=title, image_path=str(path), **flair_kw)
        )
    elif link:
        if not subreddit.get("allows_link_posts"):
            raise SubmissionExecutorError(f"{subreddit['name']} does not allow link posts")
        submission = bundle.guard.call(lambda: target.submit(title=title, url=str(link), **flair_kw))
    else:
        submission = bundle.guard.call(lambda: target.submit(title=title, selftext=body, **flair_kw))

    permalink = str(getattr(submission, "permalink", ""))
    if permalink.startswith("/"):
        permalink = f"https://reddit.com{permalink}"
    return SubmittedPost(submission_id=str(submission.id), permalink=permalink)


def run_once(
    *,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    pb_client: Optional[PocketBaseClient] = None,
    reddit_bundle: Optional[RedditClientBundle] = None,
    composer: Optional[Callable[..., dict[str, dict[str, Any]]]] = None,
    telegram_sender: Optional[Callable[[str], bool]] = None,
    schema_migrator: Optional[Callable[[], None]] = None,
    now: Optional[datetime] = None,
    dry_run: bool = False,
) -> Optional[dict[str, Any]]:
    current = now or utc_now()
    schema_migrator = schema_migrator or (lambda: ensure_publisher_runtime_schema())
    schema_migrator()

    manifest = load_manifest(manifest_path)
    validate_manifest(manifest)

    if reddit_bundle is None:
        credentials = load_reddit_credentials_from_infisical(domain=INFISICAL_DOMAIN)
        reddit_bundle = build_reddit_clients(credentials)
    account = snapshot_account(reddit_bundle, now=current)

    selected = select_next_pending(manifest, account, now=current)
    if selected is None:
        return None

    if composer is None:
        from composer import compose

        composer = compose

    drafts = composer(
        selected.post["id"],
        subs=[selected.subreddit["name"]],
        manifest_path=manifest_path,
    )
    draft = drafts.get(selected.subreddit["name"])
    if not draft or not draft.get("lint_clean"):
        raise SubmissionExecutorError(f"Composer did not produce a clean draft for {selected.subreddit['name']}: {draft}")

    if dry_run:
        return {"post_id": selected.post["id"], "sub": selected.subreddit["name"], "draft": draft, "dry_run": True}

    submitted = submit_to_reddit(reddit_bundle, selected.post, selected.subreddit, draft)
    pb = pb_client or PocketBaseClient()
    pb_row = record_submission(pb, selected.post, selected.subreddit, draft, submitted, current)
    checks = enqueue_verification_checks(pb, selected.post["id"], selected.subreddit["name"], submitted, current)
    update_manifest_after_submit(manifest, selected.post["id"], selected.subreddit["name"], draft, submitted, current)
    write_manifest(manifest, manifest_path)

    sender = telegram_sender or send_telegram_permalink
    telegram_ok = sender(
        f"Reddit post submitted to {selected.subreddit['name']}: {submitted.permalink}"
    )
    return {
        "post_id": selected.post["id"],
        "sub": selected.subreddit["name"],
        "submission_id": submitted.submission_id,
        "permalink": submitted.permalink,
        "pb_row": pb_row,
        "queued_checks": checks,
        "telegram_ok": telegram_ok,
    }


def snapshot_account(bundle: RedditClientBundle, *, now: Optional[datetime] = None) -> AccountSnapshot:
    username = ensure_authenticated(bundle)
    redditor = bundle.guard.call(lambda: bundle.authed.redditor(username))
    created_utc = float(getattr(redditor, "created_utc", 0.0) or 0.0)
    current = now or utc_now()
    age_days = 0
    if created_utc > 0:
        age_days = max(0, int((current - datetime.fromtimestamp(created_utc, tz=timezone.utc)).total_seconds() // 86400))
    karma = int(getattr(redditor, "link_karma", 0) or 0) + int(getattr(redditor, "comment_karma", 0) or 0)
    return AccountSnapshot(username=username, age_days=age_days, karma=karma)


def record_submission(
    pb: PocketBaseClient,
    post: Mapping[str, Any],
    subreddit: Mapping[str, Any],
    draft: Mapping[str, Any],
    submitted: SubmittedPost,
    ts: datetime,
) -> dict[str, Any]:
    payload = {
        "platform": "reddit",
        "post_id": post["id"],
        "sub": subreddit["name"],
        "subreddit": subreddit["name"],
        "submission_id": submitted.submission_id,
        "title": draft["chosen_title"],
        "url": post.get("link") or "",
        "permalink": submitted.permalink,
        "angle": post.get("angle") or "",
        "status": "submitted",
        "ts": isoformat_z(ts),
        "submitted_at": isoformat_z(ts),
    }
    return pb.create_record("publisher_submissions", payload)


def enqueue_verification_checks(
    pb: PocketBaseClient,
    post_id: str,
    subreddit: str,
    submitted: SubmittedPost,
    ts: datetime,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, delay in VERIFICATION_DELAYS:
        due_at = ts + delay
        rows.append(
            pb.create_record(
                "publisher_verification_queue",
                {
                    "platform": "reddit",
                    "post_id": post_id,
                    "sub": subreddit,
                    "subreddit": subreddit,
                    "submission_id": submitted.submission_id,
                    "permalink": submitted.permalink,
                    "check_label": label,
                    "due_at": isoformat_z(due_at),
                    "status": "queued",
                },
            )
        )
    return rows


def update_manifest_after_submit(
    manifest: dict[str, Any],
    post_id: str,
    subreddit: str,
    draft: Mapping[str, Any],
    submitted: SubmittedPost,
    ts: datetime,
) -> None:
    for post in manifest["posts"]:
        if post["id"] != post_id:
            continue
        post["status"] = "posted"
        post.setdefault("attempts", []).append(
            {
                "sub": subreddit,
                "ts": isoformat_z(ts),
                "submission_id": submitted.submission_id,
                "outcome": "submitted",
                "draft_title": draft["chosen_title"],
                "draft_body": draft.get("body", ""),
                "permalink": submitted.permalink,
            }
        )
        break
    for sub in manifest["subreddits"]:
        if sub["name"] == subreddit:
            sub["last_posted_ts"] = isoformat_z(ts)
            break


def send_telegram_permalink(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or _infisical_get(
        "TELEGRAM_BOT_TOKEN", path="/flotilla/telegram"
    ) or _infisical_get("TELEGRAM_TOKEN", path="/flotilla/telegram")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or _infisical_get("TELEGRAM_CHAT_ID", path="/flotilla/telegram")
    if not token or not chat_id:
        raise SubmissionExecutorError("Telegram credentials missing")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(
        url,
        data=json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": False}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return bool(payload.get("ok"))


def _infisical_get(secret_name: str, *, path: str) -> str:
    cmd = [
        "infisical",
        "secrets",
        "get",
        secret_name,
        "--domain",
        INFISICAL_DOMAIN,
        "--env",
        os.environ.get("INFISICAL_ENV", "dev"),
        "--path",
        path,
        "--plain",
        "--silent",
    ]
    project_id = os.environ.get("INFISICAL_PROJECT_ID")
    if project_id:
        cmd.extend(["--projectId", project_id])
    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    except FileNotFoundError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _ensure_submission_columns(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT schema FROM _collections WHERE name = 'publisher_submissions'")
    row = cursor.fetchone()
    if row is None:
        raise SubmissionExecutorError("publisher_submissions collection is missing; run publisher_schema.py first")
    columns = _table_columns(cursor, "publisher_submissions")
    for name in ("sub", "submission_id", "ts"):
        if name not in columns:
            cursor.execute(f"ALTER TABLE publisher_submissions ADD COLUMN {name} TEXT DEFAULT '' NOT NULL")
    _append_collection_fields(
        cursor,
        "publisher_submissions",
        [
            {"system": False, "id": "f_sub", "name": "sub", "type": "text", "required": False, "options": {}},
            {"system": False, "id": "f_submission_id", "name": "submission_id", "type": "text", "required": False, "options": {}},
            {"system": False, "id": "f_ts", "name": "ts", "type": "text", "required": False, "options": {}},
        ],
    )


def _ensure_verification_queue(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM _collections WHERE name = 'publisher_verification_queue'")
    if cursor.fetchone() is None:
        schema = [
            {"system": False, "id": "f_platform", "name": "platform", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_post_id", "name": "post_id", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_sub", "name": "sub", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_subreddit", "name": "subreddit", "type": "text", "required": False, "options": {}},
            {"system": False, "id": "f_submission_id", "name": "submission_id", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_permalink", "name": "permalink", "type": "text", "required": False, "options": {}},
            {"system": False, "id": "f_check_label", "name": "check_label", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_due_at", "name": "due_at", "type": "text", "required": True, "options": {}},
            {"system": False, "id": "f_status", "name": "status", "type": "text", "required": True, "options": {}},
        ]
        now = "2026-08-02 20:00:00.000Z"
        cursor.execute(
            "INSERT INTO _collections (id, name, type, system, schema, listRule, viewRule, createRule, updateRule, deleteRule, options, created, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_pb_id("pvq"), "publisher_verification_queue", "base", 0, json.dumps(schema), "", "", "", "", "", "{}", now, now),
        )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS publisher_verification_queue (
            id TEXT PRIMARY KEY NOT NULL,
            created TEXT DEFAULT '' NOT NULL,
            updated TEXT DEFAULT '' NOT NULL,
            platform TEXT DEFAULT '' NOT NULL,
            post_id TEXT DEFAULT '' NOT NULL,
            sub TEXT DEFAULT '' NOT NULL,
            subreddit TEXT DEFAULT '' NOT NULL,
            submission_id TEXT DEFAULT '' NOT NULL,
            permalink TEXT DEFAULT '' NOT NULL,
            check_label TEXT DEFAULT '' NOT NULL,
            due_at TEXT DEFAULT '' NOT NULL,
            status TEXT DEFAULT '' NOT NULL
        )
        """
    )


def _append_collection_fields(cursor: sqlite3.Cursor, collection: str, fields: list[dict[str, Any]]) -> None:
    cursor.execute("SELECT schema FROM _collections WHERE name = ?", (collection,))
    row = cursor.fetchone()
    if row is None:
        return
    schema = json.loads(row[0] or "[]")
    existing = {field.get("name") for field in schema}
    changed = False
    for field in fields:
        if field["name"] not in existing:
            schema.append(field)
            changed = True
    if changed:
        cursor.execute("UPDATE _collections SET schema = ? WHERE name = ?", (json.dumps(schema), collection))


def _table_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def _pb_id(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return (prefix + "".join(random.choice(alphabet) for _ in range(15)))[:15]


def main() -> int:
    parser = argparse.ArgumentParser(description="FLOT-110 submission executor")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Select and compose, but do not submit/write/alert")
    args = parser.parse_args()
    try:
        result = run_once(manifest_path=args.manifest, dry_run=args.dry_run)
    except (ManifestValidationError, RedditCredentialError, SubmissionExecutorError) as exc:
        print(f"submission executor failed: {exc}")
        return 1
    if result is None:
        print("submission executor: no eligible pending post")
        return 0
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
