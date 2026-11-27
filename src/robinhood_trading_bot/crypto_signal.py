"""Hourly crypto (BTC-USD, ETH-USD, ...) signal model, adapted from AI_TradeMate_For_BTCUSDT.

Changes from the original:
- Only scale-free features (returns, ratios, oscillators). The original fed raw
  price levels (MA5, MA20, ATR, ...) to the trees, which stop generalising once
  BTC leaves the training price range.
- No fake ``ai_sentiment`` column (it was derived from RSI) and no perpetual
  funding rate, since Robinhood crypto is spot only.
- Long-only: the model's output only opens or closes a spot position.

Requires the optional ``signals`` dependencies: pandas, numpy, lightgbm.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FEATURES = [
    "ret_1h",
    "ret_3h",
    "ret_6h",
    "ret_24h",
    "close_ma20",
    "close_ma50",
    "close_sma200",
    "rsi_14",
    "rsi_24",
    "macd_hist_pct",
    "atr_pct",
    "bb_width",
    "vol_ratio_24",
    "body_ratio",
    "upper_shadow",
    "lower_shadow",
    "hour_sin",
    "hour_cos",
]

WARMUP_BARS = 200


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0)


def build_features(candles: pd.DataFrame, horizon_hours: int = 1) -> pd.DataFrame:
    """Return a frame with FEATURES, ``sma200`` and ``target`` columns.

    ``candles`` must have a UTC DatetimeIndex and open/high/low/close/volume.
    ``target`` is the forward close-to-close return over ``horizon_hours`` and
    is NaN for the most recent bars.
    """

    df = candles.copy()
    close = df["close"]
    df["ret_1h"] = close.pct_change(1)
    df["ret_3h"] = close.pct_change(3)
    df["ret_6h"] = close.pct_change(6)
    df["ret_24h"] = close.pct_change(24)
    df["sma200"] = close.rolling(200).mean()
    df["close_ma20"] = close / close.rolling(20).mean() - 1
    df["close_ma50"] = close / close.rolling(50).mean() - 1
    df["close_sma200"] = close / df["sma200"] - 1
    df["rsi_14"] = _rsi(close, 14)
    df["rsi_24"] = _rsi(close, 24)
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    df["macd_hist_pct"] = (macd - macd.ewm(span=9, adjust=False).mean()) / close
    true_range = pd.concat(
        [df["high"] - df["low"], (df["high"] - close.shift()).abs(), (df["low"] - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    df["atr_pct"] = true_range.rolling(14).mean() / close
    df["bb_width"] = 4 * close.rolling(20).std() / close.rolling(20).mean()
    df["vol_ratio_24"] = df["volume"] / (df["volume"].rolling(24).mean() + 1e-9)
    span = (df["high"] - df["low"]).replace(0, np.nan)
    df["body_ratio"] = ((close - df["open"]).abs() / span).fillna(0)
    df["upper_shadow"] = ((df["high"] - df[["open", "close"]].max(axis=1)) / span).fillna(0)
    df["lower_shadow"] = ((df[["open", "close"]].min(axis=1) - df["low"]) / span).fillna(0)
    hours = df.index.hour
    df["hour_sin"] = np.sin(2 * np.pi * hours / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hours / 24)
    df["target"] = close.shift(-horizon_hours) / close - 1
    return df.iloc[WARMUP_BARS:]


LGB_PARAMS = {
    "objective": "regression",
    "learning_rate": 0.03,
    "num_leaves": 15,
    "max_depth": 4,
    "min_data_in_leaf": 100,
    "lambda_l2": 1.0,
    "feature_fraction": 0.8,
    "verbose": -1,
    "seed": 7,
}


def train_model(features: pd.DataFrame, num_boost_round: int = 300):
    import lightgbm as lgb

    rows = features.dropna(subset=FEATURES + ["target"])
    dataset = lgb.Dataset(rows[FEATURES], label=rows["target"])
    return lgb.train(LGB_PARAMS, dataset, num_boost_round=num_boost_round)


def predict(model, features: pd.DataFrame) -> pd.Series:
    return pd.Series(model.predict(features[FEATURES]), index=features.index)


def walk_forward_predictions(
    features: pd.DataFrame,
    train_bars: int,
    retrain_every: int = 24 * 30,
    num_boost_round: int = 300,
) -> pd.Series:
    """Out-of-sample predictions for every bar after ``train_bars``.

    The model is retrained every ``retrain_every`` bars on all data up to that
    point. A 1-bar gap is left before each test block so a training target never
    overlaps a test bar.
    """

    predictions = []
    for start in range(train_bars, len(features), retrain_every):
        train = features.iloc[: start - 1]
        test = features.iloc[start : start + retrain_every]
        model = train_model(train, num_boost_round=num_boost_round)
        predictions.append(predict(model, test))
    return pd.concat(predictions) if predictions else pd.Series(dtype=float)


@dataclass(frozen=True)
class SignalDecision:
    action: str  # "buy", "sell" or "hold"
    predicted_return: float
    above_sma200: bool
    reason: str


def decide(predicted_return: float, close: float, sma200: float, holding: bool, entry_threshold: float, exit_threshold: float) -> SignalDecision:
    above = bool(close > sma200)
    if not holding:
        if predicted_return > entry_threshold and above:
            return SignalDecision("buy", predicted_return, above, "prediction above entry threshold in uptrend")
        reason = "below SMA200" if not above else "prediction below entry threshold"
        return SignalDecision("hold", predicted_return, above, reason)
    if predicted_return < exit_threshold:
        return SignalDecision("sell", predicted_return, above, "prediction below exit threshold")
    return SignalDecision("hold", predicted_return, above, "keep position")
