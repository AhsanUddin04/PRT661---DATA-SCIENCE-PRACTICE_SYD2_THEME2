"""Validate the production (cumulative-change) models + CQR bands on the same walk-forward window."""
import sys, json; sys.path.insert(0, "src")
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from prt661 import config as C, features as F, models as M
from prt661.backtest import cqr_interval
from prt661.evaluation import metrics, interval_scores
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet"); bp = json.load(open(C.MODELS/"best_params.json"))
X = F.FEATURES + F.SEASONAL
tq = pd.date_range("2024-07-01", "2026-04-01", freq="QS"); rows = []
for h in C.HORIZONS:
    d = F.horizon_frame(fs, h, cumulative=True); d = d[d.target.notna() & (d.quarter >= "2014-01-01")]
    for T in tq:
        o = T - pd.DateOffset(months=3*h); tr = d[d.target_quarter <= o]; te = d[d.target_quarter == T].copy()
        m = M.lightgbm(**bp["LightGBM"]).fit(tr[X], tr.target, sample_weight=M.sample_weight(tr.target_n))
        _, _, lo, hi, _ = cqr_interval(tr, te, o, X); p = m.predict(te[X])
        te = te.assign(pred=p, lo=np.minimum(lo, p), hi=np.maximum(hi, p), naive=0.0)
        rows.append(te[["suburb", "target_quarter", "horizon", "target", "target_n", "pred", "lo", "hi", "naive"]])
        print(h, T.date(), flush=True)
r = pd.concat(rows); r.to_parquet(C.PROCESSED/"backtest_cumulative.parquet", index=False)
summ = []
for h, g in r.groupby("horizon"):
    summ.append({"horizon": h, **{f"model_{k}": v for k, v in metrics(g.target, g.pred).items()},
                 "naive_MAE": metrics(g.target, g.naive)["MAE"], **interval_scores(g.target, g.lo, g.hi)})
s = pd.DataFrame(summ); s.to_csv(C.TABLES/"cumulative_backtest.csv", index=False); print(s.round(2).to_string())
json.dump({"overall_coverage": float(np.mean((r.target >= r.lo) & (r.target <= r.hi)) * 100)}, open(C.TABLES/"cumulative_coverage.json", "w"))
