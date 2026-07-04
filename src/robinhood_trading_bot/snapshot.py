from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from robinhood_trading_bot.models import (
    EquityPosition,
    OptionPosition,
    OrderSummary,
    PortfolioSummary,
    RealizedPnlSummary,
    SnapshotReport,
)


def build_snapshot_from_fixture(path: str | Path) -> SnapshotReport:
    with Path(path).open(encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)

    portfolio = PortfolioSummary(
        total_market_value=data["portfolio"]["total_market_value"],
        buying_power=data["portfolio"]["buying_power"],
    )

    return SnapshotReport(
        mode=data["mode"],
        auth_profile=data["auth_profile"],
        account_label=data["account_label"],
        portfolio=portfolio,
        equity_positions=tuple(_build_equity_position(item) for item in data["equity_positions"]),
        option_positions=tuple(_build_option_position(item) for item in data["option_positions"]),
        recent_orders=tuple(_build_order_summary(item) for item in data["recent_orders"]),
        realized_pnl=_build_realized_pnl(data["realized_pnl"]),
    )


def _build_equity_position(data: dict[str, Any]) -> EquityPosition:
    average_cost = data.get("average_cost")
    market_value = data.get("market_value")
    if market_value is None and average_cost is not None:
        market_value = _money(Decimal(data["quantity"]) * Decimal(average_cost))

    return EquityPosition(
        symbol=data["symbol"],
        quantity=data["quantity"],
        market_value=market_value,
        average_price=average_cost,
    )


def _build_option_position(data: dict[str, Any]) -> OptionPosition:
    return OptionPosition(
        symbol=data["symbol"],
        quantity=data["quantity"],
        market_value=data["market_value"],
        average_price=data.get("average_price") or data.get("average_cost"),
        expiration_date=data.get("expiration_date"),
        option_type=data.get("option_type"),
        strike_price=data.get("strike_price"),
    )


def _build_order_summary(data: dict[str, Any]) -> OrderSummary:
    return OrderSummary(
        symbol=data["symbol"],
        side=data["side"],
        quantity=data["quantity"],
        status=data["status"],
        price=data.get("price"),
        submitted_at=data.get("submitted_at"),
    )


def _build_realized_pnl(data: dict[str, Any] | None) -> RealizedPnlSummary | None:
    if data is None:
        return None

    return RealizedPnlSummary(summary=data["summary"])


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"
