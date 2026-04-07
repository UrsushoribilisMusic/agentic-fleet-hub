# Domain Knowledge: Contextual Grounding

Essential external context for the fleet's operations and strategic positioning. Agents should read this before making decisions that touch compliance, funding, or public-facing positioning.

---

## Swiss AI & Regulatory Context

**Big Bear Engineering** operates primarily in the Swiss/EU market, where the regulatory environment for AI systems is stricter than in other jurisdictions.

### EU AI Act (Regulation 2024/1689)
- **Enforcement timeline**: Applies from August 2026 in full. High-risk system requirements began earlier.
- **Relevance to Flotilla**: Flotilla itself is an orchestration layer, not an end-user AI application. However, if Flotilla agents interact with systems classified as high-risk (healthcare, HR, credit), those integrations require conformity assessments.
- **Agent autonomy boundary**: Tasks involving personal data processing or automated decision-making with legal effects on individuals require a human-in-the-loop gate. The `waiting_human` status in PocketBase serves this function.
- **Documentation obligation**: High-risk AI systems must maintain logs of agent actions and decisions. The `heartbeats`, `comments`, and `lessons` PocketBase collections partially fulfill this.
- **Practical rule**: When adding a new integration or fleet capability that touches user data, flag for EU AI Act review before shipping.

### Swiss AI Governance
- Switzerland is not an EU member but maintains bilateral agreements that effectively align Swiss AI regulation with EU standards.
- The Swiss Federal Council (Bundesrat) issued AI governance guidelines in 2024 aligned with the EU AI Act risk tiers.
- For Big Bear Engineering: treat EU AI Act compliance as the baseline. Swiss-specific deviations are additive, not substitutive.

---

## Apertus / Innosuisse Angles

### Innosuisse (Swiss Innovation Agency)
- **What it is**: The Swiss federal agency for science and innovation funding. Provides grants for applied research projects, typically in partnership between companies and universities.
- **Relevance**: The multi-agent fleet architecture (Flotilla) has research novelty that could qualify for an Innosuisse collaborative project grant, particularly if partnered with a Swiss university (ETH Zurich, EPFL, or a UAS).
- **Key framing for proposals**: Position Flotilla as applied AI systems research — not a product demo, but a reproducible methodology for managing autonomous AI workforces in compliance with EU AI Act requirements.
- **Grant type to target**: "Innovation project" (CHF 150k–2M, 1–3 years, 50% company / 50% university split).

### Apertus
- **What it is**: Open-source cinema camera project. One of the few fully open-source professional camera hardware ecosystems.
- **Relevance to Robot Ross**: Robot Ross (the painting arm) uses a camera for reference imaging. Apertus hardware or software concepts may be relevant for high-quality visual input to the painting pipeline.
- **Status**: No active integration as of 2026-04. Noted as a potential future hardware partner for the artist pipeline.

---

## The Classical Remix: YouTube Context

- **Channel**: [The Classical Remix](https://youtube.com/@TheClassicalRemix)
- **Content type**: Classical music adapted with modern production.
- **Fleet role**: Agents run analytics pulls (YouTube Data API), generate video metadata, and track ROI vs. ad spend.
- **Key metric shift**: Moving from raw view counts to watch-time-weighted ROI (ad spend vs. estimated minutes watched).
- **Copyright sensitivity**: Classical compositions in the public domain, but specific recordings may have performer rights. Any AI-generated content must use licensed or PD stems.

---

## Big Bear Engineering Positioning

- **Company type**: Boutique AI engineering consultancy.
- **North Star demo**: `api.robotross.art/demo/` — showcases Flotilla to prospective clients.
- **Key differentiator**: Fixed-cost autonomous fleet vs. variable-cost API chatbots. Clients get predictable costs and 24/7 task throughput.
- **Target clients**: Engineering teams that want to augment with AI agents but lack the infrastructure to do so reliably.
