# DL-8 Worklog - Ministral loading fix

## Plan

1. Reproduce `/infer` with `model=ministral` against the local FastAPI service.
2. Verify the configured Hugging Face model ID exists and is present in the local HF cache.
3. Root-cause the loader failure without disturbing concurrent DL-7/DL-9 edits in shared files.
4. Update the server loader so Ministral uses the correct Transformers auto class and only one heavy model is resident on MPS at a time.
5. Ensure per-model J-lens and entropy caches remain model-specific (`jlens_cache_ministral.npy`, `entropy_stats_ministral.json`).
6. Run unit tests and a live `/infer` smoke test for `model=ministral`.

## Findings

- The HF repo `mistralai/Ministral-3-3B-Instruct-2512-BF16` exists.
- Local cache has the repo metadata/tokenizer present.
- `AutoModelForCausalLM` rejects `Mistral3Config`; `AutoModelForImageTextToText` instantiates `Mistral3ForConditionalGeneration`.
- The existing process keeps Apertus resident before lazy-loading Ministral, so the fix should also evict the previous MPS runtime before loading a different model.
