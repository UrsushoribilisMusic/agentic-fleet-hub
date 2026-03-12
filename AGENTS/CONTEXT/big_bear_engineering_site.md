# Big Bear Engineering Site

Last updated: March 12, 2026

## Scope

This note covers the public corporate site at `bigbearengineering.com`, not the Agentegra site on Cloudflare Pages.

## Source Files

- Landing page source: `public/index.html`
- Portfolio page: `public/gmbh.html`
- Legal pages: `public/privacy.html`, `public/cookies.html`, `public/terms.html`

## Deployment Path

The live site is a static site served by Caddy from:

`/var/www/bigbearengineering.com/`

Deployment is done by copying files directly to the VPS. No service restart is required.

Example commands:

```powershell
scp public/index.html root@159.223.22.165:/var/www/bigbearengineering.com/index.html
scp public/privacy.html root@159.223.22.165:/var/www/bigbearengineering.com/privacy.html
scp public/cookies.html root@159.223.22.165:/var/www/bigbearengineering.com/cookies.html
scp public/terms.html root@159.223.22.165:/var/www/bigbearengineering.com/terms.html
```

## Current Homepage Notes

- The contact form posts to a Google Apps Script webhook that appends rows to the shared contact sheet.
- The page includes separate privacy, cookie, and terms pages.
- Mobile hero order was explicitly tuned so the Fleet Command Preview appears directly after the main headline on phones.
- The live demo section currently points to:
  - `https://api.robotross.art/demo/`
  - `https://api.robotross.art/growth/`
  - `https://robotross.art/pages/about-robot-ross`

## Operational Reminder

Before uploading `public/index.html`, verify you are not overwriting newer homepage edits from another agent. If GitHub is current, upload only the files you changed.
