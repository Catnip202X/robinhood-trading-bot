"""Long-only hourly crypto backtest with realistic fills.

Rules match the live lane:
- Decide on bar ``i``'s close, fill at bar ``i+1``'s open.
- Every entry has a stop-loss and a take-profit. They are checked against each
  bar's high/low. If both could have triggered in the same bar, the stop is
  assumed to have hit first (pessimistic). A gap through the stop fills at the
  open.
- ``cost_per_side`` covers spread plus fee on every buy and every sell.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class BacktestConfig:
    cost_per_side: float = 0.0025
    entry_threshold: float | None = None  # default: round-trip cost
    exit_threshold: float = 0.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    max_hold_hours: int = 48
    position_fraction: float = 1.0
    daily_loss_stop_pct: float = 0.05

    @property
    def effective_entry_threshold(self) -> float:
        return 2 * self.cost_per_side if self.entry_threshold is None else self.entry_threshold


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: list[dict] = field(default_factory=list)

    def summary(self) -> dict:
        eq = self.equity
        total = eq.iloc[-1] / eq.iloc[0] - 1
        drawdown = (eq / eq.cummax() - 1).min()
        wins = [t for t in self.trades if t["return"] > 0]
        exposure = sum(t["bars"] for t in self.trades) / max(len(eq), 1)
        return {
            "total_return_pct": round(100 * total, 2),
            "max_drawdown_pct": round(100 * drawdown, 2),
            "trades": len(self.trades),
            "win_rate_pct": round(100 * len(wins) / len(self.trades), 1) if self.trades else None,
            "avg_trade_pct": round(100 * sum(t["return"] for t in self.trades) / len(self.trades), 3) if self.trades else None,
            "exposure_pct": round(100 * exposure, 1),
        }


def run_backtest(bars: pd.DataFrame, predictions: pd.Series, config: BacktestConfig, start_equity: float = 100.0) -> BacktestResult:
    """``bars`` needs open/high/low/close/sma200, indexed like ``predictions``."""

    bars = bars.loc[predictions.index]
    opens, highs, lows, closes = (bars[c].to_numpy() for c in ("open", "high", "low", "close"))
    sma = bars["sma200"].to_numpy()
    preds = predictions.to_numpy()
    days = bars.index.floor("D")
    cost = config.cost_per_side
    entry_thr = config.effective_entry_threshold

    cash = start_equity
    units = 0.0
    entry_price = stop = take = 0.0
    entry_bar = -1
    pending: str | None = None
    day_start_equity = start_equity
    current_day = days[0]
    halted = False
    trades: list[dict] = []
    equity_curve = []
    entry_cost_basis = 0.0

    def close_position(price: float, i: int, reason: str) -> None:
        nonlocal cash, units, entry_bar
        proceeds = units * price * (1 - cost)
        cash += proceeds
        trades.append({
            "entry_time": bars.index[entry_bar], "exit_time": bars.index[i], "entry": entry_price,
            "exit": price, "return": proceeds / entry_cost_basis - 1, "bars": i - entry_bar, "reason": reason,
        })
        units = 0.0
        entry_bar = -1

    for i in range(len(bars)):
        if days[i] != current_day:
            current_day = days[i]
            day_start_equity = cash + units * opens[i]
            halted = False

        # 1) act on the decision made at the previous close
        if pending == "buy" and units == 0 and not halted:
            stake = cash * config.position_fraction
            fill = opens[i]
            units = stake * (1 - cost) / fill
            cash -= stake
            entry_cost_basis = stake
            entry_price, entry_bar = fill, i
            stop = fill * (1 - config.stop_loss_pct)
            take = fill * (1 + config.take_profit_pct)
        elif pending == "sell" and units > 0:
            close_position(opens[i], i, "signal")
        pending = None

        # 2) intrabar stop / take-profit
        if units > 0:
            if lows[i] <= stop:
                close_position(min(opens[i], stop), i, "stop_loss")
            elif highs[i] >= take:
                close_position(max(opens[i], take), i, "take_profit")

        equity = cash + units * closes[i]
        if equity <= day_start_equity * (1 - config.daily_loss_stop_pct):
            halted = True
            if units > 0:
                pending = "sell"
        equity_curve.append(equity)

        # 3) decide at this close for the next bar
        if pending is None:
            if units == 0 and not halted:
                if preds[i] > entry_thr and closes[i] > sma[i]:
                    pending = "buy"
            elif units > 0:
                if preds[i] < config.exit_threshold or i - entry_bar >= config.max_hold_hours:
                    pending = "sell"

    if units > 0:
        close_position(closes[-1], len(bars) - 1, "end")
        equity_curve[-1] = cash
    return BacktestResult(pd.Series(equity_curve, index=bars.index), trades)


def buy_and_hold(bars: pd.DataFrame, index: pd.Index, cost_per_side: float) -> float:
    sub = bars.loc[index]
    return (sub["close"].iloc[-1] / sub["open"].iloc[0]) * (1 - cost_per_side) ** 2 - 1


def sma_filter_only(bars: pd.DataFrame, index: pd.Index, config: BacktestConfig) -> BacktestResult:
    """Baseline: hold the coin whenever close > SMA200, using the same stops and costs."""

    sub = bars.loc[index]
    fake = pd.Series(1.0, index=index)  # always "predict" up; the SMA filter decides
    no_stops = BacktestConfig(
        cost_per_side=config.cost_per_side, entry_threshold=0.5, exit_threshold=-1.0,
        stop_loss_pct=config.stop_loss_pct, take_profit_pct=config.take_profit_pct,
        max_hold_hours=10**9, position_fraction=config.position_fraction,
        daily_loss_stop_pct=config.daily_loss_stop_pct,
    )
    # exit when price falls below the SMA200
    signal = fake.where(sub["close"] > sub["sma200"], -2.0)
    return run_backtest(sub, signal, no_stops)
