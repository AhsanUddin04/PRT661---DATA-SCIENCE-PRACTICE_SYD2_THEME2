"""Compute every evaluation table and figure used in the A4 report from the backtest outputs."""
import json
import sys
import warnings

sys.path.insert(0, "src")
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from prt661 import config as C
from prt661.evaluation import diebold_mariano, interval_scores, metrics

# ---- palette (validated reference palette, light mode) -----------------------
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "figure.dpi": 200, "savefig.bbox": "tight"})
F, T = C.FIGURES, C.TABLES

bt = pd.read_parquet(C.PROCESSED / "backtest_ml.parquet")
sar = pd.read_parquet(C.PROCESSED / "backtest_sarima.parquet")
pro = pd.read_parquet(C.PROCESSED / "backtest_prophet.parquet")
bt = bt.merge(sar[["suburb", "target_quarter", "horizon", "sarima"]], on=["suburb", "target_quarter", "horizon"], how="left")
bt = bt.merge(pro[["suburb", "target_quarter", "horizon", "prophet"]], on=["suburb", "target_quarter", "horizon"], how="left")
bt = bt.rename(columns={"sarima": "SARIMA", "prophet": "Prophet"})
MODELS = ["Naive persistence", "Seasonal naive", "Historical mean", "Regional momentum", "SARIMA",
          "A2 Gradient Boosting", "Ridge", "Random forest", "XGBoost", "LightGBM", "Ensemble (LGBM+XGB+RF)"]
CHAMP = "LightGBM"
out = {}

# ---- 1. leaderboard: h=1, liquid suburbs, rows where every model (incl. SARIMA) has a forecast
L = bt[(bt.horizon == 1) & bt.liquid].dropna(subset=MODELS)
rows = [{"model": m, **metrics(L.actual, L[m], L.target_n)} for m in MODELS]
lb = pd.DataFrame(rows).sort_values("RMSE")
naive = lb.set_index("model").loc["Naive persistence"]
lb["RMSE_vs_naive_%"] = (1 - lb.RMSE / naive.RMSE) * 100
dm = []
for m in MODELS:
    if m in (CHAMP,):
        continue
    s, p = diebold_mariano(L.actual, L[CHAMP], L[m], h=1, power=2)
    s1, p1 = diebold_mariano(L.actual, L[CHAMP], L[m], h=1, power=1)
    dm.append({"vs": m, "DM_sq": s, "p_sq": p, "DM_abs": s1, "p_abs": p1})
pd.DataFrame(dm).to_csv(T / "dm_tests.csv", index=False)
lb.to_csv(T / "leaderboard_h1_liquid.csv", index=False)
out["leaderboard_N"] = len(L); out["leaderboard_suburbs"] = L.suburb.nunique()
print(lb.round(3).to_string())
print(pd.DataFrame(dm).round(4).to_string())

# Prophet on its stratified sample (same cells for all models)
P = bt[(bt.horizon == 1) & bt.liquid].dropna(subset=MODELS + ["Prophet"])
pl = pd.DataFrame([{"model": m, **metrics(P.actual, P[m])} for m in ["Naive persistence", "SARIMA", "Prophet",
                                                                     "A2 Gradient Boosting", CHAMP]]).sort_values("RMSE")
pl.to_csv(T / "prophet_subset_h1.csv", index=False); out["prophet_N"] = len(P); out["prophet_suburbs"] = P.suburb.nunique()
print(pl.round(3).to_string())

# all scored suburbs (not only liquid) — ML models + baselines
A = bt[bt.horizon == 1].dropna(subset=[m for m in MODELS if m != "SARIMA"])
al = pd.DataFrame([{"model": m, **metrics(A.actual, A[m], A.target_n)} for m in MODELS if m != "SARIMA"]).sort_values("RMSE")
al.to_csv(T / "leaderboard_h1_all.csv", index=False); out["all_N"] = len(A); out["all_suburbs"] = A.suburb.nunique()

# ---- 2. by horizon (liquid)
H = []
for h in C.HORIZONS:
    d = bt[(bt.horizon == h) & bt.liquid].dropna(subset=MODELS)
    for m in MODELS:
        H.append({"horizon": h, "model": m, **metrics(d.actual, d[m])})
byh = pd.DataFrame(H); byh.to_csv(T / "metrics_by_horizon.csv", index=False)

fig, ax = plt.subplots(1, 2, figsize=(8.6, 3.0))
for m, col, mk in [("Naive persistence", MUTED, "o"), ("SARIMA", YELLOW, "s"), ("A2 Gradient Boosting", ORANGE, "^"),
                   ("Ensemble (LGBM+XGB+RF)", AQUA, "D"), (CHAMP, BLUE, "o")]:
    s = byh[byh.model == m]
    ax[0].plot(s.horizon, s.MAE, marker=mk, color=col, lw=2, ms=5, label=m)
    ax[1].plot(s.horizon, s.DirAcc, marker=mk, color=col, lw=2, ms=5, label=m)
ax[0].set(xlabel="Horizon (quarters ahead)", ylabel="MAE (percentage points)", xticks=[1, 2, 3, 4], title="Error by horizon")
ax[1].set(xlabel="Horizon (quarters ahead)", ylabel="Direction correct (%)", xticks=[1, 2, 3, 4], title="Directional accuracy")
ax[1].axhline(50, color=MUTED, lw=0.8, ls=":")
ax[0].legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0, -0.22), ncol=5)
for a in ax: a.title.set_fontsize(10)
fig.savefig(F / "fig_horizon.png"); plt.close(fig)

# ---- 3. leaderboard bar chart
fig, ax = plt.subplots(figsize=(7.6, 3.3))
lbs = lb.sort_values("MAE", ascending=False)
cols = [BLUE if m == CHAMP else (ORANGE if m == "A2 Gradient Boosting" else (YELLOW if m == "SARIMA" else "#a9b9cf"))
        for m in lbs.model]
ax.barh(lbs.model, lbs.MAE, color=cols, height=0.62)
for i, (v, r) in enumerate(zip(lbs.MAE, lbs.RMSE)):
    ax.text(v + 0.1, i, f"MAE {v:.2f}  ·  RMSE {r:.2f}", va="center", fontsize=7.5, color=INK2)
ax.set_xlim(0, lbs.MAE.max() * 1.45); ax.set_xlabel("MAE, percentage points (lower is better)")
ax.grid(axis="y", visible=False)
fig.savefig(F / "fig_leaderboard.png"); plt.close(fig)

# ---- 4. liquidity / noise-floor analysis lives in scripts/run_noise_floor.py (run after this script)

# ---- 5. interval calibration
cv = []
for h in C.HORIZONS:
    d = bt[bt.horizon == h]
    raw = interval_scores(d.actual, d.q10_raw, d.q90_raw); cq = interval_scores(d.actual, d.q10_cqr, d.q90_cqr)
    dl = d[d.liquid]; cql = interval_scores(dl.actual, dl.q10_cqr, dl.q90_cqr)
    cv.append({"horizon": h, "raw_coverage": raw["coverage"], "raw_width": raw["mean_width"],
               "cqr_coverage": cq["coverage"], "cqr_width": cq["mean_width"], "cqr_interval_score": cq["interval_score"],
               "cqr_coverage_liquid": cql["coverage"], "cqr_width_liquid": cql["mean_width"], "N": cq["N"]})
cv = pd.DataFrame(cv); cv.to_csv(T / "interval_coverage.csv", index=False); print(cv.round(2).to_string())

# per-quarter stability
pq = bt[(bt.horizon == 1) & bt.liquid].dropna(subset=MODELS).groupby("target_quarter").apply(lambda g: pd.Series({
    "LightGBM": np.mean(np.abs(g.actual - g[CHAMP])), "Naive persistence": np.mean(np.abs(g.actual - g["Naive persistence"])),
    "A2 Gradient Boosting": np.mean(np.abs(g.actual - g["A2 Gradient Boosting"])),
    "SARIMA": np.mean(np.abs(g.actual - g["SARIMA"])),
    "coverage": np.mean((g.actual >= g.q10_cqr) & (g.actual <= g.q90_cqr)) * 100, "N": len(g)})).reset_index()
pq.to_csv(T / "per_quarter_h1.csv", index=False)
fig, ax = plt.subplots(1, 2, figsize=(8.6, 2.8), gridspec_kw={"width_ratios": [1.5, 1]})
lab = pd.to_datetime(pq.target_quarter).dt.to_period("Q").astype(str)
for m, col in [("Naive persistence", MUTED), ("SARIMA", YELLOW), ("A2 Gradient Boosting", ORANGE), ("LightGBM", BLUE)]:
    ax[0].plot(lab, pq[m], marker="o", ms=4, lw=2, color=col, label=m)
ax[0].set_ylabel("MAE (pp), h = 1"); ax[0].tick_params(axis="x", rotation=45, labelsize=7.5); ax[0].legend(fontsize=7, ncol=2)
ax[0].set_title("Accuracy is stable across the test window", fontsize=10)
ax[1].plot(cv.horizon, cv.raw_coverage, marker="s", color=MUTED, lw=2, label="Raw quantile LightGBM")
ax[1].plot(cv.horizon, cv.cqr_coverage, marker="o", color=BLUE, lw=2, label="Conformalised (CQR)")
ax[1].axhline(80, color=ORANGE, lw=1.2, ls="--", label="Target 80%")
ax[1].set(xticks=[1, 2, 3, 4], ylim=(55, 95), xlabel="Horizon", ylabel="Empirical coverage (%)")
ax[1].set_title("P10–P90 band calibration", fontsize=10); ax[1].legend(fontsize=7)
fig.savefig(F / "fig_stability_coverage.png"); plt.close(fig)

# ---- 6. calibration of point forecasts (binned)
c = bt[(bt.horizon == 1) & bt.liquid].dropna(subset=[CHAMP]).copy()
c["bin"] = pd.qcut(c[CHAMP], 10, duplicates="drop")
cb = c.groupby("bin", observed=True).agg(pred=(CHAMP, "mean"), act=("actual", "mean"), med=("actual", "median")).reset_index()
fig, ax = plt.subplots(figsize=(3.6, 3.0))
ax.plot(cb.pred, cb.act, marker="o", color=BLUE, lw=2, label="Mean actual")
ax.plot(cb.pred, cb.med, marker="s", color=AQUA, lw=2, label="Median actual")
lim = [min(cb.pred.min(), cb.med.min()) - 1, max(cb.pred.max(), cb.act.max()) + 1]
ax.plot(lim, lim, color=MUTED, ls=":", lw=1, label="Perfect calibration")
ax.set(xlabel="Predicted QoQ % (decile mean)", ylabel="Actual QoQ %"); ax.legend(fontsize=7)
fig.savefig(F / "fig_calibration.png"); plt.close(fig)
cb.to_csv(T / "point_calibration.csv", index=False)

# ---- 7. fairness / segment errors
seg = []
for (r, lq), g in bt[bt.horizon == 1].dropna(subset=[CHAMP]).groupby(["region", "liquid"]):
    seg.append({"region": r, "liquid": lq, **metrics(g.actual, g[CHAMP]),
                "coverage": np.mean((g.actual >= g.q10_cqr) & (g.actual <= g.q90_cqr)) * 100,
                "bias": float(np.mean(g[CHAMP] - g.actual))})
pd.DataFrame(seg).to_csv(T / "segment_errors.csv", index=False); print(pd.DataFrame(seg).round(2).to_string())

json.dump(out, open(T / "assets_meta.json", "w"), indent=1)
print(out)
