# AGENTS.md

## Project Summary

This repository is for a guarded Robinhood-connected trading bot.

The intended app has two trading lanes:

- Stocks: autonomous trading for a user-provided fixed list of technology tickers.
- Options: event/news-driven discovery with nightly human approval for next-market-day entries and automatic exits when configured exit rules trigger.

The bot must integrate with Robinhood through the authenticated `robinhood_trading-2` MCP server when available. The local app must stay safe by default and run in `dry-run` mode unless the user explicitly enables a live mode.

This project is not financial advice. Treat all trading actions as high risk. Never place real orders unless the user has explicitly requested and confirmed the specific trade action in the current context.

## Standing User Instructions

- Use Robinhood MCP as the broker/account interface.
- Use the authenticated MCP server name `robinhood_trading-2` for local profile references.
- Keep credentials, tokens, account identifiers, local databases, and logs out of Git.
- Keep `.env` local-only and ignored.
- Stocks use a fixed technology ticker watchlist supplied by the user.
- Stock price and options price-change checks should run every 30 minutes once the scheduler exists.
- Options trade confirmations should happen around 10 PM America/New_York.
- Options entries are semi-automated: present next-market-day candidates for approval or decline.
- Options exits may be automatic after position creation.
- Options profit rule: sell when value approaches 2x total purchase cost.
- Options defensive rule: if a profitable option starts dropping back toward entry, sell at +10% above entry.
- Stock trade risk cap: use the lower of 3% of account equity or half of the average absolute daily percentage move over the last 7 trading days.
- Follow current FINRA intraday-margin guidance and broker-provided constraints.
- Include a daily after-action report during the 10 PM decision phase.
- The after-action report should summarize trades made that day, skipped/rejected trades, P/L snapshots, exposure, rationale, and next-day option proposals.

## Change Discipline

Every repository change or addition must update this file's changelog in the same commit.

For each changelog entry, include:

- Date.
- Summary of what changed.
- Why it changed.
- Tests or verification performed.
- Whether any secrets, credentials, account identifiers, local data, or logs were touched.

Do not commit a change if its changelog entry is missing.

## Safety Rules For Agents

- Do not call real order-placement tools unless the user explicitly confirms the exact trade in the current thread.
- Prefer review/simulation tools before any real trading tool.
- Never default an account number from `get_accounts`; use only an account number supplied by the user or clearly implied by the immediate context.
- Do not expose account numbers, tokens, or sensitive account data in commits, public logs, or public repo files.
- Keep the app in `dry-run` unless the user explicitly asks to enable a live mode.
- Run tests before claiming code changes are complete.
- Run a secret-pattern scan before pushing public changes.
- Keep public docs generic; keep user-specific account details in ignored local files.

## Changelog

### 2026-07-04

- Sanitized snapshot negative-test sentinels to avoid account-number-shaped placeholder values in public tests.
- This keeps the repository examples and tests clearly synthetic while still proving raw account fields are rejected.
- Verification: identified the placeholder during pre-push patch review and replaced it with a nonnumeric redaction token.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Completed the Task 4 live Robinhood MCP read-only connectivity probe against the user-selected agentic account.
- The probe verified that authenticated read-only Robinhood MCP calls can be made for the selected account; account-specific results were summarized only in the private thread and are not recorded in repository files.
- Verification: used only read-only MCP calls, including user-requested account discovery and portfolio/positions/orders/P&L reads; did not call review, place, cancel, or watchlist write tools.
- Secrets/account data touched: live account data was accessed read-only during the private thread, but no secrets, credentials, account identifiers, account state, local databases, or logs were committed.

- Added the `snapshot --fixture` CLI command, a subprocess CLI test for sanitized snapshot JSON output, and README usage for the local fixture workflow.
- This exposes the Task 3 read-only snapshot report path without adding live Robinhood MCP calls to the Python package runtime.
- Verification: added the CLI subprocess test first, confirmed targeted CLI tests failed because the `snapshot` command was missing, then confirmed targeted CLI tests passed after adding the command.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Added read-only snapshot assembly in `src/robinhood_trading_bot/snapshot.py`, a sanitized fixture at `tests/fixtures/read_only_snapshot.json`, and a fixture assembly test in `tests/test_snapshot.py`.
- This lets local tests build a dry-run `SnapshotReport` from sanitized fixture data without calling Robinhood MCP or passing raw dictionaries through report collections.
- Verification: added the fixture assembly test first, confirmed targeted snapshot tests failed with missing `robinhood_trading_bot.snapshot`, then confirmed targeted snapshot tests passed after adding the fixture and builder.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Added snapshot report models in `src/robinhood_trading_bot/models.py` and a serialization test in `tests/test_snapshot.py`.
- This creates the sanitized, read-only model layer for portfolio snapshot reporting without storing account numbers.
- Verification: ran targeted snapshot unittest red before implementation, then green after adding the minimal models.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Tightened snapshot serialization so raw dictionaries are rejected instead of copied into public output.
- This prevents future raw Robinhood fields, including account identifiers, from leaking through model serialization.
- Verification: added failing tests for raw position and realized P/L dictionaries, confirmed they failed before the fix, then confirmed targeted snapshot tests passed.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Added `.worktrees/` to `.gitignore` before creating an isolated implementation worktree for subagent-driven development.
- This prevents local feature worktree contents from being accidentally committed into the public repository.
- Verification: checked `git check-ignore` before the change and confirmed `.worktrees/` was not ignored.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Added a read-only Robinhood snapshot implementation plan at `docs/superpowers/plans/2026-07-04-readonly-robinhood-snapshot.md`.
- The plan scopes the next app slice to sanitized, read-only portfolio/positions/order reporting and explicitly excludes real order placement.
- Verification: reviewed the approved design spec, current app scaffold, and available `mcp__robinhood_trading_2` tool surface before writing the plan.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.

- Added this `AGENTS.md` file to capture the project summary, standing user instructions, safety rules, and required changelog discipline.
- Confirmed that the restarted Codex app exposes `mcp__robinhood_trading_2` tools, including read-only account/portfolio tools and real order review/placement tools.
- Local ignored `.env` already points at the Robinhood MCP trading URL and uses `ROBINHOOD_AUTH_PROFILE=robinhood_trading-2`.
- Verification: inspected tool discovery results and confirmed no prior `AGENTS.md` existed.
- Secrets/account data touched: no committed secrets, credentials, account identifiers, local databases, or logs.
