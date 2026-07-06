# Local Control Panel, Risk Settings, Auth, and Scheduler Design

## Summary

Add a local desktop control panel for the trading bot. The control panel should let users manually set their own risk policy, check Robinhood MCP authentication readiness, and configure how often the bot checks prices and account status.

The Python trading core remains the source of truth for validation and trading decisions. The GUI is a wrapper that edits local-only settings, starts safe commands, and shows status. Real order placement remains blocked unless the user explicitly confirms the exact trade in the current thread or future app workflow.

## Architecture

Use a thin .NET desktop wrapper around the Python core.

- The .NET GUI reads and writes a local ignored settings file.
- The Python core loads and validates the same settings before using them.
- The GUI never stores Robinhood tokens, account numbers, or session secrets.
- The GUI can run safe local commands such as status, config validation, fixture snapshot, and auth preflight.
- Broker calls remain inside the Robinhood MCP path, not inside the GUI.

The likely first GUI technology is .NET WPF on Windows because this workspace is Windows-first. Avalonia can be considered later if cross-platform desktop support becomes important.

## User Risk Settings

Users should be able to enter their own policy values:

- stock per-trade risk cap percent;
- crypto per-trade risk cap percent;
- optional per-trade max dollar amount;
- optional daily max spend percent;
- dry-run or live preference;
- pause or kill-switch state;
- scheduler intervals for price checks and account-status checks.

The shipped defaults remain conservative. Local overrides stay out of Git.

Python validation must reject malformed or unsafe settings before the bot uses them. The GUI should make invalid settings visible, but the Python core must still enforce validation because agents or scripts might bypass the GUI.

## Robinhood Auth Interaction

The control panel should provide a guided Robinhood MCP preflight instead of collecting credentials.

It should:

- detect whether `.codex/config.toml` includes the Robinhood MCP server URL;
- display the Streamable HTTP URL: `https://agent.robinhood.com/mcp/trading`;
- show the user the login command: `codex mcp login robinhood_trading`;
- run safe read-only status/auth checks when available;
- show states such as `not configured`, `needs login`, `connected`, or `error`;
- surface setup errors without printing tokens, account numbers, or sensitive broker state.

The GUI must not become a credential store.

## Scheduler and Multithreading

Users may choose more frequent or less frequent checks than the original 30-minute cadence. The app should allow intervals from 1 second through 60 minutes, with validation and clear display of the active interval.

Scheduler behavior:

- price-check interval is user configurable;
- account-status interval is user configurable;
- default remains 30 minutes for price checks;
- allowed range is 1 second through 60 minutes;
- background work must not block the GUI;
- each job type must avoid overlap with itself;
- if a check is still running when the next tick arrives, skip the new tick and report the skip;
- failures should be captured as status events, not crash the GUI;
- the pause or kill switch stops new scheduled work.

Implementation should prefer simple background workers or task scheduling over complex concurrency. The first scheduler does not need distributed locking, multiple processes, or cloud orchestration.

## Agent-Safe Operation

People may run this app with an agent. The design must make user-owned policy explicit.

- Agents can read the active risk policy.
- Agents cannot silently invent missing caps.
- If no local user policy exists, the app uses conservative defaults and labels them as defaults.
- Changes to local policy should be explicit writes to the local settings file.
- The public repo contains sample settings only.
- Live trading remains gated separately from config editing.

## Scope

In scope:

- Design for local risk settings.
- Design for a .NET GUI wrapper around the Python core.
- Design for Robinhood MCP auth preflight and setup guidance.
- Design for configurable scheduled checks with non-overlapping background execution.
- Update project instructions and changelog.

Out of scope for the first implementation:

- Real order placement from the GUI.
- Embedded Robinhood credential entry.
- Storing account identifiers.
- Complex multi-machine scheduling.
- Cloud deployment.
- Mobile UI.

## Testing

Implementation should include tests for:

- loading defaults when no local settings file exists;
- validating user-provided risk caps and intervals;
- rejecting intervals below 1 second or above 60 minutes;
- ensuring pause state suppresses scheduled work;
- ensuring a job skip is reported when a previous run is still active;
- ensuring auth preflight output is sanitized.
