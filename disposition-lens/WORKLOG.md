# DL-2 Worklog — J-lens build + cache + /infer integration

**Ticket:** 8gmmprdsw89cxnj  
**Branch:** task/8gmmprdsw89cxnj

## Plan

1. Create `jlens.py` — builds/loads/projects the J-lens
   - `build_jlens()`: averaged Jacobian from mid layer to vocab space over 25 calibration prompts
   - `load_or_build_jlens()`: load from cache or build + cache
   - `project_jlens()`: project h_mid → top-k concept tokens with weights 0..1
2. Update `server.py` — integrate jlens on startup and in /infer
3. Update `test_server.py` — verify tokens[] is now populated in /infer response
4. Add `jlens_cache.npy` to `.gitignore`

## Key decisions

- **J-lens formula**: The Jacobian of the logit lens wrt h_mid is:
  `J_token = lm_head.weight * (ln_weight / std(h_mid))` (closed-form, no backward pass)
  Averaging over valid tokens (skip first 4 per prompt, use last to reduce redundancy):
  `J_avg = lm_head.weight * avg_scale` where `avg_scale = mean(ln_weight / std(h_mid))`
  
- **Why logit lens Jacobian**: Matches spec intent (logit-space projection from mid layer), avoids
  expensive backward passes through remaining transformer layers, and is the standard practical
  approach in J-space literature.

- **Mid layer index**: `model.config.num_hidden_layers // 2` — computed dynamically after model load.

- **Calibration**: 25 diverse short prompts, skip first 4 tokens per prompt (high-norm tokens,
  typically BOS/special tokens). Use positions 4..seq_len for the averaging.

- **Inference tap**: `outputs.hidden_states[0][mid_layer_idx][0, -1, :]` — the mid-layer hidden state
  at the last prompt position (before the first generated token). This is the "final position" the spec
  refers to.

- **Weight normalization**: min-max normalize within top-k set to 0..1.

- **Cache**: saved as `disposition-lens/jlens_cache.npy` (float32, ~256MB for typical 4B model).
  Gitignored. Rebuilt if absent on server startup.

## Status

- [x] WORKLOG.md committed
- [ ] jlens.py implemented
- [ ] server.py updated
- [ ] test_server.py updated
- [ ] .gitignore updated
- [ ] Committed and pushed
