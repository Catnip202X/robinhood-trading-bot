import unittest

from robinhood_trading_bot.crypto import (
    CryptoOrderIntent,
    crypto_market_buy_intent,
    crypto_market_sell_intent,
    public_crypto_order_intents,
)


class CryptoOrderIntentTests(unittest.TestCase):
    def test_crypto_market_buy_intent_is_sanitized_and_blocked(self):
        intent = crypto_market_buy_intent("btc-usd", "25.00")

        self.assertEqual(
            intent.to_public_dict(),
            {
                "symbol": "BTC-USD",
                "side": "buy",
                "dollar_amount": "25.00",
                "quantity": None,
                "order_type": "market",
                "dry_run_only": True,
                "execution_blocked_reason": (
                    "Robinhood MCP crypto review/place tools are not available in this session."
                ),
            },
        )

    def test_crypto_market_sell_intent_can_carry_quantity(self):
        intent = crypto_market_sell_intent("eth-usd", "0.125")

        self.assertEqual(intent.to_public_dict()["symbol"], "ETH-USD")
        self.assertEqual(intent.to_public_dict()["side"], "sell")
        self.assertIsNone(intent.to_public_dict()["dollar_amount"])
        self.assertEqual(intent.to_public_dict()["quantity"], "0.125")
        self.assertTrue(intent.to_public_dict()["dry_run_only"])

    def test_crypto_order_intent_rejects_unknown_side(self):
        with self.assertRaises(ValueError):
            CryptoOrderIntent(symbol="BTC-USD", side="hold", dollar_amount="25.00")

    def test_public_crypto_order_intents_rejects_raw_dicts(self):
        with self.assertRaises(TypeError):
            public_crypto_order_intents(({"symbol": "BTC-USD"},))


if __name__ == "__main__":
    unittest.main()
