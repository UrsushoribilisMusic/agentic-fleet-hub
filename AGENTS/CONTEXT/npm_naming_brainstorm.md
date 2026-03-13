# npm Package Name Brainstorm -- AgentFleet Scaffolder

**For:** Claude Opus (big sister) brainstorm session
**Context:** We are releasing an open-source npm scaffolder that bootstraps a multi-agent AI engineering workspace. The install pattern is `npx create-<name>`. The tool generates MISSION_CONTROL.md, agent mandate files, Kanban bridge scripts, vault scripts, and a fleet management web dashboard.

---

## Product in One Line

A zero-install scaffolder that sets up a coordinated multi-agent engineering team (Claude, Gemini, Codex, Mistral) with shared memory, vault-first security, and a GitHub Kanban bridge -- in under two minutes.

---

## Constraints

- npm `create-*` pattern (used as `npx create-<name>`)
- Must be available on npm (not already taken)
- Target market: engineering teams, EU/DACH primary
- Must survive a DACH slang check (lesson learned: "Mist" = Scheiße in German)
- No AI hype words (no "super", "ultra", "smart", "magic")
- Ideally pronounceable in English AND German
- Shorter is better -- this will appear in blog posts and README headers
- Plain ASCII only (no hyphens in the spoken name if avoidable)

---

## Working Name (Current Default)

**`create-agentfleet`**
- `npx create-agentfleet`
- Pros: descriptive, obvious, clean
- Cons: two words, slightly generic, "agentfleet" is one unhyphenated word that might look awkward

---

## Name Directions to Explore

### Direction 1: Fleet metaphor
These names lean into the multi-agent coordination angle.

| Name | npx command | Notes |
|---|---|---|
| agentfleet | `npx create-agentfleet` | Current working name |
| fleetkit | `npx create-fleetkit` | Short, toolkit feel |
| fleetbase | `npx create-fleetbase` | "base" implies foundation |
| fleetcore | `npx create-fleetcore` | Engineering credibility |
| agentcrew | `npx create-agentcrew` | "crew" is warm but informal |
| crewbase | `npx create-crewbase` | Risk: Crewbase/Crunchbase confusion |

### Direction 2: Mission control metaphor
Leans into the MISSION_CONTROL.md concept at the center of the system.

| Name | npx command | Notes |
|---|---|---|
| missionctl | `npx create-missionctl` | Nerdy/Unix suffix vibe |
| missionfleet | `npx create-missionfleet` | Long but explains itself |
| controlbase | `npx create-controlbase` | Flat, forgettable |
| hubctl | `npx create-hubctl` | Very technical, short |

### Direction 3: Discipline / precision angle
Plays to the "Swiss precision, not AI hype" brand positioning.

| Name | npx command | Notes |
|---|---|---|
| fleetops | `npx create-fleetops` | DevOps crossover appeal |
| agentops | `npx create-agentops` | Risk: agentops.ai already exists as a product |
| squadops | `npx create-squadops` | Military feel, not Swiss |
| crewops | `npx create-crewops` | Clean, short |

### Direction 4: Shorter / more brandable
Less descriptive, more memorable.

| Name | npx command | Notes |
|---|---|---|
| flotilla | `npx create-flotilla` | Beautiful word, naval fleet = correct metaphor, pronounceable in DE/FR/EN |
| armada | `npx create-armada` | Strong, but Spanish naval history baggage |
| quorum | `npx create-quorum` | Elegant, implies multi-party agreement, already used in blockchain |
| squadron | `npx create-squadron` | Military not engineering |
| convoy | `npx create-convoy` | Implies movement/delivery not coordination |

### Direction 5: Compound action names (create-X implies X is the output)
The name after "create-" should feel like what you're creating.

| Name | npx command | Notes |
|---|---|---|
| agentspace | `npx create-agentspace` | Risk: Google Agentspace is a real product |
| agentbase | `npx create-agentbase` | Clean, but "base" feels like a database |
| agentyard | `npx create-agentyard` | Unusual, memorable |
| agentport | `npx create-agentport` | Port implies gateway/ingress |
| agentdock | `npx create-agentdock` | Docker resonance -- good or bad? |

---

## Favourite Candidate (Clau's pick before brainstorm)

**`flotilla`** -- `npx create-flotilla`

Reasons:
- A flotilla is a coordinated fleet of smaller vessels working together -- perfect metaphor
- Pronounceable in English, German, French, Spanish (all EU languages)
- No obvious slang issues in DACH
- Not generic AI/tech vocabulary -- stands out
- Short (8 letters)
- Does not exist as a major npm package (check before committing)
- Pairs well with the brand: "Big Bear Engineering -- flotilla for your AI workforce"

---

## Questions for Opus

1. Which direction resonates most for a DACH B2B engineering audience?
2. Does "flotilla" test well or does it feel too naval/niche?
3. Is there a direction we haven't explored?
4. Should the package name match a potential agentegra.com product name, or can they diverge?
5. What is the optimal character count for an npx package name in terms of memorability?
6. "agentfleet" vs "fleetops" vs "flotilla" -- forced ranking?

---

## DACH Slang Checks Needed

Before committing to any name, run through:
- German slang / double meanings
- Swiss German (Zurich dialect specifically)
- Austrian German
- Known false friends between EN and DE

Already learned: "Mist" (EN: haze/mystery) = "Scheiße" in DE/CH. Renamed Mist to Misty before public use.
