# DL-9 Worklog — Disposition signal quality

**Ticket:** xfyt0c43d29d49i  
**Branch:** task/xfyt0c43d29d49i  
**Owner:** clau  

## Scope

Three improvements to the LIVE disposition signal:

### (a) Later-layer tap: num_layers//2 → ~3/4 depth
`get_mid_layer_idx()` currently returns num_layers//2 (~layer 16 for a 32-layer model).
Spec says disposition-laden concepts sharpen at ~3/4 depth (~layer 24).
- Change: `int(round(n * 3 / 4))` formula in `get_tap_layer_idx()` (rename to be explicit)
- Cache filename suffix changes to `_3q4` to force rebuild at new layer

### (b) Seed-vector matching replaces exact-keyword lexicon
Instead of prefix-matching concept tokens against a hard-coded keyword set:
1. For each disposition, define seed phrases (e.g. "I cannot do this" → reluctant)
2. Run each seed phrase through the model at tap_layer, project through J → vocab-space vector
3. L2-normalize and average per-disposition → seed_vectors dict
4. At inference: compute `z_query = J @ h_mid` (raw logit-space vector), cosine-sim to each seed vector
5. Highest similarity above threshold wins the disposition

Advantages: handles BPE fragmentation naturally, works even when exact keywords never appear in top-k.

### (c) STRETCH: True multi-layer autodiff Jacobian at inference
Current closed-form logit-lens Jacobian: `z = lm_head.weight * (norm_weight / std(h)) @ h`
This skips all remaining transformer layers (treats them as identity).

Real JVP: `z = J_real @ h` computed via `torch.autograd.functional.jvp(remaining_layers_plus_head, h, h)`.
- One forward pass + one JVP through the remaining layers (~8 layers for 3/4 tap on a 32L model)
- Activated by env var `USE_JVP=1` at server startup
- Used for top-k concept token display only; seed-vector scoring still uses the closed-form path (seed vectors are built in closed-form space)

## File changes

- `jlens.py`: `get_tap_layer_idx()`, `compute_jlens_raw()`, `SEED_PHRASES`, `build_seed_vectors()`,
  `load_or_build_seed_vectors()`, `score_seed_vectors()`, `project_jlens_jvp()` [stretch]
- `disposition.py`: `classify_by_seed_vectors()`, `resolve_disposition_seed()`
- `server.py`: cache path updates, seed_vectors in runtime, new infer() path

## Status

- [x] WORKLOG committed
- [ ] jlens.py updated
- [ ] disposition.py updated
- [ ] server.py updated
- [ ] Committed and pushed
