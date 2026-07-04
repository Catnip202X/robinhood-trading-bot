import unittest
from pathlib import Path

from robinhood_trading_bot.models import PortfolioSummary, SnapshotReport
from robinhood_trading_bot.snapshot import build_snapshot_from_fixture


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "read_only_snapshot.json"


class SnapshotTests(unittest.TestCase):
    def test_build_snapshot_from_fixture_returns_sanitized_report(self):
        report = build_snapshot_from_fixture(FIXTURE_PATH)

        payload = report.to_public_dict()

        self.assertEqual(report.mode, "dry-run")
        self.assertEqual(report.auth_profile, "robinhood_trading-2")
        self.assertIn("AAPL", [position.symbol for position in report.equity_positions])
        self.assertNotIn("account_number", payload)

    def test_snapshot_report_serializes_without_account_number(self):
        report = SnapshotReport(
            mode="dry-run",
            auth_profile="robinhood_trading-2",
            account_label="primary",
            portfolio=PortfolioSummary(total_market_value="1000.00", buying_power="250.00"),
            equity_positions=[],
            option_positions=[],
            recent_orders=[],
            realized_pnl=None,
        )

        payload = report.to_public_dict()

        self.assertEqual(payload["account_label"], "primary")
        self.assertNotIn("account_number", payload)
        self.assertEqual(payload["portfolio"]["buying_power"], "250.00")

    def test_snapshot_report_rejects_raw_position_dicts(self):
        report = SnapshotReport(
            mode="dry-run",
            auth_profile="robinhood_trading-2",
            account_label="primary",
            portfolio=PortfolioSummary(total_market_value="1000.00", buying_power="250.00"),
            equity_positions=[{"symbol": "AAPL", "account_number": "REDACTED_ACCOUNT"}],
            option_positions=[],
            recent_orders=[],
            realized_pnl=None,
        )

        with self.assertRaises(TypeError):
            report.to_public_dict()

    def test_snapshot_report_rejects_raw_realized_pnl_dict(self):
        report = SnapshotReport(
            mode="dry-run",
            auth_profile="robinhood_trading-2",
            account_label="primary",
            portfolio=PortfolioSummary(total_market_value="1000.00", buying_power="250.00"),
            equity_positions=[],
            option_positions=[],
            recent_orders=[],
            realized_pnl={"summary": "flat", "account_number": "REDACTED_ACCOUNT"},
        )

        with self.assertRaises(TypeError):
            report.to_public_dict()


if __name__ == "__main__":
    unittest.main()
