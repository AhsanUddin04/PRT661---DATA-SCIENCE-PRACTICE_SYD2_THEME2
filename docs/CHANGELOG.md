# CHANGELOG

All material changes to data rules, schema, features or models, newest first.
Format: what changed · why · effect on reported numbers.

## v4.0.0 — Assessment 4 (Sprints 9–10)

### Pipeline / reproducibility
- **Added `src/prt661/` package** (parsing, cleaning, features, models, backtest, forecast, db, pipeline CLI).
  A2 shipped notebooks and outputs but not the code that produced `cleaned_sales`; the repository
  could not regenerate its own data. The full raw→forecast run is now one command (`make all`).
- **Raw parser reproduces A2 exactly:** 2,762,903 B-records from the 13 annual archives.
- **Cleaning module fixed** — the A2 repo version (a) omitted the residential-only filter and the
  analysis-window rule that the A2 report described, and (b) de-duplicated keeping the *earliest*
  download rather than the most recent. Fixed; counts now reproduce A2 Table 3.1 (duplicates 237,770;
  non-residential 429,788; out-of-window 995; price floor 1,850 vs 1,851 reported — one record).
- **Outlier flag standardised** to Tukey 1.5×IQR of $/m² within (suburb, settlement quarter),
  m²-measured lots only, n ≥ 4: 85,800 flagged (A2 reported 84,589; the A2 grouping key was not
  recorded). Vectorised: 179 s → 5 s.
- `requirements.txt` contained unresolved Git merge-conflict markers; replaced with pinned
  `requirements.txt` (pipeline) and `requirements-app.txt` (deployment).

### Feature store v2
- **Complete suburb × quarter grid.** Audit found 7,185 of 75,795 A2 "QoQ" targets (9.5%) spanned a
  missing quarter. QoQ is now only defined between adjacent quarters that both have ≥5 sales.
- **Forecast-origin framing** with direct targets for h = 1..4 (QoQ and cumulative).
- **ABS regressor lagged one quarter** to respect its publication delay (A2 used the same-quarter value).
- New features: YoY change, deviation from 4-quarter trend, strata (unit) share and its change,
  $/m², sales-volume change, regional and state median momentum from our own data, data-coverage count.

### Models
- Hyper-parameters selected on a validation window (2022-Q3..2024-Q2) that ends before the test window.
- Added Ridge, Huber, Random Forest, LightGBM, XGBoost, and an ensemble; Huber loss and √n sample weights.
- SARIMA and Prophet re-run on the **same** suburb-quarters as the ML models (A2 compared different samples).
- Calibrated 10th–90th percentile bands via conformalised quantile regression (CQR).
- Production forecasts use direct cumulative models per horizon — no compounding of one-step forecasts.

### Database
- `schema_v2.sql`: `feature_store_v2`, `model_registry`, `forecasts`, `backtest_predictions`,
  `pipeline_runs`, privacy view `v_public_suburb_quarter`; indexes promised in A2 added.
- A2 dump restored with `raw_sales` and `suburb_dim` **empty** (0 rows); both repopulated
  (2,762,903 and 4,111 rows) via COPY.
- Shared `prt661_team` login replaced with group roles (`prt661_etl`, `prt661_analyst`,
  `prt661_app_ro`) and one personal login per member.

### Deployment
- Streamlit app v4 reads only published, privacy-filtered artefacts in `app/data/`.
- Dockerfile (non-root), GitHub Actions CI (tests + schema), weekly scheduled refresh workflow.

## v2.x — Assessment 2
See A2 report §3.10.4 (runaway-forecast fix, duplicate suburb-quarter rows, data-quality table).
