"""Hourly candles for the crypto lane.

Robinhood's Crypto Trading API only serves quotes, not candle history, so
candles come from Coinbase's free public market-data endpoint.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COINBASE_CANDLES = "https://api.exchange.coinbase.com/products/{product}/candles"


def load_csv(path: str | Path):
    """Load ``timestamp,open,high,low,close,volume`` (unix seconds, UTC)."""

    import pandas as pd

    df = pd.read_csv(path)
    df.index = pd.to_datetime(df.pop("timestamp"), unit="s", utc=True)
    return df.astype(float).sort_index()


def fetch_coinbase_hourly(product: str, hours: int = 400, sleep_seconds: float = 0.2):
    """Fetch the last ``hours`` closed hourly candles for e.g. ``BTC-USD``."""

    import pandas as pd

    end = int(time.time()) // 3600 * 3600
    rows: dict[int, list[float]] = {}
    start = end - hours * 3600
    while start < end:
        stop = min(start + 299 * 3600, end - 3600)
        query = urllib.parse.urlencode({
            "granularity": 3600,
            "start": datetime.fromtimestamp(start, timezone.utc).isoformat(),
            "end": datetime.fromtimestamp(stop, timezone.utc).isoformat(),
        })
        request = urllib.request.Request(
            COINBASE_CANDLES.format(product=product) + "?" + query,
            headers={"User-Agent": "robinhood-trading-bot"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            for ts, low, high, open_, close, volume in json.load(response):
                rows[int(ts)] = [open_, high, low, close, volume]
        start += 300 * 3600
        time.sleep(sleep_seconds)
    frame = pd.DataFrame.from_dict(rows, orient="index", columns=["open", "high", "low", "close", "volume"])
    frame.index = pd.to_datetime(frame.index, unit="s", utc=True)
    return frame.sort_index().astype(float)
