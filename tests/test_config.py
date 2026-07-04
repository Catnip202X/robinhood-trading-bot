import os
import unittest
from unittest.mock import patch

from robinhood_trading_bot.auth import RobinhoodAuthConfig
from robinhood_trading_bot.config import BotConfig


class BotConfigTests(unittest.TestCase):
    def test_bot_config_defaults_to_dry_run_without_secrets(self):
        with patch.dict(os.environ, {}, clear=True):
            config = BotConfig.from_env()

        self.assertEqual(config.mode, "dry-run")
        self.assertEqual(config.timezone, "America/New_York")
        self.assertEqual(config.tech_watchlist, ())
        self.assertEqual(config.database_path, "data/trading-bot.sqlite3")

    def test_bot_config_parses_watchlist_from_env(self):
        with patch.dict(os.environ, {"BOT_TECH_WATCHLIST": " AAPL,MSFT, nvda ,, "}, clear=True):
            config = BotConfig.from_env()

        self.assertEqual(config.tech_watchlist, ("AAPL", "MSFT", "NVDA"))

    def test_robinhood_auth_reports_presence_without_exposing_values(self):
        env = {
            "ROBINHOOD_MCP_SERVER_URL": "https://mcp.example.local",
            "ROBINHOOD_ACCOUNT_ID": "account-123",
            "ROBINHOOD_AUTH_PROFILE": "personal",
        }

        with patch.dict(os.environ, env, clear=True):
            auth = RobinhoodAuthConfig.from_env()

        self.assertTrue(auth.has_mcp_settings)
        self.assertEqual(
            auth.safe_summary(),
            {
                "mcp_server_configured": True,
                "account_id_configured": True,
                "auth_profile": "personal",
            },
        )


if __name__ == "__main__":
    unittest.main()
