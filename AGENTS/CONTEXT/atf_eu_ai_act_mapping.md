# EU AI Act Mapping Metadata for Agentegra ATF Wiki Pages

## Overview
This document defines the metadata/frontmatter fields needed to map wiki content to relevant EU AI Act obligations. The goal is to ensure that the compiled wiki is not just descriptive but also compliance-oriented.

## Metadata Schema

### Core Fields
- **`eu_ai_act_obligations`**: List of relevant EU AI Act obligations (e.g., transparency, traceability, record-keeping, human oversight).
- **`compliance_theme`**: High-level theme (e.g., "Transparency", "Traceability", "Human Oversight").
- **`provenance`**: Source files or log segments that support the content.

### Example Fields
- **`transparency_level`**: Level of transparency provided (e.g., "High", "Medium", "Low").
- **`traceability_links`**: Links to related logs or documents for traceability.
- **`human_oversight_notes`**: Notes on human oversight requirements or mechanisms.

## Examples

### Example 1: System Architecture Page
```markdown
---
eu_ai_act_obligations:
  - transparency
  - traceability
compliance_theme: Transparency
traceability_links:
  - "/logs/mexico_wood_marking/run_20260401.log"
  - "/docs/architecture.md"
---

# System Architecture

This page describes the overall architecture of the RobotRoss system.
```

### Example 2: Operational Log Page
```markdown
---
eu_ai_act_obligations:
  - record-keeping
  - human_oversight
compliance_theme: Record-Keeping
human_oversight_notes: "Logs are reviewed daily by the operations team."
---

# Operational Logs

This page contains logs from the Mexico wood-marking runs.
```

### Example 3: Compliance Summary Page
```markdown
---
eu_ai_act_obligations:
  - transparency
  - traceability
  - record-keeping
  - human_oversight
compliance_theme: Compliance Summary
provenance:
  - "/docs/compliance.md"
  - "/logs/mexico_wood_marking/run_20260401.log"
---

# Compliance Summary

This page summarizes the compliance status of the RobotRoss system.
```

## Implementation Notes
- The metadata schema is designed to be lightweight and easy to maintain automatically.
- Agents should populate these fields when generating or updating wiki pages.
- The schema should be flexible enough to accommodate future changes in regulations.

## References
- [EU AI Act](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52021PC0206)
- [EU AI Act Compliance Guide](https://www.europa.eu/youreurope/business/dealing-with-customers/product-requirements/ai-act/index_en.htm)
