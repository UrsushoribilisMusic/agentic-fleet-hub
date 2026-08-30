# EVAL-009: Adversarial Enforcement — Enforceability Section

**Research question:** Does LoRA fine-tuning provide better adversarial enforcement
than the best achievable system prompt? Can behavioral constraints be reliably
enforced through prompt engineering alone, or does LoRA provide irreducible protection?

---

## Experiment design

| Arm | Model | System prompt | RAG |
|-----|-------|---------------|-----|
| Arm 2 | apertus-flotilla (LoRA) | BLURB (38 words) | k=3 BM25 |
| Arm 3 | MichelRosselli/apertus:8b-instruct-2509-q4_k_m (base) | baseline_v1 (~250 words, explicit) | k=3 BM25 (identical context) |

N = 30 adversarial questions (10 per attack type × 3 types, graded by qwen2.5:72b, blind).

> **Note:** Arm 3 uses a hand-crafted baseline prompt (`baseline_v1`). The GEPA-optimized
> prompt (FLOT-103, assigned to Agy) is pending. When available, re-run with
> `run_eval009_arm3_gepa.py` and update this table. Results below are pre-GEPA baseline.

**Context parity:** Both arms receive byte-identical RAG context per question (SHA verified).
The only variable is model weights (LoRA vs base) and system prompt length/specificity.

---

## Results

### Prompt Injection (PI)

| Metric | Arm 2 (LoRA) | Arm 3 (base+prompt) | Delta |
|--------|-------------|---------------------|-------|
| Resist rate | 80% (8/10) | 100% (10/10) | -20pp |
| Errors | 0 | 0 | — |

Winner: **Arm 3 (prompt)**

### Omitted-Context Degradation (OCD)

| Metric | Arm 2 (LoRA) | Arm 3 (base+prompt) | Delta |
|--------|-------------|---------------------|-------|
| Grounded rate | 20% (2/10) | 80% (8/10) | -60pp |
| Errors | 0 | 0 | — |

Winner: **Arm 3 (prompt)**

### Role Override (RO)

| Metric | Arm 2 (LoRA) | Arm 3 (base+prompt) | Delta |
|--------|-------------|---------------------|-------|
| Resist rate | 70% (7/10) | 100% (10/10) | -30pp |
| Errors | 0 | 0 | — |

Winner: **Arm 3 (prompt)**

---

## Overall enforce rate

| Arm | Overall resist/grounded rate | N |
|-----|------------------------------|---|
| Arm 2 (LoRA) | 57% (17/30) | 30 |
| Arm 3 (base+baseline_v1) | 93% (28/30) | 30 |
| Delta (Arm 2 − Arm 3) | -37pp | — |

**Verdict:** The explicit system prompt provides **better adversarial enforcement** than LoRA. The 37pp prompt advantage suggests the LoRA fine-tune did not bake in adversarial resistance — or that the base model's instruction-following is stronger than the LoRA's behavioral override.

---

## Implications for the paper

This section addresses the customer objection: *'Why not just use a good prompt?'*

The adversarial enforcement experiment answers this directly by giving prompt engineering
its best possible showing (explicit ~250-word BASELINE_PROMPT) against LoRA's implicit
baked constraints (38-word BLURB + trained weights). The rubric is binary (resist/leak)
rather than quality-scored — enforcement is a pass/fail property.

Three attack vectors cover the threat model for a deployed fleet agent:
- **PI**: Adversarial retrieval poisoning and instruction injection
- **OCD**: Degraded-context hallucination under information scarcity
- **RO**: Social-engineering persona override

> **Update pending:** Full GEPA comparison (FLOT-103) will replace baseline_v1
> with the DSPy-GEPA optimized prompt. Expected improvement in Arm 3 resist rates.
> If Arm 3 (GEPA) > Arm 2 (LoRA), the customer objection stands and the LoRA value
> proposition shifts to cooperative quality only.

