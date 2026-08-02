# FLOT-118 Worklog — X composer + link-in-reply pattern

Task: X (Twitter) composer that emits hook+reply pairs.

## Plan

Pattern: publish hook post (text+image, NO URL) → capture tweet id → reply-to-self with the link → log both ids.

Scope for this ticket (composer acceptance criteria):
1. `lint.py` — add `check_x_no_url` and `check_x_char_limit`
2. `x_composer.py` — new file with `compose_x()` (LLM drafts X hook, reply_text=post.link)
3. `manifest_schema.py` — add `x_variant` to post normalization/validation
4. `tests/test_x_composer.py` — unit tests proving acceptance criteria
5. `pyproject.toml` — add script entry `flotilla-x-composer`

## Key decisions

- X hook is ≤280 chars, no URL, first-person, image-ready.
- reply_text = post.link (just the URL, no LLM composition needed for the reply).
- Overlap check: X hook vs all Reddit drafts (prior_texts) < 40% (4-gram Jaccard).
- If post.link is None, reply_text is None; caller skips the reply step.
- composer is read-only on manifest; executor (future ticket) owns writes.
- check_x_no_url is a hard fail added to lint.py (reusable).
- cross-platform corpus: caller passes reddit_texts into compose_x().

## Order of execution

1. Extend lint.py (check_x_no_url, check_x_char_limit)
2. Write x_composer.py
3. Extend manifest_schema.py (x_variant field)
4. Write tests/test_x_composer.py
5. Add pyproject.toml entry
6. Run tests
7. Commit
