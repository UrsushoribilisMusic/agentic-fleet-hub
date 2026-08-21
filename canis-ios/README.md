# Canis iOS

Canis is a new SwiftUI + MLX Swift iPhone app for the on-device disposition-lens hackathon track. It is intentionally separate from Sovereign Mind: no auth, no RAG sync, and no cloud inference.

## Scope in CANIS-A

- Dual on-device model hub:
  - Canis Apertus: `swiss-ai/Apertus-v1.1-4B-Instruct-MLX-INT4`
  - Canis Mistralis: `mlx-community/Ministral-3-3B-Instruct-2512-4bit`
- Background URLSession downloads with resume data, per-file progress, disk-space check, delete/reclaim storage, and a production cellular guard.
- Active model switch stored in `AppStorage`.
- Basic on-device chat through MLX Swift once the selected model is downloaded.
- Stable extension points for CANIS-C disposition readout.

## Build

```sh
cd canis-ios
./scripts/build-tag.sh
```

The verifier runs `xcodegen generate`, resolves packages, and builds `Canis` for an iPhone simulator.

## Notes

Large model downloads are Wi-Fi-only in Release builds. Debug builds expose a cellular override for field testing.
