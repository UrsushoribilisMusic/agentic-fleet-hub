"""
J-lens: averaged Jacobian from mid layer to vocab space.

Build: for each calibration token at position p (skip first N_SKIP high-norm tokens),
computes the closed-form Jacobian of logit_lens(h_mid) = lm_head(layer_norm(h_mid)) wrt h_mid:

    J_p = lm_head.weight * diag(ln_weight / std(h_mid_p))

Averages over all valid calibration tokens -> J_avg (vocab_size x hidden_size).
Caches to disk so subsequent startups are instant.

Inference: project h_mid (at final prompt position) through J_avg -> softmax -> top-k
concept tokens with weights normalised 0..1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import torch

JLENS_CACHE_PATH = Path(__file__).parent / "jlens_cache.npy"

N_CALIB_PROMPTS = 25
N_SKIP = 4      # skip first high-norm tokens per prompt
TOP_K = 5       # concept tokens returned per inference call

CALIB_PROMPTS: List[str] = [
    "The quick brown fox jumps over the lazy dog.",
    "Machine learning models learn patterns from data.",
    "What is the capital of France?",
    "The robot arm needs calibration before use.",
    "Artificial intelligence is transforming healthcare.",
    "How does neural network training work?",
    "The weather today is sunny with mild temperatures.",
    "Please explain quantum computing in simple terms.",
    "The system encountered an unexpected error.",
    "What are the main components of a large language model?",
    "I need help understanding this technical document.",
    "The team completed the project ahead of schedule.",
    "Can you summarize the key findings from this report?",
    "The database contains millions of records.",
    "How do transformers handle long-range dependencies?",
    "The sensor readings indicate elevated temperature.",
    "What is the best approach for fine-tuning a model?",
    "The installation requires administrator privileges.",
    "Please verify all connections are properly secured.",
    "How can we improve the efficiency of this algorithm?",
    "The model shows strong performance on benchmark tasks.",
    "What are the safety considerations for this procedure?",
    "The configuration file needs updated parameters.",
    "Can you explain how attention mechanisms work?",
    "The deployment requires careful planning and testing.",
]

assert len(CALIB_PROMPTS) == N_CALIB_PROMPTS


def get_mid_layer_idx(model) -> int:
    return model.config.num_hidden_layers // 2


def build_jlens(model, tokenizer, mid_layer_idx: int) -> np.ndarray:
    """
    Compute averaged Jacobian lens (vocab_size x hidden_size) from mid layer to vocab space.

    Uses the logit-lens Jacobian: J_p = lm_head.weight * (ln_weight / std(h_mid_p)).
    Averages across all valid calibration token positions.
    """
    model.eval()
    device = next(model.parameters()).device

    ln_weight = model.model.norm.weight.float().cpu().detach().numpy()   # (hidden_size,)
    lm_weight = model.lm_head.weight.float().cpu().detach().numpy()     # (vocab_size, hidden_size)

    # Accumulate the per-token scale vector (hidden_size,) — much cheaper than full matrix sum
    scale_accum = np.zeros(ln_weight.shape, dtype=np.float64)
    count = 0

    print(f"  Building J-lens: mid_layer={mid_layer_idx}, {N_CALIB_PROMPTS} prompts, skip first {N_SKIP} tokens")

    for i, prompt in enumerate(CALIB_PROMPTS):
        enc = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=128,
            truncation=True,
        )
        enc = {k: v.to(device) for k, v in enc.items()}
        seq_len = enc["input_ids"].shape[1]

        if seq_len <= N_SKIP:
            continue

        with torch.no_grad():
            out = model(**enc, output_hidden_states=True)
            # hidden_states[mid_layer_idx]: (1, seq_len, hidden_size)
            h_mids = out.hidden_states[mid_layer_idx].float()

        for pos in range(N_SKIP, seq_len):
            h = h_mids[0, pos].cpu().numpy()
            sigma = float(np.std(h)) + 1e-8
            scale_accum += ln_weight / sigma
            count += 1

        if (i + 1) % 5 == 0:
            print(f"  [{i + 1}/{N_CALIB_PROMPTS}] tokens collected: {count}")

    if count == 0:
        print("  Warning: no calibration tokens — falling back to raw lm_head.weight")
        return lm_weight.astype(np.float32)

    avg_scale = scale_accum / count                                   # (hidden_size,)
    J_avg = (lm_weight * avg_scale[np.newaxis, :]).astype(np.float32)  # (vocab_size, hidden_size)
    print(f"  J-lens built from {count} tokens. Shape: {J_avg.shape}")
    return J_avg


def load_or_build_jlens(model, tokenizer, mid_layer_idx: int) -> np.ndarray:
    """Load J-lens from cache; build and cache if absent."""
    if JLENS_CACHE_PATH.exists():
        J = np.load(str(JLENS_CACHE_PATH))
        print(f"J-lens loaded from cache {JLENS_CACHE_PATH} (shape: {J.shape})")
        return J

    print(f"J-lens cache not found — building (this runs once)...")
    J = build_jlens(model, tokenizer, mid_layer_idx)
    np.save(str(JLENS_CACHE_PATH), J)
    print(f"J-lens cached to {JLENS_CACHE_PATH}")
    return J


def project_jlens(
    J: np.ndarray,
    h_mid: np.ndarray,
    tokenizer,
    top_k: int = TOP_K,
) -> List[Dict]:
    """
    Project mid-layer activation through J-lens -> top-k concept tokens.

    Steps:
      z = J @ h_mid                (vocab_size,)
      probs = softmax(z)
      top_k_indices = argsort(probs)[-top_k:]
      weights normalised to 0..1 within the top-k set

    Returns list of {"t": token_str, "w": float} sorted by weight descending.
    """
    h = h_mid.astype(np.float32)
    z = J @ h                          # (vocab_size,) raw logit-lens scores
    z -= z.max()                       # numerical stability
    exp_z = np.exp(z)
    probs = exp_z / exp_z.sum()

    top_indices = np.argsort(probs)[-top_k:][::-1]   # descending
    top_probs = probs[top_indices]

    w_min, w_max = top_probs.min(), top_probs.max()
    w_range = w_max - w_min

    tokens: List[Dict] = []
    for idx, prob in zip(top_indices, top_probs):
        token_str = tokenizer.decode([int(idx)]).strip()
        if not token_str:
            continue
        # When all top-k probs are equal (or k=1), every token gets w=1.0
        w = float((prob - w_min) / w_range) if w_range > 1e-8 else 1.0
        tokens.append({"t": token_str, "w": round(w, 3)})

    return tokens
