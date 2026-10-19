"""Expanding-window walk-forward backtest for the pooled ML models (A4).

For every horizon h and every test target quarter T (last 8 complete quarters),
models are re-trained using only rows whose *target* was already observed at the
forecast origin T-h, and then forecast every suburb with a valid target in T.
Conformalised quantile regression (CQR; Romano et al., 2019) wraps a LightGBM
quantile pair to give calibrated 10th-90th percentile bands.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import config as C, features as F, models as M


def _q(ts, k):
    return ts + pd.DateOffset(months=3 * k)


def cqr_interval(train: pd.DataFrame, test: pd.DataFrame, origin, cols, alpha=C.INTERVAL_ALPHA,
                 calib_quarters: int = 4):
    """Split-conformal CQR: fit quantile models on older rows, calibrate on the most recent
    `calib_quarters` of observed targets, then widen/narrow the band by the conformal margin."""
    cal_start = _q(origin, -calib_quarters + 1)
    proper, calib = train[train.target_quarter < cal_start], train[train.target_quarter >= cal_start]
    w = M.sample_weight(proper.target_n)
    lo_m = M.lightgbm_quantile(alpha / 2).fit(proper[cols], proper.target, sample_weight=w)
    hi_m = M.lightgbm_quantile(1 - alpha / 2).fit(proper[cols], proper.target, sample_weight=w)
    lo_c, hi_c = lo_m.predict(calib[cols]), hi_m.predict(calib[cols])
    scores = np.maximum(lo_c - calib.target.values, calib.target.values - hi_c)
    n = len(scores)
    margin = np.quantile(scores, min(1.0, np.ceil((n + 1) * (1 - alpha)) / n))
    lo_t, hi_t = lo_m.predict(test[cols]), hi_m.predict(test[cols])
    return lo_t, hi_t, lo_t - margin, hi_t + margin, float(margin)


def run(fs: pd.DataFrame, horizons=C.HORIZONS, n_test=C.N_TEST_QUARTERS, best_params=None,
        verbose=True) -> tuple[pd.DataFrame, list]:
    best_params = best_params or {}
    X = F.FEATURES + F.SEASONAL
    last_full = fs.loc[fs["is_partial_quarter"] == 0, "quarter"].max()
    test_quarters = pd.date_range(_q(last_full, -(n_test - 1)), last_full, freq="QS")
    pre = fs[(fs.quarter < test_quarters[0]) & (fs.n_sales > 0)]
    liq = pre.groupby("suburb").n_sales.mean()
    liquid = set(liq[liq >= C.LIQUID_MIN_MEAN_SALES].index)
    out, log = [], []
    for h in horizons:
        d = F.horizon_frame(fs, h)
        d = d[d.target.notna() & (d.quarter >= "2014-01-01")]
        for T in test_quarters:
            t0 = time.time()
            origin = _q(T, -h)
            train = d[d.target_quarter <= origin]
            test = d[d.target_quarter == T].copy()
            w = M.sample_weight(train.target_n)
            preds = M.baseline_predictions(test, h)
            a2 = M.a2_gradient_boosting().fit(train[M.A2_COLS], train.target)
            preds["A2 Gradient Boosting"] = a2.predict(test[M.A2_COLS])
            rd = M.ridge(**best_params.get("Ridge", {})).fit(train[X], train.target, ridge__sample_weight=w)
            preds["Ridge"] = rd.predict(test[X])
            rf = M.random_forest(**{**best_params.get("Random forest", {}), "n_estimators": 200}).fit(
                train[X], train.target, randomforestregressor__sample_weight=w)
            preds["Random forest"] = rf.predict(test[X])
            lg = M.lightgbm(**best_params.get("LightGBM", {})).fit(train[X], train.target, sample_weight=w)
            preds["LightGBM"] = lg.predict(test[X])
            xg = M.xgboost(**best_params.get("XGBoost", {})).fit(train[X], train.target, sample_weight=w)
            preds["XGBoost"] = xg.predict(test[X])
            preds["Ensemble (LGBM+XGB+RF)"] = preds[["LightGBM", "XGBoost", "Random forest"]].mean(axis=1)
            lo, hi, clo, chi, margin = cqr_interval(train, test, origin, X)
            preds = preds.assign(q10_raw=lo, q90_raw=hi, q10_cqr=clo, q90_cqr=chi)
            meta = test[["suburb", "region", "quarter", "target_quarter", "target", "target_n"]].rename(
                columns={"quarter": "origin", "target": "actual"})
            block = pd.concat([meta, preds], axis=1)
            block["horizon"] = h
            block["liquid"] = block.suburb.isin(liquid)
            out.append(block)
            log.append({"h": h, "target_quarter": str(T.date()), "n_train": len(train), "n_test": len(test),
                        "cqr_margin": round(margin, 2), "sec": round(time.time() - t0, 1)})
            if verbose:
                print(log[-1], flush=True)
    return pd.concat(out, ignore_index=True), log
