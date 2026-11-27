import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from robinhood_trading_bot.portfolio import PortfolioPlan, is_rebalance_due, plan_deposit, plan_rebalance, target_weights

PICKS = ("AAPL", "MSFT", "NVDA", "GOOGL", "AMD", "MU", "WDC", "AMAT", "NET", "NFLX")


class TargetWeightTests(unittest.TestCase):
    def test_weights_sum_to_one_and_split_core_and_sleeve(self):
        weights = target_weights(PortfolioPlan(picks=PICKS[:5]))
        self.assertAlmostEqual(float(sum(weights.values())), 1.0, places=9)
        self.assertEqual(weights["AAPL"], Decimal("0.05"))
        self.assertEqual(weights["VTI"], Decimal("0.375"))

    def test_pick_cap_sends_excess_to_core(self):
        weights = target_weights(PortfolioPlan(picks=("AAPL", "MSFT"), pick_cap_fraction=Decimal("0.05")))
        self.assertEqual(weights["AAPL"], Decimal("0.05"))
        self.assertEqual(weights["VTI"], Decimal("0.45"))
        self.assertAlmostEqual(float(sum(weights.values())), 1.0, places=9)

    def test_only_max_picks_are_used(self):
        self.assertEqual(len(PortfolioPlan(picks=PICKS, max_picks=8).active_picks), 8)

    def test_invalid_plans_are_rejected(self):
        with self.assertRaises(ValueError):
            PortfolioPlan(core_weights={"VTI": Decimal("0.9")})
        with self.assertRaises(ValueError):
            PortfolioPlan(picks=("VTI",))
        with self.assertRaises(ValueError):
            PortfolioPlan(rebalance="W")


class RebalanceTests(unittest.TestCase):
    def test_first_run_spends_only_the_budget(self):
        plan = PortfolioPlan(picks=PICKS[:8])
        result = plan_rebalance(plan, {}, Decimal("500"))
        spent = sum(Decimal(o.dollar_amount) for o in result.orders)
        self.assertEqual(result.cash_used_limit, Decimal("50.00"))
        self.assertLessEqual(spent, Decimal("50"))
        self.assertTrue(all(o.side == "buy" and o.dry_run_only for o in result.orders))

    def test_never_spends_more_than_settled_cash(self):
        result = plan_rebalance(PortfolioPlan(picks=PICKS[:4]), {}, Decimal("20"))
        self.assertLessEqual(sum(Decimal(o.dollar_amount) for o in result.orders), Decimal("20"))

    def test_rebalance_sells_winners_and_buys_laggards_without_new_cash(self):
        plan = PortfolioPlan(core_fraction=Decimal("1"), core_weights={"VTI": Decimal("0.5"), "BND": Decimal("0.5")})
        result = plan_rebalance(plan, {"VTI": Decimal("70"), "BND": Decimal("30")}, Decimal("0"))
        orders = {o.symbol: o for o in result.orders}
        self.assertEqual((orders["VTI"].side, orders["VTI"].dollar_amount), ("sell", "20.00"))
        self.assertEqual((orders["BND"].side, orders["BND"].dollar_amount), ("buy", "20.00"))

    def test_dropped_pick_is_sold_in_full(self):
        plan = PortfolioPlan(picks=("AAPL",))
        result = plan_rebalance(plan, {"VTI": Decimal("20"), "TSLA": Decimal("5")}, Decimal("0"))
        sell = next(o for o in result.orders if o.symbol == "TSLA")
        self.assertTrue(sell.sell_all)

    def test_small_drift_under_minimum_order_is_left_alone(self):
        plan = PortfolioPlan(core_fraction=Decimal("1"), core_weights={"VTI": Decimal("0.5"), "BND": Decimal("0.5")})
        result = plan_rebalance(plan, {"VTI": Decimal("25.40"), "BND": Decimal("24.60")}, Decimal("0"))
        self.assertEqual(result.orders, ())

    def test_warns_when_budget_is_too_small_for_the_picks(self):
        plan = PortfolioPlan(budget_usd=Decimal("10"), picks=PICKS[:8])
        self.assertTrue(any("minimum order" in w for w in plan_rebalance(plan, {}, Decimal("10")).warnings))


class DepositTests(unittest.TestCase):
    def test_deposit_on_target_portfolio_is_spread_by_weights(self):
        plan = PortfolioPlan(picks=PICKS[:5])
        weights = target_weights(plan)
        holdings = {s: w * 100 for s, w in weights.items()}
        result = plan_deposit(plan, holdings, Decimal("100"), Decimal("100"))
        orders = {o.symbol: Decimal(o.dollar_amount) for o in result.orders}
        self.assertEqual(orders["VTI"], Decimal("37.50"))
        self.assertEqual(orders["AAPL"], Decimal("5.00"))
        self.assertLessEqual(sum(orders.values()), Decimal("100"))
        self.assertTrue(all(o.side == "buy" for o in result.orders))

    def test_deposit_goes_to_underweight_holdings_first(self):
        plan = PortfolioPlan(core_fraction=Decimal("1"), core_weights={"VTI": Decimal("0.5"), "BND": Decimal("0.5")})
        result = plan_deposit(plan, {"VTI": Decimal("60"), "BND": Decimal("40")}, Decimal("20"), Decimal("20"))
        self.assertEqual([(o.symbol, o.dollar_amount) for o in result.orders], [("BND", "20.00")])

    def test_deposit_is_not_capped_by_budget_but_is_capped_by_cash(self):
        plan = PortfolioPlan(budget_usd=Decimal("50"), picks=PICKS[:8])
        big = plan_deposit(plan, {"VTI": Decimal("50")}, Decimal("200"), Decimal("500"))
        self.assertEqual(sum(Decimal(o.dollar_amount) for o in big.orders), Decimal("200.00"))
        short = plan_deposit(plan, {}, Decimal("200"), Decimal("30"))
        self.assertLessEqual(sum(Decimal(o.dollar_amount) for o in short.orders), Decimal("30"))
        self.assertTrue(any("margin" in w for w in short.warnings))

    def test_small_deposit_skips_buys_under_minimum(self):
        plan = PortfolioPlan(picks=PICKS[:8])
        result = plan_deposit(plan, {}, Decimal("10"), Decimal("10"))
        self.assertTrue(all(Decimal(o.dollar_amount) >= Decimal("1") for o in result.orders))
        self.assertLessEqual(sum(Decimal(o.dollar_amount) for o in result.orders), Decimal("10"))


class ScheduleTests(unittest.TestCase):
    def test_quarterly_schedule(self):
        self.assertTrue(is_rebalance_due(None, date(2026, 11, 27)))
        self.assertFalse(is_rebalance_due(date(2026, 10, 2), date(2026, 12, 31), "Q"))
        self.assertTrue(is_rebalance_due(date(2026, 12, 31), date(2027, 1, 2), "Q"))
        self.assertTrue(is_rebalance_due(date(2026, 10, 2), date(2026, 11, 1), "M"))
        self.assertFalse(is_rebalance_due(date(2026, 1, 2), date(2026, 12, 1), "Y"))


class PortfolioCliTests(unittest.TestCase):
    def test_portfolio_plan_command_is_dry_run_and_logs(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.jsonl"
            result = subprocess.run(
                [sys.executable, "-m", "robinhood_trading_bot.cli", "portfolio-plan",
                 "--plan", "config/portfolio.example.json", "--cash", "50", "--today", "2026-11-27", "--log", str(log)],
                check=True, capture_output=True, env=env, text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "dry-run")
            self.assertEqual(len(payload["picks"]), 8)
            self.assertTrue(all(o["dry_run_only"] for o in payload["orders"]))
            self.assertEqual(len(log.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
