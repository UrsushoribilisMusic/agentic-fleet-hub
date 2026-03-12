# Agentegra — Project Briefing for AI Assistants

*Last updated: March 9, 2026. This document summarizes all work done on the Agentegra project and the current state of all assets. Hand this to any AI assistant to get up to speed instantly.*

---

## Who We Are

**Founder**: Miguel Rodriguez
**Company**: BigBear Engineering GmbH — Mettmenstetten, Switzerland
**Product brand**: Agentegra
**Contact**: Miguel@bigbearengineering.com
**Website**: agentegra.com (hosted on Cloudflare Pages)
**Seed ask**: CHF 250,000
**Upcoming event**: Startup Days Bern, May 21, 2026

---

## What Agentegra Builds

Agentegra provides **sovereign agentic infrastructure for European industry** — specifically for DACH (Germany, Austria, Switzerland) manufacturing and industrial companies. The core value proposition is that AI agents can run fully on-premise or on private cloud, with no customer data leaving the customer's perimeter.

### The Three-Layer Architecture

**Layer 1 — The Artisan** (standalone autonomous agent)
Runs local LLMs (Mistral, Apertus 7B Swiss open-weights from ETH/EPFL) on-premise or private cloud. Data sovereign — air-gapped if required, 24/7. Zero data leaves the customer's perimeter.

**Layer 2 — The Salesman API** (protocol-agnostic agentic commerce bridge)
Normalizes Virtuals ACP, Google AP2, A2A, MCP into a single endpoint. Human and AI buyers use the same endpoint. Agentic commerce runs on local models only — never cloud. Implement once, interact with many.

**Build System — The Development Fleet** (not a product layer — it's how the products are built and maintained)
Multi-agent fleet builds enterprise software at agent speed. GitHub workflow, human Switchboard oversight. Weeks compressed to days — fully auditable. EU AI Act compliant development pipeline.

*Website section intro: "Two sovereign product layers — built and upgraded by an agent development fleet at founder economics."*

### Why EU AI Act Matters for the Sales Pitch

The EU AI Act creates a hard deadline: companies building or deploying **agentic commerce clients** must comply from **August 2026**. This is a direct sales window — Agentegra makes compliance architectural, not retrofitted. The pitch is not about fear of fines; it's about the fact that sovereign infrastructure is the only architecturally clean way to comply.

---

## Live Demo: Robot Ross

The technology is live and running at **robotross.art** — a robot arm that paints on demand.

- **Hardware**: Mac Mini M4 + Huenit robot arm
- **LLM**: Apertus 7B (Swiss open-weights, ETH/EPFL) — fully local, narrates in the style of Bob Ross, generated entirely on-device
- **Agent commerce**: Virtuals ACP + Shopify webhooks (HMAC-signed), Bearer token 64-char
- **Live API**: api.robotross.art (OpenClaw Salesman API, port 8787, Caddy TLS proxy)
- **Architecture flow**: Salesman API → orders.json grid → Mac Mini M4 Artist Worker → YouTube Short proof at /proof/:id
- **Wall of Fame**: 8×8 grid (64 slots, A1–H8), 20% overwrite rule
- **Audit trail**: visible at api.robotross.art
- **YouTube demo**: https://www.youtube.com/embed/iyONVpFg9cA

The pen can be replaced with a drill bit or any manufactured good — this is the manufacturing demo that mirrors the actual product.

---

## Business Model

**Current (perpetual license)**: CHF 100–200k one-time license per deployment + 18–22% annual maintenance & support + CHF 15–30k consulting entry that converts to license in 3–6 months.

**Unit economics**: CHF 120–150k avg deal value Year 1, CHF 200–250k 5-yr customer LTV. Target: 2–3 deals signed in Year 1, 5–8 deals Year 2.

**Future layer (Series A story)**: First projects mature the codebase — pilot customers pay a project lump sum, not per transaction. Subsequent customers: SaaS model for those who prefer not to pay upfront. This is the scalability story for Series A.

---

## Team

### Miguel Rodriguez — Founder & CEO

- 35+ years software engineering in machinery and industrial automation
- Previous startup exit (2017) — full cycle from build to transaction
- Komax AG (7 years) — IoT, digital marketplace, industrial protocol design
- Next2OEM / Audi HQ (at Komax) — Lead definition of OPC40570 Companion spec
- Klepsydra / ESA — certification of AI inference engine for space applications
- BigBear Engineering GmbH — established Swiss market consulting track record
- First salesman: 35 years of DACH machinery relationships = the pipeline

### The Development Fleet

- Claude Code + Gemini CLI + human Switchboard
- Delivers at team velocity, founder economics
- Live platform: designed, built, operational

### Commercial Co-Founder (open position)

- Joins to scale — search for first customers ongoing
- Automation veteran
- DACH C-suite relationships at scale
- Equity + co-investment welcome

---

## Startup Days Bern Application (submitted)

All 5 sections completed (deadline March 15, 2026):
1. Team description (1,487 chars)
2. Project nutshell (340 chars)
3. Startup overview — problem/solution/USP/technology (1,987 chars)
4. Target market, market potential, business model (1,998 chars)
5. Funding info

Supporting links: LinkedIn + Robot Ross YouTube video + robotross.art. Pitch deck v6 attached at time of submission.

---

## Current Asset Versions

### Pitch Deck

**Current**: `Agentegra_Pitch_v8_March2026.pptx` — 12 slides
**Location**: `Claude/agentegra/` folder

v8 changes (March 9, 2026):
- Slide 3: Removed "HIGH RISK" framing — reworded as sales opportunity around August 2026 agentic commerce compliance deadline
- Slide 4: Layout restructure — Orchestration + Salesman API side-by-side on top; Development Fleet full-width foundation at bottom
- Slide 7: Business Model FUTURE LAYER split into two sentences — lump sum for pilots, SaaS for subsequent customers
- Slide 8: Traction — EU AI Act moved to top of Market Signal; LinkedIn reworded (organic traction, no subscriber count); Founder Track updated (OPC40570, ESA certification)
- Slide 11: Team — OPC UA renamed, ESA reworded, "first customers ongoing" (not closed), removed SAP/Siemens
- Slide 12: Closing — newcomers URL removed

v7 changes (March 9, 2026, from NotebookLM critique):
- Regulatory Catalyst: reframed deadline from fear to agent commerce arrival
- Solution: Claude/Gemini/Codex added for cloud-safe code gen; Mistral + Apertus named
- Business Model: pilot lump sum vs SaaS framing introduced
- Team: subtitle "A founder who closes the first deals"

### Pitch Script / Speaker Notes

**Current**: `Startup_Days_Pitch_Agentegra_v10_March2026.docx`
**Location**: `Claude/agentegra/` folder

v10 matches v7 deck: all 5 NotebookLM feedback points incorporated. May need v11 update to match v8 deck changes.

### Website

**Location**: `Claude/agentegra/site/` — 5 HTML pages + css/ + js/ + images/
**Pages**: index.html, robotross.html, fleet.html, faq.html, contact.html
**Deployment**: Cloudflare Pages → agentegra.com

Current state of index.html solution section (session 3): Layer 1 (The Artisan) → Layer 2 (The Salesman API) → Build System (The Development Fleet, dashed border, 72% opacity, visually demoted). Build System is last — it is explicitly "not a product layer."

Other notable website changes made in Claude sessions:
- robotross.html: context section added explaining the pen = drill bit analogy; Apertus 7B described as narrating on-device; Wall of Fame changed from 10×10 to 8×8
- fleet.html: CRM POC case study added (28 tickets, zero human dev time)
- styles.css: dark panel fix applied (`.light .dark-panel` override)

---

## Brand & Design

**Palette**: MINT=#EDF4F5, DARK=#0C1C28, TEAL=#0A7A6F, TEAL2=#159988, BORDER=#B8D4D6
**Fonts**: Consolas / JetBrains Mono for numbers, Calibri / Inter for body
**Design inspiration**: Virtuals.io aesthetic (clean, dark, teal accents)
**Logo**: Geometric "A" — two dark navy legs, teal crossbar (protocol bridge), three teal nodes (apex + two crossbar endpoints). SVG + PNG/JPEG exports available.
**Brand assets**: `Claude/agentegra/brand/` — icon.svg, icon-dark.svg, logo.svg, logo-dark.svg, logo.png, logo.jpg, logo_dark.png, logo_transparent.png, icon_512.png

---

## File Structure in Claude Folder

```
Claude/agentegra/
├── agentegra.md                          ← this file
├── SESSION_MEMORY.md                     ← technical session log (for Claude Cowork)
├── Agentegra_Pitch_v8_March2026.pptx    ← current deck
├── Agentegra_Pitch_v7_March2026.pptx    ← previous version
├── Agentegra_Pitch_v6_March2026.pdf     ← v6 export (submitted to Startup Days)
├── Startup_Days_Pitch_Agentegra_v10_March2026.docx
├── site/                                 ← full website source
│   ├── index.html
│   ├── robotross.html
│   ├── fleet.html
│   ├── faq.html
│   ├── contact.html
│   ├── css/
│   ├── js/
│   └── images/
└── brand/                                ← logo & icon files
```

---

## What's Left To Do

- Deploy website to Cloudflare Pages (hand off to Claude Code — git push agentegra.com)
- Potentially update Word doc v11 to match v8 deck (EU AI Act framing, OPC40570, ESA, first customer search)
- Prepare Robot Ross for live demo at Startup Days (May 21, 2026)
- Outreach to DACH industrial contacts for first pilot conversations
- Find Commercial Co-Founder (automation veteran, DACH C-suite network)
