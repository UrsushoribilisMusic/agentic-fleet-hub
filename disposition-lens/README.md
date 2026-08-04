# Disposition Lens

A video-able avatar for Sovereign Mind whose face reflects the model's *disposition*
(J-space / Anthropic's Jacobian lens) **before** the answer is spoken. Honest thesis:
you can *see* when the model is unsure. Reads **disposition, not emotion**.

- **`SPEC.md`** — the full fleet handoff (architecture, signal contract, J-lens tap recipe, task split).
- **`prototype/disposition_lens.jsx`** — the face UI. Runs today on a Sonnet stand-in (Ask) + a
  deterministic offline Demo Reel (clean video capture). One `>>> HOOK` in `ask()` is the swap point
  to the real Mac-Mini J-lens service.

## Tickets (PocketBase)
- **DL-1** (gem) — Mac Mini FastAPI `/infer` on Apertus-4B, PyTorch fp16. *Unblocker.*
- **DL-2** (clau) — build + cache the J-lens → concept tokens.
- **DL-3** (clau) — lexicon disposition classifier + entropy → full signal contract.
- **DL-4** (gem) — repoint the prototype HOOK → `/infer`, host it.
- **DL-5** (codi, optional) — ElevenLabs tone-by-disposition + Ministral-3B toggle.
- **DL-6** (clau) — record the offline Demo Reel video.

Critical path is kept off **codi** (out until ~2026-08-09). Server-side only — the on-device
iOS/MLX path stays untouched.
