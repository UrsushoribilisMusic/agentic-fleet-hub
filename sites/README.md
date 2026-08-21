# Tracked static-site sources (rescued orphans)

These marketing/hub pages were deployed to robotsales `/var/www/<domain>/` by fleet
agents but never committed. Tracking them here so edits are version-controlled.

Deploy: `rsync -az sites/<domain>/ robotsales:/var/www/<domain>/`
Served by Caddy (static `root` + `file_server`), proxied via Cloudflare.

- `miguelrodriguezauthor.com/` — Miguel's author/links hub (the canonical links page).
- `lifelore.wiki/` — Lifelore ("Your Life as Wikipedia") landing page.
- (canis.flotilla.cc source lives in `../canis-web/`.)
