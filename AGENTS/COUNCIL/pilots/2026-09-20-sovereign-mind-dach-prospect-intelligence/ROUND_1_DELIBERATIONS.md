# Round 1 Deliberations: Sovereign Mind DACH Prospect Intelligence

Goal: create a prospect-intelligence campaign for Sovereign Mind focused on DACH machine builders, producing a ranked target list and reusable dossier schema for outreach.

## Agent 1: GTM Planner

### Recommendation

Start with a narrow customer-conversation wedge: DACH packaging, food/pharma processing, and adjacent process-line machine builders with large installed bases and service-heavy customer relationships.

The pain is easier to discuss without leading with "AI": customers need to keep complex lines running with fewer experienced operators, higher uptime expectations, and more complex service knowledge.

### Proposed Segmentation

- Tier 1: packaging and food/pharma process-line builders.
- Tier 2: plastics, converting, and specialty production equipment.
- Tier 3: machine tools and precision manufacturing equipment.
- Tier 4: robotics and automation integrators.

Seed benchmark accounts: Krones, Syntegon, MULTIVAC, BOBST, GEA, Bühler, ENGEL, KraussMaffei, Windmöller & Hölscher, Brückner Maschinenbau, TRUMPF, DMG MORI, GF Machining Solutions, Bystronic, Starrag, KUKA, Festo, B&R/ABB.

### Ranking Criteria

- Installed-base service intensity.
- Public customer-pain visibility.
- Dossier evidence richness.
- Conversation access.
- Urgency signal.
- Sovereign Mind fit for knowledge-heavy, traceable workflows.
- Outreach safety.

### Dossier Fields

- Company name, country, headquarters, segment, core machines, customer industries.
- Installed-base/service indicators.
- Public pain signals.
- Customer-facing promises with URL.
- Digital/service initiatives.
- Parts/support/training/modernization offerings.
- Compliance/regulatory hooks.
- Recent business pressure signals.
- Likely buyers and possible champions.
- Trigger events.
- Internal-only conversation hypothesis.
- Public-safe outreach facts.
- Source URLs, confidence, next evidence needed, recommended ask.

### Risks

- Too much "AI" language could trigger vendor fatigue.
- Large accounts may already have internal digital-service programs.
- Public sources reveal pain themes, not buying urgency.
- CEO outreach may be too broad.

### Evidence Cited

- Krones Lifecycle Service: https://service.krones.eu/kse-en/
- Syntegon: https://www.syntegon.com/
- VDMA skilled workers topic: https://www.vdma.eu/en/skilled-workers

### Confidence

Medium.

## Agent 2: Research Operations Architect

### Recommendation

Build the campaign as a public-evidence research operation, not a generic lead list. The first deliverable should be a ranked shortlist where public evidence suggests customer-facing pain: service bottlenecks, commissioning delays, aftermarket complexity, multilingual documentation burden, knowledge loss, spare-parts friction, operator training, or global support scaling.

### Workflow

1. Define ICP slices around complex installed base, configurable machinery, international customers, service-heavy model, documentation burden, or dealer/service partner networks.
2. Build longlist from public directories, association pages, trade-fair lists, LinkedIn public company pages, and company websites.
3. Capture public evidence only.
4. Code evidence into pain themes.
5. Score targets while separating pain evidence from fit hypothesis.
6. Produce ranked Tier 1, Tier 2, and Tier 3 lists.
7. Create dossiers for Tier 1 and Tier 2 targets.

### Source Ledger Design

- `source_id`
- `company_name`
- `source_url`
- `source_type`
- `publication_date`
- `accessed_date`
- `quoted_fact`
- `paraphrased_fact`
- `pain_theme`
- `confidence`
- `public_copy_allowed`
- `notes_on_claim_limits`
- `researcher`
- `last_verified_date`

### Scorecard

Score 0-5, with customer pain visibility and conversation accessibility double-weighted:

- Customer pain visibility.
- Installed-base complexity.
- Aftermarket importance.
- International support burden.
- Knowledge intensity.
- Timing signal.
- Conversation accessibility.
- Sovereign Mind relevance.

### QA Rules

- No unsupported pain claim.
- No "they need AI" language.
- No private, scraped, or non-public source claims.
- Public-facing copy may use only facts marked `public_copy_allowed = yes`.
- Every score must cite source IDs.
- Tier 1 needs at least two independent public signals.
- Separate quote, paraphrase, and interpretation.

### Evidence Cited

- VDMA: https://www.vdma.eu/
- FDFA Switzerland MEM overview: https://www.aboutswitzerland.eda.admin.ch/
- Advantage Austria: https://www.advantageaustria.org/

### Confidence

Medium-high on the research architecture; medium on ICP prioritization before Sovereign Mind's strongest proof point is clarified.

## Agent 3: Skeptic / Risk Reviewer

### Recommendation

Proceed, but frame the work as a customer-conversation campaign, not a prospect list for AI. The safest wedge is: DACH machine builders are under pressure to protect margins, reduce service friction, and create credible digital/service revenue without adding compliance or integration risk.

The first campaign objective should be 8-12 exploratory conversations with service, aftermarket, product, digital, or operations leaders.

### Guardrails

Allowed:

- "Your public materials suggest you sell/service connected machinery."
- "Many machine builders are under margin, service, and demand pressure."
- "We are speaking with DACH machine builders about where service knowledge, documentation, and machine data create friction."
- "We are not assuming this is a priority for you; we are testing whether the pattern is real."

Avoid:

- "You are struggling with X."
- "Your service team is overloaded."
- "Your customers are demanding AI."
- "We can reduce downtime by Y%."
- "You need sovereign AI."
- Anything implying access to internal data, machine telemetry, customer contracts, or financial stress beyond public reporting.

### Ranking Criteria

Rank by observable signals, not assumed pain:

- Installed-base/service business.
- Connected-product offerings.
- Customer complexity.
- Outreach path quality.
- Conversation relevance.
- Timing signals.
- Evidence quality.

Do not rank by "AI readiness" unless the company explicitly discusses AI or digital service initiatives.

### Risks

- False positives from marketing language.
- Category confusion if "Sovereign Mind" sounds abstract.
- Compliance concerns around machine data, AI, and EU rules.
- Over-personalization can feel intrusive.
- English-only outreach may underperform in DACH.

### Evidence Cited

- VDMA economic situation: https://www.vdma.eu/en/economic-situation
- Swissmem recovery note: https://www.swissmem.ch/en/media-corner/media-releases/recovery-in-the-tech-industry-remains-fragile.html
- EU Data Act overview: https://digital-strategy.ec.europa.eu/

### Confidence

Medium.
