from __future__ import annotations

import argparse
import json

from robinhood_trading_bot.auth import RobinhoodAuthConfig
from robinhood_trading_bot.config import BotConfig
from robinhood_trading_bot.snapshot import build_snapshot_from_fixture


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trading-bot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Show local configuration without exposing secrets")
    snapshot_parser = subparsers.add_parser("snapshot", help="Print a sanitized read-only snapshot")
    snapshot_parser.add_argument("--fixture", required=True, help="Path to sanitized snapshot fixture JSON")
    args = parser.parse_args(argv)

    if args.command == "status":
        print(json.dumps(build_status(), indent=2, sort_keys=True))
        return 0

    if args.command == "snapshot":
        snapshot = build_snapshot_from_fixture(args.fixture)
        print(json.dumps(snapshot.to_public_dict(), indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
