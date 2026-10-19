"""Sampling-noise floor: how much of the QoQ error is explained by the sampling error of a suburb median alone?
SE(median) ~ 1.2533 * sigma / sqrt(n), sigma estimated robustly (IQR/1.349) from the suburb-quarter's own sales.
The previous quarter's sampling error is partly forecastable (mean reversion), so the irreducible part is 100 * SE_t / median_{t-1}; expected |error| from noise alone = 0.798 * SD."""
import sys; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from prt661 import config as C
c = pd.read_parquet(C.PROCESSED/"cleaned_sales.parquet", columns=["suburb", "quarter", "purchase_price", "is_outlier_flag"])
c = c[~c.is_outlier_flag]
g = c.groupby(["suburb", "quarter"]).purchase_price
s = pd.DataFrame({"n": g.size(), "med": g.median(), "iqr": g.quantile(.75) - g.quantile(.25)}).reset_index()
s["se"] = 1.2533 * (s.iqr / 1.349) / np.sqrt(s.n)
s = s.sort_values(["suburb", "quarter"])
s["se_prev"] = s.groupby("suburb").se.shift(1); s["med_prev"] = s.groupby("suburb").med.shift(1)
s["q_prev"] = s.groupby("suburb").quarter.shift(1)
s = s[(s.q_prev == s.quarter - pd.DateOffset(months=3))]
s["noise_sd"] = 100 * s.se / s.med_prev   # only THIS quarter's sampling error is unforecastable
bt = pd.read_parquet(C.PROCESSED/"backtest_ml.parquet")
d = bt[bt.horizon == 1].merge(s[["suburb", "quarter", "noise_sd"]], left_on=["suburb", "target_quarter"], right_on=["suburb", "quarter"], how="left")
d["band"] = pd.cut(d.target_n, [4, 9, 19, 39, 79, 10_000], labels=["5–9", "10–19", "20–39", "40–79", "80+"])
out = d.groupby("band", observed=True).apply(lambda x: pd.Series({"noise_floor_MAE": 0.798 * np.nanmean(x.noise_sd),
                                                                   "MAE_LightGBM": np.mean(np.abs(x.actual - x.LightGBM))})).reset_index()
out["share_of_error_from_noise_%"] = (out.noise_floor_MAE / out.MAE_LightGBM * 100)
tot = 0.798 * np.nanmean(d.noise_sd); tl = d[d.liquid]
print(out.round(2).to_string()); print("all: floor", round(tot, 2), "model", round(np.mean(np.abs(d.actual - d.LightGBM)), 2))
print("liquid: floor", round(0.798*np.nanmean(tl.noise_sd), 2), "model", round(np.mean(np.abs(tl.actual - tl.LightGBM)), 2))
out.to_csv(C.TABLES/"noise_floor.csv", index=False)

# ---- consistent band table + figure on the same rows ---------------------------------
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
dd = d.dropna(subset=["noise_sd", "LightGBM", "Naive persistence"])
tab = dd.groupby("band", observed=True).apply(lambda x: pd.Series({
    "N": len(x), "MAE_LightGBM": np.mean(np.abs(x.actual - x.LightGBM)), "MAE_naive": np.mean(np.abs(x.actual - x["Naive persistence"])),
    "noise_floor": 0.798 * np.mean(x.noise_sd), "cov_cqr": np.mean((x.actual >= x.q10_cqr) & (x.actual <= x.q90_cqr)) * 100,
    "width_cqr": np.mean(x.q90_cqr - x.q10_cqr)})).reset_index()
tab["noise_share_%"] = tab.noise_floor / tab.MAE_LightGBM * 100
tab.to_csv(C.TABLES/"error_by_liquidity.csv", index=False); print(tab.round(2).to_string())
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e5e1", "axes.axisbelow": True, "legend.frameon": False})
fig, ax = plt.subplots(figsize=(6.4, 2.9)); x = np.arange(len(tab)); w = 0.36
ax.bar(x - w/2, tab.MAE_naive, w, color="#b9c0c8", label="Naive persistence")
ax.bar(x + w/2, tab.MAE_LightGBM, w, color="#2a78d6", label="LightGBM (A4 champion)")
ax.plot(x + w/2, tab.noise_floor, color="#eb6834", marker="o", lw=2, label="Irreducible sampling error of the median")
for i, v in enumerate(tab["noise_share_%"]):
    ax.text(i + w/2, tab.MAE_LightGBM[i] + 0.6, f"{v:.0f}%", ha="center", fontsize=7.5, color="#52514e")
ax.set_xticks(x, tab.band); ax.set_xlabel("Sales in the target suburb-quarter"); ax.set_ylabel("MAE (percentage points)")
ax.grid(axis="x", visible=False); ax.legend(fontsize=7.5)
fig.savefig(C.FIGURES/"fig_liquidity.png", dpi=200, bbox_inches="tight")
