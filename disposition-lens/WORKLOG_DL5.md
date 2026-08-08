# DL-5 Worklog - ElevenLabs tone + Ministral toggle

Task: add optional ElevenLabs voice playback keyed subtly by disposition, and expose
Ministral-3B as a second inference model behind a UI toggle.

Plan:
1. Extend the FastAPI `/infer` request with a model selector while preserving the
   existing response contract.
2. Load/cache model runtimes per supported model so Apertus remains the default and
   Ministral can be selected without changing environment variables.
3. Replace browser-only TTS in the prototype with an ElevenLabs path when
   `window.ELEVENLABS_API_KEY` is configured, falling back gracefully if voice is off
   or credentials are absent.
4. Add compact prototype controls for model selection and voice provider state.
5. Run focused tests for server request parsing/model config and a syntax check for
   the prototype.

Key decisions:
- Keep Apertus as the default model to preserve DL-4 behavior.
- Keep tone nudges subtle: stability/style adjustments are small and disposition keyed.
- Do not introduce secrets into the repo. Browser-side ElevenLabs requires local
  runtime configuration only.
