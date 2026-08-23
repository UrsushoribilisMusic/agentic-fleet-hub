# Prototype Fund CH 2026–27 — Canis application (DRAFT v3)

> **Portal:** https://prototypefund-app.opendata.ch/myapplication · **Deadline:** 6 Sept 2026 EOD · English · up to **CHF 50k/team**
> **Decisions locked:** Challenge area = *Agentic AI — Trust & Accountability* · License = *MIT* · Team = *Miguel + 1 co-participant (recruit at Apertus hackathon)* · Challenge Owner = *Apertus AI + SCRAI*.
> **Big Bear Engineering removed** (in liquidation) — ⚠️ new legal entity needed for post-approval (see open items).
> Fields mirror the real form with char limits. **[BRACKETS] = still to fill.**

---

## PROJECT

**Project name** *(max 80)*
Canis: an on-device dog that shows when an AI is unsure or evasive

**Describe in 2–3 sentences** *(max 600)*
Canis is an open, on-device iOS app that reads a language model's internal "disposition" — confidence, uncertainty, evasiveness, concern — and shows it in real time as the expression of a dog, before the model even finishes answering. Users can load their own documents to build specialized on-device knowledge packs, and the dog answers from them — its face revealing when it is grounded, guessing, or evading. It runs small open-weight models (Switzerland's Apertus, and Ministral) fully on the phone, nothing sent to the cloud.

**Challenge area (select + why)**
**Agentic AI & Digital Identity: Building Trust & Accountability and Autonomous Systems.** Why: as AI shifts from answering to *acting* autonomously, the missing safety layer is knowing when a model or agent is uncertain, evasive, or concerned — before it acts. Canis is exactly that: a real-time, on-device read of an AI's disposition, made legible to the person relying on it. It puts trust and accountability for autonomous systems into the interface, not buried in logs.

**Concrete problem you address + why relevant now** *(max 600)*
People increasingly act on — and increasingly delegate to — AI systems they cannot see inside. A model or agent that is guessing, hedging, or evading produces output that looks exactly as fluent and confident as output it is sure about, so the only signal users get actively hides its real state, driving misplaced trust. As AI becomes agentic and on-device, this opacity moves from annoying to risky: the interpretability that could reveal the model's state lives in expert notebooks, in the cloud, on closed models. There is no accessible, real-time way for an ordinary person to see when their AI is uncertain or evasive. That gap is what makes this urgent.

**Proposed solution, prototype, and MVP** *(max 600)*
Canis is an open iOS app + a reusable disposition-lens library. At generation time it reads the model's internal signals and shows disposition — confident / uncertain / curious / concern / reluctant / evasive — through an expressive dog. Users load their own documents to build specialized on-device knowledge packs ("RAGs"), and the dog answers from them, its face revealing when it is grounded, guessing, or evading. MVP: Apertus-4B fully on-device via Apple MLX, a forward-only disposition read, a legible avatar, and basic personal-RAG import, shipped to TestFlight. Success: a person can see, offline, when their AI is unsure — or unsupported by their own documents.

**How does it contribute to Responsible & Sustainable AI?** *(max 1200)*
Transparency & Explainability (core): Canis exposes a model's hidden disposition, so users see uncertainty and evasiveness instead of a uniformly confident wall of text — and, paired with on-device personal RAG, it visibly shows when an answer is grounded in the user's own documents versus guessed, making hallucination legible. Accountability & Governance: as AI becomes agentic, an accessible, real-time disposition read lets a person keep autonomous systems in check and challenge output on an informed basis. Safety & Robustness: a safety override surfaces concern/reluctance states so risky or evasive responses are flagged. Environmental Sustainability: it runs on small open-weight models, fully on-device — no data-center inference, minimal energy, works offline — advancing the case that useful AI need not be centralized or large. Public-interest Technology: the method ships as a reusable, MIT-licensed library so any builder can add honest trust signals to their own apps, built on Apertus, Switzerland's sovereign public model. Long-term Societal Impact: it strengthens AI literacy by making model uncertainty something anyone can literally see.

**Exploration: what questions will your prototype answer? What does success look like during/after?** *(max 600)*
Core questions: Can a cheap, forward-only signal reliably flag uncertainty and evasiveness on a phone, without gradients or a second forward pass? What does an *honest* disposition UX look like for non-experts — one that informs without overclaiming? Where does a small on-device model's disposition read break down, especially over a user's own documents? Success during: a working app + a documented, reusable method + an honest map of what it does and does not detect. Success after: adoption of the open library by other on-device builders, and a reference point for lightweight, accessible AI-trust signals.

**Intended users; how you involve + validate them** *(max 600)*
Primary users: everyday users of on-device AI who want an honest trust cue, plus AI-literacy educators who need to *show* what uncertainty and evasiveness look like. Personal RAGs make it sticky and personal — people build specialized knowledge packs (a hobby, a course, a manual) and enjoy watching the dog reason honestly over their own material. We involve users via a TestFlight cohort (recruited through the Apertus hackathon + educator contacts) and iterate on whether they can correctly read the dog's state. Validation: task-based sessions comparing trust calibration with vs without Canis, plus feedback on legibility and on the RAG-building experience.

**Governance/organizational/legal/ethical/societal questions it raises; how it helps deploy AI more responsibly** *(max 1200)*
Canis raises the question of how to represent a model's internal state honestly to a lay audience without implying more certainty about the *signal* than is warranted — the meta-transparency problem. It surfaces the ethical risk of a "trust theater" where a friendly avatar over-reassures; we address this by publishing the method's limits alongside it. With personal RAG it raises data-governance questions too — which we answer structurally by keeping every document and embedding on-device, so nothing leaves the phone. Organizationally, a legible disposition signal points toward better human-in-the-loop patterns: where a model shows uncertainty or evasiveness, workflows can route to human review. For organizations, an open, on-device disposition read offers a lightweight oversight primitive — making model hesitation visible in the interface rather than buried in logs — adoptable without sending data to third parties.

**Sustainable AI / digital sufficiency: what consumption questions do you address; how help deploy AI more sufficiently** *(max 1200)*
Canis is a concrete argument for digital sufficiency: it deliberately uses *small* open-weight models on-device rather than reaching for the largest cloud model, and asks "how much model is actually enough" to deliver a useful, honest experience. For a large class of tasks — including answering over a user's own documents — a 3–4B on-device model is sufficient, and running it locally removes per-query data-center energy, network cost, and dependence on centralized compute entirely. By making the model's *limits* visible (uncertainty/evasiveness/ungroundedness), Canis also helps users right-size their expectations of a small model instead of assuming they need a frontier system. It thus addresses long-term consumption debates twice over: technically (edge inference, no data-center draw) and behaviorally (showing that sufficiency, honestly communicated, can be enough). Organizations could adopt the same pattern — small, local, transparent — to cut the compute and data footprint of many AI features.

**Responsible vs Sustainable AI trade-offs you expect (or why none)** *(max 1200)*
There is a real tension. The most *sustainable* choice — a small model running on-device — can produce a *less* reliable disposition signal than a large cloud model with richer internals, so pushing sustainability could weaken the responsibility signal we are trying to deliver. Conversely, the most legible, richly-explained interpretability would tempt us toward bigger models and cloud compute, undercutting sustainability. Our stance: being transparent about a small model's limits is itself a responsible act, so we treat the trade-off as a design constraint rather than a defect — the prototype's honesty about uncertainty is exactly what a small, sufficient model needs. We expect the prototyping insight to be a practical curve: how much disposition reliability you get per unit of on-device compute, and where "enough" sits. We do not claim to eliminate the trade-off; we aim to characterize it openly.

**Parameters: choose options + describe your response** *(select + max 600)*
[Portal dropdown — primary focus: **Transparency & Explainability** + **Accountability** + **Environmental Sustainability / digital sufficiency**.] Describe: Our focus sits where transparency and accountability meet sufficiency — an honest, accessible trust signal delivered by the smallest, most local model that will do the job. Expected difficulty: keeping the signal reliable and non-misleading as we shrink the model and move fully on-device; ideal outcome: a documented reliability/compute curve plus an open method others can reuse.

**Prior art: what exists, how you differ / build beyond** *(max 600)*
Logit-lens and probing methods exist in research, but as cloud/notebook tooling on closed or large models, for experts. Uncertainty estimation (entropy, calibration) exists but yields a number, not something a lay user reads. On-device RAG apps exist, but none pair grounding with a live, legible honesty signal. Canis's contribution: a forward-only, on-device, real-time disposition read cheap enough to run on a phone, packaged as an accessible signal for non-experts, over open-weight models and the user's own documents. The de-risking insight — that a useful disposition signal is obtainable without the full autodiff Jacobian — is the transferable core, and we publish it openly. We build on our own working disposition-lens prototype.

---

## FEASIBILITY & TEAM

**Planned technical implementation (AI methods, models, datasets, stack, infra) + division of work** *(max 600)*
Stack: Apple MLX on-device. Disposition read is forward-only: a closed-form logit-lens at a mid layer (J = lm_head·(ln_weight/std(h_mid))), plus seed-vector matching and an entropy axis — a marginal cost on the forward pass, no gradients, no second pass. Resolution over ~8 states with a weight-gate + entropy + safety override. Personal RAG: on-device embeddings + a local vector store, so documents never leave the phone. Backends: Apertus-4B and Ministral-3B (open weights). Front-end: SwiftUI parametric dog avatar. No user data collected. Work split: Miguel — ML/MLX, RAG, iOS; co-participant — evaluation + product/UX design.

**Why is your team well-suited? (experience + links)** *(max 600)*
Miguel Rodriguez — independent engineer specializing in on-device ML (Apple MLX) and iOS; author of the Canis disposition-lens prototype and of Sovereign Mind (on-device RAG for teams), which brings the RAG engineering in-house. Prior work: canis.flotilla.cc (live demo), [GitHub link], [Sovereign Mind link]. Co-participant (to recruit at the Apertus hackathon): strengthens interpretability evaluation + product/UX design.

**Competencies/resources you lack + workaround** *(max 600)*
We are strong on on-device ML, RAG, and iOS. We would strengthen interpretability *evaluation* (rigorously characterizing when the disposition signal is reliable) and product/UX design for non-experts. Workaround: recruit one co-participant at the Apertus hackathon with an evaluation or design background, and draw on the SCRAI mentorship offered through the programme for the responsible-AI evaluation framing.

**Where does the project stand today?** *(max 600)*
Existing prototype + research. The disposition-lens method works and there is a live gated web demo (canis.flotilla.cc); the forward-only approach (logit-lens + seed vectors + entropy) is validated conceptually, and we have on-device RAG experience from Sovereign Mind. What we have not yet built is the on-device MLX port on Apertus-4B, the accessible avatar UX, the personal-RAG integration, the reliability/limits evaluation, and the extracted open-source library — precisely the 4-month prototyping scope.

**Four most important milestones** *(max 600)*
1) Kickoff (Apertus hackathon, 1–16 Oct): forward-only disposition read on-device on Apertus-4B, end to end. 2) Robust disposition + entropy/safety states + avatar mapping + basic personal-RAG import + TestFlight alpha. 3) Second backend (Ministral) + reliability/limits evaluation + extracted MIT-licensed disposition-lens library with docs. 4) Public demo + RAG-sharing prototype + governance/limits write-up + Final Pitch (11 Feb 2027).

**How could it continue beyond the Prototype Fund?** *(max 600)*
Technical: the library is model-agnostic across open-weight LLMs and transfers to any MLX/on-device stack. Product: App Store release, and a community commons where people share the specialized RAG packs they build — a marketplace of open, on-device knowledge packs, each answered over honestly by the dog. Organizational: continue as an independent open project under a new lightweight legal entity. Dissemination via the Apertus community and AI Summit Geneva 2027; replication via the documented method.

**Main risks + mitigation** *(max 600)*
Technical: a small on-device model's disposition signal may be noisy — mitigate with the reliability/limits evaluation and by only surfacing states we can support. Ethical/societal: a friendly avatar could over-reassure ("trust theater") — mitigate by publishing limits and never implying certainty we lack. Data protection: minimal by design — model, documents, and embeddings all stay on-device, nothing leaves the phone. Legal: use models within their open-weight licenses.

**Insights for others (responsible AI / governance / policy / public-interest tech)** *(max 600)*
A reproducible, forward-only method for lightweight on-device disposition/uncertainty signalling, plus an honest account of where it works and fails — a template others can adopt to add trust signals to their own apps. Governance insight: how far a cheap, local signal can support human oversight of agentic AI, and what "honest enough" communication of model uncertainty to non-experts looks like in practice.

---

## PARTNERS

**Which Challenge Owner / partner would you most like to work with?** *(max 600)*
Apertus AI — Canis is built on Apertus, so close collaboration on the on-device model is directly valuable to both sides. SCRAI (Swiss Centre for Responsible AI) — for the responsible-AI framing and rigorous evaluation of the disposition signal. Where possible, an AI-literacy / digital-education partner to validate legibility with non-expert users.

**Why? (additional partners to loop in)** *(max 600)*
Apertus AI: we are a real, public-facing showcase of Apertus running on-device, and tight feedback on the model helps both sides. SCRAI: their responsibility/evaluation expertise directly strengthens the honesty-and-limits work that is the crux of the project. An education/literacy partner would give us a genuine non-expert user group for validation and dissemination. [Add named contacts if any.]

**Additional information for evaluation** *(max 600)*
Live demo: canis.flotilla.cc. Canis is built on Switzerland's Apertus model and dovetails with the Apertus hackathon (1–16 Oct), the natural kickoff of the prototyping phase. [Add links: GitHub, disposition-lens write-up, Sovereign Mind.]

**Video pitch link (≤3 min)** *(URL)*
[TO RECORD — a fresh ≤3-min pitch of the vision, not an existing promo. Placeholder: https://...]

---

## FINANCIALS  *(voucher up to CHF 50k; ~5% of working time donated in-kind; exceed 50k only with strong justification)*

**Total budget (CHF):** [~49,000] — *proposed, confirm*

**Personnel (Name & function / Daily rate CHF excl. VAT, min 150 / Total):**
| Name & function | Daily rate | Days | Total |
|---|---|---|---|
| Miguel Rodriguez — Lead (ML/MLX, RAG, iOS) | [700] | [44] | [30,800] |
| Co-participant — evaluation + design (TBD, hackathon) | [600] | [20] | [12,000] |

**Non-personnel:**
| Item | CHF |
|---|---|
| Apple Developer Program + test devices | [1,500] |
| Demo hosting / infra | [700] |
| Avatar / design assets | [2,500] |
| Mandatory-event travel | [1,500] |

**Budget explanation** *(max 600):* The bulk is prototyping labor: the on-device MLX port, the forward-only disposition read, personal-RAG integration, evaluation, and the open library. A co-participant is budgeted for evaluation + design, engaged at the hackathon. Non-personnel covers the Apple Developer Program + test devices, hosting for the public demo, design of the avatar rig, and travel to the mandatory programme events. ~5% of the lead's time is contributed in-kind (not billed).

---

## TEAM
**How many people?** 2 (Miguel + 1 co-participant to recruit)

**Team member 1 — Miguel Rodriguez:** Gender [__] · Year of birth [__] · LinkedIn [__] · GitHub [__] · Email [**use a personal address, not @bigbearengineering.com** — e.g. miguel.an.rodriguez@gmail.com] · Phone [+41 __] · Country of residence [Switzerland] · Citizenship [__] · Educational background [__]

**Team member 2 — TBD:** recruit at the Apertus hackathon; target profile: interpretability evaluation / product-UX design.

---

## FORMAL REQUIREMENTS (checkboxes — all must be ticked)
1. ☐ Understand a prototyping "journey" is defined at the mid-October kickoff.
2. ☐ Confirm contribution to Responsible & Sustainable AI **and the open-source ecosystem** (code, docs, reusable components, publications, or openly accessible outputs); document work + share learnings publicly. → **matches our plan (MIT library).**
3. ☐ Confirm contribution to insights documentation; work with **SCRAI** and **WWF One Planet Lab**; contributions published at events, statements, summits, white papers, research, and/or policy recommendations.
4. ☐ Understand the Prototype Fund will mention/promote the idea; we may co-promote.
5. ☐ Jury conflict-of-interest question: [likely "no relationship"].

## DOCUMENT UPLOAD / ATTACHMENTS
[Prepare: Canis demo link/screens, disposition-lens method write-up, prior-work links, Miguel CV/portfolio.]

---

## OPEN ITEMS (critical path to Sept 6)
1. **⚠️ Legal entity** — Big Bear Engineering is in liquidation, so it CANNOT be the entity. Post-approval needs a legal entity + bank account: a **sole proprietorship (Einzelfirma)** is fastest in CH, or an **association (Verein)**. Decide + set up. Also switch the portal contact email off `@bigbearengineering.com` to a personal one.
2. **Recruit 1 co-participant** at the Apertus hackathon — required (2–3 at each event) + fills the eval/design gap.
3. **Record the ≤3-min video pitch** (mandatory).
4. **Confirm the budget** — rates/days above are a proposal.
5. **Personal fields** for team member 1 (gender, YOB, LinkedIn, GitHub, phone, citizenship, education).
6. Log in, paste field-by-field (watch the counters), upload attachments, submit.
