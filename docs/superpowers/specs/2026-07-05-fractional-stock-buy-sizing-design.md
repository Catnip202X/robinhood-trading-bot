# Fractional Stock Buy Sizing Design

## Summary

Add support for stock buy candidates sized in dollars so the bot can use Robinhood fractional share market buys. The feature applies only to stock entries from the fixed technology ticker watchlist.

The bot must treat available Robinhood buying power as an upper bound, not as permission to spend all cash. Every candidate remains constrained by the existing stock risk rule: use the lower of 3% of account equity or half of the average absolute daily percentage move over the last 7 trading days.

## Behavior

- Fetch or receive the current stock buying power for the selected agentic Robinhood account.
- Compute the active stock risk percentage from the existing risk rule.
- Convert that risk percentage into a dollar allocation budget against account equity.
- Size each stock buy candidate as the lower of:
  - available buying power, and
  - the risk-budget dollar amount.
- Round the resulting dollar amount down to cents.
- Skip buy candidates when buying power, account equity, or risk budget is missing, zero, negative, or below Robinhood's minimum practical order size.

## Robinhood Order Shape

Fractional stock buys should use Robinhood equity market buy reviews with `dollar_amount`, not share `quantity`.

The app must call review/simulation before any real stock buy. Real order placement remains blocked unless the user explicitly confirms the exact trade action in the current thread and live mode has been intentionally enabled.

## Scope

In scope:

- Pure dollar-sizing logic that can be tested without live Robinhood calls.
- Documentation that explains fractional dollar buy sizing and the safety bounds.
- Changelog entry in `AGENTS.md`.

Out of scope:

- Real order placement.
- Options implementation.
- Scheduler changes.
- News/event discovery.
- Persisting account identifiers or live account data.

## Testing

Add unit tests for:

- buying power lower than risk budget,
- risk budget lower than buying power,
- cent rounding down,
- skipped candidates for missing or non-positive values,
- skipped candidates below the minimum dollar order threshold.
