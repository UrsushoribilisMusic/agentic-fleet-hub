SM-019 worklog

Plan:
- Reuse the existing Sovereign Mind static console structure from `sovereign-mind-web/index.html` and `documents.html`.
- Add `sovereign-mind-web/knowledge-base.html` with the same nav, auth gate, and dark enterprise visual language.
- Render two RAG index cards with the exact names, descriptions, statuses, chunk counts, dates, and wiki links from the ticket.
- Include disabled "Download to Device" controls with the required tooltip text.
- Validate the static HTML locally, deploy the file to `/var/www/sm.flotilla.cc/knowledge-base.html`, then commit and push.
