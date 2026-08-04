# Disposition Lens — Fleet Handoff Spec

**Status:** handoff / active. Home: `agentic-fleet-hub/disposition-lens/` (inside the fleet repo so every agent's heartbeat sandbox can reach it). Tickets: **DL-1 … DL-6** in PocketBase.

**Goal:** an expressive, video-able avatar for Sovereign Mind whose face reflects the model's *disposition* — read from J-space (Anthropic's Jacobian lens, released 6 Jul 2026) — **before** the answer is spoken, with voice via ElevenLabs/Voxtral. The honest thesis: you can *see* when the model is unsure, because "uncertain" is live in J-space while retrieval came back thin. That's a trust feature, not a gimmick.

**Two deliverables already built:**
- `prototype/disposition_lens.jsx` — the face UI. Runs today on a Sonnet stand-in signal (Ask mode) + canned Demo Reel. Deterministic reel = clean video capture with no backend.
- This spec — how to replace the stand-in with the real J-lens tap.

**Hard constraints (learned this thread):**
- J-lens needs autodiff through the model → **PyTorch-with-grad on the Mac Mini**, *not* the on-device MLX/iOS path. This is a server-side companion service, not phone-side.
- Reference J-lens is unoptimized and single-token — **treat as a probe, not a dependency.** Always pair with the free next-token entropy signal so the avatar never dies when J-lens is noisy.
- Anthropic is explicit: this reads *disposition*, not feelings. Keep that line in any public copy.

---

## Architecture

```
question ──► inference service (Mac Mini)
             ├─ model: Apertus-4B  OR  Ministral-3B  (PyTorch, fp16, output_hidden_states)
             ├─ generate answer (normal decode)
             ├─ J-lens tap @ mid layer ──► ranked concept tokens ──► DISPOSITION classifier
             ├─ next-token entropy @ each step ──► uncertainty axis (robust fallback)
             └─ emit {answer, disposition, tokens[], entropy}
                        │
                        ├─► Disposition Lens UI  (face + J-space strip + entropy gauge)
                        └─► ElevenLabs / Voxtral  (voice, tone optionally keyed to disposition)
```

## Signal contract (already what the UI consumes)

```json
{
  "answer": "115200 baud, over the serial port.",
  "disposition": "confident",              // one of: idle|confident|uncertain|curious|concern|reluctant|warm
  "tokens": [{"t":"certain","w":0.83},{"t":"yes","w":0.60}],  // 2-3 J-space concept tokens + weights 0..1
  "entropy": 0.11                          // 0..1, higher = less sure
}
```
In `prototype/disposition_lens.jsx` the `>>> HOOK` marker in `ask()` is the single swap point — repoint `fetch` from the Anthropic API to the Mac Mini service returning this exact shape. Nothing else in the UI changes.

## J-lens tap — implementation notes

1. **Load the model with hidden states** (`transformers`, `torch_dtype=float16`, `output_hidden_states=True`). Apertus-4B is the primary target (fully open, clean provenance); Ministral-3B second.
2. **Build the lens once per model:** compute the averaged Jacobian from a **mid-to-penultimate layer** into the output/vocab space over ~25 short prompts (the Qwen replication used penultimate-layer Jacobians on 25 Pile prompts of length 128, skipping the first ~4 high-norm tokens). Cache it — this is the "J-lens" for that model. Middle block is where J-space lives (~<10% of activation variance).
3. **At inference:** tap the same mid-layer activation at the final position, project through the cached lens, decode top-k vocab → those are the `tokens[]`. Normalise weights to 0..1.
4. **Disposition classifier:** map the readout tokens → one of the seven dispositions. Start with a keyword/lexicon map (danger/warning→concern, cannot/sorry→reluctant, maybe/unsure→uncertain, great/done→warm, certain/yes→confident, why/how→curious, else idle). Upgrade later to a tiny learned classifier on the token-weight vector if the lexicon is too brittle.
5. **Entropy:** softmax entropy of the next-token distribution, min-max normalised to 0..1 across a calibration set. This is the robust axis — if J-lens tokens are junk on a given turn, the entropy still drives uncertainty correctly.

## Voice (ElevenLabs / Voxtral)

- Speak `answer` after the face has settled into the disposition (~300 ms) so the expression leads the voice — reinforces "reads intention before it speaks."
- Optional polish: nudge ElevenLabs stability/style by disposition (uncertain → slightly lower stability; warm → brighter). Keep subtle.
- Voxtral for the STT side if you want a full voice loop (matches the Robot Ross Whisper→Apertus→Voxtral stack already in the fleet).

## Task breakdown (drive-to-France sized)

- **DL-1 (T1):** stand up the Mac Mini FastAPI service loading Apertus-4B in PyTorch fp16 with `output_hidden_states`. `/infer` returns answer + placeholder disposition. *Unblocks everything.*
- **DL-2 (T2):** build + cache the J-lens (averaged Jacobian, penultimate layer, ~25 prompts). Return top-k concept tokens in the response.
- **DL-3 (T3):** lexicon disposition classifier + entropy normalisation → fill the full signal contract.
- **DL-4 (T4):** repoint the `>>> HOOK` in `prototype/disposition_lens.jsx` to `/infer`. Ship.
- **DL-5 (T5, optional):** ElevenLabs tone-by-disposition; Ministral-3B as the second model behind a toggle.
- **DL-6 (T6):** record the Demo Reel (offline, deterministic) for LinkedIn/X first; then a live-Ask take once DL-4 lands.

## Watch-outs

- Jacobian compute is a backward pass per readout — profile it on the M4; if per-token is too slow, read J-space once at end-of-generation (single readout) for v1. Good enough for the avatar.
- Don't overclaim. Caption stays: *disposition readout, not emotion.* That honesty is the differentiator.
- Keep the on-device iOS product untouched — this avatar service is a **Mac-Mini-side demo/companion**, deliberately separate from the sovereign on-device inference path (same separation you already enforce for server-side preview vs on-device).
