"""Production forecasting: train champion models on all history and publish forecasts.

For each horizon h = 1..4 a direct LightGBM model predicts the *cumulative* %
change in the suburb median from the anchor quarter (last complete quarter) to
quarter t+h; a CQR-calibrated quantile pair provides the 10th-90th band. Because
each horizon has its own direct model, the price path needs no compounding of
one-step forecasts — the defect that produced the A2 "runaway forecast" bug.
"""
from __future__ import annotations

import hashlib

import joblib
import numpy as np
import pandas as pd

from . import config as C, features as F, models as M
from .backtest import cqr_interval

MODEL_VERSION = "4.0.0"


def reliability_label(n_sales_recent: float, width: float) -> str:
    if n_sales_recent >= 20 and width <= 25:
        return "high"
    if n_sales_recent >= 10:
        return "medium"
    return "low"


def _sha256(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def train_and_forecast(fs: pd.DataFrame, best_params: dict) -> tuple[pd.DataFrame, list[dict]]:
    X = F.FEATURES + F.SEASONAL
    anchor_q = fs.loc[fs["is_partial_quarter"] == 0, "quarter"].max()
    registry, frames = [], []
    for h in C.HORIZONS:
        d = F.horizon_frame(fs, h, cumulative=True)
        train = d[d.target.notna() & (d.quarter >= "2014-01-01") & (d.target_quarter <= anchor_q)]
        live = d[(d.quarter == anchor_q) & (d.n_sales >= C.MIN_SALES_FOR_TARGET)].copy()
        w = M.sample_weight(train.target_n)
        point = M.lightgbm(**best_params.get("LightGBM", {})).fit(train[X], train.target, sample_weight=w)
        _, _, lo, hi, margin = cqr_interval(train, live, anchor_q, X)
        p = point.predict(live[X])
        lo, hi = np.minimum(lo, p), np.maximum(hi, p)
        path = C.MODELS / f"lgbm_cumulative_h{h}.joblib"
        joblib.dump({"model": point, "features": X, "cqr_margin": margin, "version": MODEL_VERSION}, path)
        registry.append({"model_name": "LightGBM-cumulative", "model_version": MODEL_VERSION, "horizon": h,
                         "target": "cumulative", "trained_through": str(anchor_q.date()),
                         "artefact_path": str(path.relative_to(C.ROOT)), "artefact_sha256": _sha256(path),
                         "n_train": int(len(train)), "cqr_margin": round(margin, 3)})
        anchor = live["median_price"].values
        last4 = fs[(fs.quarter > anchor_q - pd.DateOffset(months=12)) & (fs.quarter <= anchor_q)]
        recent_n = live["suburb"].map(last4.groupby("suburb").n_sales.mean()).values
        frames.append(pd.DataFrame({
            "suburb": live.suburb.values, "origin_quarter": anchor_q, "target_quarter": live.target_quarter.values,
            "horizon": h, "anchor_price": anchor, "point_pct": p, "p10_pct": lo, "p90_pct": hi,
            "point_price": anchor * (1 + p / 100), "p10_price": anchor * (1 + lo / 100),
            "p90_price": anchor * (1 + hi / 100),
            "reliability": [reliability_label(n, wd) for n, wd in zip(recent_n, hi - lo)],
            "model_version": MODEL_VERSION}))
    fc = pd.concat(frames, ignore_index=True)
    return fc, registry
