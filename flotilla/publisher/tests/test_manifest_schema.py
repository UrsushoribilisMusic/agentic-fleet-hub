import pytest

from manifest_schema import ManifestValidationError, normalize_manifest, validate_manifest


def valid_posts():
    return [
        {
            "id": "apertus-m4-local-inference",
            "angle": "local inference on commodity Apple Silicon",
            "body_seed": "A concrete write-up of the Apertus 8B Mac Mini run.",
            "primary_sub": "r/LocalLLaMA",
            "fallback_subs": ["r/eutech"],
        }
    ]


def valid_subreddits():
    return [
        {
            "name": "r/LocalLLaMA",
            "traction_tier": "A",
            "allows_link_posts": True,
            "allows_image_posts": True,
            "requires_flair": True,
            "flair_id": "Discussion",
            "min_account_age_days": 0,
            "min_karma": 0,
            "last_posted_ts": None,
            "cooldown_hours": 168,
            "bot_policy": "mod_approval",
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
    ]


def test_normalize_manifest_fills_post_defaults():
    manifest = normalize_manifest(valid_posts(), valid_subreddits(), generated_at="2026-08-02T20:00:00Z")

    assert manifest["schema_version"] == "1.0.0"
    post = manifest["posts"][0]
    assert post["min_gap_hours"] == 48
    assert post["status"] == "pending"
    assert post["attempts"] == []


def test_validate_manifest_rejects_missing_flair_id():
    manifest = normalize_manifest(valid_posts(), valid_subreddits())
    manifest["subreddits"][0]["flair_id"] = None

    with pytest.raises(ManifestValidationError, match="flair_id must be non-null"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_required_flair_without_real_value():
    manifest = normalize_manifest(valid_posts(), valid_subreddits())
    manifest["subreddits"][0]["flair_id"] = "not_required"

    with pytest.raises(ManifestValidationError, match="cannot be not_required"):
        validate_manifest(manifest)


def test_validate_manifest_rejects_unknown_subreddit_reference():
    posts = valid_posts()
    posts[0]["fallback_subs"] = ["r/UnknownSub"]

    with pytest.raises(ManifestValidationError, match="references unknown subreddit"):
        normalize_manifest(posts, valid_subreddits())


def test_validate_manifest_rejects_bogus_bot_policy():
    subreddits = valid_subreddits()
    subreddits[0]["bot_policy"] = "shrug"

    with pytest.raises(ManifestValidationError, match="bot_policy"):
        normalize_manifest(valid_posts(), subreddits)
