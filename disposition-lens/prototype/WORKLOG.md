# DL-4 Worklog — Prototype HOOK Repoint & Hosted Build

## Goal
Repoint the `>>> HOOK` in `disposition-lens/prototype/disposition_lens.jsx` `ask()` from the Anthropic API stand-in to the Mac Mini `/infer` FastAPI service returning `{answer, disposition, tokens, entropy}`. Also create a standalone, browser-runnable `index.html` host in `disposition-lens/prototype/` so the prototype can be rendered and screen-recorded.

## Plan
1. Update `disposition_lens.jsx`:
   - Replace the Anthropic API fetch call in `ask()` with a POST request to `http://localhost:8000/infer` (or window.DISPOSITION_API_URL fallback).
   - Send `{"question": q}`.
   - Handle the returned JSON payload (`{answer, disposition, tokens, entropy}`).
   - Retain fallback behavior on network error so demo reel and keyword fallback remain reliable.
2. Create standalone `disposition-lens/prototype/index.html`:
   - Self-contained HTML entry point with React 18, Babel standalone, and Lucide icons.
   - Embed or import `disposition_lens.jsx` so it runs out-of-the-box in any modern browser.
3. Verify functionality and build.
