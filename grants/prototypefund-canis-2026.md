# Prototype Fund CH 2026–27 — Canis application (DRAFT v2, mapped to the real form)

> **Portal:** https://prototypefund-app.opendata.ch/myapplication · **Deadline:** 6 Sept 2026 EOD · English · up to **CHF 50k/team**
> Fields below mirror the actual form (with char limits). **[BRACKETS] = Miguel to fill/decide.** Answers are first-draft, trimmed toward the limits.
> New to-dos this form surfaced: **(a) record a ≤3-min video pitch**, **(b) budget assumes ~5% of your time donated in-kind**, **(c) lead partners are SCRAI + WWF One Planet Lab** (pick a Challenge Owner).

---

## PROJECT

**Project name** *(max 80)*
Canis: an on-device dog that shows when an AI is unsure or evasive

**Describe in 2–3 sentences** *(max 600)*
Canis is an open, on-device iOS app that reads a language model's internal "disposition" — confidence, uncertainty, evasiveness, concern — and shows it in real time as the expression of a dog, before the model even finishes answering. It runs small open-weight models (Switzerland's Apertus, and Ministral) fully on the phone, with nothing sent to the cloud. The goal is to make an AI's hidden state legible to any person, so they can calibrate how much to trust a given answer.

**Challenge area (select one + optionally why)**
[Pick from dropdown — best fit: **Transparency & Explainability / Public-interest Technology**.] Why: Canis turns model interpretability, today an expert lab technique, into an everyday, on-device trust signal for the public.

**Concrete problem you address + why relevant now** *(max 600)*
People increasingly act on answers from AI systems they cannot see inside. A model that is guessing, hedging, or evading produces text that looks exactly as fluent and confident as text it is sure about — so the only signal users get actively hides the model's real state, driving misplaced trust. Interpretability research can read some of that state, but it lives in notebooks and papers, runs in the cloud on closed models, and is unreadable to non-experts. As on-device AI reaches millions of phones, there is no accessible, real-time way for an ordinary person to see when their model is uncertain or evasive. That gap is what makes this urgent.

**Proposed solution, prototype, and MVP** *(max 600)*
We build an open-source iOS app plus a reusable "disposition-lens" library. At generation time it reads the model's internal signals and shows disposition (confident / uncertain / curious / concern / reluctant / evasive) through an expressive dog avatar. MVP: Apertus-4B running fully on-device via Apple's MLX, disposition surfaced through a forward-only method (see technical section), a legible avatar, shipped to TestFlight. Success = a person watching the dog can tell when the model is unsure or evading, on their own phone, offline.

**How does it contribute to Responsible & Sustainable AI?** *(max 1200)*
Transparency & Explainability (core): Canis exposes a model's hidden disposition so users can see uncertainty and evasiveness rather than a uniformly confident wall of text. Accountability & Governance: an accessible trust signal lets users — and eventually organizations — keep a human in the loop and challenge AI output on an informed basis. Safety & Robustness: a safety override surfaces "concern/reluctance" states so risky or evasive responses are visibly flagged. Environmental Sustainability: it runs on small open-weight models, fully on-device — no data-center inference, minimal energy, works offline — advancing the case that useful AI need not be centralized or large. Public-interest Technology: the method is open-sourced as a reusable library so any builder can add honest trust signals to their own on-device apps, and it is built on Apertus, Switzerland's sovereign public model. Long-term Societal Impact: it strengthens AI literacy by making an abstract idea — model uncertainty — something anyone can literally see.

**Exploration: what questions will your prototype answer? What does success look like during/after?** *(max 600)*
Core questions: Can a cheap, forward-only signal reliably flag uncertainty and evasiveness on a phone, without gradients or a second forward pass? What does an *honest* disposition UX look like for non-experts — one that informs without overclaiming? Where does a small on-device model's disposition read break down? Success during: a working app + a documented, reusable method + an honest map of what it does and does not detect. Success after: adoption of the open library by other on-device builders, and a reference point for lightweight, accessible AI-trust signals.

**Intended users; how you involve + validate them** *(max 600)*
Primary users: everyday users of on-device AI who need an honest trust cue, and AI-literacy educators who need to *show* people what uncertainty/evasiveness looks like. We involve them via a TestFlight cohort (recruited through the Apertus hackathon community and educator contacts) and iterate on whether they can correctly read the model's state from the avatar. Validation: task-based sessions comparing users' trust calibration with and without Canis, plus qualitative feedback on legibility.

**Governance/organizational/legal/ethical/societal questions it raises; how it helps deploy AI more responsibly** *(max 1200)*
Canis raises the question of how to represent a model's internal state honestly to a lay audience without implying more certainty about the *signal* than is warranted — the meta-transparency problem. It surfaces the ethical risk of a "trust theater" where a friendly avatar over-reassures; we address this by publishing the method's limits alongside it. Organizationally, a legible disposition signal points toward better human-in-the-loop patterns: where a model shows uncertainty or evasiveness, workflows can route to human review. Legally/ethically, it touches how we communicate AI reliability to non-experts and avoid overclaiming. For organizations, an open, on-device disposition read offers a lightweight oversight primitive — a way to make model hesitation visible in the interface rather than buried in logs — that they can adopt without sending data to third parties.

**Sustainable AI / digital sufficiency: what consumption questions do you address; how help deploy AI more sufficiently** *(max 1200)*
Canis is a concrete argument for digital sufficiency: it deliberately uses *small* open-weight models on-device rather than reaching for the largest cloud model, and asks "how much model is actually enough" to deliver a useful, honest experience. For a large class of tasks, a 3–4B on-device model is sufficient — and running it locally removes per-query data-center energy, network cost, and dependence on centralized compute entirely. By making the model's *limits* visible (uncertainty/evasiveness), Canis also helps users right-size their expectations of a small model instead of assuming they need a frontier system. The prototype thus addresses long-term consumption debates twice over: technically (edge inference, no data-center draw) and behaviorally (showing that sufficiency, honestly communicated, can be enough). Organizations could adopt the same pattern — small, local, transparent — to cut the compute and data footprint of many AI features.

**Responsible vs Sustainable AI trade-offs you expect (or why none)** *(max 1200)*
There is a real tension. The most *sustainable* choice — a small model running on-device — can produce a *less* reliable disposition signal than a large cloud model with richer internals, so pushing sustainability could weaken the responsibility signal we are trying to deliver. Conversely, the most legible, richly-explained interpretability would tempt us toward bigger models and cloud compute, undercutting sustainability. Our stance: being transparent about a small model's limits is itself a responsible act, so we treat the trade-off as a design constraint rather than a defect — the prototype's honesty about uncertainty is exactly what a small, sufficient model needs. We expect the prototyping insight to be a practical curve: how much disposition reliability you can get per unit of on-device compute, and where "enough" sits. We do not claim to eliminate the trade-off; we aim to characterize it openly.

**Parameters: choose options + describe your response** *(select + max 600)*
[Choose from dropdown — primary focus: **Transparency & Explainability** + **Environmental Sustainability / digital sufficiency**.] Describe: Our focus sits where transparency meets sufficiency — an honest, accessible trust signal delivered by the smallest, most local model that will do the job. Expected difficulty: keeping the signal reliable and non-misleading as we shrink the model and move fully on-device; ideal outcome: a documented reliability/compute curve plus an open method others can reuse.

**Prior art: what exists, how you differ / build beyond** *(max 600)*
Logit-lens and probing methods exist in research, but as cloud/notebook tooling on closed or large models, for experts. Uncertainty estimation (entropy, calibration) exists but yields a number, not something a lay user reads. Canis's contribution: a forward-only, on-device, real-time disposition read cheap enough to run on a phone, packaged as an accessible signal for non-experts, on open-weight models. The de-risking insight — that you can get a useful disposition signal without the full autodiff Jacobian — is the transferable core, and we publish it openly. We build on our own working disposition-lens prototype.

---

## FEASIBILITY & TEAM

**Planned technical implementation (AI methods, models, datasets, stack, infra) + division of work** *(max 600)*
Stack: Apple **MLX** on-device. Disposition read is **forward-only**: a closed-form logit-lens at a mid layer (J = lm_head·(ln_weight/std(h_mid))), plus **seed-vector matching** and an **entropy** axis — a marginal cost on the forward pass the model already runs, no gradients, no second pass. Resolution across ~8 states with a weight-gate + entropy + safety override. Backends: **Apertus-4B** and **Ministral-3B** (open weights). Front-end: SwiftUI parametric dog avatar. No user data collected; no external datasets required. Work split: [Miguel — ML/MLX + iOS; Team member 2 — [eval/design]].

**Why is your team well-suited? (experience + links)** *(max 600)*
[Miguel Rodriguez / Big Bear Engineering] — on-device ML with MLX, iOS engineering, and the author of the Canis disposition-lens prototype; also builds Sovereign Mind (on-device RAG). Prior work: canis.flotilla.cc (live demo), [GitHub link], [Sovereign Mind]. [Team member 2 — add expertise + links.]

**Competencies/resources you lack + workaround** *(max 600)*
[We are strong on on-device ML and iOS; we would strengthen interpretability *evaluation* and product design.] Workaround: recruit one teammate from the Apertus hackathon with [evaluation/design] strength, and draw on SCRAI mentorship offered through the programme for the responsible-AI evaluation framing.

**Where does the project stand today?** *(max 600)*
Existing prototype + research. The disposition-lens method works and there is a live gated web demo (canis.flotilla.cc); the forward-only approach (logit-lens + seed vectors + entropy) is validated conceptually. What we have not yet built is the on-device MLX port on Apertus-4B, the accessible avatar UX, the reliability/limits evaluation, and the extracted open-source library — which is precisely the 4-month prototyping scope.

**Four most important milestones** *(max 600)*
1) Kickoff (Apertus hackathon, 1–16 Oct): forward-only disposition read running on-device on Apertus-4B, end to end. 2) Robust disposition + entropy/safety states + avatar mapping + TestFlight alpha. 3) Second backend (Ministral) + reliability/limits evaluation + extracted open-source disposition-lens library with docs. 4) Public gated demo + governance/limits write-up + Final Pitch (11 Feb 2027).

**How could it continue beyond the Prototype Fund?** *(max 600)*
Technical: the library is model-agnostic across open-weight LLMs and transfers to any MLX/on-device stack. Adoption: App Store release of Canis + the open library for other on-device builders. Organizational: fold into Big Bear Engineering's on-device/open work; disseminate via the Apertus community and AI Summit Geneva 2027. Replication: the documented method lets others add disposition read-outs to their own apps.

**Main risks + mitigation** *(max 600)*
Technical: a small on-device model's disposition signal may be noisy — mitigate with the reliability/limits evaluation and by only surfacing states we can support. Ethical/societal: a friendly avatar could over-reassure ("trust theater") — mitigate by publishing limits and by never implying certainty we lack. Data protection: minimal — everything runs on-device, no user data leaves the phone. Legal: use models within their open-weight licenses.

**Insights for others (responsible AI / governance / policy / public-interest tech)** *(max 600)*
A reproducible, forward-only method for lightweight on-device disposition/uncertainty signalling, plus an honest account of where it works and fails — a template others can adopt to add trust signals to their own apps. Governance insight: how far a cheap, local signal can support human oversight of AI, and what "honest enough" communication of model uncertainty to non-experts looks like in practice.

---

## PARTNERS

**Which Challenge Owner / partner would you most like to work with?** *(max 600)*
[SCRAI — Swiss Centre for Responsible AI] for the responsible-AI framing and evaluation of the disposition signal; and, where possible, an AI-literacy / digital-education partner to validate legibility with non-expert users.

**Why? (additional partners to loop in)** *(max 600)*
SCRAI's responsibility/evaluation expertise directly strengthens the honesty and limits work, which is the crux of the project. An education/literacy partner would give us a real non-expert user group for validation and dissemination. [Add any named contacts.]

**Additional information for evaluation** *(max 600)*
Live demo: canis.flotilla.cc. The project is built on Switzerland's Apertus model and dovetails with the Apertus hackathon (1–16 Oct), which serves as the prototyping kickoff. [Add links: GitHub, disposition-lens write-up, Sovereign Mind.]

**Video pitch link (≤3 min)** *(URL)*
[TO RECORD — Miguel: a fresh ≤3-min pitch of the vision, not an existing promo. Placeholder: https://...]

---

## FINANCIALS
> Voucher up to CHF 50k. The fund expects ~5% of your working time donated in-kind. Can exceed 50k only with strong justification.

**Total budget (CHF):** [~50,000]
**Personnel (up to 10 functions; Name & function / Daily rate CHF excl. VAT, min 150 / Total):**
- [Miguel Rodriguez — Lead ML/iOS] · rate [CHF ___] · days [__] · total [CHF ___]
- [Team member 2 — eval/design] · rate [CHF ___] · days [__] · total [CHF ___]
**Non-personnel (up to 10):** [Apple Developer + devices ~CHF ___; demo hosting ~CHF ___; avatar design assets ~CHF ___; event travel ~CHF ___]
**Budget explanation** *(max 600):* [Brief: majority is prototyping labor for the on-device port, evaluation, and open library; non-personnel covers devices, the public demo, design of the avatar rig, and mandatory-event travel. ~5% of lead time contributed in-kind.]

---

## TEAM
**How many people?** [2 or 3]
**Team member 1:** Name Miguel Rodriguez · Gender [__] · Year of birth [__] · LinkedIn [__] · GitHub [__] · Email miguel@bigbearengineering.com · Phone [+41 __] · Country of residence [Switzerland] · Citizenship [__] · Educational background [__]
**Team member 2:** [recruit from hackathon — all same fields]

---

## FORMAL REQUIREMENTS (checkboxes — all must be ticked)
1. ☐ Understand a prototyping "journey" is defined at the mid-October kickoff.
2. ☐ Confirm contribution to Responsible & Sustainable AI **and the open-source ecosystem** (code, docs, reusable components, datasets, publications, or openly accessible outputs); document work + share learnings publicly. → **matches our plan.**
3. ☐ Confirm contribution to insights documentation; work with **SCRAI** and **WWF One Planet Lab**; contributions published at events, public statements, summits, white papers, research, and/or policy recommendations.
4. ☐ Understand the Prototype Fund will mention/promote the idea; we may co-promote.
5. ☐ Jury conflict-of-interest question: [answer — likely "no relationship"].

## DOCUMENT UPLOAD / ATTACHMENTS
[Prepare: Canis demo link/screens, disposition-lens method write-up, any prior-work links, team CVs/portfolios.]

---

## OPEN ITEMS (Miguel — critical path to Sept 6)
1. **Recruit 1–2 teammates** (Apertus hackathon) — hard requirement (2–3 at each event) + fills the eval/design gap.
2. **Record the ≤3-min video pitch** (new, mandatory).
3. **Budget:** real daily rates + days + non-personnel numbers; remember ~5% in-kind.
4. **Personal fields** for team member 1 (gender, YOB, LinkedIn, GitHub, phone, residence, citizenship, education) + entity (Big Bear Engineering) confirmation for post-approval.
5. **License pick** (MIT vs Apache-2.0) for the open library.
6. **Pick the challenge area** from the portal dropdown + confirm SCRAI/education partner choice.
7. Log in, paste field-by-field, watch the character counters (limits noted above), upload attachments, submit.
