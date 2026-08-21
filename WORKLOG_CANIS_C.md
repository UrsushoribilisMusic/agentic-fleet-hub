# CANIS-C Worklog

Task: CANIS-C on-device MLX disposition readout.
Agent: codi
Started: 2026-08-21

## Plan

1. Inspect the CANIS-A iOS skeleton and MLX streaming path.
2. Add Swift models for dispositions, entropy, seed-vector scoring, and readout payloads.
3. Integrate a forward-only readout hook into `CanisMLXEngine` without autodiff/JVP.
4. Surface disposition updates in `ChatViewModel` and the chat UI so the avatar can react.
5. Add focused unit tests for resolver behavior and run the Canis build verifier if available.

## Decisions

- Full autodiff JVP remains out of scope. The implementation is a forward-only J-lens projection contract suitable for cached matrix artifacts.
- If MLX Swift LM does not expose hidden states through the high-level chat stream, the engine will keep normal text streaming intact and expose a deterministic forward-only readout seam for the lower-level hidden-state tap to fill when CANIS-A exposes it.

## Progress

- Added `Disposition`, `DispositionReadout`, and `CanisGenerationEvent`.
- Added `DispositionReadoutEngine` with artifact loading, forward hidden-state/logit readout entry point, entropy computation, seed-score resolver, and lexical fallback.
- Changed `CanisMLXEngine.generate` to emit text + disposition events.
- Wired `ChatViewModel`, assistant messages, and `DispositionAvatarView` to drive the avatar/readout UI.
- Added unit coverage for uncertainty entropy, safety override, and mischief wording.
