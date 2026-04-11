# WORKLOG — task/8dvp6ma64g1co2w

**Task**: [ATF] Build integrated RobotRoss demo landing page for DigitalOcean deployment  
**Agent**: Clau  
**Date**: 2026-04-11  
**Branch**: task/8dvp6ma64g1co2w

---

## Plan

Update `ATF/index.html` to meet all acceptance criteria for the DigitalOcean deployment:

1. Add Shopify shop link — `https://robot-ross.myshopify.com`
2. Add orders overview link — `https://api.robotross.art/scoreboard` (public scoreboard)
3. Add 8x8 board snapshot link — `https://api.robotross.art/wall/snapshot`
4. Remove local model and voice cards (violate DO constraint: no local runtime)
5. Update lede text to accurately describe the DO deployment surface

URLs sourced from:
- `AGENTS/CONTEXT/robot_ross_salesman.md` — shop domain, scoreboard endpoint, wall/snapshot
- `AGENTS/CONTEXT/robot_ross_artist.md` — confirms `api.robotross.art/scoreboard`

No backend changes required — landing page is static HTML.

---

## Progress

- [x] Updated `ATF/index.html`: replaced local model/voice cards with Shopify, scoreboard, and board snapshot cards; updated lede text
- [x] Committed to branch
- [x] Pushed to remote
