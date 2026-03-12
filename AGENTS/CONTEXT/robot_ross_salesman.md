# Robot Ross — Salesman: Architecture, Integrations & Status

**Date:** 2026-03-07
**VPS:** DigitalOcean, root@159.223.22.165 (SSH alias: `robotsales`)
**Public API:** https://api.robotross.art
**Shopify Store:** https://robotross.art

---

## 1. Overview

The Salesman is the cloud backend for Robot Ross. It acts as a single unified queue that accepts orders from multiple sources (Shopify, Virtuals ACP, direct API), manages a competitive bidding system for the physical Wall of Fame, and coordinates proof-of-work delivery back to buyers.

The Artist (Mac Mini) polls this queue, draws jobs, and reports back with YouTube URLs as proof-of-work.

---

## 2. Infrastructure

| Component | Details |
|-----------|---------|
| VPS | DigitalOcean (Ubuntu) |
| IP | 159.223.22.165 |
| Domain | api.robotross.art |
| Reverse proxy | Caddy (automatic HTTPS/TLS) |
| API server | Node.js (server.mjs), port 8787 (localhost only) |
| Database | `/var/lib/salesman-api/orders.json` (flat JSON file) |
| Process manager | systemd (`salesman-api.service`) |
| ACP runtime | OpenClaw on VPS (Robot Ross agent) |

---

## 3. Repository

`~/salesman-cloud-infra` (local) → GitHub: `UrsushoribilisMusic/salesman-cloud-infra` (private)

```
salesman-cloud-infra/
  Caddyfile                          — reverse proxy config
  systemd/salesman-api.service       — systemd unit
  opt/salesman-api/server.mjs        — main API server
  opt/salesman-api/offering.json     — Virtuals ACP offering (robotross, 5 USDC)
  opt/salesman-api/offering_promo.json — promo offering (0 fee, voucherCode gated)
  opt/salesman-api/scoreboard.html   — public board wall page
  opt/salesman-api/dashboard.html    — private admin dashboard
  opt/salesman_status.mjs            — live grid status tool
  docs/ROBOT_ROSS_MANIFEST.md        — full project manifesto
  tests/server.test.mjs              — API test suite
```

---

## 4. API Endpoints

### Public / Artist-facing
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check |
| GET | `/scoreboard` | None | Public HTML wall board |
| GET | `/dashboard` | Bearer | Private admin HTML |
| GET | `/proof/:id` | None | Branded proof page (auto-refreshes until done, then redirects to YouTube) |
| GET | `/wall/snapshot` | None | Latest board photo |
| POST | `/wall/snapshot` | Bearer | Upload new board photo (from artist) |

### Order Workflow (Artist ↔ Salesman)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/salesman/orders/incoming?status=new&limit=1` | Bearer | Artist polls for next job |
| POST | `/salesman/orders/:id/claim` | Bearer | Artist claims a job |
| POST | `/salesman/orders/:id/ack` | Bearer | Artist acknowledges start |
| POST | `/salesman/orders/:id/complete` | Bearer | Artist reports done + YouTube URL |
| POST | `/salesman/orders/:id/fail` | Bearer | Artist reports failure |
| GET | `/salesman/orders/all` | Bearer | Admin: list all orders |
| GET | `/salesman/orders/:id` | Bearer | Get single order |

### Inbound Order Creation
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/salesman/orders` | Bearer | Direct order injection |
| POST | `/acp/orders` | Bearer | Virtuals ACP order injection |
| POST | `/salesman/webhooks/order-created` | HMAC | Shopify webhook |

---

## 5. Order Schema

```json
{
  "id": "shopify_XXXX | acp_XXXX | manual_XXXX",
  "status": "new | claimed | in_progress | complete | failed",
  "origin": "shopify | acp | artist",
  "payload": {
    "type": "sketch | write | svg",
    "content": "drawing prompt or text",
    "buyer": "customer name"
  },
  "slot": "A1-H8 (optional)",
  "bid_amount": 5.00,
  "proof_of_work_url": "https://youtube.com/watch?v=...",
  "created_at": "ISO timestamp"
}
```

---

## 6. Bidding & Wall of Fame

- **64 slots** on the physical board: A1 through H8
- **Minimum entry**: 5.00 USD/USDC
- **Overwrite rule**: New bid must be ≥ 120% of current slot price
- **Slot Sniffer**: If no slot specified, server parses slot ID from content (e.g. "Draw X in A3")
- **Grid state**: Tracked in `orders.json` under `grid` key
- **Persistence**: Drawing stays on wall until outbid; YouTube proof lives forever

---

## 7. Shopify Integration

### Flow
```
Customer buys on robotross.art (Shopify)
  ↓
Shopify fires webhook: POST /salesman/webhooks/order-created
  ↓
Server validates HMAC signature
  ↓
Order parsed: type, content, slot, buyer extracted from line items
  ↓
Order inserted into queue with status=new
  ↓
Artist picks up, draws, completes
  ↓
Server writes proof_of_work_url to Shopify metafield (custom.proof_of_work)
  ↓
Fulfilment triggered on Shopify order
```

### Config
- Shop domain: `robot-ross.myshopify.com`
- Webhook URL: `https://api.robotross.art/salesman/webhooks/order-created`
- API version: 2026-01
- Token refresh: `/usr/local/bin/refresh-shopify-token.sh` (daily cron)

---

## 8. Virtuals ACP Integration

### Overview
Robot Ross is listed on the Virtuals Protocol marketplace as an ACP seller. AI agents can hire Robot Ross directly — no human in the loop.

### Offering: `robotross`
```json
{
  "name": "robotross",
  "description": "Physical AI artist — draws on paper, uploads YouTube proof-of-work, pins to Wall of Fame.",
  "jobFee": 5.00,
  "jobFeeType": "fixed",
  "requiredFunds": true,
  "requirement": {
    "type": { "enum": ["write", "svg"] },
    "content": { "type": "string", "required": true },
    "slot": { "type": "string", "required": false }
  }
}
```

### Promotional Offering: `robotross_promo`
- Zero fee (`jobFee: 0`)
- Requires `voucherCode` field (validated in handler)
- Used for voucher-based promotional access

### Virtuals Agent Details
- Agent name: Robot Ross
- Wallet: `0x038D7069bDc99A188105beBa1e756Fcdc1baa11A`
- Profile: https://app.virtuals.io/acp/agents/auj2pb60mizox9of81hcmyhm
- ACP runtime: `acp serve start` (running on VPS as Robot Ross agent)

### ACP → Salesman Flow
```
Virtuals agent creates job via ACP protocol
  ↓
ACP runtime receives job, calls handlers.ts executeJob
  ↓  [handlers.ts currently a scaffold — NOT YET WIRED]
POST /acp/orders (localhost:8787)
  ↓
Order queued as status=new with origin=acp
  ↓
Artist picks up, draws, returns YouTube URL
  ↓
proof_of_work_url delivered back to hiring agent
```

### Direct Test (bypass ACP CLI)
```bash
curl -X POST http://localhost:8787/acp/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 14bcafb04d7b4c8f806195d975c9b92f6649f73a997e7241c85cd02df5a8b08b" \
  -d '{"order_id":"test_001","offering_id":"sketch_drawing","parameters":{"content":"a happy little tree"},"buyer_id":"testclient","funds_transferred":5}'
```

---

## 9. Authentication

| Token | Value | Used by |
|-------|-------|---------|
| ARTIST_API_TOKEN | `14bcafb...` | Artist (Mac Mini) → Salesman API |
| MARKETPLACE_API_TOKEN | `80b5d92...` | Shopify + marketplace integrations |
| VIRTUALS_ACP_API_KEY | `acp-af80c0...` | Virtuals ACP runtime |

Env vars stored in `/etc/systemd/system/salesman-api.service`.

---

## 10. Current Status

| Component | Status |
|-----------|--------|
| Salesman API | ✅ Running (systemd, auto-restart) |
| HTTPS / Caddy | ✅ Working |
| Shopify webhook | ✅ Working (HMAC validated) |
| Order queue (poll/claim/ack/complete) | ✅ Working end-to-end |
| Proof-of-work write-back to Shopify | ✅ Working |
| Wall snapshot endpoint | ✅ Working |
| Scoreboard page | ✅ Working |
| Virtuals ACP offering registered | ✅ Registered at 5 USDC |
| ACP seller runtime (`acp serve`) | ✅ Running |
| ACP → queue injection (`/acp/orders`) | ✅ Working |
| handlers.ts wired to Salesman API | ❌ Still scaffold — not implemented |
| `offering_id` type mapping bug | ❌ `"svg"` maps to `write` instead of `sketch` |

---

## 11. Known Issues & Pending Work

### Bug: ACP offering_id type mapping (server.mjs)
In `/acp/orders` handler, only `"sketch_drawing"` maps to sketch type:
```javascript
// Current (broken):
type: body.offering_id === "sketch_drawing" ? "sketch" : "write"

// Fix needed:
type: ["sketch_drawing", "svg", "sketch"].includes(body.offering_id) ? "sketch" : "write"
```

### TODO: handlers.ts (Gemini)
File at: `/root/.openclaw/workspace/skills/virtuals-protocol-acp/src/seller/offerings/robotross/handlers.ts`

Must implement `executeJob` to:
1. POST to `http://localhost:8787/acp/orders` with job parameters
2. Poll `GET /acp/orders/:id` every 5 seconds (max 10 min)
3. Return `{ deliverable: proof_of_work_url }` when complete

### TODO: Promo offering deployment
- Copy `offering_promo.json` to `/home/openclaw/.openclaw-promo/offering.json`
- Run `acp sell create robotross_promo` from that directory
- Implement `voucherCode` validation in handler

### Open Issues (assigned to Gemini)
- `#13`: Populate type/content/buyer from real Shopify line items
- `#1`: Tailscale on Artist gateway
- `#5`: Shopify storefront 100 slots
- `#22`: Virtuals Protocol marketplace full setup
