"""
J-lens: averaged Jacobian from mid layer to vocab space.

Build: for each calibration token at position p (skip first N_SKIP high-norm tokens),
computes the closed-form Jacobian of logit_lens(h_mid) = lm_head(layer_norm(h_mid)) wrt h_mid:

    J_p = lm_head.weight * diag(ln_weight / std(h_mid_p))

Averages over all valid calibration tokens -> J_avg (vocab_size x hidden_size).
Caches to disk so subsequent startups are instant.

Inference: project h_mid (at final prompt position) through J_avg -> softmax -> top-k
concept tokens with weights normalised 0..1.

Entropy calibration: collect raw next-token entropies (nats) over CALIB_PROMPTS, record
min/max, and use them for min-max normalisation at inference time.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import torch

JLENS_CACHE_PATH = Path(__file__).parent / "jlens_cache.npy"
ENTROPY_STATS_CACHE_PATH = Path(__file__).parent / "entropy_stats.json"

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


def load_or_build_jlens(model, tokenizer, mid_layer_idx: int, cache_path: Optional[Path] = None) -> np.ndarray:
    """Load J-lens from cache; build and cache if absent."""
    path = cache_path or JLENS_CACHE_PATH
    if path.exists():
        J = np.load(str(path))
        print(f"J-lens loaded from cache {path} (shape: {J.shape})")
        return J

    print(f"J-lens cache not found — building (this runs once)...")
    J = build_jlens(model, tokenizer, mid_layer_idx)
    np.save(str(path), J)
    print(f"J-lens cached to {path}")
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


# ---------------------------------------------------------------------------
# Entropy calibration
# ---------------------------------------------------------------------------

def compute_raw_entropy(logits_np: np.ndarray) -> float:
    """
    Raw softmax entropy in nats for a single logit vector.
    NOT normalised — use normalise_entropy() for 0..1 scaling.
    """
    logits = logits_np.astype(np.float32)
    logits -= logits.max()  # numerical stability
    exp_l = np.exp(logits)
    probs = exp_l / (exp_l.sum() + 1e-9)
    entropy = -float(np.sum(probs * np.log(probs + 1e-9)))
    return max(0.0, entropy)


def build_entropy_calibration(model, tokenizer) -> Dict:
    """
    Collect raw next-token entropies over CALIB_PROMPTS.
    Returns {"min": float, "max": float} in nats.
    Falls back to theoretical bounds if the model produces no samples.
    """
    model.eval()
    device = next(model.parameters()).device
    entropies: List[float] = []

    print(f"  Building entropy calibration over {N_CALIB_PROMPTS} prompts...")
    for i, prompt in enumerate(CALIB_PROMPTS):
        enc = tokenizer(prompt, return_tensors="pt", max_length=128, truncation=True)
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            out = model(**enc)
        # out.logits: (1, seq_len, vocab_size)
        logits_all = out.logits[0].float().cpu().numpy()  # (seq_len, vocab_size)
        for pos in range(N_SKIP, logits_all.shape[0]):
            entropies.append(compute_raw_entropy(logits_all[pos]))
        if (i + 1) % 5 == 0:
            print(f"  [{i + 1}/{N_CALIB_PROMPTS}] entropy samples: {len(entropies)}")

    if not entropies:
        # Degenerate fallback: theoretical bounds for a 32K-vocab model
        vocab_size = model.config.vocab_size if hasattr(model.config, "vocab_size") else 32000
        return {"min": 0.0, "max": float(math.log(vocab_size))}

    stats = {"min": float(np.min(entropies)), "max": float(np.max(entropies))}
    print(f"  Entropy calibration: min={stats['min']:.4f}, max={stats['max']:.4f} nats ({len(entropies)} samples)")
    return stats


def load_or_build_entropy_calibration(model, tokenizer, cache_path: Optional[Path] = None) -> Dict:
    """Load entropy calibration stats from cache; build and cache if absent."""
    path = cache_path or ENTROPY_STATS_CACHE_PATH
    if path.exists():
        with open(path) as f:
            stats = json.load(f)
        print(f"Entropy calibration loaded from cache: min={stats['min']:.4f}, max={stats['max']:.4f}")
        return stats

    print("Entropy calibration cache not found — building (runs once)...")
    stats = build_entropy_calibration(model, tokenizer)
    with open(path, "w") as f:
        json.dump(stats, f)
    print(f"Entropy calibration cached to {path}")
    return stats


def normalise_entropy(raw_entropy: float, stats: Dict) -> float:
    """
    Min-max normalise a raw entropy value (nats) to 0..1 using calibration stats.

    Args:
        raw_entropy: raw entropy in nats from compute_raw_entropy()
        stats: {"min": float, "max": float} from build_entropy_calibration()

    Returns:
        float in [0.0, 1.0]
    """
    e_min = stats["min"]
    e_max = stats["max"]
    if e_max <= e_min + 1e-8:
        return 0.5  # degenerate: flat calibration distribution
    normed = (raw_entropy - e_min) / (e_max - e_min)
    return float(max(0.0, min(1.0, normed)))
