# CR-004 Worklog

Task: `9uh4f66up3s91dz` / CR-004 / GitHub #639

Plan:
1. Add a daily Shopify ingestion script that reads Shopify Admin credentials from the environment or vault-injected runtime.
2. Fetch orders from the Admin API for a configurable daily window.
3. Fetch product `content_line` metafields and cache them by product id.
4. Write one PocketBase `shopify_orders` record per Shopify content line item with idempotent upsert behavior.
5. Add focused tests for attribution defaults, line totals, country extraction, and idempotent update behavior.
6. Document the runtime environment variables and run the test suite.

Key decisions:
- Store Shopify currency exactly as returned on the order.
- Default missing, blank, or unexpected `content_line` metafields to `unattributed`.
- Avoid touching the active `salesman-cloud-infra` worktree because it has unrelated uncommitted dashboard work on another task branch.
