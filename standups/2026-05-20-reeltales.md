# ReelTales — 2026-05-20 (evening session with Teddy)

## Summary
Major pipeline stabilization session. Switched to gen4_turbo, resolved duration constraints, hardened caption parsing, and fixed first live French order.

---

## Changes Shipped

### Pipeline defaults (music-video-tool)
| Setting | Before | After |
|---------|--------|-------|
| Runway model | gen3a_turbo | gen4_turbo (set in `pipeline_runner.py` RUNWAY_CLIP_MODEL) |
| Clip duration | 10s | 10s (only 5 or 10 valid for gen4_turbo — 8 rejected by API) |
| Video ratio | 768:1280 | 720:1280 (gen4_turbo requirement) |
| Clips per order | 9 | 7 |
| Caption blocks | 9 | 7 |
| `_NO_VOX_BLOCK_DUR` | 9.0s | 10.0s |
| Target video length | ~115s | ~77s (7 blocks × 10s + hook/outro) |

### gen_story_modern.py
- Caption count 9 → 7
- Prompt count fixed at 7 (was "7–9, let arc decide")
- Added `translate_runway_prompts_to_english()`: after Apertus call, FIRST_IMAGE_PROMPT and RUNWAY_PROMPTS are auto-translated via Claude Sonnet — Apertus reliably ignores the English-only instruction
- Strengthened caption format rules: no numbering, no parenthetical comments, RULES label instead of soft instruction

### assemble_fable.py + narrate_fable.py — Apertus caption guardrails
Both `read_caption_blocks` and `load_captions_text` now handle:
1. Numbered single-line format (`1. text\n2. text`) — fallback splits by `\n`, strips `N. ` prefixes
2. Trigger condition changed from `len(blocks) <= 1` to `len(blocks) <= 1 OR blocks[0] has 3+ lines` — catches the case where the numbered dump + trailing meta-comment produces 2 double-newline blocks instead of 1
3. Parenthetical meta-commentary lines `(...)` filtered out

### upload_fable.py
- Added CTA line to every YouTube description: `"Created with Classic Reel Tales. Generate yours here: https://robotross.art/"`
- Positioned between story body and hashtags

---

## Order #1033 (French — "From Earth to Moon, Again")
- First fr-CH production order
- Hit two bugs: gen4_turbo duration=8 rejected (API only accepts 5/10); Apertus returned French Runway prompts
- Retry ran on gen3a_turbo 5s (code fix landed after retry started) — clips kept as-is per Teddy
- Narration re-generated with numbered captions stripped (31.8s clean)
- Video re-assembled (9 blocks, 3.5s/block) and re-uploaded → `1NVL-oif7Ag`
- Old video `CSBNflcFNUY` to delete from YouTube Studio

---

## Known issues / next session
- Infisical vault token expired (403 on all secrets) — secrets fall back to env, no immediate breakage but should be renewed
- First fr-CH video is only ~38s (31.8s narration, 7 sentence captions narrated fast) — next French order will benefit from 7-block structure at 10s clips
- gen4_turbo not yet tested in production (all orders so far ran on gen3a_turbo due to timing of code changes)
</content>
</invoke>