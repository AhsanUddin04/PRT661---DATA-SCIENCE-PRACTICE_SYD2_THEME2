"""Feature store v2 (Assessment 4).

Changes relative to the A2 feature store, each fixing a defect found in audit:

* **Complete suburb x quarter grid.** A2 computed ``pct_change`` over whatever
  rows existed, so 9.5% of "quarter-on-quarter" targets actually spanned a
  missing quarter. Every suburb now has every quarter; a QoQ change is only
  defined when both adjacent quarters have sales.
* **Forecast-origin framing.** Features describe what is known at the end of
  quarter *t*; targets are the QoQ change in quarter *t+h* (h = 1..4). This
  makes every model a genuine ex-ante forecast.
* **No look-ahead in the ABS regressor.** ABS Total Value of Dwellings is
  published ~1 quarter after the reference quarter, so the benchmark used at
  origin *t* is the value for *t-1*.
* **Composition and market-breadth features** (strata share, $/sqm, region and
  state momentum from our own data, deviation from trend) — the
  "compositional control" item that A2 listed as not yet implemented.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def _region_for_postcode(pc: float) -> str:
    if pd.isna(pc):
        return "rest_nsw"
    return "sydney" if any(lo <= pc <= hi for lo, hi in C.SYDNEY_POSTCODE_RANGES) else "rest_nsw"


def aggregate_suburb_quarter(clean: pd.DataFrame) -> pd.DataFrame:
    d = clean[~clean["is_outlier_flag"]]
    agg = (d.groupby(["suburb", "quarter"])
             .agg(n_sales=("purchase_price", "size"),
                  median_price=("purchase_price", "median"),
                  median_price_per_sqm=("price_per_sqm", "median"),
                  strata_share=("is_strata", "mean"))
             .reset_index())
    pc = (clean.dropna(subset=["postcode"]).groupby("suburb")["postcode"]
               .agg(lambda s: s.mode().iloc[0]))
    agg["postcode"] = agg["suburb"].map(pc)
    agg["region"] = agg["postcode"].map(_region_for_postcode)
    return agg


def complete_grid(agg: pd.DataFrame) -> pd.DataFrame:
    quarters = pd.date_range(agg["quarter"].min(), agg["quarter"].max(), freq="QS")
    idx = pd.MultiIndex.from_product([agg["suburb"].unique(), quarters], names=["suburb", "quarter"])
    g = agg.set_index(["suburb", "quarter"]).reindex(idx).reset_index()
    for c in ("postcode", "region"):
        g[c] = g.groupby("suburb")[c].transform(lambda s: s.ffill().bfill())
    g["n_sales"] = g["n_sales"].fillna(0).astype(int)
    return g.sort_values(["suburb", "quarter"]).reset_index(drop=True)


def _load_abs() -> pd.DataFrame:
    a = pd.read_csv(C.ABS_CSV, parse_dates=["Date"])
    a["quarter"] = a["Date"].dt.to_period("Q").dt.start_time
    return a[["quarter", "median_price_house_sydney_qoq_pct",
              "median_price_house_rest_nsw_qoq_pct", "tvd_households_qoq_pct"]]


def build_feature_store(clean: pd.DataFrame) -> pd.DataFrame:
    g = complete_grid(aggregate_suburb_quarter(clean))
    last_q = g["quarter"].max()
    # partial quarter: the extract was taken mid-quarter (A2 §3.10.1)
    g["is_partial_quarter"] = (g["quarter"] == last_q).astype(int)

    by = g.groupby("suburb", sort=False)
    has = g["n_sales"] >= C.MIN_SALES_FOR_TARGET
    price_ok = g["median_price"].where(has)
    prev = by["median_price"].shift(1).where(by["n_sales"].shift(1) >= C.MIN_SALES_FOR_TARGET)
    g["qoq_pct_change"] = (price_ok / prev - 1) * 100
    g.loc[g["is_partial_quarter"] == 1, "qoq_pct_change"] = np.nan
    g["log_price"] = np.log(price_ok)
    g["log_n_sales"] = np.log1p(g["n_sales"])

    by = g.groupby("suburb", sort=False)
    for k in (1, 2, 3):
        g[f"qoq_lag{k}"] = by["qoq_pct_change"].shift(k)
    g["qoq_roll4_mean"] = by["qoq_pct_change"].transform(lambda s: s.rolling(4, min_periods=2).mean())
    g["qoq_roll4_std"] = by["qoq_pct_change"].transform(lambda s: s.rolling(4, min_periods=2).std())
    g["qoq_roll8_mean"] = by["qoq_pct_change"].transform(lambda s: s.rolling(8, min_periods=4).mean())
    lp_ff = by["log_price"].transform(lambda s: s.ffill(limit=2))
    g["yoy_pct_change"] = (np.exp(lp_ff - by["log_price"].shift(4)) - 1) * 100
    g["dev_from_trend"] = (g["log_price"] - by["log_price"].transform(
        lambda s: s.rolling(4, min_periods=2).mean())) * 100
    g["sales_vol_change"] = g["log_n_sales"] - by["log_n_sales"].transform(
        lambda s: s.shift(1).rolling(4, min_periods=2).mean())
    g["strata_share_change"] = g["strata_share"] - by["strata_share"].shift(1)
    g["log_ppsqm"] = np.log(g["median_price_per_sqm"])
    g["quarters_with_sales_8"] = by["n_sales"].transform(
        lambda s: (s >= C.MIN_SALES_FOR_TARGET).rolling(8, min_periods=1).sum())

    # market breadth from our own (timely) data: QoQ change of the region-wide and
    # state-wide median sale price (robust to single-suburb artefacts)
    d = clean[~clean["is_outlier_flag"]].copy()
    d["region"] = d["suburb"].map(g.drop_duplicates("suburb").set_index("suburb")["region"])
    reg = d.groupby(["region", "quarter"])["purchase_price"].median().rename("rp").reset_index()
    reg["region_qoq"] = reg.groupby("region")["rp"].pct_change() * 100
    st = d.groupby("quarter")["purchase_price"].median().rename("sp").reset_index()
    st["state_qoq"] = st["sp"].pct_change() * 100
    first_ok = d.groupby("quarter").size().loc[lambda s: s > 10_000].index.min()
    reg.loc[reg["quarter"] <= first_ok, "region_qoq"] = np.nan
    st.loc[st["quarter"] <= first_ok, "state_qoq"] = np.nan
    reg.loc[reg["quarter"] == last_q, "region_qoq"] = np.nan  # partial quarter
    st.loc[st["quarter"] == last_q, "state_qoq"] = np.nan
    g = (g.merge(reg[["region", "quarter", "region_qoq"]], on=["region", "quarter"], how="left")
          .merge(st[["quarter", "state_qoq"]], on="quarter", how="left"))
    g = g.sort_values(["suburb", "quarter"]).reset_index(drop=True)
    g["region_qoq_roll4"] = g.groupby("suburb")["region_qoq"].transform(lambda s: s.rolling(4, min_periods=2).mean())

    # ABS benchmark, lagged one quarter to respect its publication delay
    a = _load_abs()
    a["quarter"] = a["quarter"] + pd.offsets.QuarterBegin(1, startingMonth=1)
    g = g.merge(a, on="quarter", how="left")
    g["abs_region_growth_lag1"] = np.where(g["region"] == "sydney",
                                           g["median_price_house_sydney_qoq_pct"],
                                           g["median_price_house_rest_nsw_qoq_pct"])
    g = g.rename(columns={"tvd_households_qoq_pct": "abs_tvd_growth_lag1"}).drop(
        columns=["median_price_house_sydney_qoq_pct", "median_price_house_rest_nsw_qoq_pct"])

    g["quarter_of_year"] = g["quarter"].dt.quarter
    g["is_sydney"] = (g["region"] == "sydney").astype(int)
    g["flag_covid_period"] = g["quarter"].between(C.COVID_START, C.COVID_END).astype(int)
    g["flag_rate_hike_period"] = g["quarter"].between(C.RATE_HIKE_START, C.RATE_HIKE_END).astype(int)

    # direct multi-horizon targets: QoQ change in quarter t+h, plus its sale count (for weights)
    g = g.sort_values(["suburb", "quarter"]).reset_index(drop=True)
    by = g.groupby("suburb", sort=False)
    anchor_ok = g["median_price"].where(g["n_sales"] >= C.MIN_SALES_FOR_TARGET)
    for h in C.HORIZONS:
        fut = by["median_price"].shift(-h).where(by["n_sales"].shift(-h) >= C.MIN_SALES_FOR_TARGET)
        fut = fut.where(by["is_partial_quarter"].shift(-h) == 0)
        g[f"cum_target_h{h}"] = (fut / anchor_ok - 1) * 100
        g[f"target_h{h}"] = by["qoq_pct_change"].shift(-h)
        g[f"target_n_h{h}"] = by["n_sales"].shift(-h)
        g[f"target_quarter_h{h}"] = g["quarter"] + pd.DateOffset(months=3 * h)
    return g


FEATURES = [
    "qoq_pct_change", "qoq_lag1", "qoq_lag2", "qoq_lag3",
    "qoq_roll4_mean", "qoq_roll4_std", "qoq_roll8_mean", "yoy_pct_change", "dev_from_trend",
    "log_price", "log_ppsqm", "log_n_sales", "sales_vol_change", "quarters_with_sales_8",
    "strata_share", "strata_share_change",
    "region_qoq", "region_qoq_roll4", "state_qoq",
    "abs_region_growth_lag1", "abs_tvd_growth_lag1",
    "is_sydney", "flag_covid_period", "flag_rate_hike_period",
]
# target-quarter seasonality is known in advance and is added per horizon
SEASONAL = ["target_q1", "target_q2", "target_q3", "target_q4"]

# The exact A2 feature set, kept so the A2 model can be reproduced on the A4 test window
A2_FEATURES_MAP = {
    "lag_1_qoq_pct": "qoq_pct_change", "lag_2_qoq_pct": "qoq_lag1",
    "lag_3_qoq_pct": "qoq_lag2", "lag_4_qoq_pct": "qoq_lag3",
}


def horizon_frame(fs: pd.DataFrame, h: int, cumulative: bool = False) -> pd.DataFrame:
    d = fs.copy()
    d["target"] = d[f"cum_target_h{h}"] if cumulative else d[f"target_h{h}"]
    d["target_n"] = d[f"target_n_h{h}"]
    d["target_quarter"] = d[f"target_quarter_h{h}"]
    tq = d["target_quarter"].dt.quarter
    for q in (1, 2, 3, 4):
        d[f"target_q{q}"] = (tq == q).astype(int)
    d["horizon"] = h
    return d
