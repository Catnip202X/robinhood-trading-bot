# Crypto Trading Lane Design

## Summary

Add crypto as a third trading lane beside stocks and options. The lane should support Robinhood crypto pair discovery and dry-run crypto trade intents now, while keeping live crypto execution disabled until the authenticated Robinhood MCP server exposes official crypto order review and placement tools.

Crypto entries should be autonomous like stocks, but the app must remain dry-run and review-first by default. This project is not financial advice, and crypto can move sharply outside stock-market hours.

## Behavior

- Represent crypto assets as Robinhood currency-pair symbols such as `BTC-USD` and `ETH-USD`.
- Discover crypto pairs through Robinhood MCP `search` with `asset_type="currency_pair"` when the user gives a name or partial pair.
- Size buy candidates in USD notional so partial crypto purchases are supported.
- Treat available buying power as an upper bound, not as permission to spend all cash.
- Apply a separate crypto risk cap, initially capped at 3% of account equity.
- Round USD notional amounts down to cents.
- Skip candidates when buying power, account equity, risk cap, or the resulting notional is missing, zero, negative, or below the minimum practical order amount.

## Order Intent Shape

The app should produce sanitized crypto order intents with:

- `symbol`, such as `BTC-USD`;
- `side`, either `buy` or `sell`;
- `dollar_amount` for buy intents;
- `quantity`, optional for sell intents once holdings are available;
- `order_type`, initially `market`;
- `dry_run_only`, always true until official Robinhood MCP crypto order tools are available;
- `execution_blocked_reason`, explaining that this MCP session does not expose crypto review/place tools when applicable.

## Robinhood MCP Integration

Available in this session:

- `search(asset_type="currency_pair")` for pair discovery.
- watchlist tools that accept `currency_pair_ids`.
- realized P/L tools that can include `asset_classes=["crypto"]`.

Not available in this session:

- crypto-specific order review tools;
- crypto-specific order placement tools;
- crypto-specific order and position listing tools.

The first implementation must not call real crypto order placement. If future Robinhood MCP metadata exposes official tools such as `review_crypto_order` and `place_crypto_order`, the adapter can map the same dry-run order intent into a review-first live workflow.

## Safety

- Keep live crypto execution disabled unless a future MCP review/place path is present and the user explicitly confirms the exact trade in the current thread.
- Keep account numbers, tokens, holdings, orders, logs, and live account state out of Git.
- Keep crypto order intents sanitized so public fixtures and output do not expose account identifiers.
- Include crypto activity in the daily after-action report once reporting supports live crypto data.

## Scope

In scope:

- Pure crypto buy sizing logic.
- Sanitized crypto order intent model.
- Tests for sizing and blocked execution intent behavior.
- README documentation.
- `AGENTS.md` changelog and standing crypto instructions.

Out of scope:

- Real crypto order placement.
- Crypto position/order reads unless official MCP tools become available.
- Scheduler integration.
- News/event crypto discovery.
- Tax-lot accounting.

## Testing

Add unit tests for:

- crypto buy sizing using buying power when it is lower than the risk budget;
- crypto buy sizing using the risk budget when it is lower than buying power;
- cent rounding down;
- skipped candidates for invalid, missing, or non-positive values;
- skipped candidates below the minimum order threshold;
- dry-run crypto order intents marking live execution as blocked when no crypto order tool capability is available.
