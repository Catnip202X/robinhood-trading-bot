# Read-Only Robinhood Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real app slice: a read-only local CLI command that reports Robinhood MCP account connectivity, portfolio summary, equity positions, option positions, and recent order/P&L metadata without placing trades.

**Architecture:** Keep Robinhood access behind a small broker snapshot interface so tests can use fixture data and live runs can be manually populated from MCP results. The CLI remains dry-run by default and never calls real order-placement tools.

**Tech Stack:** Python 3.11+, standard-library `unittest`, local `.env` config, authenticated Robinhood MCP server `robinhood_trading-2`.

---

## File Structure

- Create `src/robinhood_trading_bot/models.py`: dataclasses for sanitized account, portfolio, position, and order/P&L summaries.
- Create `src/robinhood_trading_bot/snapshot.py`: pure functions that assemble and serialize read-only broker snapshots from sanitized dictionaries.
- Modify `src/robinhood_trading_bot/cli.py`: add `snapshot` command that can read a local sanitized JSON fixture for now and print a report.
- Create `tests/test_snapshot.py`: unit tests for snapshot assembly and no-secret serialization.
- Create `tests/fixtures/read_only_snapshot.json`: sanitized sample data with no account number or secret values.
- Modify `README.md`: document the read-only snapshot command.
- Modify `AGENTS.md`: add a changelog entry for this plan and, during execution, every implementation change.

## Task 1: Snapshot Models

**Files:**
- Create: `src/robinhood_trading_bot/models.py`
- Create: `tests/test_snapshot.py`
- Modify: `AGENTS.md`

- [ ] **Step 1: Write the failing model serialization test**

Add to `tests/test_snapshot.py`:

```python
import unittest

from robinhood_trading_bot.models import PortfolioSummary, SnapshotReport


class SnapshotTests(unittest.TestCase):
    def test_snapshot_report_serializes_without_account_number(self):
        report = SnapshotReport(
            mode="dry-run",
            auth_profile="robinhood_trading-2",
            account_label="primary",
            portfolio=PortfolioSummary(total_market_value="1000.00", buying_power="250.00"),
            equity_positions=[],
            option_positions=[],
            recent_orders=[],
            realized_pnl=None,
        )

        payload = report.to_public_dict()

        self.assertEqual(payload["account_label"], "primary")
        self.assertNotIn("account_number", payload)
        self.assertEqual(payload["portfolio"]["buying_power"], "250.00")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the model test and verify red**

Run:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_snapshot -v
```

Expected: failure because `robinhood_trading_bot.models` does not exist.

- [ ] **Step 3: Implement minimal models**

Create `src/robinhood_trading_bot/models.py` with frozen dataclasses and `to_public_dict()` methods. Store only sanitized labels, symbols, quantities, prices, and summary strings. Do not store account numbers.

- [ ] **Step 4: Run the model test and verify green**

Run the same command. Expected: all tests in `tests.test_snapshot` pass.

## Task 2: Snapshot Assembly

**Files:**
- Modify: `src/robinhood_trading_bot/snapshot.py`
- Modify: `tests/test_snapshot.py`
- Create: `tests/fixtures/read_only_snapshot.json`
- Modify: `AGENTS.md`

- [ ] **Step 1: Write failing fixture assembly test**

Add a test that loads `tests/fixtures/read_only_snapshot.json`, calls `build_snapshot_from_fixture()`, and asserts:

- `mode` is `dry-run`.
- `auth_profile` is `robinhood_trading-2`.
- equity positions contain `AAPL`.
- output JSON has no `account_number`.

- [ ] **Step 2: Run snapshot tests and verify red**

Run:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_snapshot -v
```

Expected: failure because `snapshot.py` and the fixture do not exist.

- [ ] **Step 3: Add sanitized fixture**

Create `tests/fixtures/read_only_snapshot.json`:

```json
{
  "mode": "dry-run",
  "auth_profile": "robinhood_trading-2",
  "account_label": "primary",
  "portfolio": {
    "total_market_value": "1000.00",
    "buying_power": "250.00"
  },
  "equity_positions": [
    {
      "symbol": "AAPL",
      "quantity": "2",
      "average_cost": "150.00"
    }
  ],
  "option_positions": [],
  "recent_orders": [],
  "realized_pnl": null
}
```

- [ ] **Step 4: Implement fixture snapshot assembly**

Create `src/robinhood_trading_bot/snapshot.py` with `build_snapshot_from_fixture(path)` that returns a `SnapshotReport`.

- [ ] **Step 5: Run snapshot tests and verify green**

Run the same test command. Expected: `tests.test_snapshot` passes.

## Task 3: CLI Snapshot Command

**Files:**
- Modify: `src/robinhood_trading_bot/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Write failing CLI test**

Add a CLI subprocess test for:

```powershell
python -m robinhood_trading_bot.cli snapshot --fixture tests/fixtures/read_only_snapshot.json
```

Assert that stdout is valid JSON and includes `portfolio`, `equity_positions`, and no `account_number`.

- [ ] **Step 2: Run CLI tests and verify red**

Run:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_cli -v
```

Expected: failure because the `snapshot` command does not exist.

- [ ] **Step 3: Implement CLI command**

Add `snapshot` subcommand with `--fixture` argument. The command prints sanitized JSON. Do not add live Robinhood MCP calls inside the Python CLI yet; MCP calls are available to Codex, not to the local package runtime.

- [ ] **Step 4: Run CLI tests and verify green**

Run the same command. Expected: CLI tests pass.

- [ ] **Step 5: Update README**

Document:

```powershell
$env:PYTHONPATH='src'
python -m robinhood_trading_bot.cli snapshot --fixture tests/fixtures/read_only_snapshot.json
```

State clearly that this is read-only and sanitized.

## Task 4: Live MCP Read-Only Manual Probe

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Ask the user for the brokerage account number**

Do not call account-scoped Robinhood tools without an account number supplied by the user or clearly implied by the immediate context.

- [ ] **Step 2: Call read-only MCP tools only**

After the user supplies the account number, call these tools only:

- `get_portfolio`
- `get_equity_positions`
- `get_option_positions` with `nonzero=true`
- `get_equity_orders` with a narrow recent filter
- `get_option_orders` with a narrow recent filter

Do not call any review, place, cancel, or write tools in this task.

- [ ] **Step 3: Summarize without exposing account number**

Report only sanitized totals, symbols, order states, and positions. Do not include the account number.

## Task 5: Verification And Commit

**Files:**
- Modify: all files from Tasks 1-4

- [ ] **Step 1: Run full tests**

Run:

```powershell
$env:PYTHONPATH='src'; & "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run whitespace and public-secret checks**

Run:

```powershell
git diff --check
rg -n -uu --glob '!.git/**' --glob '!.env' "(gho_[A-Za-z0-9_]+|github_pat_|sk-[A-Za-z0-9]|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH |PRIVATE )?KEY|refresh_token|access_token|client_secret|api[_-]?key\s*=\s*[^\s#]+|password\s*=\s*[^\s#]+)"
```

Expected: `git diff --check` exits 0 and `rg` exits 1 with no matches.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add AGENTS.md README.md docs/superpowers/plans/2026-07-04-readonly-robinhood-snapshot.md src tests
git commit -m "Add read-only Robinhood snapshot CLI"
git push
```

Expected: commit pushed to `main`.

## Self-Review

- Spec coverage: this plan implements the first safe slice of the Broker Adapter, UI/CLI, dry-run safety posture, and after-action/reporting foundation. It intentionally does not implement scheduling, autonomous decisions, option approvals, or real orders yet.
- Completion-marker scan: task steps avoid deferred-work markers and define the behavior they reference.
- Type consistency: `SnapshotReport`, `PortfolioSummary`, and `build_snapshot_from_fixture()` are named consistently across tests and implementation steps.
