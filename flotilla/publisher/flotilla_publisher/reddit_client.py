"""Reddit OAuth client setup for unattended Flotilla publishing."""

from __future__ import annotations

import os
import random
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Deque, Dict, Mapping, Optional, Sequence, TypeVar

REDDIT_USER_AGENT = "macos:cc.flotilla.publisher:v1.0 (by /u/robotrossart)"
INFISICAL_DOMAIN = "https://eu.infisical.com"
INFISICAL_SECRET_PATH = "/flotilla/reddit"
INFISICAL_ENV = "dev"

_T = TypeVar("_T")


@dataclass(frozen=True)
class RedditCredentials:
    client_id: str
    client_secret: str
    username: str
    password: str


@dataclass(frozen=True)
class RedditClientBundle:
    authed: Any
    readonly: Any
    guard: "RedditRateLimitGuard"
    credentials: RedditCredentials


class RedditCredentialError(RuntimeError):
    """Raised when required Reddit credentials are missing or invalid."""


class RedditRateLimitGuard:
    """Shared Reddit request guard.

    Reddit allows roughly 60 OAuth requests per minute per client. PRAW handles
    many API-specific cooldowns internally, but the unattended scheduler needs a
    single outer guard so every downstream call behaves consistently.
    """

    def __init__(
        self,
        max_requests_per_minute: int = 60,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[float, float], float] = random.uniform,
    ) -> None:
        if max_requests_per_minute < 1:
            raise ValueError("max_requests_per_minute must be >= 1")
        self.max_requests_per_minute = max_requests_per_minute
        self._clock = clock
        self._sleep = sleep
        self._jitter = jitter
        self._timestamps: Deque[float] = deque()
        self._lock = Lock()

    def wait_for_slot(self) -> None:
        while True:
            wait_seconds = 0.0
            with self._lock:
                now = self._clock()
                while self._timestamps and now - self._timestamps[0] >= 60.0:
                    self._timestamps.popleft()
                if len(self._timestamps) < self.max_requests_per_minute:
                    self._timestamps.append(now)
                    return
                wait_seconds = 60.0 - (now - self._timestamps[0])
            self._sleep(max(wait_seconds, 0.1))

    def call(self, operation: Callable[[], _T], *, max_attempts: int = 6) -> _T:
        attempt = 0
        while True:
            self.wait_for_slot()
            try:
                return operation()
            except Exception as exc:
                if not _is_reddit_429(exc) or attempt >= max_attempts - 1:
                    raise
                headers = _headers_from_exception(exc)
                delay = _retry_delay_from_headers(headers)
                if delay is None:
                    delay = min(900.0, (2.0**attempt) + self._jitter(0.0, 1.0))
                self._sleep(delay)
                attempt += 1


def load_reddit_credentials_from_infisical(
    *,
    env: Optional[str] = None,
    path: Optional[str] = None,
    domain: Optional[str] = None,
    project_id: Optional[str] = None,
    secret_names: Optional[Mapping[str, str]] = None,
) -> RedditCredentials:
    env_name = env or os.environ.get("INFISICAL_ENV", INFISICAL_ENV)
    secret_path = path or os.environ.get("REDDIT_SECRET_PATH", INFISICAL_SECRET_PATH)
    infisical_domain = domain or os.environ.get("INFISICAL_DOMAIN", INFISICAL_DOMAIN)
    infisical_project_id = project_id or os.environ.get("INFISICAL_PROJECT_ID")
    names = {
        "client_id": "REDDIT_CLIENT_ID",
        "client_secret": "REDDIT_CLIENT_SECRET",
        "username": "REDDIT_USERNAME",
        "password": "REDDIT_PASSWORD",
    }
    if secret_names:
        names.update(secret_names)

    values = {
        field: _infisical_get(
            name,
            env=env_name,
            path=secret_path,
            domain=infisical_domain,
            project_id=infisical_project_id,
        )
        for field, name in names.items()
    }
    missing = [field for field, value in values.items() if not value]
    if missing:
        raise RedditCredentialError(f"Missing Reddit credential fields: {', '.join(missing)}")

    return RedditCredentials(**values)


def build_reddit_clients(
    credentials: RedditCredentials,
    *,
    request_guard: Optional[RedditRateLimitGuard] = None,
    ratelimit_seconds: int = 900,
) -> RedditClientBundle:
    praw = _import_praw()
    guard = request_guard or RedditRateLimitGuard()

    authed = praw.Reddit(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        username=credentials.username,
        password=credentials.password,
        user_agent=REDDIT_USER_AGENT,
        ratelimit_seconds=ratelimit_seconds,
        check_for_async=False,
    )
    readonly = praw.Reddit(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        user_agent=REDDIT_USER_AGENT,
        ratelimit_seconds=ratelimit_seconds,
        check_for_async=False,
    )
    readonly.read_only = True
    return RedditClientBundle(authed=authed, readonly=readonly, guard=guard, credentials=credentials)


def ensure_authenticated(bundle: RedditClientBundle) -> str:
    me = bundle.guard.call(lambda: bundle.authed.user.me())
    if me is None:
        raise RuntimeError("Reddit authentication failed: user.me() returned None")
    username = str(me)
    expected = bundle.credentials.username.lower()
    if username.lower() != expected:
        raise RuntimeError(f"Authenticated as u/{username}, expected u/{bundle.credentials.username}")
    return username


def submit_profile_test_post(bundle: RedditClientBundle, *, title: str, body: str) -> Any:
    ensure_authenticated(bundle)
    profile_subreddit = f"u_{bundle.credentials.username}"
    return bundle.guard.call(lambda: bundle.authed.subreddit(profile_subreddit).submit(title=title, selftext=body))


def delete_submission(bundle: RedditClientBundle, submission: Any) -> None:
    bundle.guard.call(lambda: submission.delete())


def _infisical_get(
    secret_name: str,
    *,
    env: str,
    path: str,
    domain: str,
    project_id: Optional[str],
) -> str:
    cmd = [
        "infisical",
        "secrets",
        "get",
        secret_name,
        "--domain",
        domain,
        "--env",
        env,
        "--path",
        path,
        "--plain",
        "--silent",
    ]
    if project_id:
        cmd.extend(["--projectId", project_id])
    try:
        result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise RedditCredentialError("Infisical CLI is not installed or not on PATH") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RedditCredentialError(f"Failed to fetch {secret_name} from Infisical path {path}: {detail}")
    return result.stdout.strip()


def _import_praw() -> Any:
    try:
        import praw  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PRAW is required. Install with: python -m pip install -e .") from exc
    return praw


def _is_reddit_429(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    response = getattr(exc, "response", None)
    if getattr(response, "status_code", None) == 429:
        return True
    name = exc.__class__.__name__.lower()
    return "toomanyrequests" in name or "ratelimit" in name and status == 429


def _headers_from_exception(exc: Exception) -> Dict[str, str]:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None) or {}
    return {str(k).lower(): str(v) for k, v in dict(headers).items()}


def _retry_delay_from_headers(headers: Mapping[str, str]) -> Optional[float]:
    retry_after = _float_header(headers, "retry-after")
    if retry_after is not None:
        return max(retry_after, 0.0)

    remaining = _float_header(headers, "x-ratelimit-remaining")
    reset = _float_header(headers, "x-ratelimit-reset")
    if remaining is not None and remaining <= 0 and reset is not None:
        return max(reset, 1.0)
    return None


def _float_header(headers: Mapping[str, str], name: str) -> Optional[float]:
    value = headers.get(name)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
