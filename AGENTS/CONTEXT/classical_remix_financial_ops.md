# Classical Remix & Classical Reels — Financial Ops Context

**Sprint**: Financial Ops Sprint (opened 2026-05-26)  
**Prepared by**: Clau (Claude Opus), refined with Claude Code  
**Status**: Active — CR-000 through CR-013 open  

---

## Workstream Summary

Two operationally separated projects sharing the `music-video-tool` codebase and Fleet Hub infrastructure.

| | Classical Remix | Classical Reels |
| :--- | :--- | :--- |
| **Goal** | 4,000 valid public watch hours for YPP | Validate B2B sales of short-form video assets via Shopify |
| **Revenue** | YouTube ad revenue (post-YPP) | Shopify orders (~CHF 8/asset) |
| **Current state** | 1,681 h / 4,000 h (42%), +51 h/day velocity | Live at robotross.art, one confirmed sale |
| **Distribution** | YouTube + Google Ads | Shopify + organic social |

---

## Content Lines (Classical Reels)

| Line | Tag | Hashtag | Status |
| :--- | :--- | :--- | :--- |
| Fables | `cr-fables` | `#crfables` | Active — backfill existing videos |
| Lost Coins | `cr-lostcoins` | `#crlostcoins` | Active — backfill existing videos |
| Soul.MD | `cr-soulmd` | `#crsoulmd` | Not started |
| Customer-sold | `cr-sold` | `#crsold` | Active — one existing sale |

All published assets must carry the content-line hashtag as the last line of the video description. The Shopify product must carry a `content_line` metafield. See MISSION_CONTROL Financial Ops boundaries for full policy.

---

## Spending Rule

```
Available to spend = (last 30d revenue × 0.7) + remaining operating credit
```

- Operating credit: CHF 500 (PocketBase config `financial_config`)
- Initial cash position seed: CHF 300/month
- Pending Google ad credits (CHF 400 + CHF 250): NOT included in formula — tracked separately as "incoming"
- Investment ledger seed: CHF 300

Phase A unlock: revenue covers Runway + ElevenLabs + DigitalOcean.  
Phase B unlock: revenue exceeds Phase A by 25% for two consecutive months — fleet begins covering agent subscriptions.

---

## API Credentials (all in Infisical EU)

| Credential | Purpose | Sprint tickets |
| :--- | :--- | :--- |
| `YOUTUBE_API_KEY` + `YOUTUBE_CLIENT_SECRETS_JSON` | YouTube Analytics — verify Analytics scope | CR-002 |
| `GOOGLE_ADS_*` (5 keys) | Google Ads read-only snapshot | CR-003 |
| `SHOPIFY_CLIENT_ID` + `SHOPIFY_CLIENT_SECRET` | Shopify Admin API — **verify access token exists** | CR-004 |
| `ELEVENLABS_API_KEY` | Cost ingestion | CR-006 |
| `RUNWAYML_API_SECRET` | Cost ingestion | CR-006 |

⚠️ **Shopify Admin access token may be missing** — CR-000 verifies. The Client ID/Secret are OAuth app credentials; a separate access token is required for Admin API calls.

---

## Watch Hours Ledger (seed data for CR-002)

| Date | Total Hours | Day Gain | Phase |
| :--- | :--- | :--- | :--- |
| 2026-04-14 | 107 | — | Initial Tracking Baseline |
| 2026-04-21 | 133 | — | Early Setup Window |
| 2026-04-22 | 135 | +2 | Baseline Verification |
| 2026-04-24 | 161 | — | Structural Ad Adjustments |
| 2026-04-26 | 226 | — | Catalog Scaling |
| 2026-04-28 | 310 | — | Volume Building Phase |
| 2026-05-02 | 506 | — | Early May Expansion |
| 2026-05-03 | 583 | +77 | Peak 3-Campaign Sync |
| 2026-05-04 | 665 | +82 | Peak 3-Campaign Sync |
| 2026-05-05 | 725 | +60 | Peak 3-Campaign Sync |
| 2026-05-06 | 802 | +77 | Peak 3-Campaign Sync |
| 2026-05-07 | 881 | +79 | Last Day Peak 3-Campaign |
| 2026-05-08 | 957 | +76 | Transition Phase |
| 2026-05-09 | 1030 | +73 | Cleared 1,000-Hour Milestone |
| 2026-05-10 | 1102 | +72 | Final Multi-Campaign Wave |
| 2026-05-11 | 1177 | +75 | Shifted to Lean Optimization |
| 2026-05-12 | 1244 | +67 | Lean Mode: Celtic + Progressive |
| 2026-05-13 | 1294 | +50 | Lean Mode Flatline Floor |
| 2026-05-14 | 1338 | +44 | Lean Mode Flatline Floor |
| 2026-05-15 | 1381 | +43 | Lean Mode Mid-Month |
| 2026-05-16 | 1424 | +43 | The Swap: Progressive Paused / Vallenato Active |
| 2026-05-17 | 1469 | +45 | Vallenato First Data Cycles |
| 2026-05-18 | 1518 | +49 | Inflexion Phase Initiated |
| 2026-05-19 | 1575 | +57 | Algorithmic Acceleration Peak |
| 2026-05-20 | 1626 | +51 | Baseline Stabilizing Above 50h Floor |
| 2026-05-21 | 1681 | +55 | Latest Verified Position |
| 2026-05-22 | 1734.63 | +53.63 | Ongoing |
| 2026-05-23 | 1783.45 | +48.82 | Ongoing |
| 2026-05-24 | 1830.78 | +47.33 | Ongoing |

---

## Fleet Hub — Financial Ops Tab

Target file: `salesman-cloud-infra/opt/salesman-api/fleet/dashboard.html`  
New sidebar nav entry: "Financial Ops" — position between "Projects" and "Kanban".  
Sub-views: P&L (default landing), Classical Remix, Classical Reels.  
Pattern: follow existing `data-section-button` nav pattern.
