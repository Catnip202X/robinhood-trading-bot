# Authentication

This project does not include Robinhood credentials, API tokens, MCP secrets, or account identifiers.

Each user must authenticate their own Robinhood account locally. The intended production integration is Robinhood MCP:

1. Configure Robinhood MCP using the client or server instructions available to your account.
2. Keep tokens, refresh credentials, account IDs, and private configuration outside Git.
3. Store local-only settings in `.env`, your OS credential store, or your MCP client configuration.
4. Run the bot in `dry-run` mode first and verify account detection before enabling any live mode.

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
