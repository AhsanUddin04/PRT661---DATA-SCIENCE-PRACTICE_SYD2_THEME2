# models/

## gradient_boosting_pooled.pkl

A real, trained `scikit-learn` `GradientBoostingRegressor`, trained pooled
across 575+ liquid NSW suburbs on lag/rolling/seasonal features (see
`notebooks/forecasting.ipynb`). This is the model that produced the
walk-forward backtest results in `notebooks/model_evaluation.ipynb`.

Load it with:
```python
import joblib
model = joblib.load("models/gradient_boosting_pooled.pkl")

feature_cols = ["lag_1_qoq_pct","lag_2_qoq_pct","lag_3_qoq_pct","lag_4_qoq_pct",
                "rolling_mean_4q","rolling_std_4q","state_benchmark_growth",
                "n_sales","flag_covid_period","flag_rate_hike_period",
                "is_q1","is_q2","is_q3","is_q4"]
prediction = model.predict(X[feature_cols])  # X: a dataframe with these columns
```

## Real backtest results for this model (walk-forward, 8 rolling quarters, N=4,629)

| Metric | Value |
|---|---|
| RMSE | 14.22pp |
| MAE | 9.02pp |
| MAPE | 171.0% (de-emphasised — target crosses zero) |
| R² | 0.342 |
| Directional accuracy | 66.4% |

These are **real, computed** numbers from `notebooks/model_evaluation.ipynb`
— not the "pending" placeholder that was in `webapp/app.py` before this.
R² and directional accuracy for Gradient Boosting previously had no raw
per-row predictions to compute from; now they do
(`results/backtest_GB_raw_predictions.csv`).

**Next step for the team:** update `webapp/app.py`'s `FULL_METRICS` /
`PRIMARY` values to use these real numbers instead of showing "pending"
for Gradient Boosting's R² and directional accuracy.
