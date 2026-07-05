import unittest

from robinhood_trading_bot.risk import stock_buy_dollar_amount, stock_trade_risk_cap_percent


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

    def test_stock_buy_dollar_amount_uses_buying_power_when_it_is_lower(self):
        amount = stock_buy_dollar_amount("25.00", "1000.00", 3.0)

        self.assertEqual(amount, "25.00")

    def test_stock_buy_dollar_amount_uses_risk_budget_when_it_is_lower(self):
        amount = stock_buy_dollar_amount("500.00", "1000.00", 2.5)

        self.assertEqual(amount, "25.00")

    def test_stock_buy_dollar_amount_rounds_down_to_cents(self):
        amount = stock_buy_dollar_amount("500.00", "333.33", 3.0)

        self.assertEqual(amount, "9.99")

    def test_stock_buy_dollar_amount_skips_non_positive_inputs(self):
        self.assertIsNone(stock_buy_dollar_amount("0", "1000.00", 3.0))
        self.assertIsNone(stock_buy_dollar_amount("500.00", "0", 3.0))
        self.assertIsNone(stock_buy_dollar_amount("500.00", "1000.00", 0))

    def test_stock_buy_dollar_amount_skips_amounts_below_minimum(self):
        amount = stock_buy_dollar_amount("0.99", "1000.00", 3.0)

        self.assertIsNone(amount)


if __name__ == "__main__":
    unittest.main()
