from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CRYPTO_ORDER_TOOLS_UNAVAILABLE_REASON = (
    "Robinhood MCP crypto review/place tools are not available in this session."
)


@dataclass(frozen=True)
class CryptoOrderIntent:
    symbol: str
    side: str
    dollar_amount: str | None = None
    quantity: str | None = None
    order_type: str = "market"
    dry_run_only: bool = True
    execution_blocked_reason: str = CRYPTO_ORDER_TOOLS_UNAVAILABLE_REASON

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        side = self.side.strip().lower()
        order_type = self.order_type.strip().lower()

        if not symbol:
            raise ValueError("crypto order intent requires a symbol")
        if side not in {"buy", "sell"}:
            raise ValueError("crypto order intent side must be buy or sell")
        if order_type != "market":
            raise ValueError("crypto order intent currently supports market orders only")
        if side == "buy" and not self.dollar_amount:
            raise ValueError("crypto buy intent requires dollar_amount")
        if side == "sell" and not self.quantity:
            raise ValueError("crypto sell intent requires quantity")

        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "side", side)
        object.__setattr__(self, "order_type", order_type)

    def to_public_dict(self) -> dict[str, str | bool | None]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "dollar_amount": self.dollar_amount,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "dry_run_only": self.dry_run_only,
            "execution_blocked_reason": self.execution_blocked_reason,
        }


def crypto_market_buy_intent(symbol: str, dollar_amount: str) -> CryptoOrderIntent:
    return CryptoOrderIntent(symbol=symbol, side="buy", dollar_amount=dollar_amount)


def crypto_market_sell_intent(symbol: str, quantity: str) -> CryptoOrderIntent:
    return CryptoOrderIntent(symbol=symbol, side="sell", quantity=quantity)


def public_crypto_order_intents(intents: tuple[Any, ...]) -> list[dict[str, str | bool | None]]:
    public_intents = []
    for intent in intents:
        if not hasattr(intent, "to_public_dict"):
            raise TypeError("crypto order intents must be sanitized model objects")
        public_intents.append(intent.to_public_dict())
    return public_intents
