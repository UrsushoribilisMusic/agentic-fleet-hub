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
from transformers import AutoTokenizer, AutoModelForCausalLM

import jlens as jlens_mod
from disposition import classify_disposition, resolve_disposition

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
MODEL_CONFIGS = {
    "apertus": {
        "label": "Apertus-4B",
        "model_id": os.getenv("APERTUS_MODEL_ID", os.getenv("MODEL_ID", "swiss-ai/Apertus-v1.1-4B-Instruct")),
        "jlens_cache": Path(__file__).parent / "jlens_cache_apertus.npy",
        "entropy_cache": Path(__file__).parent / "entropy_stats_apertus.json",
    },
    "ministral": {
        "label": "Ministral-3B",
        "model_id": os.getenv("MINISTRAL_MODEL_ID", "mistralai/Ministral-3-3B-Instruct-2512-BF16"),
        "jlens_cache": Path(__file__).parent / "jlens_cache_ministral.npy",
        "entropy_cache": Path(__file__).parent / "entropy_stats_ministral.json",
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
}
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = None
model = None
mid_layer_idx: int = 0
jlens_matrix: Optional[np.ndarray] = None
entropy_stats: Optional[Dict[str, Any]] = None
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


def load_model(requested: Optional[str] = None) -> Dict[str, Any]:
    global tokenizer, model, mid_layer_idx, jlens_matrix, entropy_stats, model_key, model_id
    key = resolve_model_key(requested)
    if key in model_runtimes:
        runtime = model_runtimes[key]
        tokenizer = runtime["tokenizer"]
        model = runtime["model"]
        mid_layer_idx = runtime["mid_layer_idx"]
        jlens_matrix = runtime["jlens_matrix"]
        entropy_stats = runtime["entropy_stats"]
        model_key = key
        model_id = runtime["model_id"]
        return runtime

    config = MODEL_CONFIGS[key]
    selected_model_id = config["model_id"]

    print(f"Loading tokenizer: {selected_model_id}...")
    selected_tokenizer = AutoTokenizer.from_pretrained(selected_model_id, trust_remote_code=True)
    if selected_tokenizer.pad_token is None:
        selected_tokenizer.pad_token = selected_tokenizer.eos_token

    print(f"Loading model on {DEVICE} (fp16, output_hidden_states=True): {selected_model_id}...")
    device = get_device()
    selected_model = AutoModelForCausalLM.from_pretrained(
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

    # DL-2: build or load J-lens
    selected_mid_layer_idx = jlens_mod.get_mid_layer_idx(selected_model)
    print(f"Building/loading J-lens for {config['label']} (mid_layer_idx={selected_mid_layer_idx})...")
    selected_jlens_matrix = jlens_mod.load_or_build_jlens(
        selected_model,
        selected_tokenizer,
        selected_mid_layer_idx,
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

    runtime = {
        "key": key,
        "label": config["label"],
        "model_id": selected_model_id,
        "tokenizer": selected_tokenizer,
        "model": selected_model,
        "mid_layer_idx": selected_mid_layer_idx,
        "jlens_matrix": selected_jlens_matrix,
        "entropy_stats": selected_entropy_stats,
    }
    model_runtimes[key] = runtime
    tokenizer = selected_tokenizer
    model = selected_model
    mid_layer_idx = selected_mid_layer_idx
    jlens_matrix = selected_jlens_matrix
    entropy_stats = selected_entropy_stats
    model_key = key
    model_id = selected_model_id
    return runtime


@app.on_event("startup")
async def startup_event():
    load_model()


class InferRequest(BaseModel):
    question: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    max_new_tokens: Optional[int] = 128
    temperature: Optional[float] = 0.7


class TokenWeight(BaseModel):
    t: str
    w: float


class InferResponse(BaseModel):
    answer: str
    disposition: str = "idle"
    tokens: List[TokenWeight] = Field(default_factory=list)
    entropy: float


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
        "entropy_calibrated": entropy_stats is not None,
        "elevenlabs_configured": bool(os.getenv("ELEVENLABS_API_KEY")),
    }


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    input_text = req.question or req.prompt
    if not input_text or not input_text.strip():
        raise HTTPException(status_code=400, detail="Either 'question' or 'prompt' must be provided.")

    runtime = load_model(req.model)
    selected_tokenizer = runtime["tokenizer"]
    selected_model = runtime["model"]
    selected_mid_layer_idx = runtime["mid_layer_idx"]
    selected_jlens_matrix = runtime["jlens_matrix"]
    selected_entropy_stats = runtime["entropy_stats"]

    device = get_device()

    # Format input using chat template if available
    try:
        messages = [{"role": "user", "content": input_text.strip()}]
        formatted_prompt = selected_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        formatted_prompt = f"User: {input_text.strip()}\nAssistant:"

    inputs = selected_tokenizer(formatted_prompt, return_tensors="pt").to(device)
    input_length = inputs["input_ids"].shape[1]

    # Generate with output_scores=True and output_hidden_states=True
    with torch.no_grad():
        outputs = selected_model.generate(
            **inputs,
            max_new_tokens=req.max_new_tokens or 128,
            temperature=req.temperature if req.temperature and req.temperature > 0 else 0.7,
            do_sample=True if req.temperature and req.temperature > 0 else False,
            output_scores=True,
            output_hidden_states=True,
            return_dict_in_generate=True,
            pad_token_id=selected_tokenizer.pad_token_id
        )

    # Extract generated tokens
    generated_ids = outputs.sequences[0][input_length:]
    answer = selected_tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    # DL-3: compute step entropies with calibration-aware min-max normalisation
    step_entropies = []
    if outputs.scores:
        for score in outputs.scores:
            step_entropy = compute_step_entropy(score[0], stats=selected_entropy_stats)
            step_entropies.append(step_entropy)

    mean_entropy = sum(step_entropies) / len(step_entropies) if step_entropies else 0.0
    mean_entropy = round(max(0.0, min(1.0, mean_entropy)), 4)

    # DL-2: J-lens concept tokens
    # outputs.hidden_states[0] = all layer hidden states for the prefill step
    # shape per layer: (batch, prompt_len, hidden_size)
    # Take the mid-layer hidden state at the final prompt position
    concept_tokens: List[Dict] = []
    if selected_jlens_matrix is not None and outputs.hidden_states:
        try:
            h_mid_tensor = outputs.hidden_states[0][selected_mid_layer_idx][0, -1, :]  # (hidden_size,)
            h_mid = h_mid_tensor.float().cpu().numpy()
            concept_tokens = jlens_mod.project_jlens(selected_jlens_matrix, h_mid, selected_tokenizer)
        except Exception as exc:
            print(f"J-lens projection failed: {exc}")

    # Resolve disposition: weight-gated lexicon vote + entropy as the robust axis
    # (avoids stray low-weight tokens hijacking the face; entropy drives sure/unsure).
    disposition_str = resolve_disposition(concept_tokens, mean_entropy)

    return InferResponse(
        answer=answer,
        disposition=disposition_str,
        tokens=[TokenWeight(t=t["t"], w=t["w"]) for t in concept_tokens],
        entropy=mean_entropy,
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
