# Financial Ops Shopify Ingestion

CR-004 adds `scripts/financial_ops/ingest_shopify_orders.py`, a daily Shopify Admin API ingestion job for Classical Reels orders.

## Runtime

Required environment:

- `SHOPIFY_SHOP_DOMAIN`: Shopify Admin shop domain, for example `robot-ross.myshopify.com`.
- `SHOPIFY_ADMIN_ACCESS_TOKEN`: Shopify Admin API access token with order and product/metafield read access. `SHOPIFY_ADMIN_TOKEN` is accepted as a legacy alias.
- `POCKETBASE_URL`: optional, defaults to `http://127.0.0.1:8090`.
- `POCKETBASE_ADMIN_TOKEN`: optional if the `shopify_orders` collection allows service writes without auth.
- `SHOPIFY_API_VERSION`: optional, defaults to `2025-10`.

Daily run for the prior UTC day:

```bash
python3 scripts/financial_ops/ingest_shopify_orders.py
```

Specific day:

```bash
python3 scripts/financial_ops/ingest_shopify_orders.py --date 2026-05-25
```

Credential check without PocketBase writes:

```bash
python3 scripts/financial_ops/ingest_shopify_orders.py --check-credentials --created-at-min 2026-05-25T00:00:00Z
```

## PocketBase Collection

Collection name: `shopify_orders`

Fields:

| Field | Type | Notes |
|---|---|---|
| `order_id` | text | Shopify order id as returned by Admin API. |
| `created_at` | date | Shopify order creation timestamp. |
| `line_total` | text or number | Discounted line total, currency amount only. |
| `currency` | text | Stored exactly as returned on the Shopify order. |
| `product_handle` | text | Fetched from Shopify product. Blank when product lookup fails. |
| `attributed_line` | select/text | `cr-fables`, `cr-lostcoins`, `cr-soulmd`, `cr-sold`, or `unattributed`. |
| `customer_country` | text | Shipping country first, billing/default customer fallback. |

The script writes one row per Shopify line item. PocketBase record ids are deterministic SHA-1 prefixes from `order_id:line_item_id`, so reruns patch the same rows instead of duplicating them.

## Attribution

The script reads product metafield `custom.content_line`. Missing, blank, or unexpected values are stored as `unattributed`, which lets CR-011 surface warnings in the Classical Reels dashboard.
