# CANIS-A Worklog

Task: `qwd5zr506i14hto` — iOS app skeleton + dual on-device model download.

Plan:
1. Scaffold a new `canis-ios/` SwiftUI iOS app using XcodeGen, separate from Sovereign Mind.
2. Reuse the proven Sovereign Mind patterns for resumable background downloads, Wi-Fi/cellular guard, storage checks, model manifests, and serialized MLX inference.
3. Include both required model identities:
   - `Canis Apertus` using `swiss-ai/Apertus-v1.1-4B-Instruct-MLX-INT4`
   - `Canis Mistralis` using `mlx-community/Ministral-3-3B-Instruct-2512-4bit`
4. Build a model hub with progress, pause/resume semantics, delete/storage management, active-model switching, and debug cellular override.
5. Build a basic on-device chat flow that streams through MLX Swift once the selected model is downloaded.
6. Add README/architecture notes and a build verifier so CANIS-C/D/E have stable extension points.

Key decisions:
- Keep Canis independent; do not couple it to Sovereign Mind auth, RAG, or server sync.
- Store model files under `Documents/models/<model-id>` with a `.complete` marker, matching SM's loader expectations.
- Keep disposition/J-lens hooks out of CANIS-A implementation, but name stable extension points for CANIS-C.
