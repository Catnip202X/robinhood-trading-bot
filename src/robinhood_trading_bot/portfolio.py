"""Set-and-forget portfolio lane: a diversified core plus a capped picks sleeve.

The lane holds a fixed mix of core ETFs and a small equal-weight sleeve of
stock picks, and rebalances back to target weights on a schedule (quarterly by
default). It produces dry-run order intents only. It never uses margin: the
only money it can spend is the settled cash you hand it, capped by the plan
budget, plus the proceeds of its own rebalancing sells.

Backtest notes (docs/portfolio-backtest-2026-11-27.md): quarterly was as good as
monthly, and a 200-day trend filter cut drawdowns but cost too much return to
be worth it in a hands-off account, so this lane does not use one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any

CENT = Decimal("0.01")
STOCK_ORDERS_REVIEW_ONLY_REASON = (
    "Stock orders are proposals only; place them yourself or through Robinhood MCP review."
)
DEFAULT_CORE = {"VTI": Decimal("0.5"), "VXUS": Decimal("0.2"), "BND": Decimal("0.2"), "GLD": Decimal("0.1")}
REBALANCE_FREQUENCIES = ("M", "Q", "Y")


@dataclass(frozen=True)
class PortfolioPlan:
    budget_usd: Decimal = Decimal("50")
    core_fraction: Decimal = Decimal("0.75")
    core_weights: dict[str, Decimal] = field(default_factory=lambda: dict(DEFAULT_CORE))
    picks: tuple[str, ...] = ()
    max_picks: int = 8
    pick_cap_fraction: Decimal = Decimal("0.05")
    min_order_usd: Decimal = Decimal("1.00")
    rebalance: str = "Q"

    def __post_init__(self) -> None:
        if self.budget_usd <= 0:
            raise ValueError("budget_usd must be positive")
        if not Decimal("0") <= self.core_fraction <= Decimal("1"):
            raise ValueError("core_fraction must be between 0 and 1")
        if not self.core_weights or any(w <= 0 for w in self.core_weights.values()):
            raise ValueError("core_weights must be positive")
        if abs(sum(self.core_weights.values()) - 1) > Decimal("0.0001"):
            raise ValueError("core_weights must sum to 1")
        if self.max_picks < 0 or not Decimal("0") < self.pick_cap_fraction <= Decimal("1"):
            raise ValueError("max_picks must be >= 0 and pick_cap_fraction in (0, 1]")
        if self.rebalance not in REBALANCE_FREQUENCIES:
            raise ValueError(f"rebalance must be one of {REBALANCE_FREQUENCIES}")
        overlap = set(self.core_weights) & set(self.active_picks)
        if overlap:
            raise ValueError(f"symbols in both core and picks: {sorted(overlap)}")

    @property
    def active_picks(self) -> tuple[str, ...]:
        seen: list[str] = []
        for symbol in self.picks:
            symbol = symbol.strip().upper()
            if symbol and symbol not in seen:
                seen.append(symbol)
        return tuple(seen[: self.max_picks])

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_picks: tuple[str, ...] = ()) -> "PortfolioPlan":
        core = data.get("core_weights")
        picks = tuple(data.get("picks") or fallback_picks)
        return cls(
            budget_usd=Decimal(str(data.get("budget_usd", "50"))),
            core_fraction=Decimal(str(data.get("core_fraction", "0.75"))),
            core_weights={k.upper(): Decimal(str(v)) for k, v in core.items()} if core else dict(DEFAULT_CORE),
            picks=picks,
            max_picks=int(data.get("max_picks", 8)),
            pick_cap_fraction=Decimal(str(data.get("pick_cap_fraction", "0.05"))),
            min_order_usd=Decimal(str(data.get("min_order_usd", "1.00"))),
            rebalance=str(data.get("rebalance", "Q")).upper(),
        )

    @classmethod
    def from_file(cls, path: str | Path, fallback_picks: tuple[str, ...] = ()) -> "PortfolioPlan":
        with Path(path).open(encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle), fallback_picks)


def target_weights(plan: PortfolioPlan) -> dict[str, Decimal]:
    """Core weights scaled to the core fraction, plus equal-weight capped picks.

    Any sleeve weight a pick can't take because of the per-pick cap goes to the
    core, so the targets always sum to 1.
    """

    picks = plan.active_picks
    sleeve = Decimal("1") - plan.core_fraction
    per_pick = min(sleeve / len(picks), plan.pick_cap_fraction) if picks else Decimal("0")
    core_total = Decimal("1") - per_pick * len(picks)
    weights = {symbol: weight * core_total for symbol, weight in plan.core_weights.items()}
    weights.update({symbol: per_pick for symbol in picks})
    return weights


def is_rebalance_due(last_rebalance: date | None, today: date, frequency: str = "Q") -> bool:
    if last_rebalance is None:
        return True
    if frequency == "M":
        period = lambda d: (d.year, d.month)
    elif frequency == "Q":
        period = lambda d: (d.year, (d.month - 1) // 3)
    elif frequency == "Y":
        period = lambda d: (d.year,)
    else:
        raise ValueError(f"unknown rebalance frequency: {frequency}")
    return period(today) > period(last_rebalance)


@dataclass(frozen=True)
class StockOrderIntent:
    symbol: str
    side: str
    dollar_amount: str
    sell_all: bool = False
    order_type: str = "market"
    dry_run_only: bool = True
    execution_blocked_reason: str = STOCK_ORDERS_REVIEW_ONLY_REASON

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "dollar_amount": self.dollar_amount,
            "sell_all": self.sell_all,
            "order_type": self.order_type,
            "dry_run_only": self.dry_run_only,
            "execution_blocked_reason": self.execution_blocked_reason,
        }


@dataclass(frozen=True)
class RebalancePlan:
    lane_value: Decimal
    cash_used_limit: Decimal
    targets: dict[str, Decimal]
    orders: tuple[StockOrderIntent, ...]
    warnings: tuple[str, ...]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "lane_value_usd": str(self.lane_value),
            "new_cash_limit_usd": str(self.cash_used_limit),
            "targets_usd": {k: str(v) for k, v in self.targets.items()},
            "orders": [order.to_public_dict() for order in self.orders],
            "warnings": list(self.warnings),
        }


def _cents(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_DOWN)


def plan_rebalance(plan: PortfolioPlan, holdings_usd: dict[str, Decimal], settled_cash_usd: Decimal) -> RebalancePlan:
    """Return dry-run orders that move the lane back to its targets.

    ``holdings_usd`` is the market value of each position the lane manages.
    ``settled_cash_usd`` is cash only, never margin buying power. The lane adds
    at most ``budget_usd - current holdings`` of new cash, so it never grows
    past the budget with new money, though gains stay invested.
    """

    holdings = {k.upper(): Decimal(v) for k, v in holdings_usd.items() if Decimal(v) > 0}
    held_value = sum(holdings.values(), Decimal("0"))
    new_cash = _cents(max(Decimal("0"), min(Decimal(settled_cash_usd), plan.budget_usd - held_value)))
    lane_value = held_value + new_cash
    weights = target_weights(plan)
    targets = {symbol: _cents(weight * lane_value) for symbol, weight in weights.items()}
    warnings: list[str] = []

    too_small = sorted(s for s, t in targets.items() if t < plan.min_order_usd)
    if too_small and lane_value > 0:
        warnings.append(
            f"targets under the ${plan.min_order_usd} minimum order for {', '.join(too_small)}; "
            "use fewer picks or a larger budget"
        )
    if len(plan.picks) > len(plan.active_picks):
        warnings.append(f"only the first {plan.max_picks} picks are used: {', '.join(plan.active_picks)}")

    sells: list[StockOrderIntent] = []
    buys: list[tuple[str, Decimal]] = []
    proceeds = Decimal("0")
    for symbol in sorted(set(holdings) | set(targets)):
        current = holdings.get(symbol, Decimal("0"))
        target = targets.get(symbol, Decimal("0"))
        diff = target - current
        if symbol not in targets:
            sells.append(StockOrderIntent(symbol, "sell", str(_cents(current)), sell_all=True))
            proceeds += _cents(current)
        elif diff <= -plan.min_order_usd:
            amount = _cents(-diff)
            sells.append(StockOrderIntent(symbol, "sell", str(amount)))
            proceeds += amount
        elif diff >= plan.min_order_usd:
            buys.append((symbol, _cents(diff)))

    spendable = new_cash + proceeds
    wanted = sum((amount for _, amount in buys), Decimal("0"))
    scale = min(Decimal("1"), spendable / wanted) if wanted else Decimal("1")
    buy_orders = []
    for symbol, amount in buys:
        scaled = _cents(amount * scale)
        if scaled >= plan.min_order_usd:
            buy_orders.append(StockOrderIntent(symbol, "buy", str(scaled)))
    if scale < 1:
        warnings.append("buys scaled down to fit available cash")

    return RebalancePlan(lane_value, new_cash, targets, tuple(sells + buy_orders), tuple(warnings))


# ---- backtest -------------------------------------------------------------

def load_close_prices(directory: str | Path, symbols: list[str]):
    """Load ``{SYMBOL}_1d.csv`` files (timestamp,close,...) into one aligned frame."""

    import pandas as pd

    series = {}
    for symbol in symbols:
        frame = pd.read_csv(Path(directory) / f"{symbol}_1d.csv")
        index = pd.to_datetime(frame["timestamp"], unit="s").dt.normalize()
        series[symbol] = pd.Series(frame["close"].to_numpy(dtype=float), index=index)
    return pd.DataFrame(series).dropna()


def backtest_weights(prices, weights: dict[str, float], rebalance: str | None = "Q", cost_per_trade: float = 0.0002):
    """Daily returns of a portfolio rebalanced to ``weights`` each period."""

    import pandas as pd

    names = list(weights)
    target = pd.Series(weights, dtype=float)
    returns = prices[names].pct_change().fillna(0.0)
    if rebalance:
        periods = pd.Series(prices.index.to_period(rebalance), index=prices.index)
        rebalance_days = set(prices.index[periods.ne(periods.shift())])
    else:
        rebalance_days = {prices.index[0]}
    held = target.copy()
    out = []
    for day in prices.index[1:]:
        day_return = float((held * returns.loc[day]).sum())
        held = held * (1 + returns.loc[day]) / (1 + day_return)
        if day in rebalance_days:
            day_return -= float((target - held).abs().sum()) * cost_per_trade
            held = target.copy()
        out.append(day_return)
    return pd.Series(out, index=prices.index[1:])


def summarize_returns(returns) -> dict[str, float]:
    equity = (1 + returns).cumprod()
    years = len(returns) / 252
    std = returns.std()
    return {
        "total_return_pct": round(100 * (equity.iloc[-1] - 1), 2),
        "cagr_pct": round(100 * (equity.iloc[-1] ** (1 / years) - 1), 2) if years > 0 else 0.0,
        "max_drawdown_pct": round(100 * float((equity / equity.cummax() - 1).min()), 2),
        "sharpe": round(float(returns.mean() / std * 252 ** 0.5), 2) if std else 0.0,
    }
