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

CANIS-C should extend `CanisMLXEngine` around the generation loop to expose logits/hidden-state readout without changing the download hub or chat UI contracts.
