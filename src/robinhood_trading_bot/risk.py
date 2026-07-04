from __future__ import annotations


def stock_trade_risk_cap_percent(daily_percentage_moves: list[float] | tuple[float, ...]) -> float:
    """Return the stock per-trade risk cap percentage.

    The rule is the lower of 3% or half of the average absolute daily
    percentage move over the last seven trading days.
    """

    if len(daily_percentage_moves) != 7:
        raise ValueError("stock risk cap requires exactly 7 daily percentage moves")

    average_absolute_move = sum(abs(move) for move in daily_percentage_moves) / 7
    return min(3.0, average_absolute_move * 0.5)
