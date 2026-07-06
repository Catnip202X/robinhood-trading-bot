from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN

CENT = Decimal("0.01")
DEFAULT_CRYPTO_RISK_CAP_PERCENT = Decimal("3.0")


def _positive_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def stock_trade_risk_cap_percent(daily_percentage_moves: list[float] | tuple[float, ...]) -> float:
    """Return the stock per-trade risk cap percentage.

    The rule is the lower of 3% or half of the average absolute daily
    percentage move over the last seven trading days.
    """

    if len(daily_percentage_moves) != 7:
        raise ValueError("stock risk cap requires exactly 7 daily percentage moves")

    average_absolute_move = sum(abs(move) for move in daily_percentage_moves) / 7
    return min(3.0, average_absolute_move * 0.5)


def stock_buy_dollar_amount(
    buying_power: object,
    account_equity: object,
    risk_cap_percent: object,
    minimum_order_amount: object = "1.00",
) -> str | None:
    """Return a dollar amount for a fractional stock buy candidate.

    The amount is capped by both available buying power and the active
    percentage risk budget. Robinhood fractional stock buys are reviewed as
    dollar-based market orders, so this returns a cents-rounded notional value.
    """

    return _buy_dollar_amount(
        buying_power=buying_power,
        account_equity=account_equity,
        risk_cap_percent=risk_cap_percent,
        minimum_order_amount=minimum_order_amount,
    )


def crypto_buy_dollar_amount(
    buying_power: object,
    account_equity: object,
    risk_cap_percent: object = DEFAULT_CRYPTO_RISK_CAP_PERCENT,
    minimum_order_amount: object = "1.00",
) -> str | None:
    """Return a dollar amount for a fractional crypto buy candidate."""

    return _buy_dollar_amount(
        buying_power=buying_power,
        account_equity=account_equity,
        risk_cap_percent=risk_cap_percent,
        minimum_order_amount=minimum_order_amount,
    )


def _buy_dollar_amount(
    buying_power: object,
    account_equity: object,
    risk_cap_percent: object,
    minimum_order_amount: object,
) -> str | None:
    buying_power_amount = _positive_decimal(buying_power)
    account_equity_amount = _positive_decimal(account_equity)
    risk_cap = _positive_decimal(risk_cap_percent)
    minimum_order = _positive_decimal(minimum_order_amount)

    if not all((buying_power_amount, account_equity_amount, risk_cap, minimum_order)):
        return None

    risk_budget = account_equity_amount * risk_cap / Decimal("100")
    candidate_amount = min(buying_power_amount, risk_budget).quantize(CENT, rounding=ROUND_DOWN)

    if candidate_amount < minimum_order:
        return None

    return f"{candidate_amount:.2f}"
