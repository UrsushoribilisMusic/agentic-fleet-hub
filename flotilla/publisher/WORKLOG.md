# WORKLOG — FLOT-109: Post composer (per-sub drafts)

**Branch:** task/yzjynmupe10cqae  
**Agent:** clau  
**PB task:** yzjynmupe10cqae

## Plan

Build `~/flotilla/publisher/composer.py` (importable module + CLI) that generates
Reddit post drafts tuned per subreddit.

### Files to create
1. `lint.py` — lint primitives: em-dash check, marketing-word check, n-gram overlap
2. `composer.py` — main module: `compose(post_id, subs, manifest_path)` + CLI
3. `manifest.json` — schema placeholder (FLOT-108 will formalize; this gives composer something to run against)
4. `test_composer.py` — lint unit tests + acceptance smoke test

### Architecture decisions

**Caller contract:** FLOT-110 (executor) calls `compose(post_id, subs)` and gets back
`{sub: Draft}` dict. No manifest writes — executor owns state mutation.

**Per-sub conventions** (hardcoded in composer, not config):
- r/LocalLLaMA: model + quant specifics as title anchor
- r/Entrepreneur: story arc (what I tried / what happened)
- r/eutech: EU sovereignty / on-device / GDPR angle

**Cross-sub dedup:** after generating each sub's draft, add it to running
`prior_texts` so subsequent subs are checked against it. This is the primary
shadowban guard — prevents near-identical posts in the same run.

**Lint retries:** up to 3 attempts per sub. On failure, inject the failure list
into the next prompt so the model can self-correct.

**Model:** `claude-sonnet-5` via Anthropic API. Key fetched from Infisical via
`vault/agent-fetch.sh ANTHROPIC_API_KEY`.

**Acceptance criteria (from ticket):**
- For one post id + three subs: emits three materially different drafts
- Each passes lint: no em-dash, no marketing register, n-gram overlap < 40% vs prior posted text

## Commit log
- [x] WORKLOG.md
- [ ] lint.py
- [ ] composer.py
- [ ] manifest.json
- [ ] test_composer.py
