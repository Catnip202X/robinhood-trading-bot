"""Client for Robinhood's official Crypto Trading API.

Docs: https://docs.robinhood.com/crypto/trading/

Requests are signed with an Ed25519 private key. The signed message is
``f"{api_key}{timestamp}{path}{method}{body}"``, and timestamps expire after
30 seconds. This client signs the exact JSON bytes it sends.

Safety: this client refuses to place or cancel orders unless it was
constructed with ``allow_live_orders=True``. Nothing in this repository sets
that flag yet. The crypto lane produces dry-run order intents only.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

BASE_URL = "https://trading.robinhood.com"


class LiveOrdersBlocked(RuntimeError):
    """Raised when an order call is made on a client without live orders enabled."""


class RobinhoodApiError(RuntimeError):
    def __init__(self, status: int, payload: Any):
        super().__init__(f"Robinhood Crypto API error {status}: {payload}")
        self.status = status
        self.payload = payload


def sign_message(private_key_base64: str, message: str) -> str:
    """Return the base64 Ed25519 signature of ``message``.

    Requires the optional ``pynacl`` dependency (``pip install -e .[api]``).
    """

    from nacl.signing import SigningKey  # optional dependency

    signing_key = SigningKey(base64.b64decode(private_key_base64))
    return base64.b64encode(signing_key.sign(message.encode("utf-8")).signature).decode("utf-8")


def auth_headers(api_key: str, private_key_base64: str, method: str, path: str, body: str, timestamp: int) -> dict[str, str]:
    message = f"{api_key}{timestamp}{path}{method.upper()}{body}"
    return {
        "x-api-key": api_key,
        "x-signature": sign_message(private_key_base64, message),
        "x-timestamp": str(timestamp),
        "Content-Type": "application/json; charset=utf-8",
    }


Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, Any]]


def _urllib_transport(method: str, url: str, headers: dict[str, str], data: bytes | None) -> tuple[int, Any]:
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read()
        status = error.code
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = raw.decode("utf-8", errors="replace")
    return status, payload


@dataclass
class RobinhoodCryptoClient:
    api_key: str
    private_key_base64: str
    allow_live_orders: bool = False
    base_url: str = BASE_URL
    transport: Transport = field(default=_urllib_transport, repr=False)
    clock: Callable[[], float] = field(default=time.time, repr=False)

    def __repr__(self) -> str:  # never print keys
        return f"RobinhoodCryptoClient(allow_live_orders={self.allow_live_orders})"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        body_text = json.dumps(body) if body is not None else ""
        headers = auth_headers(self.api_key, self.private_key_base64, method, path, body_text, int(self.clock()))
        status, payload = self.transport(method, self.base_url + path, headers, body_text.encode("utf-8") if body_text else None)
        if status >= 400:
            raise RobinhoodApiError(status, payload)
        return payload

    # ---- read-only ----
    def get_account(self) -> Any:
        return self._request("GET", "/api/v1/crypto/trading/accounts/")

    def get_trading_pair(self, symbol: str) -> Any:
        return self._request("GET", "/api/v1/crypto/trading/trading_pairs/?" + urllib.parse.urlencode({"symbol": symbol}))

    def get_holdings(self, asset_code: str) -> Any:
        return self._request("GET", "/api/v1/crypto/trading/holdings/?" + urllib.parse.urlencode({"asset_code": asset_code}))

    def get_best_bid_ask(self, symbol: str) -> Any:
        return self._request("GET", "/api/v1/crypto/marketdata/best_bid_ask/?" + urllib.parse.urlencode({"symbol": symbol}))

    def get_estimated_price(self, symbol: str, side: str, quantity: str) -> Any:
        query = urllib.parse.urlencode({"symbol": symbol, "side": side, "quantity": quantity})
        return self._request("GET", "/api/v1/crypto/marketdata/estimated_price/?" + query)

    def get_open_orders(self, symbol: str) -> Any:
        query = urllib.parse.urlencode({"symbol": symbol, "state": "open"})
        return self._request("GET", "/api/v1/crypto/trading/orders/?" + query)

    # ---- order placement (blocked unless explicitly enabled) ----
    def place_order(self, side: str, order_type: str, symbol: str, order_config: dict[str, str]) -> Any:
        if not self.allow_live_orders:
            raise LiveOrdersBlocked("live crypto orders are disabled for this client")
        body = {
            "client_order_id": str(uuid.uuid4()),
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": order_config,
        }
        return self._request("POST", "/api/v1/crypto/trading/orders/", body)

    def cancel_order(self, order_id: str) -> Any:
        if not self.allow_live_orders:
            raise LiveOrdersBlocked("live crypto orders are disabled for this client")
        return self._request("POST", f"/api/v1/crypto/trading/orders/{urllib.parse.quote(order_id)}/cancel/")
