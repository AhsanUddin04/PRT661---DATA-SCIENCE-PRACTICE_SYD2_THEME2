"""SHAP explanation of the champion LightGBM (h=1, trained through the last test origin)."""
import sys, json; sys.path.insert(0, "src")
import warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, pandas as pd, shap
from prt661 import config as C, features as F, models as M
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
d = F.horizon_frame(fs, 1); d = d[d.target.notna() & (d.quarter >= "2014-01-01")]
X = F.FEATURES + F.SEASONAL
origin = pd.Timestamp("2026-01-01")
tr = d[d.target_quarter <= origin]; te = d[d.target_quarter == pd.Timestamp("2026-04-01")]
m = M.lightgbm(**json.load(open(C.MODELS/"best_params.json"))["LightGBM"]).fit(tr[X], tr.target, sample_weight=M.sample_weight(tr.target_n))
sv = shap.TreeExplainer(m).shap_values(te[X])
imp = pd.Series(np.abs(sv).mean(0), index=X).sort_values(ascending=False)
(imp / imp.sum() * 100).round(2).rename("share_%").to_csv(C.TABLES/"shap_importance.csv")
print((imp / imp.sum() * 100).round(1).head(12))
nice = {"qoq_pct_change": "QoQ change, latest quarter", "dev_from_trend": "Deviation from 4-qtr trend",
        "yoy_pct_change": "YoY change", "qoq_lag1": "QoQ change, t-1", "qoq_lag2": "QoQ change, t-2", "qoq_lag3": "QoQ change, t-3",
        "qoq_roll4_mean": "4-qtr mean QoQ", "qoq_roll4_std": "4-qtr volatility", "qoq_roll8_mean": "8-qtr mean QoQ",
        "log_price": "Price level (log)", "log_ppsqm": "$ per m² (log)", "log_n_sales": "Sales count (log)",
        "sales_vol_change": "Sales-volume change", "strata_share": "Unit (strata) share", "strata_share_change": "Change in unit share",
        "region_qoq": "Regional median QoQ", "region_qoq_roll4": "Regional 4-qtr momentum", "state_qoq": "NSW median QoQ",
        "abs_region_growth_lag1": "ABS regional growth (lagged)", "abs_tvd_growth_lag1": "ABS dwelling value growth (lagged)",
        "quarters_with_sales_8": "Quarters with ≥5 sales (of 8)", "is_sydney": "Greater Sydney",
        "flag_covid_period": "COVID period", "flag_rate_hike_period": "Rate-hike period",
        "target_q1": "Target in Q1", "target_q2": "Target in Q2", "target_q3": "Target in Q3", "target_q4": "Target in Q4"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
shap.summary_plot(sv, te[X].rename(columns=nice), max_display=12, show=False, plot_size=(7.2, 4.2), cmap="coolwarm")
plt.xlabel("SHAP value: contribution to forecast QoQ % (pp)")
plt.savefig(C.FIGURES/"fig_shap.png", dpi=200, bbox_inches="tight")
print("ok", len(te))
