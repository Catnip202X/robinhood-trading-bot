import json
import os
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def test_module_snapshot_command_prints_sanitized_fixture_json(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "robinhood_trading_bot.cli",
                "snapshot",
                "--fixture",
                "tests/fixtures/read_only_snapshot.json",
            ],
            check=True,
            capture_output=True,
            env=env,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertIn("portfolio", payload)
        self.assertIn("equity_positions", payload)
        self.assertNotIn("account_number", result.stdout)

    def test_module_status_command_prints_safe_json(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        env["BOT_TECH_WATCHLIST"] = "AAPL,NVDA"
        env.pop("ROBINHOOD_ACCOUNT_ID", None)

        result = subprocess.run(
            [sys.executable, "-m", "robinhood_trading_bot.cli", "status"],
            check=True,
            capture_output=True,
            env=env,
            text=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["tech_watchlist"], ["AAPL", "NVDA"])
        self.assertFalse(payload["robinhood"]["account_id_configured"])


if __name__ == "__main__":
    unittest.main()
