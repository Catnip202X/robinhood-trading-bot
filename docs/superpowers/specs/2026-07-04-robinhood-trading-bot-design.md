# Robinhood Trading Bot Design

Date: 2026-07-04

## Goal

Build a guarded trading bot that uses Robinhood MCP for broker/account integration, trades stocks autonomously from a user-owned technology watchlist, and handles options through a semi-automated approval workflow.

The first production shape is the Guarded Autonomous Core: autonomous stock execution, semi-automated options entries, automatic options exits, and a daily after-action report before the nightly options approval decision.

This design is not financial advice. The bot must treat every trade as risky, must maintain a complete audit trail, and must fail closed when data, account state, or broker state cannot be verified.

## Scope

In scope:

- Autonomous stock trading from the user's configured tech ticker list.
- Market-hours stock and options price-change checks every 30 minutes.
- Options discovery from broader news, events, price action, and market catalysts.
- Nightly 10 PM America/New_York options review and approval flow.
- Next-market-day scheduling for approved option entries.
- Automatic option exits based on profit and principal-protection rules.
- FINRA intraday-margin-aware risk checks using current FINRA Notice 26-10 framing and Robinhood MCP account constraints.
- Daily after-action reporting for trades, skipped trades, exposure, and rationale.
- Local persistent storage of signals, decisions, approvals, orders, positions, and reports.
- Dry-run, shadow, and staged rollout modes.

Out of scope for the first design:

- Fully autonomous options entries.
- High-frequency trading or sub-minute execution.
- Trading assets outside stocks and options.
- Portfolio-margin-specific optimization unless the connected Robinhood account exposes that account type and constraints.
- Building a replacement for Robinhood's regulatory, suitability, or margin systems.

## Architecture

The bot is a Python service with five bounded modules.

### Scheduler

Runs recurring jobs:

- Every 30 minutes during market hours: stock signal evaluation and option price/signal refresh.
- 10 PM America/New_York: daily after-action report and options proposal review.
- Next market day: submit approved option entry orders when eligible.

The scheduler must be market-calendar aware. It should skip closed-market days and handle holidays, half-days, and daylight saving time using an exchange calendar library.

### Signal Engine

Collects and normalizes input data:

- Stock watchlist prices, recent candles, volume, account positions, and relevant news/events.
- Options candidate discovery from broader market news, events, earnings, analyst actions, unusual movement, and options-chain data where available.
- Robinhood account notices, order status, buying power, positions, and balances when exposed by Robinhood MCP.

Stocks use only the configured tech watchlist. Options may discover tickers from broader news and events.

### Decision Engine

Turns normalized signals into candidate actions:

- Stock candidates: buy, sell, trim, add, or hold.
- Option entry candidates: proposed buy orders for nightly approval.
- Option exit candidates: automatic sell orders when exit rules trigger.

The Decision Engine produces an explanation for every candidate, including the signal inputs, confidence, expected catalyst, and reason for action or inaction.

### Risk And Compliance Gate

Every candidate must pass this gate before it can become an order or proposal.

The gate checks:

- Robinhood MCP account state and buying power.
- FINRA intraday-margin requirements and broker-provided constraints.
- Stale data and missing data.
- Duplicate or conflicting open orders.
- Existing position exposure.
- Daily loss limits.
- Max open positions.
- Max exposure per ticker.
- Approval validity for options entries.

For stocks, per-trade risk is capped at:

```text
min(3% of account equity, 0.5 * average absolute daily percentage move over the last 7 trading days)
```

The risk cap is a maximum risk budget, not a target. The bot may size smaller or skip a trade if liquidity, volatility, buying power, or margin state is unfavorable.

### Broker Adapter

Uses Robinhood MCP for account state, positions, orders, and stock execution.

Options use the same adapter boundary. If Robinhood MCP supports options execution for the account, approved option entries and automatic exits may route through it. If not, options entries and exits remain prepared, logged, and surfaced for manual action until support is confirmed.

The adapter must be replaceable enough that tests can run against a simulator and dry-run implementation.

## Data Flow

Normal trading flow:

```text
Scheduler -> Signal Engine -> Decision Engine -> Risk And Compliance Gate -> Broker Adapter -> Audit Log
```

Options approval flow:

```text
10 PM Proposal Job -> Daily After-Action Report -> Options Proposal Review -> Approve/Decline -> Next-Market-Day Entry Scheduler -> Broker Adapter
```

Every decision, rejected candidate, proposal, approval, order submission, order status update, and position snapshot is written to local storage.

## Trading Rules

### Stocks

The bot trades stocks autonomously from the configured technology ticker watchlist.

Every 30 minutes during market hours, it evaluates:

- Recent price movement.
- Recent candles and average absolute daily percentage move over the last 7 trading days.
- Volume and liquidity.
- Current positions.
- Buying power and account constraints.
- Relevant news/events for watchlist tickers.

Permitted stock actions:

- Buy.
- Sell.
- Trim.
- Add.
- Hold.

All stock orders must pass the Risk And Compliance Gate.

### Options

The bot scans for options opportunities using broader news, events, and price changes every 30 minutes. It does not autonomously open options positions.

At 10 PM America/New_York, it presents proposed option buys for the next market day. Each proposal includes:

- Ticker.
- Direction and strategy.
- Contract details where available.
- Catalyst and supporting evidence.
- Suggested entry limit.
- Risk notes.
- Exit rules.
- Expiration of approval.

Approved option buys are eligible only on the next market day. If the order is not placed or filled within its configured eligibility window, approval expires and the trade must be re-approved.

Option exits may be automatic after a position exists.

Exit rules:

- Take profit when market value reaches about 2x total purchase cost.
- Defensive exit when a profitable option starts dropping back toward entry and reaches +10% above entry.

The defensive exit is intended to protect principal and avoid allowing a winner to decay back to breakeven.

## FINRA And Broker Constraints

The bot uses the current FINRA intraday-margin framework from FINRA Notice 26-10 rather than old pattern-day-trader count rules.

The Risk And Compliance Gate must:

- Read and respect broker-provided buying power, margin, account, and order constraints.
- Track intraday exposure and margin-impacting transactions when data is available.
- Block trades if the account state cannot be verified.
- Log broker warnings, blocks, rejects, and margin-related fields.
- Fail closed when Robinhood MCP reports insufficient buying power, insufficient margin, restricted trading, or unsupported order behavior.

## Daily After-Action Report

At 10 PM America/New_York, before options approvals, the bot generates a daily after-action report.

The report includes:

- All autonomous stock trades made that day.
- All automatic option exits made that day.
- Rejected or skipped trades with risk/compliance reasons.
- Closed-trade P/L snapshot when available.
- Unrealized P/L for open positions.
- Signals that caused each trade or skip.
- Remaining exposure by ticker and asset type.
- Open orders and unresolved broker statuses.
- Next-day option proposals for approve/decline.

The report should be reviewable from the local UI and persisted to storage for later audit.

## Storage

Use a local database for:

- Watchlist tickers.
- Signal snapshots.
- News and event references.
- Trade candidates.
- Rejected candidates.
- User approvals and declines.
- Scheduled option entries.
- Submitted orders.
- Order status changes.
- Position snapshots.
- P/L snapshots.
- Daily after-action reports.
- Configuration and safety limits.

SQLite is sufficient for the first version unless multi-user or remote deployment becomes a requirement.

## User Interface

The first version should use a simple local interface:

- Command-line tools or a lightweight local web dashboard.
- 10 PM review screen.
- Daily after-action report.
- Option proposal approve/decline controls.
- Manual pause switch for all trading.
- Separate pause switches for stock buys, stock sells, option entries, and option exits.
- Current mode indicator: dry-run, shadow, stock-live, or stock-live/options-semi-auto.

The UI should make it obvious whether real orders can be submitted.

## Safety Controls

Required safety controls:

- Dry-run mode.
- Live shadow mode.
- Hard daily loss limit.
- Max open positions.
- Max exposure per ticker.
- Duplicate-order protection.
- Stale-signal blocking.
- Missing-account-state blocking.
- Unsupported-broker-operation blocking.
- Full audit log for trade and no-trade decisions.
- Emergency pause for all trading.
- Separate pauses for stock buys, stock sells, option entries, and option exits.

The bot must never place a real order when it cannot prove it is in a live-enabled mode, connected to the expected Robinhood MCP account, and operating with fresh account state.

## Rollout

Rollout stages:

1. Dry-run backtest/simulation using historical candles and captured news/event snapshots.
2. Live shadow mode using live data but no orders.
3. Stocks live, options manual: autonomous stock execution through Robinhood MCP, options proposal-only or manually executed.
4. Stocks live, options semi-auto: next-day approved option entries and automatic exits through Robinhood MCP if options support is verified for the account.

Each stage must produce after-action reports before moving to the next stage.

## Testing

Tests must cover:

- Scheduler behavior across market days, holidays, half-days, and 10 PM review timing.
- Stock risk cap sizing.
- FINRA intraday-margin gate behavior with mocked broker constraints.
- Duplicate-order blocking.
- Stale data blocking.
- Missing account-state blocking.
- Approval expiration after the next market day.
- Option take-profit trigger at about 2x purchase cost.
- Option defensive exit trigger at +10% above entry after a rollover toward entry.
- Daily after-action report generation.
- Broker adapter failure handling.
- Dry-run and shadow mode guarantees.

## Open Implementation Details

These details should be finalized during implementation planning:

- Exact external market/news providers.
- Exact Robinhood MCP tool surface available to the user's account.
- Exact order types supported for stocks and options.
- Whether options exits can be fully automated through Robinhood MCP in the user's account.
- Daily loss limit value.
- Max open positions and max exposure per ticker.
- UI choice: CLI-first or lightweight local web dashboard.

## References

- FINRA Regulatory Notice 26-10: https://www.finra.org/rules-guidance/notices/26-10
- Robinhood day trading support article: https://robinhood.com/us/en/support/articles/pattern-day-trading/
- Robinhood MCP and agentic trading public reporting: https://www.axios.com/2026/05/27/robinhood-ai-trading-credit-card
