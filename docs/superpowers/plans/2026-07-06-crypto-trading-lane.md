# Crypto Trading Lane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add test-covered crypto USD sizing and sanitized dry-run crypto order intents.

**Architecture:** Keep crypto sizing pure and broker-independent in `risk.py`, using the same decimal money handling as stock dollar sizing. Add a focused `crypto.py` module for sanitized crypto order intents that can be mapped to future Robinhood MCP crypto review/place tools once they exist.

**Tech Stack:** Python 3.11+, standard-library `dataclasses`, `decimal`, and `unittest`.

---

### Task 1: Crypto Sizing Tests

**Files:**
- Modify: `tests/test_risk.py`

- [ ] **Step 1: Write failing tests**

Add tests that import `crypto_buy_dollar_amount` and assert:

```python
self.assertEqual(crypto_buy_dollar_amount("25.00", "1000.00"), "25.00")
self.assertEqual(crypto_buy_dollar_amount("500.00", "1000.00"), "30.00")
self.assertEqual(crypto_buy_dollar_amount("500.00", "333.33"), "9.99")
self.assertIsNone(crypto_buy_dollar_amount("0", "1000.00"))
self.assertIsNone(crypto_buy_dollar_amount("500.00", "0"))
self.assertIsNone(crypto_buy_dollar_amount("500.00", "1000.00", risk_cap_percent=0))
self.assertIsNone(crypto_buy_dollar_amount("0.99", "1000.00"))
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'
& "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_risk -v
```

Expected: import failure for `crypto_buy_dollar_amount`.

### Task 2: Crypto Sizing Implementation

**Files:**
- Modify: `src/robinhood_trading_bot/risk.py`

- [ ] **Step 1: Implement crypto sizing**

Add:

```python
DEFAULT_CRYPTO_RISK_CAP_PERCENT = Decimal("3.0")

def crypto_buy_dollar_amount(
    buying_power: object,
    account_equity: object,
    risk_cap_percent: object = DEFAULT_CRYPTO_RISK_CAP_PERCENT,
    minimum_order_amount: object = "1.00",
) -> str | None:
    return _buy_dollar_amount(
        buying_power=buying_power,
        account_equity=account_equity,
        risk_cap_percent=risk_cap_percent,
        minimum_order_amount=minimum_order_amount,
    )
```

Refactor the existing stock helper through a private `_buy_dollar_amount` so stock behavior stays unchanged and crypto gets the same cents-rounded notional behavior.

- [ ] **Step 2: Run targeted tests**

Run the targeted risk tests again. Expected: all risk tests pass.

### Task 3: Crypto Order Intent Tests

**Files:**
- Create: `tests/test_crypto.py`

- [ ] **Step 1: Write failing tests**

Add tests for:

```python
intent = crypto_market_buy_intent("btc-usd", "25.00")
self.assertEqual(intent.to_public_dict()["symbol"], "BTC-USD")
self.assertEqual(intent.to_public_dict()["side"], "buy")
self.assertEqual(intent.to_public_dict()["dollar_amount"], "25.00")
self.assertTrue(intent.to_public_dict()["dry_run_only"])
self.assertIn("crypto review/place tools", intent.to_public_dict()["execution_blocked_reason"])
```

Also assert sell intents can carry `quantity` and raw dictionaries are not accepted where a `CryptoOrderIntent` is expected.

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'
& "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest tests.test_crypto -v
```

Expected: import failure for `robinhood_trading_bot.crypto`.

### Task 4: Crypto Order Intent Implementation

**Files:**
- Create: `src/robinhood_trading_bot/crypto.py`

- [ ] **Step 1: Implement sanitized intent model**

Create a frozen `CryptoOrderIntent` dataclass with fields:

```python
symbol: str
side: str
dollar_amount: str | None = None
quantity: str | None = None
order_type: str = "market"
dry_run_only: bool = True
execution_blocked_reason: str = CRYPTO_ORDER_TOOLS_UNAVAILABLE_REASON
```

Normalize symbols to uppercase and sides to lowercase. Allow only `buy` and `sell`. `to_public_dict` must return only the sanitized intent fields.

Add `crypto_market_buy_intent(symbol, dollar_amount)` and `crypto_market_sell_intent(symbol, quantity)` helpers.

- [ ] **Step 2: Run targeted crypto tests**

Run the targeted crypto tests. Expected: all crypto tests pass.

### Task 5: Repository Documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add README crypto section**

Document that crypto uses pair symbols such as `BTC-USD`, supports fractional USD notional buy intents, remains dry-run only until official Robinhood MCP crypto order review/place tools are exposed, and can use MCP pair discovery through `search(asset_type="currency_pair")`.

- [ ] **Step 2: Update `AGENTS.md` changelog**

Add a 2026-07-06 changelog entry summarizing the implementation, tests, docs, and secrets/account-data status.

### Task 6: Final Verification

**Files:**
- No source edits expected.

- [ ] **Step 1: Run full unit tests**

Run:

```powershell
$env:PYTHONPATH='src'
& "C:\Users\Catnip\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run whitespace and public secret checks**

Run `git diff --check` and the repo's public secret/account pattern scan excluding `.git`, `.env`, caches, and bytecode. Expected: no whitespace errors and only documentation/policy mentions of secret-related words.

- [ ] **Step 3: Commit and push**

Stage source, tests, docs, plan, and changelog. Commit with message `Add crypto dry-run trade intents`, then push `main`.
