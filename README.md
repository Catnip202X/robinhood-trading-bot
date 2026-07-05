# Robinhood Trading Bot

A guarded Python scaffold for a Robinhood-connected trading bot.

The design goal is a two-lane system:

- Stocks: autonomous trading from a user-owned technology watchlist.
- Options: event/news discovery with nightly human approval for next-market-day entries and automatic exits when configured profit/protection rules trigger.

This project is not financial advice. Automated trading can lose money quickly, and options can lose the entire premium paid. Start in `dry-run` mode, review every decision, and only connect live brokerage access after you understand the risks.

## Current Status

This repository currently contains the design spec and a standalone app scaffold. Broker execution is intentionally behind an adapter boundary so each user authenticates their own Robinhood MCP account locally.

## Public Repo Safety

This repo is designed to be public:

- Real secrets belong in `.env`, a local secrets manager, or your MCP client configuration.
- `.env`, token folders, key files, local data, and logs are ignored by Git.
- `.env.example` contains placeholders only.
- The app defaults to `dry-run` mode.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` locally with your own settings. Do not commit `.env`.

Configure Robinhood MCP locally before using live broker data:

1. Trust this project in Codex so [.codex/config.toml](.codex/config.toml) can load.
2. Confirm the `robinhood_trading` MCP server uses Streamable HTTP.
3. Use this MCP URL:

   ```text
   https://agent.robinhood.com/mcp/trading
   ```

4. If OAuth is required, run:

   ```powershell
   codex mcp login robinhood_trading
   ```

Keep Robinhood tokens, account identifiers, and private MCP configuration out of Git. See [docs/AUTH.md](docs/AUTH.md) for the full authentication guide.

## Run

```powershell
trading-bot status
```

The status command reports the configured mode, watchlist, and whether Robinhood MCP auth settings are present. It does not place trades.

To print a read-only sanitized snapshot from fixture data:

```powershell
$env:PYTHONPATH='src'
python -m robinhood_trading_bot.cli snapshot --fixture tests/fixtures/read_only_snapshot.json
```

The snapshot command currently reads only sanitized local fixture data and prints public JSON. It does not call Robinhood MCP, expose account numbers, or place trades.

## Stock Buy Sizing

Stock entries are sized as dollar-based fractional buy candidates. The bot uses Robinhood buying power as the available cash ceiling, then applies the stock risk rule from this repo: the active risk cap is the lower of 3% of account equity or half of the average absolute daily percentage move over the last 7 trading days.

The helper `stock_buy_dollar_amount` returns the lower of available buying power and that risk-budget dollar amount, rounded down to cents. Candidates below the minimum order amount are skipped. This value is intended for Robinhood equity market buy reviews using `dollar_amount`; it is not a live order placement path.

## Tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## Robinhood Authentication

See [docs/AUTH.md](docs/AUTH.md). In short: authenticate Robinhood MCP locally using your own account and keep all account IDs, tokens, API keys, and MCP credentials out of Git.

This repo includes a project-scoped Codex MCP entry at [.codex/config.toml](.codex/config.toml):

```toml
[mcp_servers.robinhood_trading]
url = "https://agent.robinhood.com/mcp/trading"
```

In Codex, select Streamable HTTP if adding it manually, or trust the project so the checked-in config can load. Use `codex mcp login robinhood_trading` if the Robinhood MCP server asks for OAuth.

## Design

The approved design spec is in [docs/superpowers/specs/2026-07-04-robinhood-trading-bot-design.md](docs/superpowers/specs/2026-07-04-robinhood-trading-bot-design.md).
