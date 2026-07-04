from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RobinhoodAuthConfig:
    """Local-only Robinhood MCP auth hints.

    Real MCP credentials should be managed by the user's MCP client or local
    secret store, not committed to this repository.
    """

    mcp_server_url: str = ""
    account_id: str = ""
    auth_profile: str = "default"

    @classmethod
    def from_env(cls) -> "RobinhoodAuthConfig":
        return cls(
            mcp_server_url=os.getenv("ROBINHOOD_MCP_SERVER_URL", "").strip(),
            account_id=os.getenv("ROBINHOOD_ACCOUNT_ID", "").strip(),
            auth_profile=os.getenv("ROBINHOOD_AUTH_PROFILE", "default").strip() or "default",
        )

    @property
    def has_mcp_settings(self) -> bool:
        return bool(self.mcp_server_url or self.account_id)

    def safe_summary(self) -> dict[str, bool | str]:
        return {
            "mcp_server_configured": bool(self.mcp_server_url),
            "account_id_configured": bool(self.account_id),
            "auth_profile": self.auth_profile,
        }
