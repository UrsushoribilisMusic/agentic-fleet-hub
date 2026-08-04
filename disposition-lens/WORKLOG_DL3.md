# DL-3 Worklog — Lexicon disposition classifier + entropy normalisation

**Ticket:** f9wnnhvihgtkzfo
**Branch:** task/f9wnnhvihgtkzfo

## Plan

1. `disposition.py` — new file
   - `LEXICON` dict: 6 dispositions × keyword sets (concern/reluctant/uncertain/warm/confident/curious)
   - `classify_disposition(tokens) -> str`: weighted-vote over J-space tokens; falls back to "idle"

2. `jlens.py` updates
   - `compute_raw_entropy(logits_np) -> float`: raw entropy in nats (pure numpy, no normalisation)
   - `build_entropy_calibration(model, tokenizer) -> Dict{"min","max"}`: run CALIB_PROMPTS through model, collect raw entropies
   - `load_or_build_entropy_calibration(model, tokenizer) -> Dict`: cache to `entropy_stats.json`
   - `normalise_entropy(raw, stats) -> float`: min-max scale to 0..1

3. `server.py` updates
   - Import `classify_disposition` from `disposition`
   - Import `load_or_build_entropy_calibration`, `normalise_entropy` from `jlens`
   - Add `entropy_stats: Optional[Dict]` global
   - `load_model()` also calls `load_or_build_entropy_calibration`
   - `compute_step_entropy(logits, entropy_stats=None)`: new optional param;
     with stats → min-max; without → log(vocab_size) fallback (preserves test compat)
   - `/infer` passes `entropy_stats` and calls `classify_disposition` on concept_tokens
   - Health endpoint exposes `entropy_calibrated` bool

4. `test_server.py` updates
   - Existing entropy tests pass unchanged (no entropy_stats arg → log-vocab fallback)
   - Add `TestClassifyDisposition` — 7 disposition cases + idle fallback + multi-token scoring
   - Add `TestNormaliseEntropy` — boundary cases

5. `.gitignore` — add `entropy_stats.json`

## Key decisions

- **entropy_stats optional param**: backward-compat with existing tests; production path always
  passes calibrated stats; offline/no-model path uses log(vocab_size) automatically.
- **classify_disposition prefix match**: `token.startswith(keyword)` catches BPE fragments like
  "certainly" → confident. Single disposition per token (first match wins; break).
- **entropy calibration cache**: `entropy_stats.json` alongside `jlens_cache.npy`. Both gitignored.
  Both rebuilt on server startup if absent.
- **disposition=idle when J-lens unavailable**: jlens_matrix=None path in /infer remains safe.

## Status

- [ ] WORKLOG_DL3.md committed
- [ ] disposition.py created
- [ ] jlens.py updated
- [ ] server.py updated
- [ ] test_server.py updated
- [ ] .gitignore updated
- [ ] Tests pass
- [ ] Committed and pushed
