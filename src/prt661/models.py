"""Model zoo: baselines, the A2 champion (reproduced), and the A4 candidates."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C

# ---------------------------------------------------------------- baselines ---

def baseline_predictions(d: pd.DataFrame, h: int) -> pd.DataFrame:
    """All baselines use only information available at the forecast origin."""
    seasonal_src = {1: "qoq_lag3", 2: "qoq_lag2", 3: "qoq_lag1", 4: "qoq_pct_change"}[h]
    hist_mean = d["qoq_roll8_mean"].fillna(d["region_qoq_roll4"])
    return pd.DataFrame({
        "Naive persistence": d["qoq_pct_change"],
        "Seasonal naive": d[seasonal_src],
        "Historical mean": hist_mean,
        "Regional momentum": d["region_qoq_roll4"],
    }, index=d.index)


# ---------------------------------------------------------------- ML models ---

A2_COLS = ["qoq_pct_change", "qoq_lag1", "qoq_lag2", "qoq_lag3", "qoq_roll4_mean", "qoq_roll4_std",
           "abs_region_growth_lag1", "log_n_sales", "flag_covid_period", "flag_rate_hike_period",
           "target_q1", "target_q2", "target_q3", "target_q4"]


def a2_gradient_boosting():
    """Exact A2 configuration (GradientBoostingRegressor 200/3/0.05) on the A2 feature set."""
    return make_pipeline(SimpleImputer(strategy="median"),
                         GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05,
                                                   random_state=C.RANDOM_STATE))


def ridge(alpha: float = 10.0):
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(), Ridge(alpha=alpha))


def huber(epsilon: float = 1.35, alpha: float = 1e-3):
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                         HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=500))


def random_forest(**kw):
    p = dict(n_estimators=300, max_depth=10, min_samples_leaf=30, max_features=0.5, n_jobs=2,
             random_state=C.RANDOM_STATE)
    p.update(kw)
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), RandomForestRegressor(**p))


def lightgbm(**kw):
    import lightgbm as lgb
    p = dict(n_estimators=600, learning_rate=0.03, num_leaves=31, min_child_samples=50,
             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
             objective="huber", alpha=15.0, random_state=C.RANDOM_STATE, n_jobs=2, verbose=-1)
    p.update(kw)
    return lgb.LGBMRegressor(**p)


def xgboost(**kw):
    import xgboost as xgb
    p = dict(n_estimators=600, learning_rate=0.03, max_depth=5, min_child_weight=20,
             subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, objective="reg:pseudohubererror",
             huber_slope=15.0, tree_method="hist", random_state=C.RANDOM_STATE, n_jobs=2)
    p.update(kw)
    return xgb.XGBRegressor(**p)


def lightgbm_quantile(q: float, **kw):
    import lightgbm as lgb
    p = dict(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50,
             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, objective="quantile", alpha=q,
             random_state=C.RANDOM_STATE, n_jobs=2, verbose=-1)
    p.update(kw)
    return lgb.LGBMRegressor(**p)


def winsorise(y: pd.Series, lo: float = 0.01, hi: float = 0.99) -> pd.Series:
    """Clip extreme training targets (thin-market artefacts such as the +4,066% cell in A2)."""
    ql, qh = y.quantile([lo, hi])
    return y.clip(ql, qh)


def sample_weight(n_target: pd.Series, cap: int = 100) -> np.ndarray:
    """A suburb median from n sales has sampling variance ~1/n, so weight by (capped) n."""
    return np.sqrt(np.minimum(n_target.fillna(1).values, cap))
