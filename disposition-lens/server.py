import math
import os
import sys
import time
from typing import List, Optional, Dict, Any

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM

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
MODEL_ID = os.getenv("MODEL_ID", "swiss-ai/Apertus-v1.1-4B-Instruct")
DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = None
model = None

def get_device():
    return torch.device(DEVICE)

def load_model():
    global tokenizer, model
    if model is not None and tokenizer is not None:
        return
    
    print(f"Loading tokenizer: {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading model on {DEVICE} (fp16, output_hidden_states=True): {MODEL_ID}...")
    device = get_device()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        dtype=torch.float16,
        output_hidden_states=True,
        trust_remote_code=True,
        device_map=DEVICE if DEVICE != "mps" else None
    )
    if DEVICE == "mps":
        model = model.to(device)
    model.eval()
    print("Model loaded successfully!")

@app.on_event("startup")
async def startup_event():
    load_model()

class InferRequest(BaseModel):
    question: Optional[str] = None
    prompt: Optional[str] = None
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

def compute_step_entropy(logits: torch.Tensor) -> float:
    """
    Computes normalized softmax entropy (0..1) for a single step's logits.
    Max theoretical entropy is log(vocab_size).
    """
    probs = torch.softmax(logits.squeeze(), dim=-1)
    eps = 1e-9
    log_probs = torch.log(probs + eps)
    entropy = -torch.sum(probs * log_probs).item()
    vocab_size = probs.shape[-1]
    max_entropy = math.log(vocab_size) if vocab_size > 1 else 1.0
    norm_entropy = entropy / max_entropy
    return max(0.0, min(1.0, norm_entropy))

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "disposition-lens-infer",
        "model": MODEL_ID,
        "device": DEVICE,
        "model_loaded": model is not None
    }

@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    input_text = req.question or req.prompt
    if not input_text or not input_text.strip():
        raise HTTPException(status_code=400, detail="Either 'question' or 'prompt' must be provided.")

    if model is None or tokenizer is None:
        load_model()

    device = get_device()

    # Format input using chat template if available
    try:
        messages = [{"role": "user", "content": input_text.strip()}]
        formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        formatted_prompt = f"User: {input_text.strip()}\nAssistant:"

    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(device)
    input_length = inputs["input_ids"].shape[1]

    # Generate with output_scores=True and output_hidden_states=True
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=req.max_new_tokens or 128,
            temperature=req.temperature if req.temperature and req.temperature > 0 else 0.7,
            do_sample=True if req.temperature and req.temperature > 0 else False,
            output_scores=True,
            output_hidden_states=True,
            return_dict_in_generate=True,
            pad_token_id=tokenizer.pad_token_id
        )

    # Extract generated tokens
    generated_ids = outputs.sequences[0][input_length:]
    answer = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    # Compute step entropies across generated tokens
    step_entropies = []
    if outputs.scores:
        for score in outputs.scores:
            step_entropy = compute_step_entropy(score[0])
            step_entropies.append(step_entropy)

    mean_entropy = sum(step_entropies) / len(step_entropies) if step_entropies else 0.0
    mean_entropy = round(max(0.0, min(1.0, mean_entropy)), 4)

    return InferResponse(
        answer=answer,
        disposition="idle",  # DL-1 placeholder, upgraded in DL-3
        tokens=[],            # DL-1 placeholder, upgraded in DL-2
        entropy=mean_entropy
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
