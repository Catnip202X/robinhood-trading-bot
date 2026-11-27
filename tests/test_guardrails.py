import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from robinhood_trading_bot.guardrails import CryptoGuardrails, DailyLossTracker, DecisionLog, check_buy


class GuardrailTests(unittest.TestCase):
    def setUp(self):
        self.daily = DailyLossTracker()
        self.daily.update(datetime(2026, 11, 27, 1, tzinfo=timezone.utc), Decimal("100"))

    def test_buy_capped_by_lane_room(self):
        amount, reason = check_buy(CryptoGuardrails(), "BTC-USD", Decimal("30"), Decimal("80"), Decimal("0"), self.daily, Decimal("100"))
        self.assertEqual((amount, reason), (Decimal("20.00"), None))

    def test_unknown_symbol_blocked(self):
        amount, reason = check_buy(CryptoGuardrails(), "DOGE-USD", Decimal("3"), Decimal("0"), Decimal("0"), self.daily, Decimal("100"))
        self.assertEqual(amount, 0)
        self.assertIn("not in the allowed", reason)

    def test_daily_loss_stop_blocks_and_resets_next_day(self):
        _, reason = check_buy(CryptoGuardrails(), "BTC-USD", Decimal("3"), Decimal("0"), Decimal("0"), self.daily, Decimal("94"))
        self.assertEqual(reason, "daily loss stop reached")
        self.daily.update(datetime(2026, 11, 27, 1, tzinfo=timezone.utc) + timedelta(days=1), Decimal("94"))
        _, reason = check_buy(CryptoGuardrails(), "BTC-USD", Decimal("3"), Decimal("0"), Decimal("0"), self.daily, Decimal("94"))
        self.assertIsNone(reason)

    def test_decision_log_appends_json_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = DecisionLog(Path(tmp) / "logs" / "d.jsonl")
            log.write({"action": "hold"})
            log.write({"action": "buy"})
            lines = (Path(tmp) / "logs" / "d.jsonl").read_text().splitlines()
            self.assertEqual([json.loads(l)["action"] for l in lines], ["hold", "buy"])


if __name__ == "__main__":
    unittest.main()
