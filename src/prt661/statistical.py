"""Per-suburb statistical models (SARIMA, Prophet) re-run on the A4 common test window.

In A2 SARIMA/Prophet and Gradient Boosting were evaluated on *different*
suburbs and *different* windows, so their RMSEs were not directly comparable
(A2 §3.9). Here every model forecasts exactly the same (suburb, target quarter,
horizon) cells.
"""
from __future__ import annotations

import logging
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)


def sarima_forecast(y: pd.Series, steps: int = 4) -> np.ndarray:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    y = y.astype(float)
    if y.notna().sum() < 12:
        return np.full(steps, np.nan)
    try:
        fit = SARIMAX(y.values, order=(1, 0, 1), seasonal_order=(1, 0, 0, 4), trend="c",
                      enforce_stationarity=True, enforce_invertibility=True).fit(disp=False, maxiter=200)
        return np.asarray(fit.forecast(steps))
    except Exception:
        return np.full(steps, np.nan)


def prophet_forecast(y: pd.Series, steps: int = 4) -> np.ndarray:
    from prophet import Prophet
    d = pd.DataFrame({"ds": y.index, "y": y.values}).dropna()
    if len(d) < 12:
        return np.full(steps, np.nan)
    try:
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False,
                    interval_width=0.8, uncertainty_samples=0)
        m.fit(d)
        fut = pd.DataFrame({"ds": pd.date_range(y.index[-1], periods=steps + 1, freq="QS")[1:]})
        return m.predict(fut)["yhat"].values
    except Exception:
        return np.full(steps, np.nan)


def backtest_suburb(args) -> list[dict]:
    suburb, series, origins, which = args
    out = []
    for origin in origins:
        hist = series[series.index <= origin]
        hist = hist[hist.index >= pd.Timestamp("2014-01-01")]
        fc = sarima_forecast(hist) if which == "sarima" else prophet_forecast(hist)
        for h in range(1, 5):
            out.append({"suburb": suburb, "origin": origin, "horizon": h,
                        "target_quarter": origin + pd.DateOffset(months=3 * h), which: fc[h - 1]})
    return out
