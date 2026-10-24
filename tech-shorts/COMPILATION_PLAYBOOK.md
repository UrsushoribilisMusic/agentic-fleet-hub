# Compilation Playbook — for Gem

**Written** 2026-10-24 by Clau · **Owner** Gem · **Channel** The Classical Remix

Three compilations are specified below, ready to build. Everything needed is on
this Mac: all 19 source masters are already in the asset store, so no re-download
and no NotebookLM run is required.

Read §1 for *why these three*, §2 for *what goes in them*, §3 for *how to build one*.
If you only read one section, read §3.

---

## 1 · Why compilations, and why these three

Compilations are the revenue format. Shorts bring views and almost no income;
single explainers monetise thinly. The six live compilations tell a sharp story:

| # | Theme | Watch | Views | Rev | Retention |
|---|---|---|---|---|---|
| 2 | AI Will Do the Work. Who Gets Paid? | **24.2h** | 1,040 | $0.99 | 17% |
| 1 | Does AI Have a Mind? | 9.9h | 159 | $0.85 | 16% |
| 3 | When AI Agents Break Out | 5.1h | 177 | $0.21 | 14% |
| 5 | Can We Trust AI? The Alignment Problem | 0h* | 52 | — | — |
| 4 | How We Build: Engineering in the Age of AI | 1.3h | 106 | $0.08 | 5% |
| 6 | The Global AI Race | 1.1h | 88 | $0.05 | 7% |

\* #5 is public but was missing from `insights.json` — see §5.

**The pattern: the two winners are framed as a human-stakes question. The two
losers are framed as a subject.** "Who gets paid?" and "Does AI have a mind?"
beat "Engineering in the Age of AI" and "The Global AI Race" by roughly 20×.
#6 also only had 3 parts. Compilation #7 ("Why Smart People Struggle With AI",
30 min) retains **3%** — a long block of weak parts does not survive contact.

Second signal, and it is counter-intuitive: as *single* videos, Economy & Work is
the **worst** topic on the channel ($0.024/video). As a *compilation* it is the
**best**. The money question will not hold a 5-minute slot but will hold a
38-minute one. **Do not read single-video performance as compilation potential.**

So each compilation below (a) repeats a theme that already worked, (b) has a
proven high-watch anchor as its opener, (c) runs 33–38 min like the winners, and
(d) is titled as a question a person would actually ask.

---

## 2 · The three compilations

Running order is the order listed — that *is* the edit. The opener is the
highest-watch part in each set; that is deliberate, do not re-sort.

Get the exact in/out trim points at any time with:

```bash
cd ~/projects/agentic-fleet-hub/tech-shorts
python3 -I comp_parts.py C1 C2 C3
```

### C1 — "AI Will Do the Work, Vol. 2"
*Working title. Topic: Economy & Work. ~33m11s of parts.*
Direct sequel to the best-performing compilation on the channel.

| # | Video ID | Part |
|---|---|---|
| 1 | `7UPyRA9cBtE` | The AI Bottleneck: Exponential Models, Linear World |
| 2 | `lChiYc1A4B8` | How AI Reshapes Jobs, Growth & Unemployment (Anthropic 2026–2030) |
| 3 | `Vritr444eKs` | The Grammar of Work: How LLMs Learn Career Moves |
| 4 | `jxi-GUpdhYI` | The Catch-22 of the AI Economy |
| 5 | `Miw8TeG3RFI` | Will AI Create Jobs or Destroy Them? The Jevons Paradox |
| 6 | `JFhLTSY7Pxw` | The White-Collar Bypass: How AI Is Erasing Entry-Level Jobs |

Part 3 retains only 2% as a standalone — it sits mid-block deliberately, where a
weak part costs least. Part 6 retains 46% and is the strongest closer available.

### C2 — "The Attack Surface in Your House"
*Working title. Topic: AI Threats & Security. ~35m20s of parts.*
AI Threats & Security earns the most revenue per video of any topic ($0.261,
roughly 2× the next). The domestic framing — it is in your TV, not in a lab — is
the human-stakes angle that #1 and #2 had.

| # | Video ID | Part |
|---|---|---|
| 1 | `ECuneH0hPcg` | Japan Tested US vs Chinese AI on Real Hacking |
| 2 | `KbxsK1LlVSw` | Secure Your API Keys: Stolen Keys as the AI Underworld's Free Weapon |
| 3 | `n0J3a4-1rmY` | Two Students Built an AI Zero-Day Factory |
| 4 | `D-LV9YJN2ZM` | The Convenience Paradox: Why the Internet of Things is Melting |
| 5 | `GLLa6t_MQuA` | The Convergence Point: When AI Worms Self-Replicate on Smart TVs |
| 6 | `lZ_LLtp8Ulo` | The Shadow Datacenter: Why AI Worms Are Targeting Your Smart TV |
| 7 | `cRgmoG-XqkQ` | Models as Insider Risks: Why AI Agents Need Zero-Trust Authority |

Parts 4–6 are a tight three-video arc built in one week — that run is the spine.
Part 7 retains 55%, the best closer in the set.

**Do not merge this with compilation #8**, which is already queued with five
different security parts. Ship #8 as planned; this is Vol. 2.

### C3 — "Alien Minds, Vol. 2"
*Working title. Topic: Consciousness & Mind. ~34m51s of parts.*
Compilation #1 proved the appetite ($0.85 on only 159 views). This bench has
4.95h of watch time already banked across its parts.

| # | Video ID | Part |
|---|---|---|
| 1 | `ygFTq74Vs9I` | An Alien Mind: OpenAI's Chief Scientist Sounds the Alarm |
| 2 | `hRW9NgbagLU` | Memento Is an Old AI. Misaligned Is the Next One. |
| 3 | `QKBBcGqJQ0I` | Indicators of Consciousness in AI |
| 4 | `Z71EvBczPiQ` | Is AI Conscious? Every Argument For and Against |
| 5 | `ckNAJdh26Sg` | The Flickering Mind: Why Consciousness Switches 15 Times a Second |
| 6 | `LCn_xfbxfeA` | The Autocomplete Theory of Everything |

Ranked third of the three: more banked watch time than C1 and C2, but lower
average retention (15%), so build it after the other two.

---

## 3 · How to build one

### 3.0 Where the sources are

Every part's master is already on disk. `comp_parts.py` resolves a YouTube video
id to its master via `jobs.json`; never guess from the slug — several asset-store
folder names do not match their published titles.

Two kinds of master exist, and the difference matters:

* **`raw_cinematic.mp4`** — the NotebookLM export. No channel hook card, no
  SUBSCRIBE outro. **This is what a compilation chapter wants.** It carries a
  consistent **~3.6s of trailing silence** that must come off.
* **`final_long.mp4`** — the published video. Carries *both* cards. Nine of the
  nineteen parts have only this. For those you must cut **both ends**: the hook
  card off the front, the SUBSCRIBE card off the back. Measured intro+outro
  across the archive is 18–24s combined — **it is not a constant, do not assume
  a fixed number.**

### 3.1 Trim each part

`comp_parts.py` proposes in/out points: `in` = 0 for raw masters, or the first
hard scene cut after 3s for `final_long`; `out` = the start of the trailing
silence that runs to EOF, plus 0.15s so the last word is not clipped. The same
audio-driven logic already lives in `pipeline.content_audio_end()` — reuse that
rather than writing a third copy.

**Verify every `final_long` row by eye before cutting.** Two are already known
to need a human look:

* `ygFTq74Vs9I` — scene detection found no cut in 3–40s and returned `in = 0.00`,
  so the hook card is probably still attached.
* `hRW9NgbagLU` — `in = 34.35s` is far longer than any other hook card.

Check a proposed boundary by pulling the frame on each side:

```bash
ffmpeg -ss <in> -i <master> -frames:v 1 -y /tmp/in.png
ffmpeg -ss <out> -i <master> -frames:v 1 -y /tmp/out.png
```

Then cut, re-encoding (stream copy will not cut cleanly on a non-keyframe):

```bash
ffmpeg -i <master> -ss <in> -to <out> \
  -vf scale=1920:1080 -r 30 -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -ar 44100 -ac 1 part_<n>.mp4
```

All parts must share resolution, frame rate and audio layout before concat, or
the concat filter will fail or drift out of sync.

### 3.2 The intro — two 10-second motion clips

**Never open on a still title card.** A/B on this channel showed a
motion-opener compilation took 2.4× the watch-hours of a still-opener one.

Generate **two 10s clips per compilation** and cut them back to back for a ~20s
cold open, under the channel hook VO. Clip A is the hook (the unsettling image);
clip B widens out and lands on the question. Both are 16:9, 1920×1080, 30fps, no
text and no on-screen words — the title card is composited over clip B afterwards.

Shared style suffix — append to every prompt below:

> Cinematic documentary photography, shallow depth of field, anamorphic lens,
> subtle film grain, muted teal-and-amber palette, slow deliberate camera motion,
> no text, no captions, no logos, no people looking at camera. 16:9, 1920x1080, 30fps.

**C1 — "AI Will Do the Work, Vol. 2"**

> **Clip A (10s):** An empty open-plan office at dawn, long rows of identical
> desks, every monitor glowing with scrolling output that nobody is reading. A
> single chair slowly rotates on its own. Camera pushes forward down the aisle at
> walking pace. Cold blue window light, warm desk lamps. *[+ style suffix]*

> **Clip B (10s):** Close on a payslip-sized sheet of paper on an empty desk, its
> printed figures dissolving into drifting particles that rise and scatter.
> Camera pulls back and up to reveal the whole floor of desks below, now lit only
> by screens. *[+ style suffix]*

**C2 — "The Attack Surface in Your House"**

> **Clip A (10s):** A dark suburban living room at night, lit only by a large
> smart TV showing static. The standby LEDs of a router, a speaker and a thermostat
> pulse out of sync in the foreground. Camera drifts slowly sideways past them.
> *[+ style suffix]*

> **Clip B (10s):** Macro on the back of the television — ports, a blinking
> ethernet light — then the reflection in the dark screen reveals the entire house
> glowing with dozens of small connected lights. Camera pulls back through the
> doorway. *[+ style suffix]*

**C3 — "Alien Minds, Vol. 2"**

> **Clip A (10s):** An enormous dark server hall seen from a low angle, a single
> maintenance lamp swinging gently and throwing moving shadows across endless
> identical racks. Dust drifts in the beam. Camera tilts slowly upward.
> *[+ style suffix]*

> **Clip B (10s):** Extreme close-up of a human eye, the iris slowly resolving
> into a lattice of faint moving connections, then pulling back to reveal it is a
> reflection on the curved glass of a dark monitor in an empty room.
> *[+ style suffix]*

Then build the standard channel intro over them and the standard SUBSCRIBE outro
at the end — the compilation gets the channel intro/outro exactly once, which is
the whole reason the per-part cards are stripped in §3.1.

### 3.3 Transition cards between chapters

One card before each part **after the first** (so 5 cards for C1 and C3, 6 for C2).
Each is a 4-second full-frame card: the part number small, the line large, held
on a slow push-in over a dimmed still from the part that follows, with a 0.5s
crossfade in and out. Keep the lines short — they are read in under two seconds.

**C1 — AI Will Do the Work, Vol. 2**

| Before part | Card |
|---|---|
| 2 | **TWO** — The models move exponentially. The world does not. |
| 3 | **THREE** — What a career looks like to a language model. |
| 4 | **FOUR** — Someone has to pay for the boom. |
| 5 | **FIVE** — Cheaper work has never meant less work. Until now? |
| 6 | **SIX** — The jobs that taught you the job are going first. |

**C2 — The Attack Surface in Your House**

| Before part | Card |
|---|---|
| 2 | **TWO** — The keys were never the hard part. |
| 3 | **THREE** — Two students. One pipeline. Every exploit. |
| 4 | **FOUR** — Everything in your house is now a computer. |
| 5 | **FIVE** — And computers can be told to copy themselves. |
| 6 | **SIX** — Your television has more idle compute than you think. |
| 7 | **SEVEN** — The threat with your own credentials. |

**C3 — Alien Minds, Vol. 2**

| Before part | Card |
|---|---|
| 2 | **TWO** — Memory is what makes a self. What happens without it? |
| 3 | **THREE** — If it were conscious, how would we know? |
| 4 | **FOUR** — The scientists do not agree. Here is every argument. |
| 5 | **FIVE** — Your own mind flickers fifteen times a second. |
| 6 | **SIX** — Maybe prediction is all any mind ever was. |

### 3.4 Assemble

Concat intro + (card, part)… in the running order of §2, re-encoding once:

```bash
ffmpeg -f concat -safe 0 -i parts.txt \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 final_comp.mp4
```

Target 35–38 min finished. That is where the winners sit.

### 3.5 Metadata, captions, upload

* Title: a question, not a subject. The working titles in §2 are starting points.
* Description: list the chapters with YouTube timestamps (`0:00`, `3:41`, …) —
  chapter markers are what make a 38-minute block browsable.
* Link each part's original video in the description.
* Captions: `subs_gen.py` on the final file, `en,de,fr,ja`, as per README §7.
* Upload **private** first, review, then publish.

### 3.6 Close the loop — this is the step that gets skipped

1. Add the new compilation to `tech-shorts/compilations.json`: `n`, `id` (the
   YouTube id), `title` **exactly as published**, `published`, `topic`, `status`,
   and `members` listing each part's published title verbatim.
2. Re-run `python3 gen_insights.py` (it pushes to the droplet unless you pass
   `--no-push`).
3. Confirm the new row appears in §4 of `https://api.robotross.art/fleet/insights/`.

A compilation that is not in `compilations.json` is invisible to the dashboard,
and the parts keep showing "—" in the Comp column.

---

## 4 · Definition of done

- [ ] All parts trimmed; no hook card or SUBSCRIBE card survives inside the block
- [ ] Both `final_long`-sourced boundaries eyeballed, `ygFTq74Vs9I` and `hRW9NgbagLU` especially
- [ ] 20s motion cold open, no still title card
- [ ] Transition card before every part after the first
- [ ] Channel intro and outro present exactly once
- [ ] 35–38 min finished
- [ ] Chapter timestamps in the description
- [ ] Captions generated
- [ ] Uploaded private, reviewed, then published
- [ ] `compilations.json` updated and `gen_insights.py` re-run
- [ ] Row visible in §4 of the insights dashboard
- [ ] Logged in `standups/YYYY-MM-DD.md`

---

## 5 · Open items Clau did not finish

**`gen_insights.py` was losing videos.** The YouTube uploads playlist lists some
videos more than once (367 entries, 356 unique). Chunking that duplicated list
50 at a time made `videos().list` dedupe inside a chunk, so `insights.json` ended
up with 351 records covering only **337 unique videos** — 14 duplicate rows and
19 videos missing outright, compilation #5 among them. Fixed on 2026-10-24 by
deduplicating in `channel_uploads`, **but the fix has not been run yet**. The
next `gen_insights.py` run proves it: expect ~356 records, zero duplicates, and
compilation #5 to appear in §4 with real numbers instead of zeros.

**Three new topics were added** to `TOPIC_RULES`: `Science & Discovery`,
`Compute & Energy`, `Working With AI`. October's "Other" rate drops from 52% to
4%. These are also unproven until a regen runs — check the pill colours render
(`c-lime`, `c-amber`, `c-rose` were added to the dashboard CSS).

**Compilations #5 and #7** had wrong metadata in `compilations.json`; both are
public and both were corrected against the YouTube Data API on 2026-10-24. #7 was
retitled to its published title and moved to the new `Working With AI` topic.

**`Working With AI` is worth watching as a format, not just a topic.** It is the
largest of the three new topics by watch time (5.9h), and "How to Be More
Ambitious: A Tutorial for Humans with Models" alone carries 4.2h of that — the
fastest-accumulating single video on the channel, 285 views in eight days. It was
invisible before because it classified as "Other". If it keeps that pace it is a
fourth compilation, and a strong one.
