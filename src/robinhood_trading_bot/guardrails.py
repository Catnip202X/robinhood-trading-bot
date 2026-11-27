"""Hard limits for the crypto lane, plus an append-only decision log.

These checks run before any order intent is produced. They fix problems from
the original AI_TradeMate bot: its daily loss stop never reset, it could trade
on startup, and it only printed what it did.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CryptoGuardrails:
    max_total_usd: Decimal = Decimal("100")       # never deploy more than this in the lane
    max_position_usd: Decimal = Decimal("100")    # per-coin position cap
    daily_loss_stop_pct: Decimal = Decimal("5")   # stop new entries after this loss today
    allowed_symbols: tuple[str, ...] = ("BTC-USD", "ETH-USD")


@dataclass
class DailyLossTracker:
    """Tracks equity at the start of each UTC day. Resets automatically."""

    day: date | None = None
    start_equity: Decimal | None = None

    def update(self, now: datetime, equity: Decimal) -> None:
        today = now.astimezone(timezone.utc).date()
        if self.day != today:
            self.day = today
            self.start_equity = equity

    def loss_pct(self, equity: Decimal) -> Decimal:
        if not self.start_equity:
            return Decimal("0")
        return (self.start_equity - equity) / self.start_equity * 100

    def halted(self, equity: Decimal, limit_pct: Decimal) -> bool:
        return self.loss_pct(equity) >= limit_pct


def check_buy(
    guardrails: CryptoGuardrails,
    symbol: str,
    dollar_amount: Decimal,
    lane_exposure_usd: Decimal,
    symbol_exposure_usd: Decimal,
    daily: DailyLossTracker,
    equity: Decimal,
) -> tuple[Decimal, str | None]:
    """Return (allowed_amount, block_reason). allowed_amount is 0 when blocked."""

    if symbol not in guardrails.allowed_symbols:
        return Decimal("0"), f"{symbol} is not in the allowed symbols list"
    if daily.halted(equity, guardrails.daily_loss_stop_pct):
        return Decimal("0"), "daily loss stop reached"
    room = min(
        guardrails.max_total_usd - lane_exposure_usd,
        guardrails.max_position_usd - symbol_exposure_usd,
        dollar_amount,
    )
    if room <= 0:
        return Decimal("0"), "position or lane cap reached"
    return room.quantize(Decimal("0.01")), None


class DecisionLog:
    """Append-only JSON Lines log. Keep it in the ignored ``logs/`` folder."""

    def __init__(self, path: str | Path = "logs/crypto_decisions.jsonl"):
        self.path = Path(path)

    def write(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"logged_at": datetime.now(timezone.utc).isoformat(), **record}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")
