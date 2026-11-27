# Portfolio lane backtest (2026-11-27)

General information from a backtest, not financial advice. Past results don't predict future ones.

Daily adjusted closes from Yahoo Finance, 2021-11 to 2026-11. Settings were chosen on 2021-11 to 2024-11 and scored on 2024-11 to 2026-11. "Diversified core" is VTI 50%, VXUS 20%, BND 20%, GLD 10%. "Tech-12" is an equal-weight basket of 12 large tech stocks.

## Test window, quarterly rebalance

| Portfolio | Return | Max drawdown | Sharpe |
|---|---|---|---|
| Tech-12 only | +117% | −31% | 1.32 |
| 50% diversified core + 50% Tech-12 | +68% | −21% | 1.27 |
| 70% diversified core + 30% Tech-12 | +50% | −18% | 1.20 |
| 80% diversified core + 20% Tech-12 | +41% | −16% | 1.13 |
| Diversified core alone | +24% | −12% | 0.90 |
| S&P 500 (SPY) | +24% | −19% | 0.69 |

The default plan (75% core, 8 picks at 3.125% each) scored +53%, −16% max drawdown and Sharpe 1.23 on `portfolio-backtest`.

## Findings

- The diversified core beat a plain VTI or QQQ core at every split, with similar return and smaller drawdowns.
- Diversification inside the sleeve mattered most. Random one-stock picks had a 10th-percentile return of −28%. Every random 8-stock basket returned at least +51%.
- Quarterly rebalancing matched monthly. Yearly or never had larger drawdowns.
- A 200-day trend filter cut drawdowns by about 5 points but lowered the average test return from +45% to +24%, so the lane doesn't use one.
- 2024–26 was a strong period for large tech, and the stocks were chosen with hindsight. Expect less from a picks sleeve going forward.
