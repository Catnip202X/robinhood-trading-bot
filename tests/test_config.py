import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robinhood_trading_bot.auth import RobinhoodAuthConfig
from robinhood_trading_bot.config import BotConfig


class BotConfigTests(unittest.TestCase):
    def test_bot_config_defaults_to_dry_run_without_secrets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_env_file = Path(temp_dir) / ".env"
            with patch.dict(os.environ, {}, clear=True):
                config = BotConfig.from_env(env_file=missing_env_file)

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

    def test_config_reads_local_env_file_without_requiring_exported_variables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "BOT_MODE=dry-run",
                        "BOT_TECH_WATCHLIST=AAPL,MSFT,NVDA",
                        "ROBINHOOD_MCP_SERVER_URL=https://agent.robinhood.com/mcp/trading",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                config = BotConfig.from_env(env_file=env_file)
                auth = RobinhoodAuthConfig.from_env(env_file=env_file)

        self.assertEqual(config.tech_watchlist, ("AAPL", "MSFT", "NVDA"))
        self.assertTrue(auth.has_mcp_settings)
        self.assertTrue(auth.safe_summary()["mcp_server_configured"])

    def test_exported_environment_overrides_local_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("BOT_MODE=stock-live\n", encoding="utf-8")

            with patch.dict(os.environ, {"BOT_MODE": "dry-run"}, clear=True):
                config = BotConfig.from_env(env_file=env_file)

        self.assertEqual(config.mode, "dry-run")


if __name__ == "__main__":
    unittest.main()
