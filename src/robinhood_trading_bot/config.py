from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from robinhood_trading_bot.env import merged_env


def _parse_watchlist(raw_value: str) -> tuple[str, ...]:
    tickers = []
    for item in raw_value.split(","):
        ticker = item.strip().upper()
        if ticker:
            tickers.append(ticker)
    return tuple(tickers)


@dataclass(frozen=True)
class BotConfig:
    mode: str = "dry-run"
    timezone: str = "America/New_York"
    database_path: str = "data/trading-bot.sqlite3"
    tech_watchlist: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "BotConfig":
        env = merged_env(env_file)
        return cls(
            mode=env.get("BOT_MODE", "dry-run").strip() or "dry-run",
            timezone=env.get("BOT_TIMEZONE", "America/New_York").strip() or "America/New_York",
            database_path=env.get("BOT_DATABASE_PATH", "data/trading-bot.sqlite3").strip()
            or "data/trading-bot.sqlite3",
            tech_watchlist=_parse_watchlist(env.get("BOT_TECH_WATCHLIST", "")),
        )
