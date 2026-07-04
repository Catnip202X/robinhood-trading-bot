# Public Standalone Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the Robinhood trading bot repository for safe public GitHub publication as a standalone Python app scaffold with user-provided Robinhood/MCP authentication.

**Architecture:** Add a small Python package with runtime configuration, auth-mode detection, and stock risk cap logic. Keep real credentials outside Git through `.gitignore`, `.env.example`, and docs that explain local auth without committing secrets.

**Tech Stack:** Python 3.11+, standard-library unittest, GitHub CLI for repository creation and push.

---

### Task 1: Public Repo Hygiene

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `docs/AUTH.md`
- Create: `LICENSE`

- [ ] **Step 1: Add secret-safe ignore rules**

Create `.gitignore` with:

```gitignore
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
secrets/
credentials/
tokens/
.pytest_cache/
__pycache__/
*.py[cod]
.venv/
venv/
dist/
build/
*.egg-info/
data/
logs/
.superpowers/
```

- [ ] **Step 2: Add example environment file**

Create `.env.example` with non-secret placeholders for local-only configuration.

- [ ] **Step 3: Add public README**

Create `README.md` explaining the app, risk warnings, setup, dry-run defaults, and that users must authenticate their own Robinhood/MCP account locally.

- [ ] **Step 4: Add auth documentation**

Create `docs/AUTH.md` explaining that real tokens, account identifiers, and MCP credentials stay outside Git.

- [ ] **Step 5: Add MIT license**

Create `LICENSE` with the MIT license text.

### Task 2: Config And Auth Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/robinhood_trading_bot/__init__.py`
- Create: `src/robinhood_trading_bot/config.py`
- Create: `src/robinhood_trading_bot/auth.py`
- Create: `src/robinhood_trading_bot/cli.py`
- Create: `tests/test_config.py`
- Create: `tests/test_risk.py`

- [ ] **Step 1: Write failing config tests**

Create tests proving defaults are dry-run and no secret values are required.

- [ ] **Step 2: Run config tests and verify they fail**

Run: `$env:PYTHONPATH='src'; python -m unittest tests.test_config -v`

Expected: FAIL because the package does not exist yet.

- [ ] **Step 3: Implement minimal config and auth detection**

Create the package with `BotConfig.from_env()` and `RobinhoodAuthConfig.from_env()`.

- [ ] **Step 4: Run config tests and verify they pass**

Run: `$env:PYTHONPATH='src'; python -m unittest tests.test_config -v`

Expected: PASS.

- [ ] **Step 5: Write failing stock risk tests**

Create tests for `min(3% equity, 0.5 * average absolute daily percentage move over 7 trading days)`.

- [ ] **Step 6: Run risk tests and verify they fail**

Run: `$env:PYTHONPATH='src'; python -m unittest tests.test_risk -v`

Expected: FAIL because risk calculation is not implemented yet.

- [ ] **Step 7: Implement stock risk calculation**

Add `src/robinhood_trading_bot/risk.py` with `stock_trade_risk_cap_percent()`.

- [ ] **Step 8: Run all tests**

Run: `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`

Expected: PASS.

### Task 3: Secret Scan, Commit, Public Repo, Push

**Files:**
- Modify only files created in Tasks 1 and 2.

- [ ] **Step 1: Inspect Git status and diff**

Run: `git status -sb` and `git diff --check`.

- [ ] **Step 2: Run a local secret pattern scan**

Run repository text searches for common committed secret patterns and ensure only placeholders exist.

- [ ] **Step 3: Commit public app scaffold**

Run:

```bash
git add .gitignore .env.example README.md LICENSE docs/AUTH.md docs/superpowers/plans/2026-07-04-public-standalone-repo.md pyproject.toml src tests
git commit -m "Add public standalone app scaffold"
```

- [ ] **Step 4: Create public GitHub repository**

Run:

```bash
gh repo create robinhood-trading-bot --public --source . --remote origin --push
```

- [ ] **Step 5: Verify remote and pushed branch**

Run:

```bash
git remote -v
git status -sb
```

Expected: `origin` exists, the current branch tracks GitHub, and the worktree is clean.
