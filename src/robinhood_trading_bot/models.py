from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _public_items(items: tuple[Any, ...]) -> list[dict[str, Any]]:
    public_items = []
    for item in items:
        if not hasattr(item, "to_public_dict"):
            raise TypeError("snapshot items must be sanitized model objects")
        public_items.append(item.to_public_dict())
    return public_items


@dataclass(frozen=True)
class PortfolioSummary:
    total_market_value: str
    buying_power: str

    def to_public_dict(self) -> dict[str, str]:
        return {
            "total_market_value": self.total_market_value,
            "buying_power": self.buying_power,
        }


@dataclass(frozen=True)
class EquityPosition:
    symbol: str
    quantity: str
    market_value: str
    average_price: str | None = None

    def to_public_dict(self) -> dict[str, str | None]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "market_value": self.market_value,
            "average_price": self.average_price,
        }


@dataclass(frozen=True)
class OptionPosition:
    symbol: str
    quantity: str
    market_value: str
    average_price: str | None = None
    expiration_date: str | None = None
    option_type: str | None = None
    strike_price: str | None = None

    def to_public_dict(self) -> dict[str, str | None]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "market_value": self.market_value,
            "average_price": self.average_price,
            "expiration_date": self.expiration_date,
            "option_type": self.option_type,
            "strike_price": self.strike_price,
        }


@dataclass(frozen=True)
class OrderSummary:
    symbol: str
    side: str
    quantity: str
    status: str
    price: str | None = None
    submitted_at: str | None = None

    def to_public_dict(self) -> dict[str, str | None]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "status": self.status,
            "price": self.price,
            "submitted_at": self.submitted_at,
        }


@dataclass(frozen=True)
class RealizedPnlSummary:
    summary: str

    def to_public_dict(self) -> dict[str, str]:
        return {"summary": self.summary}


@dataclass(frozen=True)
class SnapshotReport:
    mode: str
    auth_profile: str
    account_label: str
    portfolio: PortfolioSummary
    equity_positions: tuple[EquityPosition, ...]
    option_positions: tuple[OptionPosition, ...]
    recent_orders: tuple[OrderSummary, ...]
    realized_pnl: RealizedPnlSummary | None

    def to_public_dict(self) -> dict[str, Any]:
        if self.realized_pnl is None:
            realized_pnl = None
        elif hasattr(self.realized_pnl, "to_public_dict"):
            realized_pnl = self.realized_pnl.to_public_dict()
        else:
            raise TypeError("realized_pnl must be a sanitized model object")

        return {
            "mode": self.mode,
            "auth_profile": self.auth_profile,
            "account_label": self.account_label,
            "portfolio": self.portfolio.to_public_dict(),
            "equity_positions": _public_items(tuple(self.equity_positions)),
            "option_positions": _public_items(tuple(self.option_positions)),
            "recent_orders": _public_items(tuple(self.recent_orders)),
            "realized_pnl": realized_pnl,
        }
