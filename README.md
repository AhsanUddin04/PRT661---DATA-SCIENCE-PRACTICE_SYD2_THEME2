# NSW Suburb House-Price Forecasting — PRT661 Sydn2 · Theme 2

Forecasts the quarter-on-quarter change in each NSW suburb's median residential sale price 1–4 quarters ahead,
with calibrated 10th–90th percentile bands, from NSW Valuer General bulk sales data and ABS benchmarks.

**Status:** Assessment 4 — final release v4.0.0 (reproducible pipeline, tested, deployable app).

## Quick start
```bash
pip install -r requirements.txt
streamlit run app/app.py                       # the web app (uses only app/data/)
pytest -q                                      # 13 tests incl. look-ahead and reproduction tests
python -m prt661.pipeline --stages parse clean features     # rebuild data from data/raw/nsw/*.zip
make all                                       # everything, incl. back-tests and report figures
```

## Headline results (walk-forward test 2024-Q3–2026-Q2, h = 1, liquid suburbs, identical cells)
| Model | RMSE (pp) | MAE (pp) | R² |
|---|---|---|---|
| **LightGBM (champion)** | 12.89 | 8.36 | 0.369 |
| A2 Gradient Boosting (re-run fairly) | 13.20 | 8.54 | 0.339 |
| SARIMA | 15.58 | 9.75 | 0.078 |
| Naive persistence | 27.39 | 17.14 | -1.848 |

P10–P90 band coverage: 80–81% (target 80%).

## Repository layout
| Path | Contents |
|---|---|
| `src/prt661/` | Package: parsing, cleaning, features, models, backtest, statistical, evaluation, forecast, db, pipeline CLI |
| `scripts/` | Run scripts for each stage, report assets, app-data publishing |
| `tests/` | pytest suite (parsing, cleaning reconciliation, gap & look-ahead tests, metrics, published-forecast checks) |
| `app/` | Streamlit app v4 + its published data (`app/data/`) |
| `database/` | `schema_a2.sql`, `schema_v2.sql` (new tables, privacy view, roles), `create_member_logins.sql` |
| `models/` | Production models (`lgbm_cumulative_h*.joblib`), `best_params.json`, `model_registry.json` |
| `reports/` | Figures, tables (every number in the report), report build scripts, final PDF |
| `docs/` | CHANGELOG, MODEL_CARD, DATA_SOURCES, SECURITY_AND_PRIVACY, DEPLOYMENT |
| `notebooks/a2_legacy/` | Assessment 2 notebooks kept for the record |
| `.github/workflows/` | CI (tests + schema) and weekly scheduled refresh |

Raw archives (`data/raw/`) and intermediate parquet files (`data/processed/`) are git-ignored; see `docs/DATA_SOURCES.md`.

## Team
Ahsan Uddin (lead, acquisition & automation) · Ferdous Anwar Anik (data engineering & database) ·
Mohd Yah Ya Raiyan (modelling & evaluation) · Abrar Bin Khaiyum (app, deployment & documentation)
