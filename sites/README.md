# Tracked static-site sources (rescued orphans)

These marketing/hub pages were deployed to robotsales `/var/www/<domain>/` by fleet
agents but never committed. Tracking them here so edits are version-controlled.

Deploy: `rsync -az sites/<domain>/ robotsales:/var/www/<domain>/`
Served by Caddy (static `root` + `file_server`), proxied via Cloudflare.

- `miguelrodriguezauthor.com/` — Miguel's author/links hub (the canonical links page).
- `flotilla.cc/` — Flotilla projects landing page (+ `fleet/`). Also hosts `graceful-degradation.pdf` (not tracked here — 205 KB binary).
- `agentegra.com/` — only the tracked page(s), currently `agentegra-flotilla-eval.html` (the LoRA × RAG eval). Deploy the file individually so the domain's other pages aren't touched: `rsync -az sites/agentegra.com/agentegra-flotilla-eval.html robotsales:/var/www/agentegra.com/`.
- `lifelore.wiki/` — Lifelore ("Your Life as Wikipedia") landing page.
- (canis.flotilla.cc source lives in `../canis-web/`.)
