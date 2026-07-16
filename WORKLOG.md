SM-018 worklog

Plan:
- Reuse the SM-017 web console dashboard structure for nav, account display, and auth gate.
- Add `sovereign-mind-web/documents.html` as a static mock upload page with no ingestion behavior.
- Deploy the page to `robotsales:/var/www/sm.flotilla.cc/documents.html`.
- Verify auth-gated route behavior and static file availability.
- Post task output and move SM-018 to peer review.

Key decisions:
- Keep all CSS and JavaScript inline to match the existing static dashboard approach.
- Disable the ingest action intentionally and expose the coming-soon copy through the native `title` tooltip and nearby muted text.
