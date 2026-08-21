# Canis iOS Architecture

## App Flow

`CanisApp` creates the shared `ModelDownloadManager` and shows `RootView`.

`RootView` owns two tabs:
- `ChatView`: active model selector, chat transcript, streaming on-device answer.
- `ModelHubView`: model download, progress, storage, delete, and cellular guard controls.

## Model Storage

Models live under:

```text
Documents/models/<model-id>/
```

Each completed model directory gets a `.complete` marker. MLX loading requires `config.json`; the marker is used for UI state and resume bookkeeping.

## Download Path

`CanisModel` defines Hugging Face repos and required files. `ModelDownloadManager` uses a background `URLSessionDownloadDelegate`, persists verified files and pending manifests in `download_state.json`, writes resume data beside the interrupted file, and resumes pending files after app restart.

Release builds allow only Wi-Fi downloads. Debug builds include `setCellularBypass(_:)` for tester/demo devices without Wi-Fi.

## Inference Path

`CanisMLXEngine` serializes model residency and token streaming. It unloads on backgrounding, clears MLX cache on memory warning, and swaps models by unloading the previous resident container before loading the next one.

## Disposition Readout

`CanisMLXEngine.generate` emits `CanisGenerationEvent` values:
- `.text(String)` for normal streamed assistant output.
- `.disposition(DispositionReadout)` for the live avatar/readout signal.

`DispositionReadoutEngine` owns the forward-only CANIS-C path. When model artifacts are present under:

```text
Documents/models/<model-id>/disposition-readout/
```

it can consume a tapped MLX hidden state plus logits, project the hidden state through `jlens_projection.json`, cosine-score the projected J-space vector against `seed_vectors.json`, compute normalized next-token entropy from logits, and resolve the final disposition with safety overrides.

The current high-level `MLXLMCommon.ChatSession` API streams text but does not expose hidden states. Until CANIS-A exposes that lower-level tap, the engine keeps text streaming live and emits a lexical fallback readout through the same event channel. The forward-only MLX entry point is `DispositionReadoutEngine.forwardReadout(hiddenState:logits:)`; no autodiff/JVP path is used.
