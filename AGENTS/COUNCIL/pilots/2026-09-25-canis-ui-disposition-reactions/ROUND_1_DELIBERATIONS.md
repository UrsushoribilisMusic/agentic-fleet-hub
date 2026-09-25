# ROUND 1 — Independent Proposals

# Canis Disposition Reactions — Round 1 Proposal
### Disposition-Reaction Designer, Flotilla Council

## Recommendation: 7 disposition states

Seven is the sweet spot for a hackathon: enough emotional range to feel like a real mind, few enough that each gets a *visually unmistakable* silhouette. I've deliberately spread them across the two dimensions an animator can read at a glance — **energy** (droopy ↔ perked) and **valence** (relaxed ↔ tense) — so no two states collide.

| Code | One-word read | Energy | Valence |
|------|--------------|--------|---------|
| `curious` | "ooh, what's this?" | high | positive |
| `confident` | "I've got this" | mid | positive |
| `focused` | "working hard" | high | neutral |
| `uncertain` | "hmm… not sure" | mid | tense |
| `cautious` | "careful now" | low | tense |
| `playful` | "let's gooo" | very high | positive |
| `tired` | "that took a lot" | low | relaxed |

Design rule for the team: **each state must be legible from the ears + tail alone** (thumbnail test). Body and eyes reinforce; ears and tail carry the signal because they're the fastest-moving, highest-contrast parts of a dog.

---

## The seven states

### 1. `curious`
The default "engaged, listening" state — where the dog spends most of its time when the user is interacting.

- **Body pose:** Weight forward, front paws planted, slight lean toward the screen/user. Head tilted ~15° to one side.
- **Tail:** Raised to ~1 o'clock, slow wide wag (1 per 1.5s).
- **Ears:** Both perked fully upright, one twitching independently toward "sound."
- **Eyes:** Wide, bright, pupils large; occasional quick glance-around.
- **Signature micro-motion:** The **head-tilt snap** — quick 15° tilt with an ear-flick, then settle. Repeats every few seconds with alternating side.
- **Emotional read:** *"I'm interested and paying attention to you."*

### 2. `confident`
Emitted when the model's internal state is stable/high-certainty — clean answers, familiar territory.

- **Body pose:** Tall, square stance, chest out, head held high and level.
- **Tail:** High and still-ish, with a slow, assured swish (not excited — proud).
- **Ears:** Relaxed-upright, symmetric, calm.
- **Eyes:** Half-relaxed, steady gaze, soft blink. No darting.
- **Signature micro-motion:** A single slow **chest-lift breath** + a small satisfied nod.
- **Emotional read:** *"I know this. Trust me."*
- **Distinctness note:** vs `curious` — confident is *still and tall*; curious is *forward and fidgety*.

### 3. `focused`
High-effort concentration — long generation, heavy RAG retrieval, complex reasoning.

- **Body pose:** Lowered stance, head down and forward, shoulders slightly hunched — "on the scent."
- **Tail:** Held straight out horizontally, rigid, tip barely quivering (tension, not wag).
- **Ears:** Pinned forward and locked, no twitching.
- **Eyes:** Narrowed, intense, fixed on a single point; minimal blinking.
- **Signature micro-motion:** **Nose-twitch sniffing** — rhythmic small sniffs, occasional paw-scuff. Reads as "tracking hard."
- **Emotional read:** *"Don't interrupt — I'm working."*

### 4. `uncertain`
Mid-tension, low-confidence — the model is torn between competing answers or the query is ambiguous.

- **Body pose:** Weight shifted back slightly, head tilted *and* dipped, one front paw half-raised (hesitant step).
- **Tail:** Mid-height, small tentative uneven wag that stops and starts.
- **Ears:** Asymmetric — one up, one half-back. This asymmetry is the key tell.
- **Eyes:** Darting side to side, quick blinks, brows raised (worried).
- **Signature micro-motion:** The **raised-paw hover** + a small head-shake, as if reconsidering.
- **Emotional read:** *"I'm… not totally sure about this."*
- **Distinctness note:** asymmetric ears = uncertain; symmetric ears everywhere else. Cheap, unmistakable signal.

### 5. `cautious`
Low-energy tension — sensitive content, a risky action, or the "I shouldn't do that" lean.

- **Body pose:** Crouched low, backed up half a step, tail-end tucked, weight on hind legs (ready to retreat).
- **Tail:** Low, tucked partway under, slow nervous sway.
- **Ears:** Both flattened back against the head.
- **Eyes:** Wide but wary, whites showing slightly, fixed watchfully on the user.
- **Signature micro-motion:** A slow **lean-back with a single soft look up** — the "are you sure?" glance.
- **Emotional read:** *"I'll do this carefully — or maybe we shouldn't."*
- **Distinctness note:** vs `uncertain` — cautious is *low and backed-away*; uncertain is *upright and fidgeting*. Different body height instantly separates them.

### 6. `playful`
Peak positive energy — greetings, successful playful actions, light chit-chat, easter-egg moments.

- **Body pose:** The classic **play-bow** — front down, rear up, tail high. Bouncy, springy weight shifts.
- **Tail:** Fast full-arc wag (helicopter-fast at peak), whole rear wagging with it.
- **Ears:** Flopping/bouncing with the motion, loose and lively.
- **Eyes:** Sparkling, mouth open in a "smile," tongue out.
- **Signature micro-motion:** **Play-bow → bounce → spin** loop; occasional excited hop.
- **Emotional read:** *"Yay! Let's have fun!"*

### 7. `tired`
Low energy, relaxed — after heavy load, long sessions, or a "cooling down" thermal/battery-aware state (ties nicely to on-device thermal gating).

- **Body pose:** Lying down / slumped, head resting on paws or drooping.
- **Tail:** Flat on the ground, occasional weak single thump.
- **Ears:** Relaxed and drooping, no tension.
- **Eyes:** Heavy-lidded, slow long blinks, occasional full close.
- **Signature micro-motion:** A big **yawn + stretch** on entry, then slow breathing (visible belly rise/fall).
- **Emotional read:** *"Whew… that was a lot. Resting a sec."*

---

## Cross-state animator guidance

**The 5-part signal grammar** (fill this table for every state — it's the whole spec):

| Part | Carries | Why |
|------|---------|-----|
| Ears | primary emotion tell | fastest to read, high contrast |
| Tail | energy + valence | large motion, visible in thumbnail |
| Body height | tension/confidence | separates lookalike states |
| Eyes | fine emotional detail | reinforces, not primary |
| Micro-motion | "alive" signature | the one loop that makes it memorable |

**Transitions:** Don't hard-cut between states — the disposition engine emits continuous-ish values, so build **short (200–400ms) blend/settle transitions** through a neutral mid-pose. A dog that snaps instantly between poses reads as broken; a dog that *eases* reads as feeling.

**Blend at the edges:** because dispositions are axes, consider letting two adjacent states cross-blend (e.g. `curious`→`playful` share the forward lean). Not required for hackathon MVP, but if the rig is built as weighted poses rather than fixed clips, you get this for free.

**Asset production shortcut for a small time-boxed team:** build **one rig, one base dog**, and express all seven states as parameter presets on (ears-angle, tail-height, tail-speed, body-height, eye-openness, head-tilt) + one hero micro-motion clip per state. That's 7 short clips + a shared idle skeleton, not 7 bespoke animations — critical for hitting the Oct 1–16 window.

---

*Round-1 scope note:* this covers the **disposition** reactions only. Idle states and fun/action states (bone-chewing on doc feed, retrieving, thinking, responding, error) are the other two council deliverables — I've kept `tired`'s yawn/stretch and `playful`'s bow deliberately reusable so they can double as idle/action building blocks when we get there.

---

# CANIS Dog Avatar — Idle & Ambient-Life States (Round 1)

**Author:** Idle & Ambient-Life Designer
**Scope:** The "alive while waiting" layer. Not disposition reactions, not action states — just what the dog *does* when nothing is happening, so it never reads as a frozen loop.

---

## Design principle: the Idle Layer is a scheduler, not a loop

The failure mode we're avoiding is the single-loop breathing dog that everyone recognizes as "the app is idle." Instead, treat idle as a **weighted random scheduler** that sits on top of one continuous base and occasionally fires short one-shot "life beats."

Three tiers:

1. **Base (always running):** breathing + micro head/ear drift. Never stops, never a discrete event.
2. **Ambient beats (fired on a timer):** short one-shots — sniff, scratch, look-around, yawn, etc. Return to base when done.
3. **Rare specials:** low-probability delight moments (tail chase, sigh-and-flop). Long cooldowns so they stay special.

Everything blends back to **NEUTRAL_BASE**, which is also the hand-off point to the Disposition layer (their reactions start and end on the same neutral pose so the two systems compose cleanly).

---

## The base state

**`idle_base` (continuous, looping)**
- Slow breathing (chest/belly rise ~0.25 Hz), subtle ear twitch, occasional slow blink, tiny weight-shift sway.
- This is the canvas. Ambient beats are layered/spliced over it and it resumes underneath.
- **Disposition tint:** the base is modulated (not replaced) by current disposition — e.g. an "alert/curious" tint raises the ears and speeds breathing slightly; a "tired" tint lowers the head. The idle *beats* below inherit this tint so the dog feels continuous with its mood. Devs: expose a single `dispositionTint` param (0–1 per axis) that scales base pose offsets. If the Disposition layer isn't ready, tint = neutral and everything still works.

---

## The ambient beats (the core deliverable — 8 states)

Each is a **short one-shot** (1–3.5 s) that plays, then blends back to base over ~300–400 ms. Devs build each as an independent clip that starts and ends on the neutral pose so splicing is seamless.

| # | State | Duration | What it looks like | Feel |
|---|-------|----------|--------------------|------|
| 1 | `look_around` | ~2.0 s | Head turns L, holds, turns R, returns; ears track | scanning, present |
| 2 | `sniff` | ~1.5 s | Nose dips, quick sniff-twitches (3–4), head lifts | curious, doggy |
| 3 | `scratch` | ~2.5 s | Sits back, hind leg scratches ear/neck, shakes head | candid, natural |
| 4 | `ear_flick_shake` | ~1.0 s | Quick full-body/ear shake (like shrugging off water) | reset, alive |
| 5 | `yawn` | ~2.0 s | Big yawn, tongue curl, small full-body stretch | relaxed, time-passing |
| 6 | `lie_down` | ~3.0 s in | Settles to lying pose (a **sustained sub-base**, see below) | patient, cozy |
| 7 | `perk_up` | ~1.2 s | Head snaps up, ears prick, freezes alert for a beat | "heard something" |
| 8 | `paw_lick_groom` | ~2.5 s | Licks a front paw, small nuzzle | self-soothing, homey |

**Note on #6 `lie_down`:** this isn't a one-shot — it's a *transition into an alternate base*. Once lying, the dog runs a `idle_base_lying` (breathing lying down, occasional head-lift). It only fires after prolonged idle (see timing) and must be interruptible: any input or a `perk_up` trigger pops the dog back up (`stand_up`, ~1.0 s) before handing to whatever comes next. This gives the strongest "settled in for the wait" signal without looking dead.

---

## The rare specials (2 states — delight, long cooldowns)

| State | Prob. | Cooldown | Description |
|-------|-------|----------|-------------|
| `tail_chase` | very low | ≥5 min, never twice/session ideally | 2–3 quick spins after own tail, then stop, slightly sheepish. Pure charm. |
| `sigh_flop` | low | ≥3 min | Audible sigh, flops onto side dramatically (deep idle only). "You still there?" energy. |

Keep these rare on purpose. If a user sees the tail chase once per session it's magic; three times it's a loop.

---

## Idle timing & weighting (so it's natural, not repetitive)

Model idle time as a clock that starts when the app goes quiet (no input, no active task).

**Beat scheduler:**
- After entering idle, wait a **random inter-beat interval** drawn from ~6–14 s (uniform jitter — never a fixed cadence).
- Pick a beat by **weight**, then apply an **anti-repeat rule**: the last-played beat's weight is temporarily set to ~0 and recovers over the next two picks. Never play the same beat twice in a row.
- Suggested base weights: `look_around` 22, `sniff` 20, `ear_flick_shake` 14, `paw_lick_groom` 12, `scratch` 12, `yawn` 10, `perk_up` 10. (`lie_down` and specials are gated by phase/cooldown, not the weight pool.)

**Idle phases (weights shift as idle deepens):**

| Phase | Idle elapsed | Behavior |
|-------|-------------|----------|
| **Fresh** | 0–20 s | Alert-leaning beats: `look_around`, `perk_up`, `sniff` weighted up. Longer inter-beat gaps (dog assumes you're coming back). |
| **Settling** | 20–90 s | Full pool, balanced weights. `yawn`, `scratch`, `groom` become more likely. |
| **Deep idle** | 90 s+ | `yawn` up; `lie_down` becomes eligible (fires once, then lying-base). `sigh_flop`/`tail_chase` eligible under cooldown. Inter-beat gaps stretch (~12–20 s) — a settled dog does less. |

Weights are just data — ship them in a JSON/plist the hackathon team can tune without touching animation code.

---

## The "just noticed you / re-engage" transition (required)

The single most important moment for making the dog feel like a companion. It fires the instant *any* signal of user return arrives.

**Triggers (any of):**
- Text field focus / keyboard appears
- Tap on the avatar or input area
- App returns to foreground
- (Optional/nice) device motion / proximity — phone picked up

**Behavior — `reengage` (interrupt-anything, ~1.0–1.4 s):**
1. **Interrupt** whatever idle beat is mid-play (fast blend-out, ~150 ms) — including standing up from `lie_down`.
2. **Play `perk_up` + a warm greeting flourish:** head snaps toward the "user" (screen/camera direction), ears prick, **one tail wag burst**, a tiny happy bounce or paw-lift.
3. **Settle into an attentive neutral base** (ears slightly forward, ready) and **hand off** to whatever comes next — Disposition layer or an action state.

Design note: the *depth* of the greeting scales with how long the dog was idle. Back after 5 s → a small ear-prick. Back after 3 minutes of deep idle → full stand-up, stretch, big wag. Reward the user for returning; make absence feel noticed. One tuning param: `idleDurationAtReturn`.

---

## Blending & hand-off rules (for the implementers)

- **One neutral contract:** every idle beat, `reengage`, and (per the other councilors) every disposition/action state must begin and end on the shared **`NEUTRAL_BASE`** pose. This is the whole reason the systems compose without janky snaps.
- **Blend times:** base→beat ~250 ms in, beat→base ~350 ms out. `reengage` interrupts with a faster ~150 ms out-blend on the current beat.
- **Priority:** `reengage` and any incoming Disposition/Action state **always outrank** idle. Idle is the lowest-priority layer and yields immediately.
- **Interruptibility:** no idle beat may be "uncancellable." If real work arrives 0.4 s into a yawn, blend out of the yawn — don't make the user wait for the dog to finish.

---

## Asset & performance budget (hackathon-friendly)

- **~10 short clips + 2 bases + 1 reengage** — all buildable as short skeletal/sprite loops. No clip over ~3.5 s.
- Reuse rig/poses across beats (same neutral start/end) so the team animates deltas, not full sequences.
- Runs off a lightweight state machine + a weighted picker reading a tunable config file. No per-frame ML, no heavy physics. Fully compatible with on-device / low-power.
- **If time runs out:** ship tiers in this order → (1) `idle_base` + `reengage`, (2) beats 1,2,3,7 (`look_around`, `sniff`, `scratch`, `perk_up`), (3) the rest, (4) specials. Even tier 1+2 already reads as alive.

---

## Open questions for the council

1. **Disposition ↔ idle coupling:** do we want idle *beat selection* biased by disposition (an anxious dog scratches/looks-around more; a tired dog yawns/lies-down more)? I've assumed the tint modulates *pose* but not *weights* for Round 1 — easy to extend if the Disposition designer wants it. Recommend we align the axis names first.
2. **Sound:** yawn, sniff, sigh, greeting wag — do we have an audio budget, or is this silent? Changes the emotional weight of `reengage` a lot.
3. **"User direction":** for `look_around`/`reengage` head-turn, is there a consistent on-screen anchor to turn *toward* (input field / camera)? Needed so the greeting feels aimed at the user, not random.

---

# Canis — Action & Playful-Moments States (Round-1 Proposal)
### From: Action & Playful-Moments Designer, Flotilla Council

Scope: the **action-tied** dog reactions — the moments where the app *does something* and the dog performs it. These are the states that make Canis feel alive and earn the "aww." I've written them dev-ready: each has a trigger, a beat sheet with timing, loop points, asset requirements, and a note on how it couples to the Disposition Lens so the same rig serves both systems.

---

## Design principles (read first, 60 seconds)

1. **One rig, layered.** Every action below is built from a shared skeletal/puppet rig: head, ears (L/R), eyes/blink, mouth, tail, front paws, body bob. UI devs animate *channels*, not bespoke sprites. This keeps assets tiny and lets disposition tint any action (a *confident* fetch vs. an *anxious* fetch = same clip, different ear/tail bias).
2. **Three-part grammar for every action:** `ENTER (anticipation) → LOOP (the work) → EXIT (payoff)`. Only the LOOP repeats; ENTER/EXIT are one-shots. This is the whole trick to "feels alive but costs nothing."
3. **Loop the *uncertain-duration* middle only.** We never know how long RAG retrieval or token generation takes, so the LOOP covers the wait; ENTER/EXIT are fixed and short (≤0.6 s each).
4. **Disposition is an overlay, not a new clip.** The engine's current disposition biases three cheap channels during any action: **ear height**, **tail speed/amplitude**, **eye openness**. Devs get one function: `applyDisposition(axis) → {ears, tail, eyes}`. See coupling notes per state.
5. **Interruptible.** Every LOOP must accept a `cancel()` that snaps to a 0.2 s "abort" pose (ears up, head to camera) rather than finishing the beat. Async apps interrupt constantly.
6. **Perf budget:** target is a puppet (2D skeletal, e.g. Rive/Lottie-style bone animation) — NOT frame-by-frame sprite sheets. ≤ 12 bones, ≤ 3 simultaneous tweens, 60 fps on an iPhone 12. No per-frame texture swaps. Haptics on ENTER and EXIT only (never during loops — battery + annoyance).

---

## 1. FEED A DOCUMENT — "Chewing the Bone" 🦴
*The signature moment. When a user ingests a doc into local RAG, the doc visibly becomes a bone the dog eats. This is the one to nail.*

**Trigger:** user drops/imports a file for ingestion. Duration = real ingestion time (chunk + embed). Usually 1–8 s.

**Beat sheet:**

| Phase | Beat | Timing | What animates |
|---|---|---|---|
| ENTER | **Sniff** | 0.0–0.7 s | Doc icon slides in and morphs into a bone. Dog's nose dips to it, 2 quick sniff twitches (nostril + ear flick). Tail gives one curious wag. *One-shot.* |
| ENTER | **Grab** | 0.7–1.0 s | Head snaps down, mouth closes on bone, small "pounce" body dip. Haptic: single medium tap. Bone now parented to jaw. |
| LOOP | **Chew** | 1.0 s → until done | Rhythmic chew: jaw open/close ~2 Hz, head bobs slightly, ears joggle, eyes half-close in contentment. **This loop = the progress bar.** A subtle crumb/sparkle particle per chew doubles as ingestion-progress feedback (particles accumulate → fill a faint ring). *Seamless loop, ~0.5 s.* |
| EXIT | **Swallow + satisfied** | on `done`, 0.6 s | One big gulp (throat bob), lick lips (tongue flick), single tail-thump, eyes blink up to camera as if to say "got it." Bone disappears. Haptic: success tap. |

**Progress coupling:** map ingestion % to chew *count*, not chew *speed* (constant-speed chew reads as calm competence; speeding up reads as panic). If the doc is large, the ring fills; when RAG is ready, EXIT fires.

**Disposition overlay:** *focused* → ears forward, minimal tail. *playful* → exaggerated head bob, tail wags between chews. If the doc **fails to parse**, do NOT swallow — cut to the *"Can't Chew That"* variant (see §5): dog spits the bone out, paws at it, looks up puzzled.

**Assets:** 1 bone shape (+ optional variants: scroll-bone for PDF, chew-toy for image). Reuse dog rig. ~4 keyable poses.

---

## 2. SEARCH / RETRIEVE — "Fetch" 🦯
*When the app queries the local RAG index to retrieve "bones" (knowledge chunks) relevant to the user's question.*

**Trigger:** retrieval begins (user asks something that hits RAG). Duration = retrieval latency (short, often <1 s) — so this state is snappy.

Two flavors, pick per latency:

**2a. Quick Fetch (retrieval < ~1.2 s) — default**
- ENTER (0.3 s): ears perk, head whips toward an off-screen point, hagent crouch (anticipation).
- LOOP (0.4 s, 0–2 reps): dog darts off-frame / becomes a motion streak, OR a "*sniffing along a trail*" nose-to-ground scan. Keep it to 1–2 loops max.
- EXIT (0.4 s): trots back into frame carrying a **stick** (= the retrieved context), tail high. Segues directly into §3 (Thinking) or §4 (Deliver).

**2b. Dig (retrieval slow, or "deep search" mode)**
- ENTER: dog paws the ground twice, glances down.
- LOOP: **digging** — front paws alternate, dirt/particle puffs fly back, ears bounce. Genuinely charming and reads instantly as "searching hard." Loop ~0.6 s. Occasional variation frame (pause + sniff the hole) breaks monotony on long digs.
- EXIT: pulls a **bone** out of the hole, triumphant head-toss.

**Disposition overlay:** *confident* → straight-line fetch, sticks the landing. *uncertain* → the "sniffing trail" scan variant, more hesitant, ears lower. *curious* → extra sniff before darting.

**Assets:** stick, dirt-puff particle, reuse bone from §1. No new rig.

---

## 3. THINKING / GENERATING — "Head Tilt & Focus" 🐕
*Token generation is running. Classic dog head-tilt = universally read as "processing what you said." This is the most-seen state; it must be endlessly watchable.*

**Trigger:** model starts generating. Duration = generation time (can be several seconds).

**Beat sheet:**
- ENTER (0.4 s): the iconic **head tilt** — head rotates 12–18°, one ear flops, eyes lock on user. Tiny "hm?" — this alone sells intelligence.
- LOOP (the wait): a *pondering micro-loop* — slow blink, occasional ear twitch, head drifts to tilt the *other* way every ~3 s, faint tail sway. **Add a "thought" tell:** a soft glowing particle or a floating faint bone-outline above the head that pulses in sync with token throughput (fast tokens = quicker pulse). This is where **Disposition Lens output shines live** — see coupling.
- EXIT: head straightens, ears up, one bright blink → hands off to §4 (Deliver).

**Live disposition coupling (this is the state where the Lens is most visible):**
- *confident* → still head, steady slow blink, relaxed tail. Calm authority.
- *uncertain/anxious* → more frequent head re-tilts, ears drift down, faster shallow tail, thought-particle flickers. The user *sees* the model hedging.
- *curious* → perked ears, thought-particle brightens, head cranes forward.
- *tired* → slow heavy blinks, a yawn every ~5 s, ears low.

**Anti-monotony:** three head-tilt hold variants (left, right, up) chosen at random on entry so no two generations look identical.

**Assets:** thought-particle/bone-outline glow. Reuse rig. This state doubles as the primary disposition display, so invest most polish here.

---

## 4. DELIVER THE ANSWER — "Drop It At Your Feet" 🎁
*Generation done, answer ready to present.*

**Trigger:** final token / answer render.

**Beat sheet:**
- ENTER (0.4 s): dog trots forward toward the "camera"/user, carrying the stick-or-bone from §2 (or conjures it if pure-generation, no RAG).
- CORE (0.5 s): **drops it at your feet** — head lowers, releases the object, which morphs/expands into the answer card/text as it lands. Small dust settle. This literally *hands the answer to the reader* — great affordance.
- EXIT (0.4 s): dog sits back, looks up expectantly, single hopeful tail-thump, ears up. Optional: soft "waiting for praise" hold that bridges into an Idle state if the user doesn't respond.

**Disposition overlay:** *confident* → brisk drop, proud sit. *uncertain* → sets it down gently, glances between answer and user (mirrors a low-confidence generation — honest signal). *playful* → drops it, then a tiny play-bow.

**Assets:** the object→card morph (shared with §1/§2 objects). Reuse rig.

---

## 5. ERROR / REFUSAL — "Can't-Do Shrug" & "Can't Chew That" 😕
*Something failed or the model won't/can't answer. This is where charm prevents frustration — a whining dog is forgivable; a red error toast is not.*

**Three variants by cause:**

**5a. Refusal / out-of-scope ("I can't help with that")**
- **Confused whine:** head tilts, ONE ear up one down, a small backward step, front paw lifts and paws the air twice (the "shrug"), soft whine tell (rising eyebrow-marks + open mouth). Tail tucks slightly, not fully. Loops once, holds on the paw-up pose. Charming, apologetic — never scary.

**5b. Ingestion failed ("Can't Chew That")** *(routed from §1)*
- Dog spits the bone out (head shake), it lands cracked/greyed. Dog paws at it, sniffs, looks up at user with ears back. Reads instantly as "this file didn't work" without a modal.

**5c. Hard/system error (network, engine crash, OOM)**
- Brief startle → sit → single low whine → ears flat → the answer-card slot shows the error text as a chewed/torn scrap the dog nudges forward. Keep it under 1 s; don't wallow.

**Rules:** never anger, never a "bad dog" read — always *apologetic/confused*, so the user blames the situation, not themselves or the pet. Haptic: soft double-tap (gentle, not the harsh error buzz). Auto-recovers to Idle after ~2 s.

**Disposition overlay:** *cautious* tint by default here (ears back, low tail).

**Assets:** cracked-bone variant, torn-scrap card, whine eyebrow marks. Reuse rig.

---

## 6. SUCCESS / PRAISE MOMENT — "Good Dog!" 🎉
*Fires on user positive feedback (thumbs-up, "good boy," pat gesture, or a completed task).*

**Beat sheet:**
- Trigger: user praise/thumbs-up OR pat-the-dog tap on the avatar.
- CORE (0.8 s): full-body **happy wiggle** — tail goes to blur-speed, ears up, a small hop or **play-bow** (front down, rear up), quick spin option, tongue out, joyful blink. One celebratory sparkle burst.
- Haptic: light "success" rhythm (tap-tap).
- EXIT: settles into a pleased sit, warm slow blink, then bridges to Idle.

**Pat interaction (bonus, high delight/low cost):** tapping/stroking the dog anytime triggers a lightweight lean-into-hand + tail wag + eye-squint. Costs nothing, massively increases session warmth and demo "wow." Strongly recommend for the hackathon build — it's the moment judges will screenshot.

**Disposition overlay:** *playful* amplifies (adds the spin); *tired* → gentler wiggle, grateful lean.

**Assets:** sparkle burst (shared with §1 crumbs). Reuse rig.

---

## Handoff summary for the hackathon team

**Total NEW assets across all action states:** ~6 small props (bone + PDF/scroll variant, stick, dirt-puff, thought-glow, sparkle, cracked-bone/torn-scrap) + one shared dog puppet rig. Everything else is channel animation. This is a **1–2 day rig + 3–4 day animation** job for one animator — hackathon-feasible.

**Build order (if time-boxed):**
1. **Rig + Chew-the-Bone (§1)** — signature moment, do first.
2. **Head-Tilt Thinking (§3)** — most-seen + the disposition showcase.
3. **Deliver (§4)** and **Fetch (§2)** — complete the core loop.
4. **Error (§5)** and **Praise/Pat (§6)** — the polish that wins the demo.

**Contract each state must expose to the app:**
```
enter()            // one-shot anticipation, ≤0.6s
loop()             // seamless, covers unknown wait; cancel()-able
exit(result)       // one-shot payoff; result ∈ {success, fail}
applyDisposition(axis, magnitude)   // biases ears/tail/eyes, any time
onTap()            // pat interaction, global
```

**Two things I'm asking the council to lock:**
- **ENTER/LOOP/EXIT grammar** as the standard for *all* dog states (including Idle & pure-Disposition states from the other designers) — so one animator's work composes cleanly.
- **The pat-the-dog interaction (§6 bonus)** as an approved scope item — highest delight-per-hour of anything in this brief.

The through-line: **every async operation in the app is a thing the dog physically does with an object** — eat it, fetch it, ponder it, bring it, or fail to chew it. The dog metaphor isn't decoration; it *is* the progress and status system. That's what makes Canis feel like a companion instead of a spinner.

---

# CANIS — Round-1 Proposal: How to Build the Dog Avatar Animations
### From: On-Device Animation & Feasibility Lead

## TL;DR
**Primary: Rive** (state-machine-driven, GPU-rendered vector). **Fallback: pre-rendered sprite sheets** for any state the designer can't finish in Rive in time. Do **not** use Lottie as the driver of the live avatar — its CPU vector rasterization contends directly with MLX's tokenizer/sampling on the main thread and blends poorly between states. Drive the dog from a small set of Rive **inputs** (2 continuous axes + 1 discrete state enum + action triggers). Update those inputs at **~6–8 Hz with damping**, never per-token, and throttle animation framerate when `thermalState` climbs.

---

## 1. Option comparison

| Option | Perf while MLX runs | Asset speed (small team) | Blend/transition quality | Cost | Verdict |
|---|---|---|---|---|---|
| **Rive** | GPU (Metal) vector; tiny CPU. Shares GPU with MLX but render command buffers are cheap next to decode compute. Low memory footprint. | **Fast** — one designer builds character + state machine in the Rive editor; inputs wire straight to Swift. | **Excellent** — built-in blend states, additive layers, number-input-driven interpolation. Purpose-built for a character reacting to continuous signals. | Free tier is enough for a hackathon; runtime is open-source (MIT). | **PRIMARY** |
| **Lottie / JSON** | **CPU-bound** vector raster on the render path; complex dog vectors can jank and it competes with MLX for CPU during generation. | Fast IF you have an After Effects artist; slow otherwise. | Poor — segment playback, manual cross-fades, no real blend space between dispositions. | Free. | One-shot flourishes only, not the live driver. |
| **Sprite sheets / frame anim** | **Cheapest & most predictable** — GPU texture blit, no runtime vector math. But high memory (textures sit alongside MLX weights → pressure) and large asset count. | Slow to produce many states/frames; re-renders on every tweak. | **None** — hard cuts; cross-fade only. Transitions look robotic. | Free (pipeline cost). | **FALLBACK** + good for tight loops (chewing bone). |
| **SF Symbols + SwiftUI transforms** | Trivially cheap. | Fast. | Fine for glyphs, cannot carry a warm dog character. | Free. | Micro-status only (see §5). Not the avatar. |
| **Spine** | Good skeletal 2D, but heavier runtime, larger integration. | Slower ramp; smaller Swift community than Rive. | Excellent skeletal blends. | **$69–$399 license.** | **Skip** — cost + overkill for a time-boxed team. |

**Why Rive specifically for Canis:** the whole point is a character that *interpolates* to a continuously-changing internal signal (the Disposition Lens). Rive's number/boolean/trigger inputs + blend states are the exact primitive for "map a float to how the dog looks." Lottie and sprites can only *switch* states; Rive can *become* a blend of them, which is what sells "the dog is feeling the model think."

---

## 2. Recommended architecture

**One `.riv` file, one artboard ("Canis"), one State Machine ("CanisSM") with 3 layers:**

- **Layer 1 — Body/Disposition (blend):** the resting posture + facial state driven by the disposition inputs. This is where curious/confident/anxious/etc. live and blend.
- **Layer 2 — Action overlay (triggers):** transient, one-shot actions fired by app events (chew bone, sniff/search, respond, error). Overlays on top of the body layer so a "confident" dog and a "chewing" dog compose.
- **Layer 3 — Idle variation (random):** micro-animations layered on the baseline so idle never looks like a single loop.

### State-machine inputs (the handoff contract)
```
CanisSM inputs:
  number  energy        // 0–100  arousal / activation
  number  confidence    // 0–100  certainty / valence
  number  dispositionState  // 0–6 discrete enum (see map below)
  trigger feedBone      // user fed a document
  trigger search        // RAG retrieval running
  trigger respond       // model started emitting answer
  trigger error         // "can't do that"
  boolean isGenerating  // true while MLX decodes (gates the thinking loop)
```

**Design intent:** `dispositionState` gives the designer a clean, nameable target per state; `energy` + `confidence` are continuous trims that let the same base pose breathe and blend (a "focused" dog at low energy vs. high energy looks different without a new state). Hackathon devs can ship using only `dispositionState` on day 1 and layer in the two continuous axes later — the app should still set all three.

### Disposition enum map
| value | state | dog reads as |
|---|---|---|
| 0 | curious | ears up, head tilt, bright eyes, slow tail |
| 1 | confident | chest up, steady, relaxed open mouth, easy tail wag |
| 2 | uncertain / anxious | ears back, lowered head, quick glances, tucked tail |
| 3 | focused | locked forward gaze, still body, minimal tail |
| 4 | playful | play-bow, fast tail, bouncy weight shift |
| 5 | cautious | slow approach, one paw lifted, sniff-check posture |
| 6 | tired | slow blink, lowered lids, yawn, settling down |

---

## 3. Idle states (multiple, alive-not-looping)
Build these as Layer-3 clips, selected by a Swift-side random timer (pick a new one every 4–9 s, weighted by `energy`):

- `idle_breathe` (always-on baseline, subtle chest movement)
- `idle_lookAround`
- `idle_earTwitch`
- `idle_tailWagLazy`
- `idle_yawnStretch` (bias when `energy` low / `dispositionState == tired`)
- `idle_sitDown` / `idle_lieDown` (settle after long inactivity)
- `idle_scratch` (rare, "personality" beat)

Rule for devs: never play the same idle twice in a row; bias selection by current `energy` so a low-energy dog yawns/settles and a high-energy dog looks around and wags. This is what breaks the "single loop" feel cheaply.

## 4. Fun / action states (trigger-driven overlays)
- **Feed document → `feedBone`**: dog receives a bone and **chews it** (the signature moment). This is a good candidate to render as a **sprite-sheet loop** if the Rive chew is slow to author — it's a self-contained flourish, so the fallback pipeline fits here perfectly. Then bone "digests" into the knowledge base (subtle sparkle → dog looks satisfied).
- **Retrieve / RAG search → `search`**: nose-to-ground sniffing / light digging ("finding the bone"). Loops while retrieval runs, resolves when results return.
- **Thinking / generating → `isGenerating = true`**: head-tilt + focused loop, **deliberately low-cost** (see §6). Blend with `dispositionState` so a confident-thinking dog differs from an anxious-thinking one.
- **Responding → `respond`**: attentive lean-in, mouth "speaking" motion, tail wag scaled by `confidence`.
- **Error / can't-do → `error`**: confused head-shake + soft whimper posture / paw-over-face. Warm, never scolding.

---

## 5. Swift integration (rive-ios)
- Use `RiveViewModel(fileName: "canis", stateMachineName: "CanisSM")` in a `UIViewRepresentable` (or the SwiftUI `RiveViewModel.view()`).
- Disposition engine emits on a background queue; **coalesce to the main actor at ~6–8 Hz** and call `setInput(_:value:)`. Never call it per generated token.
- **Damp the continuous inputs** before setting them: `smoothed += (target - smoothed) * k` (k ≈ 0.2 at 8 Hz). Raw Jacobian values will be noisy; undamped they make the dog twitch and read as broken.
- Fire triggers on app events (`feedBone` on document import, `respond` on first token, `error` on failure).
- SF Symbols/SwiftUI are fine for the **surrounding status chrome** (a tiny "bone count", a mic glyph) — not the avatar.

---

## 6. Jank risks while MLX is generating — flag list

1. **CPU contention (biggest risk):** MLX tokenization/sampling runs hot on CPU. This is the reason Lottie is rejected as the driver — its vector raster shares that CPU. Rive's vector path is far lighter, but still: keep the *thinking* loop simple.
2. **Per-token input updates = jitter + main-thread churn.** Decouple: engine → background → 6–8 Hz coalesced main-thread `setInput`. Mandatory.
3. **Metal command-buffer contention:** MLX submits large compute buffers; Rive submits render buffers. They interleave OK on A-series, but during peak decode you may drop animation frames. **Policy: always favor tokens over animation frames** — a dropped dog frame is invisible; a stalled token is not. Do not raise the animation layer's priority.
4. **Thermal throttling:** MLX already heats the device (their MLX checklist has a thermal gate). Watch `ProcessInfo.processInfo.thermalState`; at `.serious`/`.critical`, drop the Rive view to ~15 fps and suppress Layer-2/3 overlays, keeping only `idle_breathe` + disposition. Re-enable on cooldown.
5. **Memory pressure:** don't ship large sprite atlases loaded simultaneously with MLX weights. Rive's tiny vector footprint is a real advantage here — restrict sprite fallback to one or two short loops (the bone chew) and unload when off-screen.
6. **First-token stall:** avoid firing a heavy full-body transition on the same frame generation starts. Enter the `isGenerating` thinking loop *before* the first token, so the transition cost is already paid.

---

## 7. Asset / handoff structure (devs can start immediately)
```
canis-avatar/
  canis.riv                  # single file, artboard "Canis", SM "CanisSM"
  README-inputs.md           # the input contract from §2 (source of truth)
  fallback-sprites/          # only if a Rive state slips
    bone_chew@2x.png (+ .json frame data)
  reference/
    disposition-poses.png    # 7 keyframe poses, one per enum value
```
**Naming conventions:** states `disp_<name>`, actions `act_<verb>`, idles `idle_<verb>`, inputs exactly as spelled in §2 (case-sensitive on the Swift side). Enum values are frozen in the §2 table — engine team and animation team key off the same 0–6 map.

**Day-1 minimum viable handoff:** `dispositionState` (7 poses) + `idle_breathe` + `feedBone` chew + `isGenerating` thinking loop. Everything else (continuous axes, extra idles, search/respond/error polish) is additive and won't break the contract.