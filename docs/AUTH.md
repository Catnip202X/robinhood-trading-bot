# Authentication

This project does not include Robinhood credentials, API tokens, MCP secrets, or account identifiers.

Each user must authenticate their own Robinhood account locally. The intended production integration is Robinhood MCP:

1. Trust this project in Codex so project-scoped `.codex/config.toml` can load.
2. Confirm the `robinhood_trading` MCP server is configured as a Streamable HTTP server with this URL:

   ```text
   https://agent.robinhood.com/mcp/trading
   ```

3. If Robinhood MCP requires OAuth in your Codex surface, run:

   ```powershell
   codex mcp login robinhood_trading
   ```

4. Keep tokens, refresh credentials, account IDs, and private configuration outside Git.
5. Store local-only settings in `.env`, your OS credential store, or your MCP client configuration.
6. Run the bot in `dry-run` mode first and verify account detection before enabling any live mode.

Codex MCP reference: https://developers.openai.com/codex/mcp

The app scaffold reads optional local settings:

- `ROBINHOOD_MCP_SERVER_URL`
- `ROBINHOOD_ACCOUNT_ID`
- `ROBINHOOD_AUTH_PROFILE`

Depending on the MCP setup, some or all of these may be unnecessary because authentication may be handled by the MCP client itself.

Never commit:

- `.env`
- access tokens
- refresh tokens
- session cookies
- account numbers
- private keys
- downloaded broker statements
- local SQLite databases
- trading logs containing account identifiers

If a secret is accidentally committed, rotate it immediately and rewrite repository history before pushing publicly.
