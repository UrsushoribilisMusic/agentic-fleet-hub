# LoRA and RAG — The Two Ways to Make an AI Yours

*Source brief / narration text for a cinematic explainer. Teaches the tech on its own
terms; products appear only as brief, optional examples — not as an advertisement.*

## The problem

A large language model arrives knowing a little about almost everything and nothing about
you. It has never read your company's handbook, your codebase, last night's sensor logs, or
the way your field engineers actually talk. Out of the box it is a brilliant generalist with
amnesia about your world.

There are two fundamentally different ways to close that gap — and confusing them is one of
the most common mistakes in applied AI. One **gives the model the knowledge**. The other
**teaches the model a skill**. They solve different problems, cost different amounts, and —
crucially — they combine.

## RAG: give it the knowledge

*(Retrieval-Augmented Generation)*

Retrieval is the **open-book exam**. You don't change the model at all. Instead, the moment
someone asks a question, you search a collection of your own documents, pull out the handful
of passages most likely to hold the answer, and hand them to the model alongside the
question. The model reads them on the spot and answers from what it was just given.

Under the hood: your documents are split into chunks and indexed so they can be searched —
by keyword, or by meaning. A question comes in, the system retrieves the top matches, and
stuffs them into the prompt with an instruction like *"answer using only these passages, and
cite them."*

**What retrieval is good at:** facts that change, facts that are private, and answers that
must be grounded and checkable. Update a document and the next answer reflects it — no
retraining. Because the model quotes its sources, you can verify its work. *(This is, for
example, how an on-device assistant can answer questions about a PDF you just imported
without that file ever leaving your phone.)*

**What retrieval can't do:** it doesn't change how the model writes or reasons. Give a
generalist your legal documents and it still answers like a generalist who happens to be
holding your legal documents.

## LoRA: teach it the skill

*(Low-Rank Adaptation — a lightweight kind of fine-tuning)*

Fine-tuning is the opposite move: you actually adjust the model so it internalizes a new
behavior, style, or domain. Full fine-tuning is expensive — you'd retrain billions of
parameters. LoRA is the clever shortcut that made this practical: you **freeze the big model
and train a tiny set of extra "adapter" weights** bolted onto it. You nudge a few million
parameters instead of a few billion — cheaper, faster, and small enough that you can keep a
whole library of adapters and snap a different one on for each task.

The intuition: the base model already knows how to speak, reason, and structure text. You're
not re-teaching it English — you're teaching it a **specialty**. A small nudge in the right
direction is enough to make it default to your format, your tone, or your field's vocabulary.

**What LoRA is good at:** consistent style and format, following your conventions, and
fluency in a narrow domain the base model fumbles. *(You might, for instance, give a general
open model a LoRA so it reliably speaks the language of one specific trade.)*

**What LoRA can't do:** it doesn't give the model fresh or private *facts* reliably. Teaching
facts by fine-tuning is slow, and the model can still blur or forget them. And once trained,
an adapter is frozen — new information means training again.

## The punchline: they're not rivals

The mistake is treating this as LoRA *versus* RAG. It's LoRA *and* RAG.

- Need **current, private, verifiable facts?** Reach for **retrieval**.
- Need a **consistent behavior, style, or domain skill?** Reach for a **LoRA**.
- Need both — a model that talks like your domain expert *and* cites today's documents? Use a
  LoRA for the skill and retrieval for the knowledge, together.

A way to remember it: **RAG changes what the model knows in the moment. LoRA changes who the
model is.** One hands it the right book. The other sends it to school. Most real systems need
a little of both.
