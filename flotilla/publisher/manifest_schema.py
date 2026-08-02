"""Versioned manifest schema and validation for Flotilla publisher.

FLOT-108 owns the canonical on-disk contract at:
    ~/flotilla/publisher/manifest.json

The normalizer accepts operator-supplied post/subreddit lists, fills safe
defaults, and then validates the result. It deliberately fails closed on
subreddit pre-flight fields because missing flair/policy data can make Reddit
submissions look successful while they are filtered.
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0.0"
DEFAULT_MANIFEST_PATH = Path.home() / "flotilla/publisher/manifest.json"

POST_STATUSES = frozenset({"pending", "posted", "bounced", "exhausted", "live"})
ATTEMPT_OUTCOMES = frozenset({"submitted", "live", "bounced", "stalled", "failed"})
TRACTION_TIERS = frozenset({"A", "B", "C"})
BOT_POLICIES = frozenset({"allowed", "mod_approval", "banned"})
SUBREDDIT_NAME_RE = re.compile(r"^r/[A-Za-z0-9_][A-Za-z0-9_]{1,20}$")
POST_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ManifestValidationError(ValueError):
    """Raised when a publisher manifest cannot be accepted."""


def normalize_manifest(
    posts: list[dict[str, Any]],
    subreddits: list[dict[str, Any]],
    *,
    version: str = SCHEMA_VERSION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return a canonical manifest from operator-supplied lists."""

    manifest = {
        "schema_version": version,
        "generated_at": generated_at or _utc_now(),
        "posts": [_normalize_post(post) for post in posts],
        "subreddits": [_normalize_subreddit(subreddit) for subreddit in subreddits],
    }
    validate_manifest(manifest)
    return manifest


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def write_manifest(manifest: dict[str, Any], path: Path = DEFAULT_MANIFEST_PATH) -> None:
    validate_manifest(manifest)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n")


def validate_manifest(manifest: dict[str, Any]) -> None:
    errors: list[str] = []

    version = manifest.get("schema_version") or manifest.get("_version")
    if not _non_empty_string(version):
        errors.append("schema_version must be a non-empty string")

    posts = manifest.get("posts")
    subreddits = manifest.get("subreddits")
    if not isinstance(posts, list) or not posts:
        errors.append("posts must be a non-empty list")
        posts = []
    if not isinstance(subreddits, list) or not subreddits:
        errors.append("subreddits must be a non-empty list")
        subreddits = []

    subreddit_names = _validate_subreddits(subreddits, errors)
    _validate_posts(posts, subreddit_names, errors)

    if errors:
        raise ManifestValidationError("\n".join(errors))


def validate_file(path: Path = DEFAULT_MANIFEST_PATH) -> None:
    validate_manifest(load_manifest(path))


def _normalize_post(post: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(post)
    normalized["id"] = str(normalized.get("id", "")).strip()
    normalized["angle"] = str(normalized.get("angle", "")).strip()
    normalized["body_seed"] = str(normalized.get("body_seed", "")).strip()
    normalized["artwork"] = normalized.get("artwork")
    normalized["link"] = normalized.get("link")
    normalized["primary_sub"] = _normalize_sub_name(normalized.get("primary_sub"))
    normalized["fallback_subs"] = [
        _normalize_sub_name(value) for value in normalized.get("fallback_subs", [])
    ]
    normalized["min_gap_hours"] = int(normalized.get("min_gap_hours", 48))
    normalized["status"] = normalized.get("status") or "pending"
    normalized["attempts"] = list(normalized.get("attempts") or [])
    normalized["x_variant"] = _normalize_x_variant(normalized.get("x_variant"))
    return normalized


def _normalize_x_variant(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    hook = value.get("hook")
    reply_text = value.get("reply_text")
    return {
        "hook": str(hook).strip() if hook is not None else None,
        "reply_text": str(reply_text).strip() if reply_text is not None else None,
    }


def _normalize_subreddit(subreddit: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(subreddit)
    normalized["name"] = _normalize_sub_name(normalized.get("name"))
    normalized["traction_tier"] = normalized.get("traction_tier") or "C"
    for field in ("allows_link_posts", "allows_image_posts", "requires_flair"):
        normalized[field] = bool(normalized.get(field, False))
    normalized["flair_id"] = _normalize_flair_id(
        normalized.get("flair_id"), requires_flair=normalized["requires_flair"]
    )
    normalized["min_account_age_days"] = int(normalized.get("min_account_age_days", 0))
    normalized["min_karma"] = int(normalized.get("min_karma", 0))
    normalized["last_posted_ts"] = normalized.get("last_posted_ts")
    normalized["cooldown_hours"] = int(normalized.get("cooldown_hours", 168))
    normalized["bot_policy"] = normalized.get("bot_policy") or "mod_approval"
    return normalized


def _validate_posts(
    posts: list[Any], subreddit_names: set[str], errors: list[str]
) -> None:
    seen_post_ids: set[str] = set()
    for index, post in enumerate(posts):
        prefix = f"posts[{index}]"
        if not isinstance(post, dict):
            errors.append(f"{prefix} must be an object")
            continue

        post_id = post.get("id")
        if not _non_empty_string(post_id) or not POST_ID_RE.match(post_id):
            errors.append(f"{prefix}.id must be a lowercase slug")
        elif post_id in seen_post_ids:
            errors.append(f"{prefix}.id duplicates {post_id}")
        seen_post_ids.add(str(post_id))

        _require_string(post, "angle", prefix, errors)
        _require_string(post, "body_seed", prefix, errors)
        _optional_string_or_null(post, "artwork", prefix, errors)
        _validate_url_or_null(post.get("link"), f"{prefix}.link", errors)

        primary = post.get("primary_sub")
        if primary not in subreddit_names:
            errors.append(f"{prefix}.primary_sub references unknown subreddit {primary!r}")

        fallback_subs = post.get("fallback_subs")
        if not isinstance(fallback_subs, list):
            errors.append(f"{prefix}.fallback_subs must be a list")
        else:
            for fallback_index, sub_name in enumerate(fallback_subs):
                if sub_name not in subreddit_names:
                    errors.append(
                        f"{prefix}.fallback_subs[{fallback_index}] "
                        f"references unknown subreddit {sub_name!r}"
                    )

        _require_non_negative_int(post, "min_gap_hours", prefix, errors, minimum=1)
        if post.get("status") not in POST_STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(POST_STATUSES)}")
        _validate_attempts(post.get("attempts"), prefix, errors)
        _validate_x_variant(post.get("x_variant"), f"{prefix}.x_variant", errors)


def _validate_subreddits(subreddits: list[Any], errors: list[str]) -> set[str]:
    names: set[str] = set()
    for index, subreddit in enumerate(subreddits):
        prefix = f"subreddits[{index}]"
        if not isinstance(subreddit, dict):
            errors.append(f"{prefix} must be an object")
            continue

        name = subreddit.get("name")
        if not _non_empty_string(name) or not SUBREDDIT_NAME_RE.match(name):
            errors.append(f"{prefix}.name must look like r/Subreddit")
        elif name in names:
            errors.append(f"{prefix}.name duplicates {name}")
        names.add(str(name))

        if subreddit.get("traction_tier") not in TRACTION_TIERS:
            errors.append(f"{prefix}.traction_tier must be one of {sorted(TRACTION_TIERS)}")
        for field in ("allows_link_posts", "allows_image_posts", "requires_flair"):
            if not isinstance(subreddit.get(field), bool):
                errors.append(f"{prefix}.{field} must be a boolean")

        flair_id = subreddit.get("flair_id")
        if not _non_empty_string(flair_id):
            errors.append(f"{prefix}.flair_id must be non-null after pre-flight")
        if subreddit.get("requires_flair") is True and flair_id == "not_required":
            errors.append(f"{prefix}.flair_id cannot be not_required when flair is required")

        _require_non_negative_int(
            subreddit, "min_account_age_days", prefix, errors, minimum=0
        )
        _require_non_negative_int(subreddit, "min_karma", prefix, errors, minimum=0)
        _validate_timestamp_or_null(subreddit.get("last_posted_ts"), f"{prefix}.last_posted_ts", errors)
        _require_non_negative_int(subreddit, "cooldown_hours", prefix, errors, minimum=1)
        if subreddit.get("bot_policy") not in BOT_POLICIES:
            errors.append(f"{prefix}.bot_policy must be one of {sorted(BOT_POLICIES)}")
    return names


def _validate_attempts(attempts: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(attempts, list):
        errors.append(f"{prefix}.attempts must be a list")
        return
    for index, attempt in enumerate(attempts):
        attempt_prefix = f"{prefix}.attempts[{index}]"
        if not isinstance(attempt, dict):
            errors.append(f"{attempt_prefix} must be an object")
            continue
        _require_string(attempt, "sub", attempt_prefix, errors)
        _validate_timestamp_or_null(attempt.get("ts"), f"{attempt_prefix}.ts", errors, allow_null=False)
        _require_string(attempt, "submission_id", attempt_prefix, errors)
        if attempt.get("outcome") not in ATTEMPT_OUTCOMES:
            errors.append(
                f"{attempt_prefix}.outcome must be one of {sorted(ATTEMPT_OUTCOMES)}"
            )


def _validate_x_variant(value: Any, prefix: str, errors: list[str]) -> None:
    """x_variant is optional (null = not yet drafted). When present, validate fields."""
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be an object or null")
        return
    hook = value.get("hook")
    if hook is not None and not _non_empty_string(hook):
        errors.append(f"{prefix}.hook must be a non-empty string or null")
    if hook is not None and isinstance(hook, str) and len(hook) > 280:
        errors.append(f"{prefix}.hook exceeds 280 characters")
    _validate_url_or_null(value.get("reply_text"), f"{prefix}.reply_text", errors)


def _require_string(
    obj: dict[str, Any], field: str, prefix: str, errors: list[str]
) -> None:
    if not _non_empty_string(obj.get(field)):
        errors.append(f"{prefix}.{field} must be a non-empty string")


def _optional_string_or_null(
    obj: dict[str, Any], field: str, prefix: str, errors: list[str]
) -> None:
    value = obj.get(field)
    if value is not None and not _non_empty_string(value):
        errors.append(f"{prefix}.{field} must be a non-empty string or null")


def _require_non_negative_int(
    obj: dict[str, Any], field: str, prefix: str, errors: list[str], *, minimum: int
) -> None:
    value = obj.get(field)
    if not isinstance(value, int) or value < minimum:
        errors.append(f"{prefix}.{field} must be an integer >= {minimum}")


def _validate_url_or_null(value: Any, field: str, errors: list[str]) -> None:
    if value is None:
        return
    if not _non_empty_string(value):
        errors.append(f"{field} must be a URL string or null")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"{field} must be an http(s) URL or null")


def _validate_timestamp_or_null(
    value: Any, field: str, errors: list[str], *, allow_null: bool = True
) -> None:
    if value is None:
        if not allow_null:
            errors.append(f"{field} must be an ISO-8601 timestamp")
        return
    if not _non_empty_string(value):
        errors.append(f"{field} must be an ISO-8601 timestamp or null")
        return
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 timestamp or null")


def _normalize_sub_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    return text if text.startswith("r/") else f"r/{text}"


def _normalize_flair_id(value: Any, *, requires_flair: bool) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return "" if requires_flair else "not_required"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Flotilla publisher manifest")
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to manifest.json",
    )
    args = parser.parse_args()
    try:
        validate_file(args.manifest)
    except ManifestValidationError as exc:
        print(f"manifest invalid: {exc}")
        return 1
    print(f"manifest valid: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
