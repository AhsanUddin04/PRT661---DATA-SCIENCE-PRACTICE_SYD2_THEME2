# Model card — NSW suburb price outlook (v4.0.0)

**Owner:** PRT661 Sydn2–Theme2 · **Champion:** LightGBM, direct models for h = 1…4 · **Trained through:** 2026-Q2

## Intended use
Indicative, uncertainty-aware outlook of a NSW suburb's median residential sale price for the next 1–4 quarters,
for buyers, investors and policy analysts exploring market trends. Always read with its P10–P90 band and reliability label.

## Out of scope
Valuing an individual property · lending, insurance or other automated decisions about people · investment advice ·
suburbs with fewer than 5 sales in the anchor quarter (not forecast) · states other than NSW.

## Data
NSW Valuer General bulk sales 2013-Q1–2026-Q3 (2,762,903 raw → 2,092,500 cleaned residential sales) and ABS Total
Value of Dwellings (lagged one quarter). See `DATA_SOURCES.md`. Feature store v2: 226,160 suburb-quarters, 24 features.

## Model selection rule (fixed before testing)
Design choices and hyper-parameters chosen on validation window 2022-Q3–2024-Q2 only; champion = best validation RMSE
(LightGBM 14.61 pp). Test window 2024-Q3–2026-Q2 evaluated once, every model re-trained at each origin.

## Performance (test, h = 1, 4,435 liquid suburb-quarters, identical cells for all models)
| Model | RMSE | MAE | R² | Direction % |
|---|---|---|---|---|
| LightGBM | 12.89 | 8.36 | 0.369 | 66.4 |
| Ensemble (LGBM+XGB+RF) | 12.79 | 8.33 | 0.379 | 66.7 |
| A2 Gradient Boosting | 13.20 | 8.54 | 0.339 | 66.6 |
| SARIMA | 15.58 | 9.75 | 0.078 | 63.5 |
| Regional momentum | 16.27 | 9.97 | -0.005 | 56.3 |
| Naive persistence | 27.39 | 17.14 | -1.848 | 37.7 |

Beyond one quarter, suburb-level skill falls to that of the regional-momentum baseline (MAE ≈ 10.0 pp at h = 4).

## Uncertainty
Conformalised quantile regression; empirical P10–P90 coverage 80.4 / 80.5 / 81.4 / 81.3 % (h = 1…4,
target 80%). Production cumulative-change bands: 80.8% overall.

## Segment results (h = 1, all scored suburbs)
| Segment | MAE | Coverage % | Bias (pred − actual) |
|---|---|---|---|
| Greater Sydney | 10.87 | 81.5 | -1.53 |
| Rest of NSW | 10.64 | 79.3 | -1.73 |

Error falls sharply with sales volume; ~70–77% of error in typical suburbs is estimated irreducible sampling noise
(`reports/tables/error_by_liquidity.csv`).

## Caveats
Suburb medians move with the mix of homes sold · no interest-rate or macro drivers · single regime test window ·
postcode-range region proxy · small negative bias in a rising market.
