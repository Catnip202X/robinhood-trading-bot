import unittest

try:
    import numpy as np
    import pandas as pd
    HAVE_PANDAS = True
except ImportError:
    HAVE_PANDAS = False


@unittest.skipUnless(HAVE_PANDAS, "pandas/numpy not installed")
class BacktestTests(unittest.TestCase):
    def bars(self, closes):
        idx = pd.date_range("2026-01-01", periods=len(closes), freq="h", tz="UTC")
        c = pd.Series(closes, index=idx, dtype=float)
        return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "high": c * 1.001, "low": c * 0.999, "close": c, "sma200": 0.0, "volume": 1.0})

    def test_entry_fills_next_open_and_costs_both_sides(self):
        from robinhood_trading_bot.crypto_backtest import BacktestConfig, run_backtest

        bars = self.bars([100, 100, 101, 102, 103])
        preds = pd.Series([0.05, 0.05, 0.05, -0.01, -0.01], index=bars.index)
        result = run_backtest(bars, preds, BacktestConfig(cost_per_side=0.01, stop_loss_pct=0.5, take_profit_pct=0.5))
        trade = result.trades[0]
        self.assertEqual(trade["entry"], 100)  # bar 1 open = bar 0 close
        self.assertEqual(trade["exit"], 102)   # sell decided at bar 3 close, filled at bar 4 open
        self.assertAlmostEqual(trade["return"], 1.02 * 0.99 * 0.99 - 1, places=9)

    def test_stop_loss_wins_ties_and_gap_fills_at_open(self):
        from robinhood_trading_bot.crypto_backtest import BacktestConfig, run_backtest

        bars = self.bars([100, 100, 90, 90])
        preds = pd.Series([0.01, 0.01, 0.01, 0.01], index=bars.index)
        result = run_backtest(bars, preds, BacktestConfig(cost_per_side=0.0, stop_loss_pct=0.02))
        self.assertEqual(result.trades[0]["reason"], "stop_loss")
        self.assertEqual(result.trades[0]["exit"], 98.0)

    def test_no_entries_below_sma200(self):
        from robinhood_trading_bot.crypto_backtest import BacktestConfig, run_backtest

        bars = self.bars([100] * 6)
        bars["sma200"] = 200.0
        preds = pd.Series(0.05, index=bars.index)
        self.assertEqual(run_backtest(bars, preds, BacktestConfig()).trades, [])

    def test_features_are_scale_free(self):
        from robinhood_trading_bot.crypto_signal import FEATURES, build_features

        rng = np.random.default_rng(0)
        closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
        bars = self.bars(closes)
        a = build_features(bars)[FEATURES]
        scaled = bars.copy()
        for col in ("open", "high", "low", "close"):
            scaled[col] *= 1000
        b = build_features(scaled)[FEATURES]
        pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
