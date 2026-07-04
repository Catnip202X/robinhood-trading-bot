import unittest

from robinhood_trading_bot.risk import stock_trade_risk_cap_percent


class StockRiskTests(unittest.TestCase):
    def test_stock_risk_cap_uses_three_percent_when_volatility_half_is_higher(self):
        cap = stock_trade_risk_cap_percent([8.0, -7.0, 6.0, -9.0, 5.0, -8.0, 7.0])

        self.assertEqual(cap, 3.0)

    def test_stock_risk_cap_uses_half_average_absolute_move_when_lower_than_three_percent(self):
        cap = stock_trade_risk_cap_percent([1.0, -1.2, 0.8, -1.0, 1.4, -0.6, 1.2])

        self.assertAlmostEqual(cap, 0.5142857142857143)

    def test_stock_risk_cap_requires_seven_daily_moves(self):
        with self.assertRaises(ValueError):
            stock_trade_risk_cap_percent([1.0, 1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
