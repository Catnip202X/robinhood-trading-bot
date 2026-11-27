# Crypto Signal Backtest, 2026-11-27

Data: Coinbase public hourly candles, 2024-11-27 to 2026-11-27 (about 17,500 bars per coin). The model was trained walk-forward on the first year and retrained every 30 days. It was tested out-of-sample on 2025-12-01 to 2026-11-27. Long-only, $100 start, full allocation per trade, 2% stop-loss, 4% take-profit, 5% daily loss stop. An entry needs predicted return > 2 x cost per side and close > SMA200.

"Correlation" is between the predicted and actual next-hour return (0 = no information).

| Coin | Horizon | Correlation | Cost/side | Strategy | Trades | Buy and hold |
|------|---------|-------------|-----------|----------|--------|--------------|
| BTC | 1h | 0.011 | 0% | -16.3% | 846 | -28.7% |
| BTC | 1h | | 0.10% | -2.1% | 6 | -28.8% |
| BTC | 1h | | 0.25% | 0.0% | 0 | -29.0% |
| BTC | 4h | 0.024 | 0% | +3.8% | 642 | -28.7% |
| BTC | 4h | | 0.10% | -6.2% | 19 | -28.8% |
| ETH | 1h | -0.002 | 0% | +9.8% | 798 | -39.1% |
| ETH | 1h | | 0.10% | +8.7% | 30 | -39.2% |
| ETH | 1h | | 0.25% | 0.0% | 0 | -39.4% |
| ETH | 4h | -0.022 | 0.10% | -10.8% | 102 | -39.2% |

## Takeaways

- The model has essentially no predictive power. Correlations are within noise of zero, and negative for ETH.
- Most of the "beat buy and hold" comes from staying in cash during a year when BTC fell 29% and ETH fell 39%, not from good trade picks.
- At realistic Robinhood costs (an unknown spread, likely 0.25% or more per side), the predictions almost never clear the round-trip cost, so the bot rarely trades.
- The one positive cell (ETH 1h at 0.10%) comes from a signal with negative correlation, so it is luck, not edge.

Live execution should stay off until a strategy shows an edge after costs on out-of-sample data.
