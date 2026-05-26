#!/usr/bin/env python3
"""Ingest Shopify orders into PocketBase for Classical Reels finance reporting."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


ATTRIBUTED_LINES = {"cr-fables", "cr-lostcoins", "cr-soulmd", "cr-sold"}
DEFAULT_API_VERSION = "2025-10"
DEFAULT_PB_URL = "http://127.0.0.1:8090"
DEFAULT_COLLECTION = "shopify_orders"


class IngestionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShopifyProductInfo:
    handle: str
    attributed_line: str


@dataclass(frozen=True)
class ShopifyOrderLine:
    record_id: str
    order_id: str
    created_at: str
    line_total: str
    currency: str
    product_handle: str
    attributed_line: str
    customer_country: str

    def as_pocketbase_record(self) -> dict[str, str]:
        return {
            "id": self.record_id,
            "order_id": self.order_id,
            "created_at": self.created_at,
            "line_total": self.line_total,
            "currency": self.currency,
            "product_handle": self.product_handle,
            "attributed_line": self.attributed_line,
            "customer_country": self.customer_country,
        }


def normalize_shop_domain(raw: str) -> str:
    value = raw.strip().removeprefix("https://").removeprefix("http://").strip("/")
    if not value:
        raise IngestionError("SHOPIFY_SHOP_DOMAIN is empty")
    return value


def normalize_attributed_line(value: Any) -> str:
    text = str(value or "").strip()
    return text if text in ATTRIBUTED_LINES else "unattributed"


def decimal_money(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except InvalidOperation:
        return Decimal("0")


def money_string(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(rounded, "f")


def line_item_total(line_item: dict[str, Any]) -> str:
    presentment = line_item.get("discounted_total_set", {}).get("shop_money", {}).get("amount")
    if presentment not in (None, ""):
        return money_string(decimal_money(presentment))

    price = decimal_money(line_item.get("price"))
    quantity = decimal_money(line_item.get("quantity") or 1)
    discount = decimal_money(line_item.get("total_discount"))
    total = price * quantity - discount
    return money_string(max(total, Decimal("0")))


def customer_country(order: dict[str, Any]) -> str:
    for section in ("shipping_address", "billing_address"):
        address = order.get(section) or {}
        country = address.get("country_code") or address.get("country")
        if country:
            return str(country)

    default_address = (order.get("customer") or {}).get("default_address") or {}
    country = default_address.get("country_code") or default_address.get("country")
    return str(country or "")


def record_id_for_line(order_id: Any, line_item_id: Any) -> str:
    digest = hashlib.sha1(f"{order_id}:{line_item_id}".encode("utf-8")).hexdigest()
    return digest[:15]


def build_order_lines(
    order: dict[str, Any],
    products: dict[str, ShopifyProductInfo],
) -> list[ShopifyOrderLine]:
    order_id = str(order.get("id") or "")
    created_at = str(order.get("created_at") or "")
    currency = str(order.get("currency") or "")
    country = customer_country(order)
    rows: list[ShopifyOrderLine] = []

    for index, line_item in enumerate(order.get("line_items") or []):
        line_item_id = line_item.get("id") or f"index-{index}"
        product_id = str(line_item.get("product_id") or "")
        product = products.get(product_id, ShopifyProductInfo(handle="", attributed_line="unattributed"))
        rows.append(
            ShopifyOrderLine(
                record_id=record_id_for_line(order_id, line_item_id),
                order_id=order_id,
                created_at=created_at,
                line_total=line_item_total(line_item),
                currency=currency,
                product_handle=product.handle,
                attributed_line=product.attributed_line,
                customer_country=country,
            )
        )

    return rows


class JsonHttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        payload = None
        request_headers = {"Accept": "application/json", **(headers or {})}
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            request_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=payload, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8") or "{}"
                return json.loads(raw), dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise IngestionError(f"{method} {url} failed: HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise IngestionError(f"{method} {url} failed: {exc.reason}") from exc


class ShopifyClient:
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = DEFAULT_API_VERSION,
        http: JsonHttpClient | None = None,
    ) -> None:
        self.shop_domain = normalize_shop_domain(shop_domain)
        self.access_token = access_token
        self.api_version = api_version
        self.http = http or JsonHttpClient()

    def admin_url(self, path: str, params: dict[str, str] | None = None) -> str:
        query = f"?{urllib.parse.urlencode(params or {})}" if params else ""
        return f"https://{self.shop_domain}/admin/api/{self.api_version}/{path.lstrip('/')}{query}"

    def headers(self) -> dict[str, str]:
        return {"X-Shopify-Access-Token": self.access_token}

    def fetch_orders(self, created_at_min: str, created_at_max: str) -> list[dict[str, Any]]:
        params = {
            "status": "any",
            "limit": "250",
            "created_at_min": created_at_min,
            "created_at_max": created_at_max,
            "fields": "id,created_at,currency,line_items,shipping_address,billing_address,customer",
        }
        url = self.admin_url("orders.json", params)
        orders: list[dict[str, Any]] = []

        while url:
            payload, headers = self.http.request_json("GET", url, headers=self.headers())
            orders.extend(payload.get("orders") or [])
            url = next_link(headers.get("Link", ""))

        return orders

    def fetch_product_info(self, product_id: str) -> ShopifyProductInfo:
        if not product_id:
            return ShopifyProductInfo(handle="", attributed_line="unattributed")

        product_payload, _ = self.http.request_json(
            "GET",
            self.admin_url(f"products/{product_id}.json", {"fields": "id,handle"}),
            headers=self.headers(),
        )
        product = product_payload.get("product") or {}
        handle = str(product.get("handle") or "")

        metafields_payload, _ = self.http.request_json(
            "GET",
            self.admin_url(
                f"products/{product_id}/metafields.json",
                {"namespace": "custom", "key": "content_line", "limit": "1"},
            ),
            headers=self.headers(),
        )
        metafields = metafields_payload.get("metafields") or []
        content_line = metafields[0].get("value") if metafields else ""
        return ShopifyProductInfo(handle=handle, attributed_line=normalize_attributed_line(content_line))


def next_link(link_header: str) -> str:
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        if section.startswith("<") and ">" in section:
            return section[1 : section.index(">")]
    return ""


class PocketBaseClient:
    def __init__(
        self,
        base_url: str = DEFAULT_PB_URL,
        collection: str = DEFAULT_COLLECTION,
        admin_token: str = "",
        http: JsonHttpClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.admin_token = admin_token
        self.http = http or JsonHttpClient()

    def headers(self) -> dict[str, str]:
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}

    def record_url(self, record_id: str = "") -> str:
        base = f"{self.base_url}/api/collections/{self.collection}/records"
        return f"{base}/{record_id}" if record_id else base

    def upsert_order_line(self, line: ShopifyOrderLine) -> str:
        record = line.as_pocketbase_record()
        try:
            self.http.request_json("POST", self.record_url(), headers=self.headers(), body=record)
            return "created"
        except IngestionError as exc:
            if "HTTP 400" not in str(exc):
                raise

        patch_record = dict(record)
        patch_record.pop("id", None)
        self.http.request_json(
            "PATCH",
            self.record_url(line.record_id),
            headers=self.headers(),
            body=patch_record,
        )
        return "updated"


def utc_window_for_day(day: dt.date) -> tuple[str, str]:
    start = dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def load_product_cache(client: ShopifyClient, orders: list[dict[str, Any]]) -> dict[str, ShopifyProductInfo]:
    product_ids = sorted(
        {
            str(line.get("product_id") or "")
            for order in orders
            for line in (order.get("line_items") or [])
            if line.get("product_id")
        }
    )
    cache: dict[str, ShopifyProductInfo] = {}
    for product_id in product_ids:
        try:
            cache[product_id] = client.fetch_product_info(product_id)
        except IngestionError as exc:
            print(f"warning: product {product_id} attribution unavailable: {exc}", file=sys.stderr)
            cache[product_id] = ShopifyProductInfo(handle="", attributed_line="unattributed")
    return cache


def run_ingestion(args: argparse.Namespace) -> dict[str, int]:
    shop_domain = args.shop_domain or os.getenv("SHOPIFY_SHOP_DOMAIN", "")
    access_token = (
        args.shopify_token
        or os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN", "")
        or os.getenv("SHOPIFY_ADMIN_TOKEN", "")
    )
    if not shop_domain or not access_token:
        raise IngestionError("SHOPIFY_SHOP_DOMAIN and SHOPIFY_ADMIN_ACCESS_TOKEN are required")

    day = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    created_at_min, created_at_max = utc_window_for_day(day)
    if args.created_at_min:
        created_at_min = args.created_at_min
    if args.created_at_max:
        created_at_max = args.created_at_max

    shopify = ShopifyClient(
        shop_domain=shop_domain,
        access_token=access_token,
        api_version=args.shopify_api_version,
    )
    pocketbase = PocketBaseClient(
        base_url=args.pocketbase_url,
        collection=args.pocketbase_collection,
        admin_token=args.pocketbase_token or os.getenv("POCKETBASE_ADMIN_TOKEN", ""),
    )

    if args.check_credentials:
        shopify.fetch_orders(created_at_min, created_at_min)
        return {"orders": 0, "lines": 0, "created": 0, "updated": 0}

    orders = shopify.fetch_orders(created_at_min, created_at_max)
    products = load_product_cache(shopify, orders)
    stats = {"orders": len(orders), "lines": 0, "created": 0, "updated": 0}

    for order in orders:
        for line in build_order_lines(order, products):
            result = pocketbase.upsert_order_line(line)
            stats["lines"] += 1
            stats[result] += 1

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest Shopify order lines into PocketBase shopify_orders.")
    parser.add_argument("--date", help="UTC order date to ingest, YYYY-MM-DD. Defaults to yesterday UTC.")
    parser.add_argument("--created-at-min", help="Override Shopify created_at_min ISO timestamp.")
    parser.add_argument("--created-at-max", help="Override Shopify created_at_max ISO timestamp.")
    parser.add_argument("--shop-domain", help="Shopify shop domain. Env: SHOPIFY_SHOP_DOMAIN.")
    parser.add_argument("--shopify-token", help="Shopify Admin access token. Env: SHOPIFY_ADMIN_ACCESS_TOKEN.")
    parser.add_argument("--shopify-api-version", default=os.getenv("SHOPIFY_API_VERSION", DEFAULT_API_VERSION))
    parser.add_argument("--pocketbase-url", default=os.getenv("POCKETBASE_URL", DEFAULT_PB_URL))
    parser.add_argument("--pocketbase-token", help="PocketBase admin token. Env: POCKETBASE_ADMIN_TOKEN.")
    parser.add_argument("--pocketbase-collection", default=os.getenv("SHOPIFY_ORDERS_COLLECTION", DEFAULT_COLLECTION))
    parser.add_argument("--check-credentials", action="store_true", help="Validate Shopify token access without writing rows.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    started = time.time()
    try:
        stats = run_ingestion(args)
    except Exception as exc:
        print(f"shopify ingestion failed: {exc}", file=sys.stderr)
        return 1

    elapsed = time.time() - started
    print(json.dumps({"ok": True, "elapsed_seconds": round(elapsed, 3), **stats}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
