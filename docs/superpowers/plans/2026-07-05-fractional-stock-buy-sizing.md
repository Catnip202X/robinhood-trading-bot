# Fractional Stock Buy Sizing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add test-covered dollar sizing for fractional Robinhood stock buy candidates.

**Architecture:** Keep sizing as pure Python logic in the existing risk module so it can be tested without Robinhood MCP calls. The function receives buying power, account equity, and the active risk cap percentage, then returns a cents-rounded dollar amount or `None` when no safe candidate can be sized.

**Tech Stack:** Python 3.11+, standard-library `decimal`, `unittest`.

---

### Task 1: Dollar Sizing Tests

**Files:**
- Modify: `tests/test_risk.py`

- [ ] **Step 1: Write failing tests**

Add tests importing `stock_buy_dollar_amount` and asserting:

```python
self.assertEqual(stock_buy_dollar_amount("25.00", "1000.00", 3.0), "25.00")
self.assertEqual(stock_buy_dollar_amount("500.00", "1000.00", 2.5), "25.00")
self.assertEqual(stock_buy_dollar_amount("500.00", "333.33", 3.0), "9.99")
self.assertIsNone(stock_buy_dollar_amount("0", "1000.00", 3.0))
self.assertIsNone(stock_buy_dollar_amount("500.00", "0", 3.0))
self.assertIsNone(stock_buy_dollar_amount("500.00", "1000.00", 0))
self.assertIsNone(stock_buy_dollar_amount("0.99", "1000.00", 3.0))
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.test_risk -v
```

Expected: import failure for `stock_buy_dollar_amount`.

### Task 2: Dollar Sizing Implementation

**Files:**
- Modify: `src/robinhood_trading_bot/risk.py`

- [ ] **Step 1: Add minimal implementation**

Implement `stock_buy_dollar_amount(buying_power, account_equity, risk_cap_percent, minimum_order_amount="1.00") -> str | None`.

The function must:

- parse inputs with `Decimal(str(value))`,
- reject missing, invalid, zero, or negative inputs,
- compute `account_equity * risk_cap_percent / 100`,
- choose the lower of that budget and buying power,
- round down to cents using `ROUND_DOWN`,
- return `None` when below `minimum_order_amount`,
- return a two-decimal string otherwise.

- [ ] **Step 2: Run targeted tests**

Run:

```powershell
$env:PYTHONPATH='src'
python -m unittest tests.test_risk -v
```

Expected: all risk tests pass.

### Task 3: Repository Documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Document fractional buy sizing**

Add README documentation explaining that stock entries use dollar-based fractional market buy reviews, capped by buying power and the existing stock risk rule.

- [ ] **Step 2: Update changelog**

Add a `2026-07-05` `AGENTS.md` changelog entry for implementation, docs, tests, and secrets/account-data status.

### Task 4: Final Verification

**Files:**
- No source edits expected.

- [ ] **Step 1: Run the full test suite**

Run:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run public secret scan**

Run a repository scan excluding `.git`, `.env`, caches, and bytecode for common secret/account-number patterns. Expected findings are only policy/documentation mentions, not actual secret values or account numbers.

- [ ] **Step 3: Commit and push**

Stage the source, tests, docs, plan, and changelog. Commit with message `Add fractional stock buy sizing`, then push `main`.
