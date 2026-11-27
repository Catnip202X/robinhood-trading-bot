import json
import unittest

try:
    import nacl  # noqa: F401
    HAVE_NACL = True
except ImportError:
    HAVE_NACL = False

from robinhood_trading_bot.rh_crypto_api import LiveOrdersBlocked, RobinhoodCryptoClient

# Example values published in Robinhood's Crypto Trading API docs (not real credentials).
DOC_PRIVATE_KEY = "xQnTJVeQLmw1/Mg2YimEViSpw/SdJcgNXZ5kQkAXNPU="
DOC_API_KEY = "rh-api-6148effc-c0b1-486c-8940-a1d099456be6"


@unittest.skipUnless(HAVE_NACL, "pynacl not installed")
class SignatureTests(unittest.TestCase):
    def test_matches_documented_example_signature(self):
        from robinhood_trading_bot.rh_crypto_api import sign_message

        body = {
            "client_order_id": "131de903-5a9c-4260-abc1-28d562a5dcf0",
            "side": "buy",
            "symbol": "BTC-USD",
            "type": "market",
            "market_order_config": {"asset_quantity": "0.1"},
        }
        message = f"{DOC_API_KEY}1698708981/api/v1/crypto/trading/orders/POST{body}"
        self.assertEqual(
            sign_message(DOC_PRIVATE_KEY, message),
            "q/nEtxp/P2Or3hph3KejBqnw5o9qeuQ+hYRnB56FaHbjDsNUY9KhB1asMxohDnzdVFSD7StaTqjSd9U9HvaRAw==",
        )

    def test_get_request_sends_signed_headers(self):
        calls = []

        def transport(method, url, headers, data):
            calls.append((method, url, headers, data))
            return 200, {"ok": True}

        client = RobinhoodCryptoClient(DOC_API_KEY, DOC_PRIVATE_KEY, transport=transport, clock=lambda: 1698708981)
        self.assertEqual(client.get_best_bid_ask("BTC-USD"), {"ok": True})
        method, url, headers, data = calls[0]
        self.assertEqual(method, "GET")
        self.assertTrue(url.endswith("/api/v1/crypto/marketdata/best_bid_ask/?symbol=BTC-USD"))
        self.assertEqual(headers["x-timestamp"], "1698708981")
        self.assertIsNone(data)


class LiveOrderBlockTests(unittest.TestCase):
    def test_place_and_cancel_are_blocked_by_default(self):
        def transport(*_):
            raise AssertionError("no request should be sent")

        client = RobinhoodCryptoClient("key", DOC_PRIVATE_KEY, transport=transport)
        with self.assertRaises(LiveOrdersBlocked):
            client.place_order("buy", "market", "BTC-USD", {"quote_amount": "3.00"})
        with self.assertRaises(LiveOrdersBlocked):
            client.cancel_order("abc")

    def test_repr_hides_keys(self):
        self.assertNotIn("key", repr(RobinhoodCryptoClient("secret-key", "secret-private")).lower().replace("allow_live_orders", ""))


if __name__ == "__main__":
    unittest.main()
