import datetime as dt
import unittest

from ingest_shopify_orders import (
    IngestionError,
    PocketBaseClient,
    ShopifyProductInfo,
    build_order_lines,
    customer_country,
    line_item_total,
    next_link,
    normalize_attributed_line,
    record_id_for_line,
    utc_window_for_day,
)


class FakeHttp:
    def __init__(self):
        self.calls = []
        self.fail_post = False

    def request_json(self, method, url, headers=None, body=None):
        self.calls.append((method, url, headers or {}, body or {}))
        if method == "POST" and self.fail_post:
            raise IngestionError("POST failed: HTTP 400 duplicate id")
        return {"ok": True}, {}


class ShopifyIngestionTests(unittest.TestCase):
    def test_normalize_attributed_line_defaults_unknown_values(self):
        self.assertEqual(normalize_attributed_line("cr-fables"), "cr-fables")
        self.assertEqual(normalize_attributed_line(""), "unattributed")
        self.assertEqual(normalize_attributed_line("bad-value"), "unattributed")
        self.assertEqual(normalize_attributed_line(None), "unattributed")

    def test_line_item_total_prefers_shopify_discounted_total(self):
        line_item = {
            "price": "25.00",
            "quantity": 2,
            "total_discount": "3.00",
            "discounted_total_set": {"shop_money": {"amount": "41.50"}},
        }
        self.assertEqual(line_item_total(line_item), "41.50")

    def test_line_item_total_falls_back_to_price_quantity_discount(self):
        line_item = {"price": "15.25", "quantity": 2, "total_discount": "0.50"}
        self.assertEqual(line_item_total(line_item), "30.00")

    def test_customer_country_uses_shipping_then_billing_then_customer_default(self):
        self.assertEqual(customer_country({"shipping_address": {"country_code": "CH"}}), "CH")
        self.assertEqual(customer_country({"billing_address": {"country": "Switzerland"}}), "Switzerland")
        self.assertEqual(
            customer_country({"customer": {"default_address": {"country_code": "US"}}}),
            "US",
        )
        self.assertEqual(customer_country({}), "")

    def test_build_order_lines_maps_product_metafield_attribution(self):
        order = {
            "id": 123,
            "created_at": "2026-05-25T12:30:00Z",
            "currency": "CHF",
            "shipping_address": {"country_code": "CH"},
            "line_items": [
                {"id": 987, "product_id": 456, "price": "20.00", "quantity": 1},
                {"id": 988, "product_id": 999, "price": "3.00", "quantity": 2},
            ],
        }
        products = {"456": ShopifyProductInfo(handle="lost-coins-reel", attributed_line="cr-lostcoins")}

        rows = build_order_lines(order, products)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].order_id, "123")
        self.assertEqual(rows[0].line_total, "20.00")
        self.assertEqual(rows[0].currency, "CHF")
        self.assertEqual(rows[0].product_handle, "lost-coins-reel")
        self.assertEqual(rows[0].attributed_line, "cr-lostcoins")
        self.assertEqual(rows[0].customer_country, "CH")
        self.assertEqual(rows[1].attributed_line, "unattributed")
        self.assertEqual(rows[1].product_handle, "")

    def test_record_id_is_deterministic_pocketbase_safe_length(self):
        first = record_id_for_line("123", "987")
        second = record_id_for_line("123", "987")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 15)
        self.assertRegex(first, r"^[a-f0-9]{15}$")

    def test_pocketbase_upsert_patches_existing_record_on_duplicate(self):
        http = FakeHttp()
        http.fail_post = True
        client = PocketBaseClient(base_url="http://pb.local", http=http)
        line = build_order_lines(
            {
                "id": 1,
                "created_at": "2026-05-25T00:00:00Z",
                "currency": "CHF",
                "line_items": [{"id": 2, "product_id": 3, "price": "10", "quantity": 1}],
            },
            {"3": ShopifyProductInfo(handle="fables", attributed_line="cr-fables")},
        )[0]

        result = client.upsert_order_line(line)

        self.assertEqual(result, "updated")
        self.assertEqual(http.calls[0][0], "POST")
        self.assertEqual(http.calls[1][0], "PATCH")
        self.assertTrue(http.calls[1][1].endswith(f"/{line.record_id}"))
        self.assertNotIn("id", http.calls[1][3])

    def test_utc_window_for_day(self):
        start, end = utc_window_for_day(dt.date(2026, 5, 25))
        self.assertEqual(start, "2026-05-25T00:00:00Z")
        self.assertEqual(end, "2026-05-26T00:00:00Z")

    def test_next_link_parses_shopify_link_header(self):
        header = '<https://shop/admin/api/orders.json?page_info=abc>; rel="next"'
        self.assertEqual(next_link(header), "https://shop/admin/api/orders.json?page_info=abc")
        self.assertEqual(next_link('<https://shop/prev>; rel="previous"'), "")


if __name__ == "__main__":
    unittest.main()
