# PC-108 — 2-stage Translate pipeline + Qwen2.5 1.5B text model

## Goal
Move Capture translate off the vision model. OCR should extract source text first, then a text-only chat request should route through a stronger small translation model. The chat UI also needs to expose the OCR source text so users can inspect what was extracted.

## Plan
1. Add `Qwen2.5 1.5B Instruct Q4` to `ModelManager` and teach `ModelRouter` to prefer it for text work when downloaded, while keeping `SmolLM2 135M` as a fallback for one cycle.
2. Extend session/chat request state so Capture can open a text-only chat with a hidden model prompt, a clean visible label, and the OCR source text attached.
3. Rewrite `CaptureView.translateNow` to perform OCR first and launch a direct text-generation request instead of sending the image to the VLM.
4. Add a collapsible `Original text` section in `ChatView` and route direct text requests through MLX without retrieval context injection.
5. Run `scripts/build-tag.sh` and report any verifier failures honestly.
