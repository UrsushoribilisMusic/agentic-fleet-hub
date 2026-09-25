# DECISION BRIEF — Canis Dog-Avatar UI/Animation States

_Flotilla Council first run, 2026-09-25. 4 role proposals + 4 skeptical revisions, synthesized. Awaiting Miguel's approval before any execution tickets._

---

# CANIS Dog Avatar — DECISION BRIEF (Council Synthesis, dev-ready)

*Merges the four revised council proposals (Disposition, Idle, Action/Playful, Feasibility). Where the council genuinely disagreed, the resolution is stated and the dissent is preserved as a noted trade-off. Target: Apertus hackathon gated demo, Oct 1–16 2026. Build platform: SwiftUI + Rive on-device, alongside MLX Swift inference.*

---

## 1. Avatar behavior model (one paragraph)

The dog is composited from **three layers with strict precedence: Action/System (highest) → Disposition (middle) → Idle (base).** A deterministic app event (chewing a fed document, retrieving, responding, error, cooling) always owns the screen; the **Disposition Lens** paints the dog only while the model is actively working and no action state is playing; **Idle** plays otherwise. Disposition is modeled as a **continuous 2D emotion space (arousal × valence)** with a small set of **named anchor poses** that Rive blends between as the point moves — *not* a flat enum of hard-switched states. The engine emits this signal at a fixed low rate (~8 Hz, never per-token), **damped and hysteresis-gated** so a noisy Jacobian reading can't make the dog thrash; if the reading is weak/untrustworthy the dog falls through to Idle rather than inventing a mood. The whole system runs on a lightweight 2D vector rig kept deliberately off MLX's heavy GPU path, with a framerate governor that freezes avatar work during token generation. The unifying metaphor is physical and warm (Pebbles-inspired): **every async operation is something the dog does with a bone** — eat it (ingest a doc), fetch it (RAG retrieval), ponder it (thinking), bring it to your feet (answer), or fail to chew it (error).

---

## 2. Consolidated STATE TABLE

Priorities: **P0** = hackathon-demo minimum (build first). **P1** = high value, add next. **P2** = polish / optional.

Feasibility notes assume **Rive** primary (see §3). "Overlay" = the §disposition vector multiplies onto this state's pose live.

### Engine → UI contract (build FIRST — not a state, but everything depends on it)
Engine emits at **~8 Hz** a vector: `arousal` [0..1] (calm↔activated), `valence` [0..1] (wary/uncertain↔confident), `magnitude` [0..1] (reading confidence). UI applies: **damping** (`smoothed += (target−smoothed)*0.2`), **hysteresis / min-dwell ≥0.5 s** before the dominant anchor switches, and a **floor: if `magnitude` < 0.25, show no disposition → fall to Idle.** This contract is an **engine deliverable**; it is the single difference between "alive" and "broken."

| State | Category | Trigger | Animation (1–2 lines) | Priority | Feasibility note |
|---|---|---|---|---|---|
| **curious** | Disposition | arousal high, valence mid | Ears up + one cocked, ~15° head-tilt with ear-flick, weight forward, slow wide tail wag. The engaged "listening" face. | P1 | Anchor pose in 2D blend; overlay on active state. |
| **confident** | Disposition | arousal mid, valence high | Tall square stance, head high & level, slow proud tail swish, single settle-nod. Still & tall. | P1 | Anchor pose. |
| **uncertain** | Disposition | arousal low–mid, valence low | **Asymmetric ears (one up, one back)** — the whole tell; weight back, head tilted+dipped, one paw half-raised, small stop-start tail. | P1 | Anchor pose; asymmetric ears cheap + unmistakable. |
| **focused** | Disposition | arousal mid, valence mid, low motion | Ears pinned forward, gaze locked, body still, tail minimal/rigid with tip-quiver. "On the scent." | P1 | Anchor pose; distinct via body-height/stillness. |
| **idle_breathe** | Idle | no signal, baseline | Slow breathing ~0.25 Hz, occasional slow blink, tiny weight-shift. Always-on canvas. | **P0** | Always running; degrades to this under Reduce Motion / thermal. |
| **idle_lookAround** | Idle | idle scheduler | Head L, hold, R, return; ears track. Scanning, present. (~most common.) | **P0** | One-shot ~2 s → returns to neutral base. |
| **idle_sniff** | Idle | idle scheduler | Nose dips, 3–4 sniff twitches, lifts. The "doggy" signature. | **P0** | One-shot ~1.5 s. |
| **idle_earFlickShake** | Idle | idle scheduler | Quick ear/head shake. Cheap, high alive-per-frame. | P1 | ~1 s. |
| **idle_stretchYawn** | Idle | idle scheduler; biased when arousal low | Yawn + small stretch. **Absorbs old "tired."** | P1 | ~2 s. Bias low-arousal, not a disposition. |
| **idle_scratch / paw-groom** | Idle | idle scheduler (rare) | Hind-leg ear scratch or front-paw lick. Candid personality. | P2 | ~2.5 s. |
| **idle_settle / sleep** | Idle | prolonged inactivity | Sit → lie down → near-static, minimal breathing. Doubles as **battery win** (drop to low fps). | P2 | Replaces expensive dual-base "lie_down"; near-static frame. |
| **tail_chase** | Idle (special) | very rare, cooldown ≥90 s | 2–3 spins, stop, slightly sheepish. Pure charm. | P2 | 2D puppet: fake spin / play-bow substitute — no true back view. |
| **flop_relax** | Idle (special) | rare, cooldown ≥60 s | Relaxed flop onto side — the dog getting comfy. **No sigh/guilt-trip framing.** | P2 | Warm, on-brand; not "you still there?". |
| **reengage / listening** | Action | text-field focus, keyboard, tap on avatar/input, app foreground, dictation start | Fast blend-out of any idle beat → perk toward user, ears prick, one wag burst, small paw-lift → settle attentive. Greeting depth scales with prior idle duration. | **P0** | Owns ALL perk-up (removes idle "false-alarm" bug). Interrupts within ~150 ms. |
| **feed-bone / chew** (HERO) | Action | document imported for ingestion | Doc icon slides in → morphs to bone → sniff+grab → chew loop (~2 Hz, content half-closed eyes) until `done` → gulp + lip-lick + tail-thump; bone drops onto a **visible RAG "bones" stash**. | **P0** | Signature moment — most polish. Duration = ingest time, **indeterminate** (elapsed-time ring, NOT chew-count %). Good sprite-fallback candidate. |
| **retrieve / fetch bone** | Action | RAG retrieval running | Ears perk, nose-to-floor **trail-sniff** along bottom edge, pulls a **bone** (same noun — no "stick") back into frame → hands to respond/deliver. | P1 | Usually <1 s. **If retrieval <250 ms → skip animation entirely** (common case) to avoid enter/exit flash. Dig-variant backlogged. |
| **thinking / generating** | Action | `isGenerating == true` | Head-tilt 12–18°, one ear flops, gaze locks; pondering micro-loop, head drifts to other tilt every ~3 s; optional thought-glow. **Primary Lens showcase** — disposition overlay lives here. | **P0** | Driven by app generation flag (fires even if Lens quiet). Glow pulse from **4 Hz throttled** throughput, never per-token. Enter loop *before* first token to avoid stall. |
| **respond / deliver** | Action | first answer token / answer ready | Leans in carrying the bone → **drops it at the floor line, front-center**, bone morphs into the answer card; sits back, hopeful tail-thump → bridges to Idle. Tail-wag amplitude scaled by `valence`. | **P0** (respond) / P1 (bone→card morph) | One success haptic on drop (the user-facing payoff). |
| **success / praise** | Action | task complete cleanly / thumbs-up | Full-body happy wiggle, ears up, **play-bow**, tongue out, sparkle burst. **Absorbs "playful."** | P1 | **No 360° spin** (2D puppet, extra art) — play-bow gives the joy. Light tap-tap haptic. |
| **error / refusal / can't-do** | Action/System | out-of-scope refusal, ingestion-parse fail, or system error (net/OOM) | Apologetic, never scolding: ears back, small back-step, paw air-shrug / paw-over-nose, soft whine marks, tail *slightly* tucked. **Absorbs old "cautious"** (policy signal, not a disposition). Ingestion-fail = spits a cracked/greyed bone. | P1 | Auto-recover to Idle ~2 s. Soft double-tap haptic. 3 sub-variants share one apologetic base. |
| **empty knowledge base** | Action/System | first-run, no bones ingested yet | "Hungry, looking around for a bone" — strongest nudge to feed a first document. | P1 | Idle-flavored; strongest onboarding cue. |
| **wake / greet** | Action | app launch / first foreground | Wake-up + stretch + big wag toward user. | P1 | Deeper variant of reengage. |
| **pat** | Action (overlay) | tap/stroke the dog anytime | Additive lean-into-hand + tail wag + eye-squint. **Never `cancel()`s, never interrupts a work loop** — layers on top and releases. | P2 | Highest delight-per-hour; must be additive-only. |
| **cooling** | System | `thermalState` .serious/.critical or low battery | Yawn → lie down → slow breathing, **captioned "cooling down."** **Absorbs old "tired" device case.** | P2 | Honestly labeled so a warm phone ≠ a sad AI. Governor also cuts fps here. |

**Orchestration:** the app owns transitions via a state machine (`Idle → Feed? → Fetch? → Think → Deliver → Idle`); states never self-chain. **Min-display guard:** any loop that would show <0.6 s is either held to one full beat (chew) or skipped (fetch). **`cancel()` during chew:** dog spits the bone → 0.2 s abort pose → Idle (never leave a half-eaten bone). **Busy-gate:** a shared `avatarActivityState ∈ {idle, busy, reacting}` suppresses ALL idle beats while `busy` (no yawning mid-inference). **Haptics only on user-perceivable boundaries:** feed-grab, feed-swallow, deliver-drop, error, praise — never on internal fetch/think transitions.

---

## 3. Recommended tech + handoff structure

**Primary: Rive** (Metal-rendered vector, state-machine driven). Chosen for blend quality (the Lens signal *becomes* an interpolated stance, which Lottie/sprites can only hard-switch), fast single-artist authoring, and tiny footprint next to MLX weights. **2D, off the model's heavy compute path** — but note the corrected risk below.

**Corrected perf model (council consensus):** On iPhone, MLX inference runs on the **GPU** (matmuls dominate; tokenize/sample are light CPU). Rive *also* renders on the GPU — so **GPU contention during generation is the top risk, not CPU.** Rive is lighter than a full render, not free. Manage it directly:
- **Generation governor (the key mechanism):** while `isGenerating == true`, **cap Rive to ~20–24 fps and FREEZE arousal/valence updates** (hold last damped value). A near-still dog during a 3 s generation is invisible; a stalled token is not.
- **Thermal gate (secondary):** at `.serious`/`.critical`, drop to ~15 fps, keep only `idle_breathe` + current pose.
- **Update inputs at ~8 Hz, damped, coalesced to main actor. Never per-token.**
- Idle capped at 30 fps; **all timers stop + render loop yields on background.**
- **Freeze mid-pose if the frame budget is tight** — a dog holding still "to think" reads perfectly fine.

**Reduce Motion (MANDATORY — App Store + a11y):** if `UIAccessibility.isReduceMotionEnabled`, each state resolves to **one expressive still + 150 ms crossfade**; suppress idle beats/specials and overlay motion; keep only slow breathing. Observe the change notification live.

**Whole-approach fallback (real hackathon risk — the team may have no Rive-fluent designer):**
- **Fallback A:** Lottie one-shots, disposition as nearest-anchor discrete swaps (lose the blend "magic," keep the state contract).
- **Fallback B:** sprite-sheet loops per state (cheapest runtime, heaviest authoring/memory; unload off-screen).
- **The engine-facing input contract is identical across all three renderers**, so the engine team is never blocked by the tooling choice.

**Input contract (source of truth — case-sensitive):**
```
CanisSM inputs:
  number  arousal        // 0–100, damped @8Hz, hysteresis ≥0.5s, floor mag<0.25→idle
  number  valence        // 0–100, damped
  number  magnitude      // 0–100, reading confidence (gates disposition)
  boolean isGenerating   // true while MLX decodes (drives thinking loop + governor)
  boolean isEmpty        // no bones ingested yet
  boolean isListening    // user typing/dictating (drives reengage)
  trigger feedBone       // document imported
  trigger search         // RAG retrieval running
  trigger respond        // first answer token
  trigger success        // clean completion
  trigger error          // refusal / parse-fail / system error
```

**Per-state Swift contract:** `enter()` (one-shot ≤0.6 s) · `loop()` (seamless, covers unknown wait) · `exit(result)` · `cancel()` (→0.2 s abort pose) · `applyDisposition(arousal,valence,magnitude)` (interpolated overlay, non-interrupting) · `onTap()` (additive pat, never cancels) · `setReducedMotion(bool)`.

**Handoff structure:**
```
canis-avatar/
  canis.riv                 # artboard "Canis", state machine "CanisSM"
  README-inputs.md          # the input contract above — source of truth
  reference/
    disposition-space.png   # 2D arousal×valence grid, anchor poses marked
    NEUTRAL_BASE.png        # the shared rest pose (see below)
  fallback/                 # only if Rive or a state slips
    bone_chew@2x.png (+ .json)
```
**Staging (fixed for all states):** dog lives in a **fixed 3/4-body frame, centered, shallow floor line at bottom third. The dog never leaves frame** — objects (bone, answer card) enter/exit; the dog does not. **`NEUTRAL_BASE`** = untinted rest pose (sit/stand relaxed, ears neutral, facing user anchor, mid-breath); every idle beat and reengage starts and ends exactly on it. Disposition tint is applied live on top by the compositor, never baked into the handoff pose.
**Naming:** `disp_<name>`, `act_<verb>`, `idle_<verb>`, inputs exactly as spelled above.
**Assets total budget:** target < ~3 MB, 30 fps cap. New props: bone (+PDF/scroll variant), bone-stash, thought-glow, sparkle, cracked-bone, torn-scrap answer-card. Everything else is channel animation off the shared rig. **"Stick" and the Dig-flavor are cut** (tighter metaphor, less art).

**Demo mode:** a single config flag `demoMode: true` (ships in the same tunable JSON as idle weights) that compresses idle-phase timers ~4× and drops special cooldowns to ~20–30 s, plus an optional hidden dev-tap to fire any beat on stage. **Production defaults stay realistic; judges still see the charm.**

---

## 4. P0 hackathon-demo subset (build first, in order)

Infrastructure and the deterministic layer come first — they're high-certainty and don't depend on the engine behaving. The Lens overlay is the product's signature, so wire it the moment the engine emits the vector.

1. **Rig + `NEUTRAL_BASE` + state machine + Reduce-Motion scaffold + framerate governor.** Infrastructure, or every state re-invents it.
2. **`idle_breathe` + `idle_lookAround` + `idle_sniff` + `reengage`/listening.** This alone reads as *alive* (not one loop).
3. **`feed-bone` chew (HERO)** — the signature demo money-shot; give it the most polish.
4. **`thinking` loop** (app-driven `isGenerating`) — most-seen state and the Lens showcase surface.
5. **`respond`/deliver** (bone → answer-card drop).
6. **Disposition overlay wired** — the 4 anchors (curious/confident/uncertain/focused) blended live onto the thinking loop via the §contract. This is what makes the demo say "the AI has a felt state."
7. **`error`** + **`empty knowledge base`** if time — refusal warmth + the onboarding nudge.

**Demo mode ON** for judging so idle personality and specials surface inside a ~30 s look.

---

## 5. Open questions for Miguel

1. **Final disposition axis names.** Council converged on a **2D arousal × valence space with 4 named anchors** (curious, confident, uncertain, focused). Confirm these names and that the engine will emit exactly `arousal`, `valence`, `magnitude`. (The whole handoff is frozen on this.)
2. **Does the engine team own the §contract (8 Hz, damping, hysteresis, magnitude floor)?** This is an *engine* deliverable, not animation. Without it the prettiest dog reads as broken. Who commits to it, and by when?
3. **Rive designer availability.** Is anyone on the small team fluent in the Rive editor? If not, we fall to Lottie/sprites and **lose the blend "magic"** (disposition becomes hard swaps). Decide the primary before day 1.
4. **Ratify `NEUTRAL_BASE`** as the shared boundary pose for all three layers, and confirm the disposition/action layers honor start/end-on-neutral.
5. **User-facing legibility.** Show an optional one-word caption under the dog (`curious`, `chewing`, `cooling down`) + tap-to-explain + a first-run legend? A label-free dog lets users invent meanings; a caption gives them the vocabulary once. (Also settles whether `cooling` is honestly labeled.)
6. **`pat` (§6b) in scope for the hackathon?** Highest delight-per-hour, but must be built as a non-interrupting additive overlay.
7. **Fixed on-screen user-anchor** for `look_around`/`reengage` head-turns — input field, camera, or center?

### Noted trade-offs (dissent preserved, not hidden)
- **7 → 4 disposition states.** The council cut `playful`, `cautious`, `tired` from the Lens set: `playful` is an *event* (relocated to praise/success), `cautious` is a *policy* signal (relocated to error/can't-do), `tired` is a *device/idle* condition (relocated to `idle_stretchYawn` + `cooling`). Trade-off: the Disposition designer argues a noisy real-time lens *can't* cleanly resolve 7 lookalikes and 4 orthogonal states prevent flicker; the Feasibility lead notes each dropped state is also one less pose the small team must author. Dissent on record: the Feasibility lead would have kept `playful` as a 5th blend anchor for richer interpolation — resolved in favor of 4 + event-driven playful to save author time.
- **Idle realism vs demo-ability.** The Idle designer explicitly **disagrees with shortening production idle timers to chase 30 s judges** (it makes the shipped app twitchy). Resolved by **decoupling via `demoMode`** — production stays realistic, demo compresses. Ship both.
- **GPU contention.** Corrected from the Round-1 feasibility framing: MLX saturates the **GPU**, and so does Rive — so the governor must **freeze on `isGenerating`**, not merely gate on thermal state (which triggers too late).
- **Blending is not "free."** Weighted-pose blending requires the Rive state-machine build cost; the sprite fallback has *no* blend (opacity crossfade only). Budget accordingly.