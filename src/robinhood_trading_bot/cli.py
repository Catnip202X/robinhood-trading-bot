from __future__ import annotations

import argparse
import json

from robinhood_trading_bot.auth import RobinhoodAuthConfig
from robinhood_trading_bot.config import BotConfig
from robinhood_trading_bot.snapshot import build_snapshot_from_fixture


DEFAULT_PLAN = "config/portfolio.json"


def build_status() -> dict[str, object]:
    config = BotConfig.from_env()
    auth = RobinhoodAuthConfig.from_env()
    return {
        "mode": config.mode,
        "timezone": config.timezone,
        "database_path": config.database_path,
        "tech_watchlist": list(config.tech_watchlist),
        "robinhood": auth.safe_summary(),
    }


def run_crypto_backtest(args) -> dict[str, object]:
    from robinhood_trading_bot.candles import load_csv
    from robinhood_trading_bot.crypto_backtest import BacktestConfig, buy_and_hold, run_backtest
    from robinhood_trading_bot.crypto_signal import build_features, walk_forward_predictions

    features = build_features(load_csv(args.candles), horizon_hours=args.horizon_hours)
    predictions = walk_forward_predictions(features, train_bars=len(features) // 2)
    results = []
    for cost in args.cost_per_side or [0.0, 0.001, 0.0025, 0.005]:
        summary = run_backtest(features, predictions, BacktestConfig(cost_per_side=cost)).summary()
        summary["cost_per_side_pct"] = cost * 100
        summary["buy_and_hold_pct"] = round(100 * buy_and_hold(features, predictions.index, cost), 2)
        results.append(summary)
    return {
        "test_start": predictions.index[0],
        "test_end": predictions.index[-1],
        "signal_correlation": round(float(predictions.corr(features.loc[predictions.index, "target"])), 4),
        "results": results,
    }


def run_crypto_signal(args) -> dict[str, object]:
    from datetime import datetime, timezone
    from decimal import Decimal

    from robinhood_trading_bot.candles import fetch_coinbase_hourly, load_csv
    from robinhood_trading_bot.crypto import crypto_market_buy_intent, crypto_market_sell_intent
    from robinhood_trading_bot.crypto_signal import build_features, decide, predict, train_model
    from robinhood_trading_bot.guardrails import CryptoGuardrails, DailyLossTracker, DecisionLog, check_buy
    from robinhood_trading_bot.risk import crypto_buy_dollar_amount

    symbol = args.symbol.upper()
    candles = fetch_coinbase_hourly(symbol, hours=24 * 365) if args.coinbase else load_csv(args.candles)
    features = build_features(candles)
    model = train_model(features.iloc[:-1])
    latest = features.iloc[-1:]
    predicted = float(predict(model, latest).iloc[0])
    holding_quantity = Decimal(args.holding_quantity)
    decision = decide(
        predicted, float(latest["close"].iloc[0]), float(latest["sma200"].iloc[0]),
        holding=holding_quantity > 0, entry_threshold=2 * args.cost_per_side, exit_threshold=0.0,
    )
    equity = Decimal(args.equity)
    close = Decimal(str(latest["close"].iloc[0]))
    intent = None
    blocked = None
    if decision.action == "buy":
        sized = crypto_buy_dollar_amount(args.buying_power, args.equity)
        if sized is None:
            blocked = "buy size below minimum"
        else:
            daily = DailyLossTracker()
            daily.update(datetime.now(timezone.utc), equity)
            amount, blocked = check_buy(
                CryptoGuardrails(), symbol, Decimal(sized), Decimal("0"), holding_quantity * close, daily, equity,
            )
            if not blocked:
                intent = crypto_market_buy_intent(symbol, f"{amount:.2f}")
    elif decision.action == "sell":
        intent = crypto_market_sell_intent(symbol, str(holding_quantity))
    record = {
        "symbol": symbol,
        "bar_time": latest.index[0],
        "close": float(close),
        "predicted_return": predicted,
        "action": decision.action,
        "reason": decision.reason,
        "blocked_reason": blocked,
        "order_intent": intent.to_public_dict() if intent else None,
    }
    DecisionLog(args.log).write(record)
    return record


def _load_plan(path: str):
    from pathlib import Path

    from robinhood_trading_bot.portfolio import PortfolioPlan

    # An empty "picks" list falls back to BOT_TECH_WATCHLIST from .env.
    plan_path = Path(path)
    if path == DEFAULT_PLAN and not plan_path.exists():
        plan_path = Path("config/portfolio.example.json")
    return PortfolioPlan.from_file(plan_path, fallback_picks=BotConfig.from_env().tech_watchlist)


def run_portfolio_plan(args) -> dict[str, object]:
    from datetime import date
    from decimal import Decimal

    from robinhood_trading_bot.guardrails import DecisionLog
    from robinhood_trading_bot.portfolio import is_rebalance_due, plan_deposit, plan_rebalance

    plan = _load_plan(args.plan)
    holdings = {}
    for item in args.holding or []:
        symbol, _, value = item.partition("=")
        holdings[symbol.strip().upper()] = Decimal(value)
    today = date.fromisoformat(args.today) if args.today else date.today()
    if args.deposit:
        result = plan_deposit(plan, holdings, Decimal(args.deposit), Decimal(args.cash))
        record = {"lane": "portfolio", "mode": "dry-run", "today": today.isoformat(), "action": "deposit",
                  "picks": list(plan.active_picks), **result.to_public_dict()}
        DecisionLog(args.log).write(record)
        return record
    last = date.fromisoformat(args.last_rebalance) if args.last_rebalance else None
    due = args.force or is_rebalance_due(last, today, plan.rebalance)
    result = plan_rebalance(plan, holdings, Decimal(args.cash))
    record = {
        "lane": "portfolio",
        "mode": "dry-run",
        "today": today.isoformat(),
        "action": "rebalance",
        "rebalance_due": due,
        "picks": list(plan.active_picks),
        **result.to_public_dict(),
    }
    if not due:
        record["orders"] = []
        record["warnings"] = [*record["warnings"], "not due yet; pass --force to plan anyway"]
    DecisionLog(args.log).write(record)
    return record


def run_portfolio_backtest(args) -> dict[str, object]:
    from robinhood_trading_bot.portfolio import backtest_weights, load_close_prices, summarize_returns, target_weights

    plan = _load_plan(args.plan)
    weights = {k: float(v) for k, v in target_weights(plan).items()}
    core = {k: float(v) for k, v in plan.core_weights.items()}
    symbols = sorted(set(weights) | {"SPY"})
    frames = []
    for directory in args.prices_dir:
        from pathlib import Path

        available = [s for s in symbols if (Path(directory) / f"{s}_1d.csv").exists()]
        if available:
            frames.append(load_close_prices(directory, available))
    import pandas as pd

    prices = pd.concat(frames, axis=1).dropna()
    missing = sorted(set(symbols) - set(prices.columns))
    if missing:
        raise SystemExit(f"missing price files for: {', '.join(missing)}")
    test = prices.iloc[-args.test_days:]
    portfolios = {"plan": weights, "core only": core, "SPY": {"SPY": 1.0}}
    return {
        "window_start": test.index[0].date(),
        "window_end": test.index[-1].date(),
        "rebalance": plan.rebalance,
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "results": {
            name: summarize_returns(backtest_weights(test, w, plan.rebalance)) for name, w in portfolios.items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trading-bot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show local configuration without exposing secrets")
    snapshot_parser = subparsers.add_parser("snapshot", help="Print a sanitized read-only snapshot")
    snapshot_parser.add_argument("--fixture", required=True, help="Path to sanitized snapshot fixture JSON")
    backtest_parser = subparsers.add_parser("crypto-backtest", help="Walk-forward backtest of the long-only crypto signal")
    backtest_parser.add_argument("--candles", required=True, help="CSV of hourly candles (timestamp,open,high,low,close,volume)")
    backtest_parser.add_argument("--cost-per-side", type=float, action="append", help="Spread+fee per buy or sell, e.g. 0.0025 (repeatable)")
    backtest_parser.add_argument("--horizon-hours", type=int, default=1)
    signal_parser = subparsers.add_parser("crypto-signal", help="Dry-run: compute the latest signal and order intent")
    signal_parser.add_argument("--symbol", default="BTC-USD")
    source = signal_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--candles", help="CSV of hourly candles")
    source.add_argument("--coinbase", action="store_true", help="Fetch recent candles from Coinbase public data")
    signal_parser.add_argument("--equity", default="100", help="Account equity in USD (dry-run input)")
    signal_parser.add_argument("--buying-power", default="100", help="Buying power in USD (dry-run input)")
    signal_parser.add_argument("--holding-quantity", default="0", help="Coin quantity currently held")
    signal_parser.add_argument("--cost-per-side", type=float, default=0.0025)
    signal_parser.add_argument("--log", default="logs/crypto_decisions.jsonl")
    plan_parser = subparsers.add_parser("portfolio-plan", help="Dry-run: rebalance orders for the core + picks portfolio")
    plan_parser.add_argument("--plan", default=DEFAULT_PLAN, help="Plan JSON (falls back to config/portfolio.example.json)")
    plan_parser.add_argument("--holding", action="append", help="SYMBOL=USD market value held by this lane (repeatable)")
    plan_parser.add_argument("--cash", required=True, help="Settled cash in USD the lane may use. Never margin buying power.")
    plan_parser.add_argument("--last-rebalance", help="YYYY-MM-DD of the last rebalance")
    plan_parser.add_argument("--today", help="YYYY-MM-DD override for testing")
    plan_parser.add_argument("--deposit", help="USD of new money to invest now, split by target weights")
    plan_parser.add_argument("--force", action="store_true", help="Plan orders even if a rebalance isn't due")
    plan_parser.add_argument("--log", default="logs/portfolio_decisions.jsonl")
    pbt_parser = subparsers.add_parser("portfolio-backtest", help="Backtest the plan's target weights on daily closes")
    pbt_parser.add_argument("--plan", default=DEFAULT_PLAN)
    pbt_parser.add_argument("--prices-dir", action="append", required=True, help="Folder of SYMBOL_1d.csv files (repeatable)")
    pbt_parser.add_argument("--test-days", type=int, default=504, help="Trading days to test, ending at the latest bar")
    args = parser.parse_args(argv)

    if args.command == "status":
        print(json.dumps(build_status(), indent=2, sort_keys=True))
        return 0

    if args.command == "snapshot":
        snapshot = build_snapshot_from_fixture(args.fixture)
        print(json.dumps(snapshot.to_public_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "crypto-backtest":
        print(json.dumps(run_crypto_backtest(args), indent=2, default=str))
        return 0

    if args.command == "crypto-signal":
        print(json.dumps(run_crypto_signal(args), indent=2, default=str))
        return 0

    if args.command == "portfolio-plan":
        print(json.dumps(run_portfolio_plan(args), indent=2, default=str))
        return 0

    if args.command == "portfolio-backtest":
        print(json.dumps(run_portfolio_backtest(args), indent=2, default=str))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
