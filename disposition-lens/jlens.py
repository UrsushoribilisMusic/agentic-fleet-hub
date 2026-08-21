"""
J-lens: averaged Jacobian from tap layer to vocab space.

Build: for each calibration token at position p (skip first N_SKIP high-norm tokens),
computes the closed-form Jacobian of logit_lens(h_tap) = lm_head(layer_norm(h_tap)) wrt h_tap:

    J_p = lm_head.weight * diag(ln_weight / std(h_tap_p))

Averages over all valid calibration tokens -> J_avg (vocab_size x hidden_size).
Caches to disk so subsequent startups are instant.

Inference: project h_tap (at final prompt position) through J_avg -> softmax -> top-k
concept tokens with weights normalised 0..1.

Seed-vector matching (DL-9b): for each disposition, run seed phrases through the model at the
tap layer, project through J, L2-normalise and average -> seed vector per disposition.
At inference, score query z = J @ h_tap against each seed vector via cosine similarity.
This replaces the exact-keyword lexicon, surviving BPE fragmentation naturally.

Entropy calibration: collect raw next-token entropies (nats) over CALIB_PROMPTS, record
min/max, and use them for min-max normalisation at inference time.

STRETCH (DL-9c, optional via USE_JVP=1): project_jlens_jvp() computes z via a true
autodiff JVP through the remaining transformer layers instead of the closed-form
logit-lens formula, so the Jacobian accounts for all nonlinear intermediate layers.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch

JLENS_CACHE_PATH = Path(__file__).parent / "jlens_cache.npy"
ENTROPY_STATS_CACHE_PATH = Path(__file__).parent / "entropy_stats.json"

N_CALIB_PROMPTS = 25
N_SKIP = 4      # skip first high-norm tokens per prompt
TOP_K = 5       # concept tokens returned per inference call

# ---------------------------------------------------------------------------
# Seed phrases for disposition seed-vector matching (DL-9b)
# Each phrase should strongly evoke one disposition at the tap layer.
# Keep them short (< 12 tokens) so the final-position hidden state is clean.
# ---------------------------------------------------------------------------
SEED_PHRASES: Dict[str, List[str]] = {
    "confident":  [
        "I can confirm that",
        "The answer is definitely",
        "Certainly, yes.",
        "Absolutely correct.",
        "The correct answer is",
    ],
    "uncertain":  [
        "I'm not entirely sure, but",
        "It's possible that",
        "Maybe, though I'm unsure.",
        "Perhaps, but it depends.",
        "I'm uncertain about this.",
    ],
    "curious":    [
        "How does this actually work?",
        "Why would that be the case?",
        "What is the underlying reason?",
        "I wonder why this happens.",
        "Interesting — can you explain?",
    ],
    "concern":    [
        "Warning: this is dangerous.",
        "Be careful, there is a serious risk.",
        "Danger — do not proceed.",
        "This could cause harm.",
        "Alert: safety hazard present.",
    ],
    "reluctant":  [
        "I cannot do that.",
        "I'm sorry, I'm unable to help.",
        "I must decline this request.",
        "Unfortunately I cannot assist.",
        "I'm not able to comply with this.",
    ],
    "warm":       [
        "That's wonderful, I'm so glad!",
        "Great question, happy to help.",
        "Excellent — let me explain.",
        "I'm delighted to assist you.",
        "What a fantastic opportunity!",
    ],
    # Tier-1: detects evasive/hedging wording — NOT genuine scheming (small models don't scheme).
    # Tier-2 real deception detection (behavioural/intent-level) is a research roadmap item.
    "mischief":   [
        "I'll find a way around this.",
        "They won't notice if I",
        "Technically I didn't say that.",
        "Let me rephrase so it slips through.",
        "There's a loophole here I can use.",
    ],
}

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


def _decoder_model(model):
    """Return the text decoder module for plain CausalLMs and Mistral3 wrappers."""
    candidate = getattr(model, "model", model)
    if hasattr(candidate, "norm"):
        return candidate
    nested = getattr(candidate, "language_model", None)
    if nested is not None and hasattr(nested, "norm"):
        return nested
    return candidate


def _num_hidden_layers(model) -> int:
    """Resolve the number of hidden layers for any CausalLM / Mistral3 wrapper."""
    config = getattr(model, "config", None)
    num_layers = getattr(config, "num_hidden_layers", None)
    text_config = getattr(config, "text_config", None)
    if num_layers is None and text_config is not None:
        num_layers = getattr(text_config, "num_hidden_layers", None)
    if num_layers is None:
        decoder = _decoder_model(model)
        layers = getattr(decoder, "layers", None)
        if layers is not None:
            num_layers = len(layers)
    if num_layers is None:
        raise ValueError("Cannot determine number of hidden layers for J-lens tap")
    return int(num_layers)


def get_tap_layer_idx(model) -> int:
    """
    Return the tap-layer index at ~3/4 depth (DL-9a).

    Disposition-laden concepts sharpen at ~3/4 depth rather than the midpoint:
      - For a 32-layer model: was 16 (//2), now 24 (round(32 * 0.75))
      - For a 28-layer model: 21
    Cached J-lens matrices built at the old index are NOT compatible — rename
    cache files (e.g. add _3q4 suffix) to force a rebuild.
    """
    n = _num_hidden_layers(model)
    return int(round(n * 3 / 4))


def get_mid_layer_idx(model) -> int:
    """Backward-compat alias — now returns 3/4-depth tap (same as get_tap_layer_idx)."""
    return get_tap_layer_idx(model)


def build_jlens(model, tokenizer, mid_layer_idx: int) -> np.ndarray:
    """
    Compute averaged Jacobian lens (vocab_size x hidden_size) from mid layer to vocab space.

    Uses the logit-lens Jacobian: J_p = lm_head.weight * (ln_weight / std(h_mid_p)).
    Averages across all valid calibration token positions.
    """
    model.eval()
    device = next(model.parameters()).device

    decoder = _decoder_model(model)
    ln_weight = decoder.norm.weight.float().cpu().detach().numpy()      # (hidden_size,)
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


def compute_jlens_raw(J: np.ndarray, h_mid: np.ndarray) -> np.ndarray:
    """
    Return the raw logit-space projection z = J @ h_mid (vocab_size,), unnormalised.

    This is the full-vocabulary vector before softmax / top-k. Use it for:
      - Seed-vector cosine similarity (DL-9b)
      - Stretch JVP comparison
    """
    return (J @ h_mid.astype(np.float32)).astype(np.float32)


# ---------------------------------------------------------------------------
# Seed-vector matching (DL-9b)
# ---------------------------------------------------------------------------

def build_seed_vectors(
    model,
    tokenizer,
    J: np.ndarray,
    tap_layer_idx: int,
) -> Dict[str, np.ndarray]:
    """
    Precompute a L2-normalised seed vector in J-space for each disposition.

    For each disposition's seed phrases:
      1. Run the phrase through the model at tap_layer_idx
      2. Project the final-position hidden state through J → z (vocab_size,)
      3. L2-normalise z
      4. Average the normalised vectors and renormalise

    Returns {disposition: unit_vec (vocab_size,)}.
    """
    model.eval()
    device = next(model.parameters()).device
    seed_vectors: Dict[str, np.ndarray] = {}

    print(f"  Building seed vectors: tap_layer={tap_layer_idx}, {len(SEED_PHRASES)} dispositions")
    for disp, phrases in SEED_PHRASES.items():
        vecs: List[np.ndarray] = []
        for phrase in phrases:
            enc = tokenizer(phrase, return_tensors="pt", max_length=64, truncation=True)
            enc = {k: v.to(device) for k, v in enc.items()}
            with torch.no_grad():
                out = model(**enc, output_hidden_states=True)
            h = out.hidden_states[tap_layer_idx][0, -1, :].float().cpu().numpy()
            z = J @ h.astype(np.float32)          # (vocab_size,)
            norm = float(np.linalg.norm(z))
            if norm > 1e-8:
                z = z / norm
            vecs.append(z)

        avg = np.mean(vecs, axis=0)
        norm = float(np.linalg.norm(avg))
        if norm > 1e-8:
            avg = avg / norm
        seed_vectors[disp] = avg.astype(np.float32)
        print(f"    {disp}: {len(vecs)} phrases averaged")

    print(f"  Seed vectors built for: {list(seed_vectors.keys())}")
    return seed_vectors


def load_or_build_seed_vectors(
    model,
    tokenizer,
    J: np.ndarray,
    tap_layer_idx: int,
    cache_path: Optional[Path] = None,
) -> Dict[str, np.ndarray]:
    """Load seed vectors from cache (.npz); build and cache if absent."""
    path = cache_path
    if path is None:
        path = JLENS_CACHE_PATH.parent / "seed_vectors.npz"

    if path.exists():
        data = np.load(str(path))
        sv = {k: data[k] for k in data.files}
        print(f"Seed vectors loaded from cache {path} (dispositions: {list(sv.keys())})")
        return sv

    print("Seed vector cache not found — building (runs once)...")
    sv = build_seed_vectors(model, tokenizer, J, tap_layer_idx)
    np.savez(str(path), **sv)
    print(f"Seed vectors cached to {path}")
    return sv


def score_seed_vectors(
    z_query: np.ndarray,
    seed_vectors: Dict[str, np.ndarray],
) -> Dict[str, float]:
    """
    Cosine similarity of z_query (raw J @ h_mid, vocab-space) to each disposition seed vector.

    z_query is unnormalised; seed vectors are pre-normalised.
    Returns {disposition: cosine_similarity} in [-1.0, 1.0].
    """
    q = z_query.astype(np.float32)
    q_norm = float(np.linalg.norm(q))
    if q_norm < 1e-8:
        return {d: 0.0 for d in seed_vectors}
    q_unit = q / q_norm
    return {disp: float(np.dot(q_unit, sv)) for disp, sv in seed_vectors.items()}


# ---------------------------------------------------------------------------
# STRETCH: True autodiff JVP projection (DL-9c)
# ---------------------------------------------------------------------------

def _run_remaining_layers(model, h_mid: torch.Tensor, tap_layer_idx: int) -> torch.Tensor:
    """
    Run h_mid (1, 1, hidden_size) through transformer layers [tap_layer_idx+1:] + head.
    Returns logits (vocab_size,).

    Simplified single-position forward: no KV cache, position_ids defaults to zeros.
    This is used inside the JVP call, so all ops must be differentiable.
    """
    decoder = _decoder_model(model)
    x = h_mid  # (1, 1, hidden_size)
    position_ids = torch.zeros(1, 1, dtype=torch.long, device=h_mid.device)

    for layer in decoder.layers[tap_layer_idx + 1:]:
        try:
            out = layer(x, position_ids=position_ids, use_cache=False)
        except TypeError:
            try:
                out = layer(x, attention_mask=None, position_ids=position_ids)
            except TypeError:
                out = layer(x)
        x = out[0] if isinstance(out, (tuple, list)) else out

    x = decoder.norm(x)                       # (1, 1, hidden_size)
    logits = model.lm_head(x).squeeze()       # (vocab_size,)
    return logits


def project_jlens_jvp(
    model,
    h_mid_np: np.ndarray,
    tap_layer_idx: int,
    tokenizer,
    top_k: int = TOP_K,
) -> List[Dict]:
    """
    STRETCH (DL-9c): True autodiff Jacobian-vector product from tap layer to vocab space.

    Instead of the closed-form logit-lens (z = J_avg @ h_mid, which treats all intermediate
    layers as identity), this computes:

        z_jvp = d(remaining_layers(h)) / d(h) @ h   evaluated at h = h_mid

    via torch.autograd.functional.jvp through ALL remaining transformer layers + head.
    The result accounts for the actual nonlinear contributions of layers [tap+1:n].

    Falls back to the standard forward pass (logits = remaining_layers(h_mid)) if JVP
    encounters an unsupported op (e.g. in-place, non-differentiable) in a given model.
    """
    device = next(model.parameters()).device
    h_np = h_mid_np.astype(np.float32)
    h_3d = torch.tensor(h_np, device=device).unsqueeze(0).unsqueeze(0)  # (1, 1, hidden_size)

    def f(h_in):
        return _run_remaining_layers(model, h_in, tap_layer_idx)

    try:
        _, z_tensor = torch.autograd.functional.jvp(
            f, (h_3d,), (h_3d,), create_graph=False
        )
        z_np = z_tensor.detach().cpu().float().numpy()
        method = "jvp"
    except Exception as exc:
        print(f"  project_jlens_jvp: JVP failed ({exc}), falling back to forward pass")
        with torch.no_grad():
            z_tensor = f(h_3d)
        z_np = z_tensor.detach().cpu().float().numpy()
        method = "forward"

    if z_np.ndim > 1:
        z_np = z_np.ravel()

    print(f"  [stretch] JVP projection via {method}: vocab_size={z_np.shape[0]}")

    # Softmax + top-k (same as project_jlens)
    z_np -= z_np.max()
    exp_z = np.exp(z_np)
    probs = exp_z / (exp_z.sum() + 1e-9)

    top_indices = np.argsort(probs)[-top_k:][::-1]
    top_probs = probs[top_indices]
    w_min, w_max = top_probs.min(), top_probs.max()
    w_range = w_max - w_min

    tokens: List[Dict] = []
    for idx, prob in zip(top_indices, top_probs):
        token_str = tokenizer.decode([int(idx)]).strip()
        if not token_str:
            continue
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
