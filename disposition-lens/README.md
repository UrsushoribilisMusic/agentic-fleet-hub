# Disposition Lens

A video-able avatar for Sovereign Mind whose face reflects the model's *disposition*
(J-space / Anthropic's Jacobian lens) **before** the answer is spoken. Honest thesis:
you can *see* when the model is unsure. Reads **disposition, not emotion**.

- **`SPEC.md`** — the full fleet handoff (architecture, signal contract, J-lens tap recipe, task split).
- **`prototype/disposition_lens.jsx`** — the face UI. Runs today on a Sonnet stand-in (Ask) + a
  deterministic offline Demo Reel (clean video capture). One `>>> HOOK` in `ask()` is the swap point
  to the real Mac-Mini J-lens service.

## DL-5 Runtime Toggles

The `/infer` request accepts an optional `model` field:

```json
{"question": "What baud rate?", "model": "apertus"}
```

Supported values are `apertus` and `ministral`. Apertus remains the default. Override model IDs at
startup with `APERTUS_MODEL_ID`, `MINISTRAL_MODEL_ID`, and `DEFAULT_MODEL`; legacy `MODEL_ID` still
maps to Apertus for compatibility.

The prototype voice button calls the local FastAPI `/voice` endpoint. Configure ElevenLabs on the
server process only:

```bash
ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM ./run_server.sh
```

Disposition-specific ElevenLabs stability/style nudges are intentionally subtle. Do not commit keys.

## Tickets (PocketBase)
- **DL-1** (gem) — Mac Mini FastAPI `/infer` on Apertus-4B, PyTorch fp16. *Unblocker.*
- **DL-2** (clau) — build + cache the J-lens → concept tokens.
- **DL-3** (clau) — lexicon disposition classifier + entropy → full signal contract.
- **DL-4** (gem) — repoint the prototype HOOK → `/infer`, host it.
- **DL-5** (codi, optional) — ElevenLabs tone-by-disposition + Ministral-3B toggle.
- **DL-6** (clau) — record the offline Demo Reel video.

Critical path is kept off **codi** (out until ~2026-08-09). Server-side only — the on-device
iOS/MLX path stays untouched.
