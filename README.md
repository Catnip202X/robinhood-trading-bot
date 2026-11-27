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

## Crypto Lane

Crypto uses Robinhood currency-pair symbols such as `BTC-USD` and `ETH-USD`. Pair discovery can use Robinhood MCP search with `asset_type="currency_pair"` when the MCP server is available.

Crypto buy candidates are sized as USD notional amounts so partial crypto purchases are supported. The helper `crypto_buy_dollar_amount` uses buying power as the cash ceiling, applies the crypto risk cap of 3% of account equity by default, rounds down to cents, and skips candidates below the minimum order amount.

The app currently creates sanitized dry-run crypto order intents only. Live crypto execution remains blocked until the authenticated Robinhood MCP server exposes official crypto order review and placement tools, and even then real orders require explicit confirmation of the exact trade.

## Crypto Signal Lane (BTC-USD, ETH-USD)

A long-only hourly signal adapted from [AI_TradeMate_For_BTCUSDT](https://github.com/KisaragiMomoe/AI_TradeMate_For_BTCUSDT), rebuilt for Robinhood spot crypto (no shorting, no leverage):

- `crypto_signal.py`: scale-free features and a LightGBM model predicting the next hour's return. Entries need a prediction above the round-trip cost and price above the 200-hour SMA.
- `crypto_backtest.py`: walk-forward backtest with next-bar fills, pessimistic stop/take-profit handling, per-side costs and a daily loss stop.
- `guardrails.py`: lane and per-coin USD caps, an allowed-symbols list, a daily loss stop that resets each UTC day, and an append-only JSON Lines decision log in `logs/`.
- `rh_crypto_api.py`: a signed client for Robinhood's official [Crypto Trading API](https://docs.robinhood.com/crypto/trading/). Order placement raises `LiveOrdersBlocked` unless the client is built with `allow_live_orders=True`, and nothing in the app does that yet.
- `candles.py`: hourly candles from Coinbase public data, because the Robinhood API has no candle history.

```powershell
python -m pip install -e ".[signals,api]"
$env:PYTHONPATH='src'
python -m robinhood_trading_bot.cli crypto-backtest --candles data/btc_usd_1h.csv
python -m robinhood_trading_bot.cli crypto-signal --symbol ETH-USD --coinbase --equity 100 --buying-power 100
```

`crypto-signal` is dry-run only. It prints and logs the decision and a sanitized order intent. See [docs/crypto-backtest-2026-11-27.md](docs/crypto-backtest-2026-11-27.md) for the first backtest: the signal showed no edge after costs, so live execution stays off.

## Portfolio Lane (set-and-forget, dry-run)

A long-term lane: a diversified core of ETFs plus a small equal-weight sleeve of stock picks, rebalanced back to target weights once a quarter. It only prints and logs proposed orders.

- Default plan (`config/portfolio.example.json`): $50 budget, 75% core (VTI 50%, VXUS 20%, BND 20%, GLD 10%) and 25% picks, at most 8 picks, each capped at 5% of the lane, $1 minimum order.
- Default picks: MSFT, AAPL, GOOGL, NVDA, MU, NFLX, PYPL, TSLA (one or two per industry, chosen from 2021-24 return correlations so the sleeve isn't mostly chip stocks).
- Copy it to `config/portfolio.json` (ignored by Git) to customise. An empty `picks` list uses the first 8 tickers in `BOT_TECH_WATCHLIST`.
- Deposits: `--deposit 100` invests new money right away, split by the target weights and tilted toward whatever is under target. Deposits aren't limited by the starting budget but never exceed settled cash.
- `--cash` must be settled cash. The lane never uses margin buying power, and new cash is capped at the budget minus what the lane already holds.
- Picks dropped from the plan are sold in full. Drift under the $1 minimum is left alone.

```bash
# What would a rebalance do today?
python -m robinhood_trading_bot.cli portfolio-plan --cash 50 --holding VTI=18.40 --last-rebalance 2026-09-30

# Invest a new deposit (e.g. on payday)
python -m robinhood_trading_bot.cli portfolio-plan --cash 120 --deposit 100 --holding VTI=40 --holding BND=15

# Backtest the plan's weights on daily closes (folders of SYMBOL_1d.csv files)
python -m robinhood_trading_bot.cli portfolio-backtest --prices-dir path/to/etfs --prices-dir path/to/stocks
```

See `docs/portfolio-backtest-2026-11-27.md` for the backtest behind these defaults.

## Connecting the Robinhood Crypto API

The Crypto Trading API covers crypto only. Stock and ETF orders from the portfolio lane are proposals you place yourself.

1. `pip install -e .[api]`, then `python -m robinhood_trading_bot.cli crypto-keygen`. It prints a public and a private key once.
2. On a desktop browser, open Robinhood (web classic), go to crypto account settings, choose **Add key**, paste the **public** key, and pick read-only actions to start.
3. Copy `.env.example` to `.env` and fill in `ROBINHOOD_CRYPTO_API_KEY` (from Robinhood) and `ROBINHOOD_CRYPTO_PRIVATE_KEY` (from step 1). `.env` is ignored by Git.
4. `python -m robinhood_trading_bot.cli crypto-check` makes a read-only call to confirm the keys work. Order placement stays blocked in code.

If a private key is ever exposed, delete that key on Robinhood and make a new one.

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
