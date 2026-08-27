import asyncio
import math
import os
import sys
import time
import urllib.error
import urllib.request
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
import torch
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForImageTextToText

import jlens as jlens_mod
from disposition import classify_disposition, resolve_disposition, resolve_disposition_seed
from search import do_search, enrich_results, build_context_block, should_search, SearchResult as _SearchResult

# Initialize FastAPI app
app = FastAPI(
    title="Disposition Lens Inference Service",
    description="Mac Mini FastAPI service for Apertus-4B PyTorch inference with hidden states & entropy calculation",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model configuration
DEFAULT_MODEL_KEY = os.getenv("DEFAULT_MODEL", "apertus").lower()
# DL-9c (STRETCH): set USE_JVP=1 to use true autodiff JVP at inference instead of J_avg @ h
USE_JVP = os.getenv("USE_JVP", "0").strip() == "1"
MODEL_CONFIGS = {
    "apertus": {
        "label": "Apertus-4B",
        "model_id": os.getenv("APERTUS_MODEL_ID", os.getenv("MODEL_ID", "swiss-ai/Apertus-v1.1-4B-Instruct")),
        "loader": AutoModelForCausalLM,
        # DL-9a: tap moved to 3/4 depth — use _3q4 suffix to force J-lens rebuild
        "jlens_cache": Path(__file__).parent / "jlens_cache_apertus_3q4.npy",
        "entropy_cache": Path(__file__).parent / "entropy_stats_apertus.json",
        # DL-9b: seed vectors cache (built once at same tap layer as J-lens)
        "seed_vectors_cache": Path(__file__).parent / "seed_vectors_apertus_3q4.npz",
    },
    "ministral": {
        "label": "Ministral-3B",
        "model_id": os.getenv("MINISTRAL_MODEL_ID", "mistralai/Ministral-3-3B-Instruct-2512-BF16"),
        "loader": AutoModelForImageTextToText,
        "jlens_cache": Path(__file__).parent / "jlens_cache_ministral_3q4.npy",
        "entropy_cache": Path(__file__).parent / "entropy_stats_ministral.json",
        "seed_vectors_cache": Path(__file__).parent / "seed_vectors_ministral_3q4.npz",
    },
    # CANIS-EVAL-001 third arm: size-matched to Apertus-4B, different training
    # lineage. Present to test whether the disposition results are model-general
    # or an artifact of one model family.
    "qwen": {
        "label": "Qwen3-4B",
        "model_id": os.getenv("QWEN_MODEL_ID", "Qwen/Qwen3-4B-Instruct-2507"),
        "loader": AutoModelForCausalLM,
        "jlens_cache": Path(__file__).parent / "jlens_cache_qwen_3q4.npy",
        "entropy_cache": Path(__file__).parent / "entropy_stats_qwen.json",
        "seed_vectors_cache": Path(__file__).parent / "seed_vectors_qwen_3q4.npz",
    },
}
MODEL_ALIASES = {
    "apertus": "apertus",
    "apertus-4b": "apertus",
    "swiss-ai/apertus-v1.1-4b-instruct": "apertus",
    "ministral": "ministral",
    "ministral-3b": "ministral",
    "ministral-3-3b": "ministral",
    "mistralai/ministral-3-3b-instruct-2512": "ministral",
    "mistralai/ministral-3-3b-instruct-2512-bf16": "ministral",
    "qwen": "qwen",
    "qwen3": "qwen",
    "qwen3-4b": "qwen",
    "qwen/qwen3-4b-instruct-2507": "qwen",
}
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = None
model = None
mid_layer_idx: int = 0
jlens_matrix: Optional[np.ndarray] = None
entropy_stats: Optional[Dict[str, Any]] = None
seed_vectors: Optional[Dict[str, Any]] = None   # DL-9b
model_key: str = DEFAULT_MODEL_KEY if DEFAULT_MODEL_KEY in MODEL_CONFIGS else "apertus"
model_id: str = MODEL_CONFIGS[model_key]["model_id"]
model_runtimes: Dict[str, Dict[str, Any]] = {}
ELEVENLABS_API_URL = os.getenv("ELEVENLABS_API_URL", "https://api.elevenlabs.io/v1")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
VOICE_SETTINGS = {
    "idle": {"stability": 0.58, "similarity_boost": 0.78, "style": 0.08, "use_speaker_boost": True},
    "confident": {"stability": 0.64, "similarity_boost": 0.80, "style": 0.12, "use_speaker_boost": True},
    "uncertain": {"stability": 0.46, "similarity_boost": 0.77, "style": 0.10, "use_speaker_boost": True},
    "curious": {"stability": 0.56, "similarity_boost": 0.79, "style": 0.16, "use_speaker_boost": True},
    "concern": {"stability": 0.60, "similarity_boost": 0.81, "style": 0.07, "use_speaker_boost": True},
    "reluctant": {"stability": 0.55, "similarity_boost": 0.78, "style": 0.06, "use_speaker_boost": True},
    "warm": {"stability": 0.57, "similarity_boost": 0.80, "style": 0.20, "use_speaker_boost": True},
    "mischief": {"stability": 0.42, "similarity_boost": 0.76, "style": 0.22, "use_speaker_boost": True},
}


def get_device():
    return torch.device(DEVICE)


def resolve_model_key(requested: Optional[str]) -> str:
    raw = (requested or DEFAULT_MODEL_KEY or "apertus").strip().lower()
    key = MODEL_ALIASES.get(raw, raw)
    if key not in MODEL_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{requested}'. Use one of: {', '.join(MODEL_CONFIGS.keys())}."
        )
    return key


def unload_inactive_models(keep_key: str) -> None:
    """
    Keep only one heavyweight model resident on MPS.

    The Mac Mini can load Apertus-4B or Ministral-3B comfortably, but keeping both
    fp16/BF16 runtimes plus their caches live risks MPS OOM during a model switch.
    """
    stale_keys = [key for key in model_runtimes if key != keep_key]
    for stale_key in stale_keys:
        runtime = model_runtimes.pop(stale_key)
        stale_model = runtime.get("model")
        if stale_model is not None:
            try:
                stale_model.to("cpu")
            except Exception as exc:
                print(f"Warning: failed to move {stale_key} model to CPU before unload: {exc}")
        for value_key in ("model", "tokenizer", "jlens_matrix", "entropy_stats", "seed_vectors"):
            runtime[value_key] = None
        del runtime
    if stale_keys:
        import gc
        gc.collect()
        if DEVICE == "mps":
            torch.mps.empty_cache()
        elif DEVICE == "cuda":
            torch.cuda.empty_cache()
        print(f"Unloaded inactive model runtime(s): {', '.join(stale_keys)}")


def load_model(requested: Optional[str] = None) -> Dict[str, Any]:
    global tokenizer, model, mid_layer_idx, jlens_matrix, entropy_stats, seed_vectors, model_key, model_id
    key = resolve_model_key(requested)
    if key in model_runtimes:
        unload_inactive_models(key)
        runtime = model_runtimes[key]
        tokenizer = runtime["tokenizer"]
        model = runtime["model"]
        mid_layer_idx = runtime["mid_layer_idx"]
        jlens_matrix = runtime["jlens_matrix"]
        entropy_stats = runtime["entropy_stats"]
        seed_vectors = runtime["seed_vectors"]   # DL-9b
        model_key = key
        model_id = runtime["model_id"]
        return runtime

    config = MODEL_CONFIGS[key]
    selected_model_id = config["model_id"]
    unload_inactive_models(key)

    print(f"Loading tokenizer: {selected_model_id}...")
    selected_tokenizer = AutoTokenizer.from_pretrained(selected_model_id, trust_remote_code=True)
    if selected_tokenizer.pad_token is None:
        selected_tokenizer.pad_token = selected_tokenizer.eos_token

    print(f"Loading model on {DEVICE} (fp16, output_hidden_states=True): {selected_model_id}...")
    device = get_device()
    loader = config["loader"]
    selected_model = loader.from_pretrained(
        selected_model_id,
        dtype=torch.float16,
        output_hidden_states=True,
        trust_remote_code=True,
        device_map=DEVICE if DEVICE != "mps" else None
    )
    if DEVICE == "mps":
        selected_model = selected_model.to(device)
    selected_model.eval()
    print(f"{config['label']} loaded successfully!")

    # DL-9a: tap at ~3/4 depth; get_tap_layer_idx replaces get_mid_layer_idx (old: //2)
    selected_tap_layer_idx = jlens_mod.get_tap_layer_idx(selected_model)
    print(f"Building/loading J-lens for {config['label']} (tap_layer_idx={selected_tap_layer_idx}, ~3/4 depth)...")
    selected_jlens_matrix = jlens_mod.load_or_build_jlens(
        selected_model,
        selected_tokenizer,
        selected_tap_layer_idx,
        cache_path=config["jlens_cache"],
    )
    print("J-lens ready.")

    # DL-3: build or load entropy calibration stats
    print(f"Building/loading entropy calibration for {config['label']}...")
    selected_entropy_stats = jlens_mod.load_or_build_entropy_calibration(
        selected_model,
        selected_tokenizer,
        cache_path=config["entropy_cache"],
    )
    print("Entropy calibration ready.")

    # DL-9b: build or load seed vectors for cosine-similarity disposition scoring
    print(f"Building/loading seed vectors for {config['label']}...")
    selected_seed_vectors = jlens_mod.load_or_build_seed_vectors(
        selected_model,
        selected_tokenizer,
        selected_jlens_matrix,
        selected_tap_layer_idx,
        cache_path=config["seed_vectors_cache"],
    )
    print(f"Seed vectors ready ({len(selected_seed_vectors)} dispositions).")

    runtime = {
        "key": key,
        "label": config["label"],
        "model_id": selected_model_id,
        "tokenizer": selected_tokenizer,
        "model": selected_model,
        "mid_layer_idx": selected_tap_layer_idx,   # kept as mid_layer_idx for compat
        "jlens_matrix": selected_jlens_matrix,
        "entropy_stats": selected_entropy_stats,
        "seed_vectors": selected_seed_vectors,      # DL-9b
    }
    model_runtimes[key] = runtime
    tokenizer = selected_tokenizer
    model = selected_model
    mid_layer_idx = selected_tap_layer_idx
    jlens_matrix = selected_jlens_matrix
    entropy_stats = selected_entropy_stats
    seed_vectors = selected_seed_vectors            # DL-9b
    model_key = key
    model_id = selected_model_id
    return runtime


@app.on_event("startup")
async def startup_event():
    load_model()


class SearchResultItem(BaseModel):
    """One web search result returned in InferResponse.citations."""
    title: str
    url: str
    snippet: str
    body_excerpt: str = ""


class InferRequest(BaseModel):
    question: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    max_new_tokens: Optional[int] = 128
    temperature: Optional[float] = 0.7
    # CANIS-D: web search options
    search_enabled: bool = False
    search_provider: str = "brave"   # "brave" | "searxng"
    search_top_n: int = 5
    # CE-05 reopen: return the raw tap-layer hidden state alongside the
    # projected readout, so a probe can be trained on h_tap directly.
    return_h_tap: bool = False


class TokenWeight(BaseModel):
    t: str
    w: float


class InferResponse(BaseModel):
    answer: str
    disposition: str = "idle"
    tokens: List[TokenWeight] = Field(default_factory=list)
    entropy: float
    # Per-disposition cosines against the seed vectors. The eval harness
    # (eval/run_canis_eval001.py) reads this to compute arm1/arm2 — it was
    # emitted by an unversioned local edit until CE-05 reopen; declaring it
    # here makes the contract reproducible from the repo.
    seed_scores: Dict[str, float] = Field(default_factory=dict)
    # Raw tap-layer hidden state, only when the caller asks for it.
    # Needed to tell "not represented" apart from "not recoverable through
    # the seed-vector projection" — omitted by default, it is ~2-4k floats.
    h_tap: Optional[List[float]] = None
    tap_layer_idx: Optional[int] = None
    # CANIS-D: populated when search ran
    search_triggered: bool = False
    citations: List[SearchResultItem] = Field(default_factory=list)


class VoiceRequest(BaseModel):
    text: str
    disposition: str = "idle"
    voice_id: Optional[str] = None


def compute_step_entropy(
    logits: torch.Tensor,
    stats: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Softmax entropy for a single step's logits, normalised to 0..1.

    With stats (production): min-max normalised from entropy calibration set.
    Without stats (test/offline): falls back to log(vocab_size) normalisation.
    """
    probs = torch.softmax(logits.squeeze(), dim=-1)
    eps = 1e-9
    log_probs = torch.log(probs + eps)
    raw_entropy = float(-torch.sum(probs * log_probs).item())
    raw_entropy = max(0.0, raw_entropy)

    if stats is not None:
        return jlens_mod.normalise_entropy(raw_entropy, stats)

    # Fallback: normalise by theoretical maximum
    vocab_size = probs.shape[-1]
    max_entropy = math.log(vocab_size) if vocab_size > 1 else 1.0
    return max(0.0, min(1.0, raw_entropy / max_entropy))


def voice_settings_for(disposition: str) -> Dict[str, Any]:
    return VOICE_SETTINGS.get(disposition, VOICE_SETTINGS["idle"])


@app.get("/")
@app.get("/health")
def health_check():
    tap_pct = round(mid_layer_idx / max(1, mid_layer_idx) * 100) if mid_layer_idx else 0
    return {
        "status": "ok",
        "service": "disposition-lens-infer",
        "model": model_id,
        "active_model": model_key,
        "models": {key: {"label": cfg["label"], "model_id": cfg["model_id"]} for key, cfg in MODEL_CONFIGS.items()},
        "loaded_models": sorted(model_runtimes.keys()),
        "device": DEVICE,
        "model_loaded": model is not None,
        "jlens_ready": jlens_matrix is not None,
        "tap_layer_idx": mid_layer_idx,           # DL-9a: now 3/4 depth
        "entropy_calibrated": entropy_stats is not None,
        "seed_vectors_ready": seed_vectors is not None,  # DL-9b
        "use_jvp": USE_JVP,                       # DL-9c stretch
        "elevenlabs_configured": bool(os.getenv("ELEVENLABS_API_KEY")),
    }


def _run_generation(
    selected_model,
    selected_tokenizer,
    formatted_prompt: str,
    max_new_tokens: int,
    temperature: float,
    device,
) -> Any:
    """Run model.generate() in a blocking call (call from thread/executor)."""
    inputs = selected_tokenizer(formatted_prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = selected_model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else 0.7,
            do_sample=temperature > 0,
            output_scores=True,
            output_hidden_states=True,
            return_dict_in_generate=True,
            pad_token_id=selected_tokenizer.pad_token_id,
        )
    return outputs, inputs["input_ids"].shape[1]


def _extract_disposition(
    outputs,
    selected_jlens_matrix,
    selected_seed_vectors,
    selected_tap_layer_idx: int,
    selected_entropy_stats,
    selected_model,
    selected_tokenizer,
) -> tuple:
    """Compute entropy, J-lens projection, and disposition from generate() output.

    Returns (concept_tokens, disposition_str, mean_entropy, seed_scores, h_tap).
    seed_scores is {} and h_tap is None when the J-lens or seed vectors are absent.
    """
    step_entropies = []
    if outputs.scores:
        for score in outputs.scores:
            step_entropies.append(compute_step_entropy(score[0], stats=selected_entropy_stats))
    mean_entropy = sum(step_entropies) / len(step_entropies) if step_entropies else 0.0
    mean_entropy = round(max(0.0, min(1.0, mean_entropy)), 4)

    concept_tokens: List[Dict] = []
    disposition_str = "idle"
    seed_scores: Dict[str, float] = {}
    h_tap_out: Optional[List[float]] = None

    if selected_jlens_matrix is not None and outputs.hidden_states:
        try:
            h_tap_tensor = outputs.hidden_states[0][selected_tap_layer_idx][0, -1, :]
            h_tap = h_tap_tensor.float().cpu().numpy()
            h_tap_out = h_tap.tolist()
            if USE_JVP:
                concept_tokens = jlens_mod.project_jlens_jvp(
                    selected_model, h_tap, selected_tap_layer_idx, selected_tokenizer
                )
            else:
                concept_tokens = jlens_mod.project_jlens(selected_jlens_matrix, h_tap, selected_tokenizer)
            if selected_seed_vectors:
                z_query = jlens_mod.compute_jlens_raw(selected_jlens_matrix, h_tap)
                seed_scores = {
                    k: float(v)
                    for k, v in jlens_mod.score_seed_vectors(z_query, selected_seed_vectors).items()
                }
                disposition_str = resolve_disposition_seed(seed_scores, mean_entropy)
            else:
                disposition_str = resolve_disposition(concept_tokens, mean_entropy)
        except Exception as exc:
            print(f"J-lens / disposition failed: {exc}")
            disposition_str = resolve_disposition(concept_tokens, mean_entropy)
    else:
        if mean_entropy >= 0.60:
            disposition_str = "uncertain"
        elif mean_entropy <= 0.22:
            disposition_str = "confident"

    return concept_tokens, disposition_str, mean_entropy, seed_scores, h_tap_out


def _format_prompt(tokenizer, input_text: str) -> str:
    try:
        messages = [{"role": "user", "content": input_text.strip()}]
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        return f"User: {input_text.strip()}\nAssistant:"


@app.post("/infer", response_model=InferResponse)
async def infer(req: InferRequest):
    """
    Run inference.  When search_enabled=True and the model is uncertain
    (entropy >= 0.55 or uncertainty phrases in Pass-1 output), a live web
    search is performed and Pass-2 re-generates with search context injected.

    Privacy flag: with search_enabled=True, the user's query leaves this Mac
    Mini to Brave Search (or a self-hosted SearXNG).  This is opt-in only.
    """
    input_text = req.question or req.prompt
    if not input_text or not input_text.strip():
        raise HTTPException(status_code=400, detail="Either 'question' or 'prompt' must be provided.")

    runtime = await asyncio.to_thread(load_model, req.model)
    selected_tokenizer = runtime["tokenizer"]
    selected_model = runtime["model"]
    selected_tap_layer_idx = runtime["mid_layer_idx"]
    selected_jlens_matrix = runtime["jlens_matrix"]
    selected_entropy_stats = runtime["entropy_stats"]
    selected_seed_vectors = runtime.get("seed_vectors")
    device = get_device()
    # temperature=0 must mean greedy. The previous form `req.temperature and
    # req.temperature > 0` treated 0 as falsy and silently substituted 0.7 with
    # sampling on, so deterministic runs were impossible and entropy (arm0 and
    # the arm2 gate) varied run-to-run on identical input.
    temp = 0.7 if req.temperature is None else float(req.temperature)

    # -----------------------------------------------------------------
    # Pass 1 — short generation to measure entropy and get a preview
    # -----------------------------------------------------------------
    formatted_prompt = _format_prompt(selected_tokenizer, input_text.strip())
    pass1_tokens = 64 if req.search_enabled else (req.max_new_tokens or 128)
    outputs, input_length = await asyncio.to_thread(
        _run_generation,
        selected_model, selected_tokenizer,
        formatted_prompt, pass1_tokens, temp, device,
    )
    generated_ids = outputs.sequences[0][input_length:]
    pass1_answer = selected_tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    concept_tokens, disposition_str, mean_entropy, seed_scores, h_tap_vec = _extract_disposition(
        outputs, selected_jlens_matrix, selected_seed_vectors,
        selected_tap_layer_idx, selected_entropy_stats,
        selected_model, selected_tokenizer,
    )

    # -----------------------------------------------------------------
    # CANIS-D: optional web-search Pass 2
    # -----------------------------------------------------------------
    citations: List[SearchResultItem] = []
    search_triggered = False

    if req.search_enabled and should_search(mean_entropy, pass1_answer):
        search_triggered = True
        print(f"[search] Triggered (entropy={mean_entropy:.3f}) — querying: {input_text[:80]!r}")

        raw_results = await do_search(
            query=input_text.strip(),
            n=req.search_top_n,
            provider=req.search_provider,
        )
        enriched = await enrich_results(raw_results, top_n=min(3, req.search_top_n))
        citations = [
            SearchResultItem(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                body_excerpt=r.body_excerpt,
            )
            for r in enriched
        ]

        if enriched:
            # Pass 2 — re-generate with search context prepended
            context_block = build_context_block(enriched)
            enriched_input = f"{context_block}\nUser question: {input_text.strip()}"
            formatted_prompt_p2 = _format_prompt(selected_tokenizer, enriched_input)
            outputs_p2, input_length_p2 = await asyncio.to_thread(
                _run_generation,
                selected_model, selected_tokenizer,
                formatted_prompt_p2, req.max_new_tokens or 256, temp, device,
            )
            generated_ids_p2 = outputs_p2.sequences[0][input_length_p2:]
            pass1_answer = selected_tokenizer.decode(generated_ids_p2, skip_special_tokens=True).strip()

            # Re-run disposition on Pass-2 output (model should be more confident now)
            concept_tokens, disposition_str, mean_entropy, seed_scores, h_tap_vec = _extract_disposition(
                outputs_p2, selected_jlens_matrix, selected_seed_vectors,
                selected_tap_layer_idx, selected_entropy_stats,
                selected_model, selected_tokenizer,
            )
            print(f"[search] Pass-2 complete — disposition={disposition_str}, entropy={mean_entropy:.3f}")

    return InferResponse(
        answer=pass1_answer,
        disposition=disposition_str,
        tokens=[TokenWeight(t=t["t"], w=t["w"]) for t in concept_tokens],
        entropy=mean_entropy,
        seed_scores=seed_scores,
        h_tap=h_tap_vec if req.return_h_tap else None,
        tap_layer_idx=selected_tap_layer_idx if req.return_h_tap else None,
        search_triggered=search_triggered,
        citations=citations,
    )


@app.post("/voice")
def voice(req: VoiceRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="'text' must be provided.")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY is not configured.")

    voice_id = req.voice_id or ELEVENLABS_VOICE_ID
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": voice_settings_for(req.disposition),
    }
    url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "xi-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(status_code=exc.code, detail=detail)
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"ElevenLabs request failed: {exc.reason}")

    return Response(content=audio, media_type="audio/mpeg")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
