# ROUND 2 — Critique & Revision (skeptical peer pass)

## Critique

**1. The whole brief assumes an animation runtime it never names — this is the single biggest risk.** "Blend base→beat over 250 ms," "`dispositionTint` scales base pose offsets," "additive tint inherited by beats" all presuppose a *skeletal rig with runtime additive blending*. SwiftUI has none of this natively. The real options are Rive (state machine + blending — the only one that does everything here), Lottie (poor runtime pose blending), or sprite sheets / AI-baked frames (cheapest to produce, but **cannot pose-blend or tint at all** — only opacity crossfade). A small hackathon team will most likely reach for baked frames or Lottie, in which case half this document (tinting, additive blends, delta-animation reuse) is physically impossible. Round 1 must pick the runtime, or scope collapses on day one.

**2. Disposition-tint contradicts the "produceable quickly" constraint.** If there's no additive rig, tinting the base by mood means baking separate variants per disposition — an asset explosion. And it contradicts the shared-pose contract (point 3). Pick one: a live rig with tint offsets, OR discrete disposition pose-swaps with **no** idle tint for Round 1.

**3. The `NEUTRAL_BASE` contract is self-inconsistent and assumes compliance you don't own.** You say every beat begins/ends on NEUTRAL_BASE, but you also say the base is *continuously tinted by disposition*. Then the start/end pose is not neutral — it's tinted — so the handoff to the disposition layer lands on a moving target. Also, you assert "per the other councilors" that disposition/action states honor the same neutral. You don't control that. Define the pose precisely as a spec, don't assume adoption.

**4. `perk_up` as a random idle beat is a false-alarm bug, not a feature.** A dog that snaps alert "heard something" when nothing happened trains the user to distrust the signal, and it semantically collides with `reengage` (which also perks up toward the user). Reserve perk-up for actual events/return. If you want idle alertness, make it self-directed (watches an imaginary butterfly, *away* from the user) so it can't be mistaken for "I noticed you."

**5. The timing model kills demo-ability — a real tension, not a nit.** Deep idle at 90 s, `tail_chase` cooldown ≥5 min "never twice/session." Hackathon judges look for ~30 s. Your signature delight moments and your best "settled in" state will **never be seen by the people you're building the demo for**. Idle realism and demo-ability are in direct conflict here and the proposal only optimizes for the former.

**6. `lie_down` as a second sustained base roughly doubles the base-state and transition workload** (settle-in, lying-base loop, head-lift-while-lying, `stand_up`, plus the reengage variant). For a time-boxed team this is the most expensive single item and it's mid-priority. It should be explicitly late-tier, or reframed as a battery *win* (a sleeping dog = near-static frame).

**7. Eight beats + two specials + two bases + reengage is too many; the doc already admits only four ship first.** Be honest up front: name the minimum viable set (~4) and mark everything else optional, rather than presenting 13 states and burying the cut list at the bottom.

**8. Two feasibility/UX items are under-weighted, not just "open questions":**
- **Sound:** random dog noises (yawn/sniff/sigh) from an idle phone in someone's hand or pocket is annoying/embarrassing, not charming. This is a default decision (silent idle), not a budget question.
- **Device-motion / proximity reengage** contradicts the low-power claim (CoreMotion polling) and adds complexity. Mark it cut, not "optional/nice."

**9. Missing states that fall inside "ambient life":**
- **iOS Reduce Motion** is unaddressed. A perpetually-animating dog must degrade to slow breathing / static or it's an accessibility fail and an App Store risk.
- **Busy-but-not-idle gate.** While the model is *generating* (active work, several seconds), it's neither idle nor a discrete action. The doc excludes action states but never says "suppress idle beats during work." Without that gate the dog will play a yawn mid-inference. Define the gate even if the animation belongs to another councilor.
- **Battery/backgrounding:** confirm all timers stop on background and the render loop yields; ideally a deep-sleep static frame to let the screen/GPU idle.

**10. Tone risk in `sigh_flop`.** "You still there?" / dramatic flop reads as the app being *bored with the user* — mildly passive-aggressive, off-brand for a warm Pebbles-inspired companion. Keep the flop, drop the guilt-trip framing (it's the dog relaxing, not judging you).

**11. Minor:** the anti-repeat "weight →0, recovers over two picks" is over-specified; "don't repeat the last beat" is enough. Ship weights as config (agreed, good).

---

## Revised

# CANIS Dog Avatar — Idle & Ambient-Life States (Round 2)

**Author:** Idle & Ambient-Life Designer (revised after peer review)
**Scope:** The "alive while waiting" layer only. Disposition reactions and action states are other councilors'. This revision fixes the runtime gap, trims the state set, resolves the neutral-pose contract, and adds demo-mode, a busy-gate, and reduced-motion.

---

## 0. Decision the council must make first: the animation runtime

Everything below depends on this. **Recommendation: Rive.** It is the only common iOS-friendly option that supports a state machine, runtime blending, and layered pose offsets (our `dispositionTint`) in a hackathon-sized asset. It also ships tunable inputs the team can wire without touching Swift.

If Rive is rejected, we fall back to **baked sprite/Lottie frames**, and the following features are **dropped, not deferred**, because they're impossible without runtime pose blending:
- `dispositionTint` on the idle base (→ disposition becomes discrete pose-swaps owned by that councilor; idle stays neutral).
- Additive layering of beats over a tinted base.
- Sub-second cross-pose blends (→ replaced by short opacity crossfades).

I'm preserving my disagreement with the optimists here: **do not promise mood-tinted idle unless we commit to Rive.** Pick the runtime in Round 2 or the brief is unbuildable.

---

## 1. `NEUTRAL_BASE` — the one hard contract (defined, not assumed)

- `NEUTRAL_BASE` = the **untinted rig rest pose**: sitting/standing relaxed, ears neutral, facing the user anchor, mid-breath. Exact pose ships as a reference frame + rig file, not prose.
- Every idle beat and `reengage` **must start and end exactly on `NEUTRAL_BASE`** (untinted).
- `dispositionTint` (Rive path only) is a **live offset applied on top of the current frame by whichever layer owns the frame** — it is *not* baked into the pose. So the handoff pose is always the shared untinted neutral; tint is re-applied continuously by the compositor. This removes the Round-1 inconsistency.
- I am **defining** this contract, not assuming the disposition/action councilors adopt it. Council action item: ratify `NEUTRAL_BASE` as the shared boundary for all three layers.

---

## 2. Base states

**`idle_base` (continuous):** slow breathing (~0.25 Hz), subtle ear twitch, occasional slow blink, tiny weight-shift. The canvas.

**`dispositionTint` (Rive only, optional):** single param set (0–1 per axis) scaling base pose offsets — alert raises ears/quickens breath, tired lowers head. If the disposition layer isn't ready, tint = 0 and everything still works. **Dropped entirely on the baked-frame fallback.**

**`idle_sleep` (deep idle only — battery win):** dog fully settled, near-static frame, minimal breathing. Doubles as our power-saver: after very deep idle the render loop can drop to a low frame rate. This *replaces* Round-1's expensive `lie_down` second-base machinery as the default "settled" signal (see §6).

---

## 3. Ambient beats — trimmed to a ranked, honest set

Each is a one-shot (1–3 s) that returns to `NEUTRAL_BASE`. Grouped by ship priority, not presented as one flat list.

**MVP set (build these four first — this alone reads as alive):**

| State | Dur | Looks like | Notes |
|---|---|---|---|
| `look_around` | ~2.0 s | Head L, hold, R, return; ears track | scanning, present |
| `sniff` | ~1.5 s | Nose dips, 3–4 sniff-twitches, lifts | the "doggy" signature |
| `ear_flick_shake` | ~1.0 s | Quick ear/head shake | cheap, high alive-per-frame |
| `stretch_yawn` | ~2.0 s | Yawn + small stretch | time-passing (merged Round-1 yawn + micro-stretch) |

**Second tier (add if time):**

| State | Dur | Notes |
|---|---|---|
| `scratch` | ~2.5 s | Hind-leg ear scratch; candid |
| `paw_lick_groom` | ~2.5 s | Licks front paw; homey |

**Cut / reassigned:**
- `perk_up` as an idle beat — **removed.** Perk-up now belongs *only* to `reengage` and real events (§5), to avoid the false-alarm/collision bug. (If we later want idle alertness, it must look self-directed and turn *away* from the user, explicitly not a "noticed you" pose.)
- `lie_down` alternate-base — **demoted**; superseded by `idle_sleep` (§6).

Anti-repeat rule simplified: **never play the last beat twice in a row.** Weights live in a tunable JSON/plist:
`look_around 24, sniff 22, ear_flick_shake 18, stretch_yawn 14, scratch 12, paw_lick_groom 10`.

---

## 4. Rare specials — kept, but demo-reachable

| State | Prob | Cooldown | Notes |
|---|---|---|---|
| `tail_chase` | very low | ≥90 s (was 5 min) | 2–3 spins, stop, slightly sheepish. Pure charm. |
| `flop_relax` | low | ≥60 s | Relaxed flop onto side. **Reframed:** the dog getting comfy, *not* "you still there?" — no sigh/guilt, on-brand warm. |

Cooldowns cut so a real demo session can actually surface one. Paired with **demo mode** (§7) which compresses these further for judges.

---

## 5. `reengage` — the companion moment (owns all perk-up)

Fires the instant any real return signal arrives. **Triggers:** text-field focus / keyboard, tap on avatar or input, app foreground. **Device-motion / proximity: cut** (battery + complexity vs the low-power mandate).

**Behavior (`reengage`, interrupt-anything, ~1.0–1.4 s):**
1. Fast blend-out (~150 ms) of any active beat, including waking from `idle_sleep`.
2. Perk toward the user anchor: ears prick, one tail-wag burst, small happy paw-lift/bounce.
3. Settle into attentive neutral (ears slightly forward) and hand off to the disposition/action layer.

Greeting depth scales with `idleDurationAtReturn`: back after 5 s → small ear-prick; back after deep idle/sleep → wake-up + stretch + big wag. One tuning param.

---

## 6. Timing, phases, and the demo-ability tension

Idle clock starts on quiet (no input, no active task). Random inter-beat interval, jittered, never fixed cadence.

| Phase | Elapsed (default) | Behavior |
|---|---|---|
| Fresh | 0–20 s | Alert-leaning (`look_around`, `sniff`); longer gaps |
| Settling | 20–75 s | Full pool, balanced; `stretch_yawn`/`groom` rise |
| Deep | 75 s+ | `stretch_yawn` up; `idle_sleep` eligible; specials eligible under cooldown; gaps stretch |

**Real disagreement preserved:** these defaults optimize for *realism*, and they will hide our best moments from 30-second judges. I do **not** think we should shorten the production defaults to chase demos — that makes the shipped app twitchy. Instead, decouple the two via demo mode (§7).

---

## 7. Demo mode (new — required for the hackathon)

A single config flag `demoMode: true` that:
- Compresses phase timers ~4× (Deep idle ~20 s).
- Drops special cooldowns to ~20–30 s so `tail_chase`/`flop_relax` actually appear.
- Optionally exposes a hidden dev tap to fire any beat/special on demand for stage demos.

Ships in the same JSON as weights. Production defaults stay realistic; judges still see the charm.

---

## 8. Busy-gate and hand-off (new — closes the mid-inference gap)

Idle is the **lowest-priority layer.** A shared `avatarActivityState ∈ {idle, busy, reacting}` governs it:
- `busy` (model generating, RAG retrieving, any active task) → **all idle beats suppressed.** The busy/thinking animation belongs to the action councilor; idle only guarantees it stays out of the way. Without this the dog yawns mid-inference.
- `reacting` (disposition/action state playing) → idle yields.
- `idle` → scheduler runs.

`reengage` and any incoming disposition/action state always outrank idle and interrupt within ~150 ms. No idle beat is uncancellable.

---

## 9. Accessibility, sound, and power (were open questions — now decisions)

- **Reduce Motion (iOS):** when set, disable beats and specials; keep only slow breathing (or a static `idle_sleep` frame). Required for App Store and a11y. Non-negotiable.
- **Sound: silent idle by default.** No random sniff/yawn/sigh from a pocketed phone. Audio, if we have budget, is limited to **user-initiated** moments (`reengage` wag, action states) — never ambient. This is a decision, not a question.
- **Power/backgrounding:** all timers stop on background (foreground event drives `reengage`); deep idle drops to `idle_sleep` at a low frame rate to let the GPU/screen idle. Confirm no CoreMotion, no background timers.

---

## 10. Asset & performance budget

- **Rive path:** 1 rig, 4 MVP beats + 2 second-tier + 2 specials + `idle_sleep` + `reengage`, built as blended deltas off `NEUTRAL_BASE`. `dispositionTint` = layered offsets.
- **Baked-frame fallback:** same clips as short sprite/Lottie loops; **no tint, no cross-pose blend** (opacity crossfade only), disposition handled as discrete swaps by that layer.
- State machine + weighted picker reading a tunable config (weights, phase timers, cooldowns, `demoMode`). No per-frame ML, no physics.

**Ship order if time runs out:** (1) `idle_base` + `reengage` + reduce-motion path; (2) MVP beats 1–4; (3) `idle_sleep` + second-tier beats; (4) specials + `dispositionTint`. Tier 1+2 already reads as alive.

---

## 11. Council action items (things I can't decide alone)

1. **Ratify the runtime (Rive vs baked frames).** Determines whether mood-tinted idle exists at all.
2. **Ratify `NEUTRAL_BASE`** as the shared boundary pose for all three layers, and confirm the disposition/action councilors will honor start/end-on-neutral.
3. **Align disposition axis names** before we consider mood-biasing beat *weights* (Round-1's open Q — still deferred; I recommend tint-pose-only for the hackathon, weight-biasing post-hackathon).
4. **Confirm the `avatarActivityState` enum** with the action councilor so the busy-gate has something to read.
5. **User-anchor direction** for `look_around`/`reengage` head-turn — confirm a fixed on-screen anchor (input field or camera) exists.

---

## Critique

Strong bones (keep these): the `ENTER → LOOP → EXIT` grammar, one-layered-rig, disposition-as-overlay, and the core thesis that *every async op is a physical thing the dog does with an object*. That through-line is the proposal's best idea and should survive intact. My objections are about the parts that will bite the animator, the app engineer, or the user.

**1. It ignores half the ask.** Miguel asked for THREE things; this covers only Fun/Action. IDLE (multiple, explicitly) and pure-DISPOSITION states are punted to "other designers" — yet the proposal simultaneously asks the council to lock grammar *for* those states. You can't own the contract and disown the deliverable. At minimum the action brief must define the idle *bridge* and hand the idle designer a filled-in contract, or the handoff has a hole.

**2. `applyDisposition(axis, magnitude)` is asserted, never specified — and it takes the wrong shape.** The Lens emits a *vector* over several axes (curious AND slightly anxious), not one axis. Passing a single `axis` forces the app to pick, with no rule given. And nowhere is there the one genuinely dev-ready artifact the whole thing hinges on: **a table mapping each disposition to concrete channel values** (ear height, tail speed, eye openness, blink rate). Without it, "confident fetch vs anxious fetch = same clip" is a promise the animator can't build.

**3. Disposition update rate is hand-waved, and it will jitter.** On-device Jacobian analysis is not free per token; it lands a few times a second, and its argmax will flip (curious→uncertain→curious). "Devs get one function they can call any time" + a flipping input = a twitching dog. Missing: **smoothing/hysteresis + interpolation** (~200–300 ms lerp, don't switch dominant axis until it's held ~0.5 s).

**4. No reduced-motion path.** iOS "Reduce Motion" is an accessibility requirement and a demo-safety net (judges' phones, screen recordings). Every state needs a static/low-motion fallback pose. Absent entirely.

**5. Two object metaphors fight each other.** The app's whole vocabulary is *bones = your RAG knowledge*. Then §2 retrieval returns a **stick** and §4 delivers a **stick-or-bone**. Retrieval should bring back a **bone** — the same bones you fed. "Stick" is a second noun that dilutes the one metaphor the product is named around. Cut it.

**6. Redundant / over-scoped for a time-box.** §2 ships *two* fetch flavors (Quick + Dig) selected by latency — but on-device retrieval is almost always <1 s, so **Dig may never fire**, yet it doubles the animation work and needs a *ground plane* the UI doesn't have. Backlog Dig. Likewise the §6 **spin**: a 2D skeletal puppet has no back view — a real spin is extra art, not "free." Play-bow gives the same joy for zero turnaround art.

**7. No state machine, no min-display guard, no staging.** The per-state `enter/loop/exit` contract says nothing about *orchestration*: fetch→think→deliver chains, what a `cancel()` mid-chew does to the half-eaten bone, or what happens when retrieval returns in 180 ms (you'd flash enter+exit — visual garbage). And every state says "darts off-frame / trots back into frame / paws the ground" without ever defining the **stage**: is this a fixed bust, a full-body frame, where's the floor? The animator cannot start without that.

**8. Haptic spam.** Haptics on *every* enter and exit means a fetch→think→deliver sequence fires ~3 buzzes in ~2 s. Haptics belong only on user-perceivable boundaries (doc grab, final answer, error, praise), never on internal chained transitions.

**9. `onTap` pat collides with work loops.** Global pat is lovely, but tapping the dog mid-chew or mid-generation — does it interrupt ingestion? Undefined. It must be a *non-interrupting additive overlay*, never a `cancel()`.

**10. Two "progress" claims that don't hold.** (a) "Map ingestion % to chew count" assumes a determinate percentage; streaming chunk+embed often has no reliable total. (b) "Thought-particle pulses in sync with token throughput" implies per-token UI updates — that's main-thread churn and jank. Both should degrade to *indeterminate* (loop until `done`) with any throughput signal **throttled to ~4 Hz**, decoupled from the token callback.

**Minor:** §1 "Sniff" is 0.7 s but the stated ENTER budget is ≤0.6 s (self-violation); "hagent crouch" is garbled; the §2 🦯 emoji is a white cane. Small, but they signal an un-proofed brief going to an external team.

---

## Revised

# Canis — Action & Playful-Moments States (Round-2, Revised)
### Skeptical-peer revision. Scope: action-tied dog states + the disposition-overlay contract that idle/pure-disposition states also consume.

### Design principles (unchanged core, tightened)

1. **One rig, layered.** Shared 2D skeletal puppet: head, ears L/R, eyes+lids (blink), brows, mouth/jaw, tongue, tail, 2 front paws, body bob. ≤ 12 bones. Animators drive *channels*, never sprite sheets. 60 fps on iPhone 12; ≤ 3 simultaneous tweens.
2. **Grammar: `ENTER → LOOP → EXIT`.** Only LOOP repeats and covers unknown wait. ENTER/EXIT are one-shots, **each ≤ 0.6 s** (hard budget — no exceptions this time).
3. **Disposition is an overlay vector, not a clip** (see §0 — now fully specified).
4. **Interruptible, but orchestrated** via a state machine (§7), not free-floating per-state calls.
5. **Perf:** no per-frame texture swaps; particles are cheap faked emitters (≤ ~12 live), not a physics system. Throughput signals throttled to 4 Hz. Haptics only per §7 policy.
6. **Reduced-Motion fallback is mandatory** (§8). If disabled, every state resolves to a single expressive still + crossfade.

### Staging (NEW — read before animating anything)

- The dog lives in a **fixed frame: 3/4-body, seated/standing, centered**, with a shallow implied floor line at the bottom third. **The dog never leaves frame.** Objects (bones, answer card) enter/exit; the dog does not.
- "Fetch" is therefore *nose-dips-off-edge-and-pulls-a-bone-back-into-frame*, not "darts off-screen." "Dig" (backlogged) would need a real floor dig-hole — deferred for that reason.
- Answer card materializes at the **floor line, front-center** (where a real dog drops a toy).

---

## §0. Disposition overlay — the actual contract

The Lens emits a small vector each tick (a few Hz). The app reduces it before it touches the rig:

- **Reduction:** take the **argmax axis**; apply **hysteresis** — don't switch the displayed dominant axis until a new one leads for ≥ 0.5 s. `magnitude` = that axis's normalized strength (0–1).
- **Application:** `applyDisposition(axis, magnitude)` biases three channels; the app **interpolates over 250 ms** to the new targets (no snapping). Overlay multiplies onto whatever action LOOP is running.

**Channel table (dev-ready defaults — animator tunes magnitudes):**

| Axis | Ears | Tail | Eyes/blink | Extra tell |
|---|---|---|---|---|
| curious | forward, high | mid, quick flicks | wide, few blinks | head cranes forward |
| confident | neutral-up, still | slow relaxed sway | steady, slow blink | still head |
| uncertain/anxious | drifting down | fast, shallow, low | narrower, faster blink | small head re-tilts |
| focused | forward, pinned | minimal | locked, rare blink | body still |
| playful | up + one flick | blur-fast wag | bright, quick | micro play-bow bias |
| cautious | back/lowered | low, tucked-ish | half-lidded, watchful | slight backward lean |
| tired | low, heavy | slow drag | heavy slow blinks | occasional yawn |

`magnitude` scales the deviation from neutral, so a *weak* anxious reads as a hint, not a panic. Same table feeds idle and pure-disposition states — one source of truth.

---

## §1. FEED A DOCUMENT — "Chewing the Bone" 🦴 *(signature — build first)*

**Trigger:** file imported for ingestion. Duration = real ingest time (~1–8 s), **treated as indeterminate.**

| Phase | Beat | Timing | Animates |
|---|---|---|---|
| ENTER | Sniff + Grab | 0.0–0.55 s | Doc icon slides in, morphs to bone; nose dips, 2 sniff twitches, one curious wag; head snaps down, jaw closes, small body dip. Bone parents to jaw. |
| LOOP | Chew | until `done` | Jaw ~2 Hz, head bob, ear joggle, eyes half-close content. Seamless ~0.5 s. A faint progress ring fills — **by elapsed-time/indeterminate spinner, NOT by chew count.** |
| EXIT | Swallow | on `done`, 0.55 s | Gulp, lip-lick, tail-thump, blink up to user. Bone gone. |

- **Chew is constant-speed** (calm competence; never speed up = panic). No % faking.
- **Min-display guard:** if `done` fires < 0.6 s after ENTER, still play a single full chew then EXIT (no flicker).
- **Overlay:** *focused* → ears fwd, minimal tail; *playful* → bigger bob, tail between chews.
- **Fail path:** on parse failure, do NOT swallow → route to §5b.
- **Haptics:** ONE medium tap on Grab; ONE success tap on Swallow.
- **Assets:** 1 bone (+ optional PDF/scroll variant). Rig reuse. ~4 poses.

## §2. RETRIEVE — "Fetch a Bone" 🐾 *(single flavor; Dig → backlog)*

**Trigger:** RAG retrieval. Usually < 1 s → snappy. Retrieved knowledge is a **bone** (same noun as feed — no "stick").

- ENTER (0.3 s): ears perk, haunches crouch (anticipation), nose turns to frame edge.
- LOOP (~0.4 s, 0–2 reps): nose-to-floor **trail-sniff** scan along the bottom edge.
- EXIT (0.35 s): pulls a **bone** back into frame, tail high → hands to §3 or §4.
- **Min-display guard:** retrieval < 250 ms → **skip the animation entirely**, go straight to §3/§4 (avoids enter/exit flash). This is the common case; design for it.
- **Overlay:** *confident* → clean single scan; *uncertain* → extra hesitant sniffs, ears lower; *curious* → one extra sniff.
- **No haptic** (internal transition).
- **Assets:** reuse bone. No new rig. *(Dig variant with dirt puffs = backlog: needs a floor dig-hole and doubles animation for a rarely-hit slow path.)*

## §3. THINKING / GENERATING — "Head Tilt & Focus" 🐕 *(build second; primary disposition showcase)*

**Trigger:** generation running. Duration seconds.

- ENTER (0.4 s): iconic **head tilt** 12–18°, one ear flops, eyes lock on user.
- LOOP: pondering micro-loop — slow blink, ear twitch, head drifts to the *other* tilt every ~3 s, faint tail sway. Optional **thought-glow** above head pulsing with generation activity — **pulse driven by a 4 Hz throttled throughput sample, NOT per-token.**
- EXIT: head straightens, bright blink → §4.
- **This is where the Lens is most visible** — the §0 overlay does the heavy lifting live (confident=still, anxious=re-tilts+ear drift, curious=crane, tired=heavy blinks + a yawn ~every 5 s).
- **Anti-monotony:** 3 tilt-hold variants (L/R/up), random on entry.
- **No haptic.**
- **Assets:** thought-glow. Rig reuse. Invest most polish here.

## §4. DELIVER — "Drop It At Your Feet" 🎁

**Trigger:** answer ready.

- ENTER (0.4 s): dog leans toward user carrying the **bone** (from §2, or conjures one for pure-gen).
- CORE (0.45 s): **drops it at the floor line**; bone morphs/expands into the answer card. Small settle.
- EXIT (0.4 s): sits back, looks up, one hopeful tail-thump → bridges to Idle if no user action.
- **Overlay:** *confident* → brisk proud drop; *uncertain* → gentle set-down, glances between card and user (honest low-confidence signal); *playful* → drop + micro play-bow.
- **Haptic:** ONE success tap on CORE (this is the user-facing payoff — the only haptic in the fetch→think→deliver chain).
- **Assets:** bone→card morph (shared). Rig reuse.

## §5. ERROR / REFUSAL — apologetic, never "bad dog" 😕

- **5a Refusal (out-of-scope):** head tilt, one ear up/one down, small back-step, front paw air-shrug ×2, soft whine (raised brow-marks + open mouth), tail *slightly* tucked. Loops once, holds on paw-up.
- **5b Ingestion failed (from §1):** spits bone (head shake), bone lands cracked/greyed, dog paws + sniffs it, looks up ears-back. Reads as "this file didn't work" with no modal.
- **5c System error (network/OOM/crash):** brief startle → sit → single low whine → ears flat → error text shown as a torn scrap the dog nudges forward. Under 1 s; don't wallow.
- **Rules:** always apologetic/confused, never angry. **Haptic:** soft double-tap. Auto-recover to Idle ~2 s. Default *cautious* overlay tint.
- **Assets:** cracked-bone, torn-scrap card, whine brow-marks.

## §6. PRAISE — "Good Dog!" 🎉

- **Trigger:** thumbs-up / positive feedback / task complete.
- CORE (0.8 s): full-body happy wiggle — blur-tail, ears up, **play-bow** (front down/rear up), tongue out, joyful blink, one sparkle burst. **No 360° spin** (2D puppet has no back view = extra turnaround art for marginal gain; play-bow delivers the joy for free).
- **Haptic:** light tap-tap. EXIT → pleased sit → Idle.
- **Overlay:** *playful* amplifies; *tired* → gentler grateful lean.
- **Assets:** sparkle burst (shared with §1). Rig reuse.

## §6b. PAT interaction (global, non-interrupting)

Tapping/stroking the dog anytime → **additive overlay**: lean-into-hand + tail wag + eye-squint. **Never calls `cancel()`, never interrupts an active work LOOP** — it layers on top and releases. Highest delight-per-hour item; strongly recommend for the build. During chew/think, it plays as a brief lean without breaking the loop.

---

## §7. Orchestration — state machine, min-display, haptic policy (NEW)

The app owns transitions; states don't self-chain.

- **Normal flow:** `Idle → (Feed →)? Idle → Fetch? → Think → Deliver → Idle`. Fetch is skipped for pure-gen; Feed is its own entry.
- **`cancel()`** during Chew: dog **spits the bone** (reuse §5b spit, no cracked-bone) → 0.2 s abort pose (ears up, to camera) → Idle. Never leave a bone half-eaten off-screen.
- **`cancel()`** during Fetch/Think: 0.2 s abort pose → Idle.
- **Min-display:** any LOOP that would show < 0.6 s is either held to one full beat (§1) or skipped (§2). No sub-250 ms flashes.
- **Haptic policy (fixes spam):** fire ONLY on Feed-grab, Feed-swallow, Deliver-drop, Error, Praise. **No haptics on internal Fetch/Think transitions.**
- **Disposition:** applied continuously via §0 with 250 ms interpolation + 0.5 s hysteresis, on top of whichever state is active.

**Contract each state exposes:**
```
enter()                              // one-shot, ≤0.6 s
loop()                               // seamless; covers unknown wait
exit(result ∈ {success, fail})       // one-shot payoff
cancel()                             // → 0.2 s abort pose (state machine handles route)
applyDisposition(axis, magnitude)    // §0 overlay; interpolated, non-interrupting
onTap()                              // §6b additive pat; never cancels
setReducedMotion(bool)               // §8 fallback
```

## §8. Reduced-Motion fallback (NEW, mandatory)

When iOS Reduce Motion is on (or a low-power flag): each state resolves to **one expressive still pose + 150 ms crossfade** — chew→a single "holding bone" pose with the indeterminate ring; think→static head-tilt; deliver→card fades in at floor; error→ears-back apologetic still; praise→play-bow still. No loops, no particles, no throughput pulse. Disposition still tints the still via §0 targets (no interpolation needed).

---

## §9. IDLE — not my lane, but the council deliverable has a hole

I am **not** building idle states (that's the idle designer). But the Round-1 brief can't both lock the shared grammar and drop idle from the handoff. So I'm shipping the idle designer a filled-in contract, not the animations:

- **Bridge:** Deliver-EXIT and Praise-EXIT both resolve to **Idle** after ~2 s of no input. Idle consumes §0 unchanged.
- **Minimum idle set (for that designer to build):** ≥ 3 non-looping micro-behaviors on a randomized weighted timer (look-around, sit-scratch, sniff-the-air, settle/lie-down after long idle), each ≤ 1.5 s, returning to a calm base pose — so it never reads as one loop. Disposition tints all of them.
- **Disagreement flagged for the council:** don't approve this action brief as "the deliverable" until idle + pure-disposition states are attached. My scope is 2 of 3 boxes.

---

## Handoff summary

**New assets:** ~5 props (bone + PDF/scroll variant, thought-glow, sparkle, cracked-bone, torn-scrap) + shared rig. Everything else is channel animation + the §0 table. **"Stick" and the Dig flavor are cut** → less art, tighter metaphor.

**Build order (time-boxed):**
1. Rig + §0 disposition table + Reduced-Motion scaffolding + state machine (§7) — *infrastructure first, or every state re-invents it.*
2. Chew-the-Bone (§1) — signature.
3. Head-Tilt Thinking (§3) — most-seen + Lens showcase.
4. Deliver (§4) + Fetch (§2).
5. Error (§5) + Praise/Pat (§6/§6b) — demo-winning polish.

**Two things I ask the council to lock:**
- The **§0 disposition contract** (reduction + hysteresis + interpolation + channel table) as the single overlay all designers consume.
- The **§6b pat** as approved scope — but as a *non-interrupting overlay*, explicitly.

**Through-line preserved:** every async op is a physical thing the dog does with a **bone** — eat it, fetch it, ponder it, bring it, or fail to chew it. The dog *is* the progress and status system. What Round-1 was missing wasn't the metaphor — it was the plumbing (disposition math, staging, orchestration, accessibility) that keeps the metaphor from twitching on a real phone.

---

## Critique

I agree with the headline call — **Rive is the right primary** — but the proposal justifies it with a perf model that's partly wrong, over-engineers the input contract, and misses several product-critical states. Points where I actively disagree with the Round-1 author:

**1. The CPU-vs-GPU story is backwards, and it undersells the real risk.** The proposal's central argument ("reject Lottie because its CPU raster contends with MLX's CPU tokenizer/sampler") misjudges where MLX spends time. On iPhone, MLX Swift runs inference on the **GPU via Metal** — the matmuls dominate; tokenization/sampling/detokenization are light CPU. So the resource MLX saturates is the GPU. That's *also* what Rive renders on. The proposal waves this away ("render command buffers are cheap next to decode compute… interleave OK"), but during peak decode the GPU is exactly the contended resource, and Rive at 60 fps will both drop frames *and* steal cycles from token generation. The conclusion (use Rive) still holds — for blend quality, authoring speed, and low footprint — but the reasoning needs inverting: **GPU contention during generation is the top risk, not CPU.**

**2. "Always favor tokens over animation frames" is stated as a policy with no mechanism.** You can't deprioritize Rive's Metal submissions below MLX's from the app layer. The only real levers are: cap Rive's framerate and freeze animation work *during* `isGenerating`. The proposal only throttles on `thermalState`, which triggers too late. The framerate governor must key off active generation, not just heat.

**3. The input contract is redundant and will confuse the animator.** Shipping a 7-value discrete enum *and* two independent 0–100 axes double-encodes the same information: "tired" ≈ low energy, "anxious" ≈ low confidence, "cautious" ≈ low-confidence-plus-focused. The brief "a focused dog at low vs high energy looks different" is hand-waved — Rive blends between *authored* poses, so someone still has to author every pose the axes interpolate through. As written, the animator can't tell what to actually build. This should be one model, not two stapled together.

**4. Seven disposition states is too many for a time-boxed team, and two of them aren't dispositions.** `cautious` overlaps `uncertain`+`focused`; `tired` is a low-arousal *idle*, not a stance the reasoning model takes. Each extra state is a full authored pose the small team must produce and QA.

**5. Missing states that matter for the demo:**
- **Empty knowledge base** — a first-run "hungry, no bones yet" beat is the strongest nudge to feed a document; it's absent.
- **Wake / greet** on launch.
- **Listening / receiving** when the user starts typing or speaking (perk-up), distinct from passive idle.
- **Success / task-complete** celebratory beat (currently folded into `respond`).

**6. No `Reduce Motion` handling.** A twitchy avatar that ignores `UIAccessibility.isReduceMotionEnabled` is an accessibility miss and a likely reviewer ding — trivial to add (freeze to a static disposition pose, suppress idle/overlay layers).

**7. No battery/foreground policy.** Continuous vector animation stacked on on-device inference drains battery; idle should cap fps and pause when backgrounded. Off-screen unload is mentioned only for sprites.

**8. Single-point authoring risk.** The whole plan assumes a Rive-fluent designer on a small hackathon team. Lottie/After Effects skills are far more common. If nobody knows the Rive editor, the plan collapses — this contingency isn't addressed. (The proposal treats sprites as a per-state fallback, not as a whole-approach fallback.)

Minor: idle selection is pushed to a Swift timer when Rive can shuffle idles internally (less main-thread coupling); and the `isGenerating`→`respond` transition overlap is left ambiguous.

---

## Revised

# CANIS — Dog Avatar Animation Brief (Rev 2)
### On-Device Animation & Feasibility — for the hackathon UI team

## TL;DR
**Primary: Rive** (Metal-rendered vector, state-machine driven) — chosen for blend quality, fast single-artist authoring, and small footprint. **Whole-approach fallback: Lottie or sprite sheets** if no Rive-fluent designer is available (see §7). Model disposition as a **2D space (valence × arousal)** with **5 named anchor poses**; the two axes trim *within* those poses. The real perf threat is **GPU contention with MLX during generation** — so the animation runtime **caps framerate and freezes axis updates while `isGenerating`**, on top of a thermal gate. Update inputs at **~8 Hz with damping**, never per-token. Honor **Reduce Motion**.

---

## 1. Why Rive (corrected rationale)
Not because MLX is "CPU-bound" — it isn't. On iPhone MLX runs inference on the **GPU**; tokenization/sampling are light CPU. Rive wins because:
- **Blend space is the whole point.** The Disposition Lens emits a *continuously moving* signal. Rive's 2D blend + additive layers let one authored set of poses *become* an interpolated stance. Lottie and sprites can only *switch*.
- **Authoring speed** for a small team: one designer builds character + state machine in the editor; inputs wire straight to Swift.
- **Small footprint** next to MLX weights (vector, not texture atlases).

**Explicitly acknowledged trade-off:** Rive renders on the GPU, the same resource MLX saturates during decode. Rive is *lighter* than a full render, not free. We manage this in §6, not by pretending it away. Spine is skipped (license + integration weight). SF Symbols are status chrome only.

---

## 2. Disposition model — one space, not two systems

Disposition is a point in a **2D emotion space**:
- **arousal** (`0–100`): calm ↔ activated
- **valence** (`0–100`): uncertain/wary ↔ confident/positive

The **5 named states are anchor regions** in that space — the animator authors one pose per anchor, and Rive's 2D blend interpolates between them as the point moves. There is no separate enum encoding the same thing.

| anchor | region (arousal, valence) | dog reads as |
|---|---|---|
| **curious** | high arousal, mid valence | ears up, head tilt, bright eyes, slow tail |
| **confident** | mid arousal, high valence | chest up, steady, easy tail wag, relaxed mouth |
| **uncertain** | low–mid arousal, low valence | ears back, lowered head, quick glances, tucked tail |
| **focused** | mid arousal, mid valence, low motion | locked forward gaze, still body, minimal tail |
| **playful** | high arousal, high valence | play-bow, fast tail, bouncy weight shift |

**Dropped from R1 as separate states:** `cautious` (emerges as the uncertain↔focused blend region) and `tired` (it's a *low-arousal idle*, see §3 — not a reasoning stance). This cuts two full authored poses.

**Handoff contract (inputs):**
```
CanisSM inputs:
  number  arousal        // 0–100, damped
  number  valence        // 0–100, damped
  trigger feedBone       // document imported
  trigger search         // RAG retrieval running
  trigger respond        // first answer token emitted
  trigger success        // task completed cleanly
  trigger error          // "can't do that"
  boolean isGenerating   // true while MLX decodes
  boolean isEmpty        // no bones in knowledge base yet
  boolean isListening    // user is typing / dictating
```
Two floats replace R1's `energy`+`confidence`+`dispositionState`. The animator builds to a 2D blend grid with 5 authored corners/center; the engine only has to emit two numbers plus event triggers.

**Day-1 MVP:** the 5 anchor poses + `feedBone` chew + `isGenerating` thinking loop + `idle_breathe`. Everything else is additive and can't break the contract.

---

## 3. Idle states (alive, not a loop)
Built on Layer 3, composited over the current disposition pose. **Selection lives inside the Rive state machine** (weighted-random shuffle driven by `arousal`), not a Swift timer — less main-thread coupling.

- `idle_breathe` — always-on baseline
- `idle_lookAround`
- `idle_earTwitch`
- `idle_tailWagLazy`
- `idle_yawnStretch` — the former "tired": biased when `arousal` is low
- `idle_settle` (sit → lie down) — after prolonged inactivity
- `idle_scratch` — rare personality beat

Rules: never repeat the same idle twice in a row; bias by `arousal` (low → yawn/settle, high → lookAround/wag).

---

## 4. Action & fun states (trigger-driven overlays, Layer 2)
- **Feed document → `feedBone`** *(signature moment)*: dog receives and **chews a bone**, which then "digests" into the knowledge base (sparkle → satisfied). Good sprite-sheet fallback candidate — self-contained loop.
- **Empty knowledge base → `isEmpty`**: a "hungry, looking around for a bone" idle-flavored state that nudges first-time users to feed a document. *(New — strongest onboarding cue.)*
- **Listening → `isListening`**: perk-up, head toward user, attentive ears — distinct from passive idle. *(New.)*
- **Retrieve / RAG → `search`**: nose-to-ground sniffing / light digging ("finding the bone"); loops during retrieval.
- **Thinking → `isGenerating`**: low-cost head-tilt focus loop, blended with current disposition (confident-thinking ≠ uncertain-thinking).
- **Responding → `respond`**: attentive lean-in, "speaking" mouth motion, tail wag scaled by `valence`.
- **Success → `success`**: brief tail-wag / ear-perk celebratory beat on clean completion. *(Split out from respond.)*
- **Error → `error`**: confused head-shake, soft paw-over-face. Warm, never scolding.

State ordering (resolve R1 ambiguity): `isGenerating=true` (thinking) → on first token fire `respond` (thinking loop exits) → on completion `success`; `isGenerating=false`.

---

## 5. Swift integration
- `RiveViewModel(fileName: "canis", stateMachineName: "CanisSM")` in a `UIViewRepresentable`.
- Disposition engine runs on a background queue; **coalesce to the main actor at ~8 Hz** and `setInput(_:value:)`. Never per-token.
- **Damp continuous inputs:** `smoothed += (target - smoothed) * k`, k ≈ 0.2 @ 8 Hz. Raw Jacobian output is noisy; undamped it reads as broken.
- Fire triggers on app events; set `isEmpty`/`isListening` from app state.
- **Reduce Motion:** if `UIAccessibility.isReduceMotionEnabled`, hold a static disposition pose, suppress Layer 2/3, disable idle shuffle. Observe the change notification live.

---

## 6. Perf policy — GPU contention is the headline risk

1. **GPU is the shared bottleneck (corrected from R1).** MLX decode saturates the GPU; so does Rive rendering. Manage it directly:
2. **Generation governor (the missing mechanism):** while `isGenerating == true`, **cap Rive to ~20–24 fps and FREEZE the arousal/valence updates** (hold last damped value). Full rate + live axis tracking resume only when idle. This is where GPU cycles actually matter — a still-ish dog during a 3-second generation is invisible; a stalled token is not.
3. **Thermal gate (secondary):** at `thermalState` `.serious`/`.critical`, drop to ~15 fps and keep only `idle_breathe` + disposition pose; restore on cooldown.
4. **No per-token updates.** Background → 8 Hz coalesced main-thread `setInput`. Mandatory.
5. **Memory:** no large sprite atlases resident beside MLX weights. If sprites are used, restrict to one or two short loops (bone chew) and unload off-screen.
6. **Battery / foreground:** cap idle to 30 fps; pause the animation entirely when the app is backgrounded.
7. **First-token stall:** enter the `isGenerating` thinking loop *before* the first token so no heavy transition lands on the frame generation starts.

---

## 7. Contingency — if no one on the team knows Rive
This is a real hackathon risk the tooling choice must survive.
- **Fallback A (preferred):** Lottie for the disposition poses as discrete states (no true blend — hard cuts + cross-fades) driven by nearest-anchor selection from the 2D point, plus Lottie one-shots for actions. Accept that the "dog becomes a blend" magic is lost; the state contract in §2 is unchanged (Swift picks nearest anchor).
- **Fallback B:** sprite-sheet loops per anchor + per action. Cheapest to run, heaviest to author and highest memory.
- The **input contract (§2) is engine-facing and identical across all three renderers**, so the engine team is unblocked regardless of which the UI team can execute.

---

## 8. Handoff structure
```
canis-avatar/
  canis.riv                 # artboard "Canis", SM "CanisSM"
  README-inputs.md          # §2 contract — source of truth
  reference/
    disposition-space.png   # 2D valence×arousal grid, 5 anchor poses marked
  fallback/                 # only if a state (or the whole approach) slips
    bone_chew@2x.png (+ .json)
```
**Naming:** disposition anchors `disp_<name>`, actions `act_<verb>`, idles `idle_<verb>`, inputs exactly as spelled in §2 (case-sensitive). The 5 anchors and two axes are frozen — engine and animation teams key off the same model.

**Day-1 minimum:** 5 anchor poses (2D blend) + `idle_breathe` + `feedBone` chew + `isGenerating` thinking loop + Reduce-Motion static fallback. Search / listening / empty / success / error and the extra idles are additive.

---

## Critique

Strong bones (the ears+tail thumbnail test, the 5-part signal grammar, the energy/valence framing, easing transitions) — but as a dev-ready handoff it has real gaps and a few things I'd push back on hard.

**1. It punts two of the three requested deliverables.** Miguel asked for disposition *and* idle (multiple) *and* fun/action (bone-chew, retrieve, think, respond, error). Round 1 delivers only disposition and defers the rest to "other council work." A hackathon team can't build from a third of the spec. Worse, disposition is the layer *most* dependent on the engine behaving; idle and action are deterministic app events the team can build immediately. We shipped the hard-to-ground layer and skipped the easy, high-certainty wins.

**2. It ignores the single biggest engine risk: flicker.** The Jacobian lens emits a continuous, noisy, real-time signal. With no hysteresis or min-dwell contract, a dog mapped 1:1 to that signal will thrash between states several times per second during generation and read as broken. 200–400 ms visual blends do *not* fix this — the fix is a debounce/dwell + threshold in the engine→UI mapping, and that contract is completely absent. This matters more than any pose.

**3. Two of the seven states are category errors.**
- `cautious` is described as "sensitive content / risky action / I shouldn't do that." That's a **content/policy** signal, not a disposition the Jacobian emits. It belongs in the action/error layer ("hold on / can't do that"), not the emotional-lens set.
- `tired` doubles as a **thermal/battery** state. That conflates a *device* condition with the *model's* mood — a user whose phone is warm will read "the AI is emotionally exhausted." Keep it, but as an explicit **system** state, honestly labeled, not a disposition.

**4. Seven positive/engaged lookalikes overload a noisy signal.** `curious`, `confident`, `focused` are three flavors of "engaged." An animator can differentiate them (and the poses are genuinely good) — but can the *engine* reliably and stably separate curious from confident from focused frame to frame? I doubt it. Painting more states than the signal can cleanly resolve guarantees the flicker in (2). Fewer, more orthogonal states are a feature, not a compromise.

**5. The production plan contradicts itself and mis-reads the platform.**
- It says "build one rig, express states as parameter presets" *and* "7 bespoke micro-motion clips." Those are different pipelines. Pick one.
- "Blend at the edges for free" is not free — weighted-pose blending requires a blend-tree/state-machine rig (Rive or custom), which is real build cost for a time-boxed team.
- **Feasibility miss:** it never says 2D vs 3D. A real-time skeletal rig runs on Metal/GPU — the exact resource MLX inference is saturating. The dog would jank worst precisely when it's meant to look `focused` (heavy compute). This needs to be 2D/vector on the Core Animation path, deliberately off the model's Metal path.

**6. Over-authored detail no one will see at phone size.** Independent single-ear twitch, visible belly breathing, whites-of-eyes, soft blinks — invisible on a 1-inch avatar and expensive to author. Spend the team's hours on ears/tail/body-height, cut the rest.

**7. No accessibility, no user-legibility plan.** Helicopter-tail spins and bouncing risk failing Reduce Motion / triggering nausea (App Store review notices this). And a label-free dog means users invent their own meanings — there's no legend, caption, or tap-to-explain. The emotional reads are written for us, not surfaced to the user.

**8. No layering/precedence.** When disposition says `confident` but the app is mid-retrieval, which plays? Undefined. There's no priority model, no explicit neutral/no-signal default (curious is called "default" but it's an active state — exhausting as a resting face), and no asset budget (format, fps, memory ceiling).

---

## Revised

# Canis Dog Avatar — Reaction Spec v2 (dev-ready)
### Skeptical-peer revision, Flotilla Council

## The core reframe: three layers with strict precedence

The dog is composited from **three layers**. Higher layers override lower ones. This resolves "what plays when." A dev builds it as a simple priority stack.

| Layer | Priority | Driven by | Certainty |
|-------|----------|-----------|-----------|
| **System / Action** | highest | deterministic app events (feed doc, retrieve, respond, error, thermal) | high — build first |
| **Disposition** | middle | the Jacobian lens (noisy, real-time) | medium — needs the contract below |
| **Idle** | base | no active signal | high — build first |

Rule: an explicit app event (chewing a bone, retrieving, cooling down) **always** wins over the disposition lens. Disposition only paints the dog *while the model is actively working and no action state owns the screen.* Idle plays otherwise.

---

## 1. Engine → UI contract (the missing spec — do this first)

Animation is worthless if the signal thrashes. Define the contract before any art:

- Engine emits at a **fixed ~5 Hz** (not per-token) a small vector: **`energy` [0..1]**, **`tension` [-1..1]** (calm↔tense), and **`magnitude` [0..1]** (how strong/trustworthy the reading is).
- UI maps the vector to the **nearest disposition state**, with:
  - **Hysteresis:** must cross a threshold *and* hold for a **min-dwell of ~1.0 s** before switching states.
  - **Floor:** if `magnitude` < 0.25, do **not** show a disposition — fall through to Idle. (No signal ≠ curious.)
- This is an **engine deliverable**, not an animation one. It is the difference between "alive" and "broken." Everything below assumes it exists.

---

## 2. Disposition states — cut 7 → 4

Four orthogonal states the noisy signal can actually resolve, one per quadrant of energy × tension. `playful`, `cautious`, `tired` are **relocated** (see §4) — they're not lens outputs.

| Code | Read | Energy | Tension | Thumbnail tell (ears + tail) |
|------|------|--------|---------|------------------------------|
| `curious` | "ooh, what's this?" | high | low | ears up + one cocked, tail 1 o'clock slow wide wag |
| `confident` | "I've got this" | low | low | ears relaxed-symmetric, tail high + slow proud swish |
| `focused` | "on the scent" | high | neutral | ears pinned forward locked, tail rigid horizontal, tip quiver |
| `uncertain` | "hmm, not sure" | low–mid | high | **asymmetric ears** (one up, one back), tail small stop-start wag |

Poses (reused from R1, trimmed to readable channels — ears, tail, **body height**, head-tilt; drop belly-breathing / eye-whites / independent twitches):

- **`curious`** — weight forward, ~15° head-tilt snap with ear-flick every few sec, alternating sides. *The engaged "listening" face.*
- **`confident`** — tall square stance, head high and level, single slow settle-nod. Still and tall (vs curious's forward fidget).
- **`focused`** — lowered stance, head down/forward, rhythmic nose-sniff, occasional paw-scuff. *"Tracking hard."*
- **`uncertain`** — weight back, head tilted *and* dipped, one paw half-raised hover + small head-shake. **Asymmetric ears are the whole tell** — cheap and unmistakable.

Distinctness is carried by **body height**: curious/focused are forward/low-active, confident is tall-still, uncertain is back-hesitant. Two of these paint from the same engaged silhouette, so the min-dwell in §1 is what keeps them from flickering.

---

## 3. Idle states — multiple, weighted, non-looping (requested, was missing)

Base layer when no signal. Never a single loop. A weighted random picker with **long dwell (6–12 s each)** returns through a neutral "sit" between variants so it reads organic:

- **`idle-sit-scan`** — sits, head scans slowly left/right, occasional ear swivel. (Most common, ~40%.)
- **`idle-liedown`** — lies down, slow blink, tail flat with a lazy single thump. (Low-activity, ~25%.)
- **`idle-sniff`** — stands, sniffs the ground, one slow circle. (~15%.)
- **`idle-shakeoff`** — full body shake or a quick ear-scratch. Rare "spice" (~10%).
- **`idle-invite`** — looks straight at the user, soft tail thump, small head-tilt. "Feed me a bone?" (~10%.)

`idle-liedown` is the resting default, **not** `curious`. The dog rests when idle; it perks when there's a signal.

---

## 4. Action / System states — the fun layer + relocations (requested, was missing)

Deterministic, high-priority, build-first. This is where the warmth and the demo money-shots live.

- **`feed-bone` (HERO — doc ingestion = chewing a bone):** bone drops in → dog catches → chews (3–4 chomps) → satisfied lick + tail wag → bone drops onto a **visible stash/pile** (the RAG "bones" made literal). This is the signature moment; give it the most polish. Ends → `confident`.
- **`retrieve` (RAG search):** nose-to-ground tracking, follows a scent trail, **digs up** the relevant bone. Visually distinct from `focused` because there's a scent-trail/dig prop.
- **`thinking` (generation running):** head-tilt + subtle "gears turning." Driven by the **app** (generation-in-progress flag), *not* the engine — so a thinking cue always fires even if the lens is quiet. Disposition modulates *on top* if a signal is present.
- **`responding` (streaming answer):** sits up alert, presents/"talks," tail-wag amplitude scaled to `confidence`. Winds down as the stream ends.
- **`cant-do` / `hold-on` (absorbs old `cautious`):** ears back, sits, small apologetic head-shake, paw-over-nose. Warm, never scary. This is where refusals/sensitive-content/blocked-action live — a **policy** signal, correctly out of the disposition set.
- **`cooling` (system: thermal/battery — old `tired`):** yawn → lies down → slow breathing. **Triggered by device state, labeled honestly** ("cooling down" caption) so users don't read a warm phone as a sad AI.
- **`playful` / `greeting` (relocated from disposition):** play-bow → bounce → spin, floppy ears, tongue out. Fires on **greetings, successful actions, easter eggs** — discrete events, which is where it actually belongs. (See reduced-motion note.)

---

## 5. Production plan — resolve the contradiction, fit the platform

- **2D, vector/frame-based, on the Core Animation path — NOT a real-time 3D skeletal rig.** The GPU/Metal is busy running MLX inference; a 3D rig competes for it and janks worst during `focused`/`thinking`. Keep the avatar off the model's compute path.
- **Pick ONE pipeline** (this was contradictory in R1):
  - **Recommended: Rive** — one artboard + a state-machine with `energy`/`tension`/`event` inputs. Tiny runtime, tiny assets, blending genuinely comes with the state machine, and the engine can drive inputs directly. Best fit for a small time-boxed team.
  - **Safe fallback: sprite atlas** — one clip set per state, no blending. Simplest and most predictable; use if Rive integration risk is too high for the hackathon window.
- **Asset budget:** target total avatar assets **< ~3 MB**, **30 fps cap**, short loops (12–24 frames / short timelines). If the frame budget is tight during peak token generation, **freeze the avatar mid-pose** — a dog that holds still "to think" reads perfectly fine.
- **Transitions:** keep R1's 200–400 ms ease/settle through a neutral mid-pose. This is a *polish* layer on top of the §1 dwell logic, not a substitute for it.

---

## 6. User legibility & accessibility (was absent)

- **Optional one-word caption** under the dog (`curious`, `chewing`, `cooling down`…) + **tap-to-explain** + a **first-run legend**. A label-free dog lets users invent meanings; give them the vocabulary once.
- **Reduce Motion variant (required for App Store):** replace bounces / spins / helicopter-tail with **pose + eye + ear changes only**. `playful` becomes an eager sit-up wag; `cooling` a still lie-down. No large translational or rotational motion.

---

## What I kept from Round 1
The ears+tail thumbnail test, the 5-part signal grammar, eased transitions, the energy/valence framing, and the specific poses — they're good. I recategorized rather than rewrote them.

## Where I still disagree with Round 1 (on the record)
Seven disposition states is too many for a noisy real-time lens and will flicker; `cautious` and `tired` are not dispositions (policy and device state respectively); `playful` is an event, not a lens output; blending is **not** free; and the biggest risk was never animation — it was the missing engine→UI dwell/hysteresis contract in §1. Fix that first or the prettiest dog in the world reads as broken.