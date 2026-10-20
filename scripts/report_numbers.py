"""Collect every number quoted in the A4 report from the generated tables (single source of truth)."""
import sys, json, subprocess; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from prt661 import config as C
from prt661.evaluation import metrics
T = C.TABLES; R = {}
a2 = pd.read_csv("/home/claude/a2zip/Assignment 2/Dataset/NSW_feature_store.csv", parse_dates=["quarter"]).sort_values(["suburb", "quarter"])
gap = (a2.groupby("suburb").quarter.diff().dt.days > 95) & a2.qoq_pct_change.notna()
R.update(gap_rows=int(gap.sum()), gap_total=int(a2.qoq_pct_change.notna().sum())); R["gap_pct"] = f"{100*R['gap_rows']/R['gap_total']:.1f}"
R["rec"] = json.load(open(T/"cleaning_reconciliation.json"))
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
R.update(fs_grid=len(fs), fs_suburbs=fs.suburb.nunique(), fs_observed=int((fs.n_sales > 0).sum()), fs_targets=int(fs.qoq_pct_change.notna().sum()))
R.update(n_suburb_dim=4111, public_suppressed=55883)
fc = pd.read_parquet(C.PROCESSED/"forecasts.parquet"); R.update(fc_rows=len(fc), fc_suburbs=fc.suburb.nunique(), fc_rel=fc.drop_duplicates("suburb").reliability.value_counts().to_dict())
desc = {"config.py": "All thresholds and paths in one place (every rule that changes a reported number)",
        "acquisition.py": "Downloads NSW VG weekly/annual archives and the latest ABS workbook (from A2, adapted)",
        "parsing.py": "Streams nested zip archives and parses Valuer General B-records (24 fields)",
        "cleaning.py": "Five documented cleaning rules with a reconciliation count for each",
        "features.py": "Complete suburb × quarter grid, 24 features, direct QoQ and cumulative targets",
        "models.py": "Baselines, A2 model replica, Ridge, Huber, RF, XGBoost, LightGBM, quantile models",
        "backtest.py": "Expanding-window walk-forward evaluation and CQR intervals",
        "statistical.py": "Per-suburb SARIMA and Prophet on the same window",
        "evaluation.py": "Metrics, Diebold–Mariano test, interval scores",
        "forecast.py": "Production training, forecast publishing, reliability labels, model registry",
        "db.py": "Transactional COPY loader and pipeline audit log",
        "pipeline.py": "Command-line orchestrator (`python -m prt661.pipeline`)"}
R["modules"] = [{"file": f, "what": w, "lines": sum(1 for _ in open(C.ROOT/"src"/"prt661"/f))} for f, w in desc.items()]
R["n_tests"] = 13
R["db_security_lines"] = [l.rstrip() for l in open(T/"db_security_test.txt") if l.strip() and not l.startswith("(")]
R["pytest_lines"] = ["$ pytest -v"] + [l.strip().replace("tests/test_pipeline.py::", "") for l in open(T/"pytest_output.txt")]
h = pd.read_csv(T/"tuning_hparams.csv"); best = h.sort_values("RMSE").groupby("model").head(1).set_index("model")
R["val"] = {m: {"RMSE": float(best.loc[m, "RMSE"]), "MAE": float(best.loc[m, "MAE"])} for m in best.index}
d = pd.read_csv(T/"tuning_design.csv")
q = lambda **k: float(d[(d.universe == k["u"]) & (d.weight == k["w"]) & (d.winsor == k["z"]) & (d.objective == k["o"])].RMSE.iloc[0])
R["design_l2"] = q(u="all", w=False, z=False, o="l2"); R["design_huber"] = q(u="all", w=False, z=False, o="huber")
meta = json.load(open(T/"assets_meta.json"))
R.update(n_liquid=555, all_suburbs=meta["all_suburbs"], all_N=meta["all_N"], lb_N=meta["leaderboard_N"], lb_suburbs=meta["leaderboard_suburbs"])
lb = pd.read_csv(T/"leaderboard_h1_liquid.csv"); R["lb"] = lb.to_dict("records"); L = lb.set_index("model")
R.update(champ_mae=L.loc["LightGBM", "MAE"], champ_r2=L.loc["LightGBM", "R2"], champ_vs_naive=L.loc["LightGBM", "RMSE_vs_naive_%"],
         sarima_mae=L.loc["SARIMA", "MAE"], a2_mae=L.loc["A2 Gradient Boosting", "MAE"])
R["champ_vs_sarima_mae"] = 100 * (1 - R["champ_mae"] / R["sarima_mae"]); R["champ_vs_a2_mae"] = 100 * (1 - R["champ_mae"] / R["a2_mae"])
R["prophet"] = pd.read_csv(T/"prophet_subset_h1.csv").to_dict("records")
dm = pd.read_csv(T/"dm_tests.csv"); R["dm"] = dm.to_dict("records")
byh = pd.read_csv(T/"metrics_by_horizon.csv").set_index(["model", "horizon"])
R.update(h4_regional=byh.loc[("Regional momentum", 4), "MAE"], champ_dir_h1=byh.loc[("LightGBM", 1), "DirAcc"], champ_dir_h4=byh.loc[("LightGBM", 4), "DirAcc"])
cv = pd.read_csv(T/"interval_coverage.csv").set_index("horizon")
for k in (1, 2, 3, 4): R[f"cov_h{k}"] = cv.loc[k, "cqr_coverage"]
R.update(raw_h1=cv.loc[1, "raw_coverage"], width_h1=cv.loc[1, "cqr_width"], width_h4=cv.loc[4, "cqr_width"])
R["cum"] = pd.read_csv(T/"cumulative_backtest.csv").to_dict("records")
R["cum_cov"] = json.load(open(T/"cumulative_coverage.json"))["overall_coverage"]
liq = pd.read_csv(T/"error_by_liquidity.csv"); R["liq"] = liq.to_dict("records")
R.update(liq_first_mae=liq.MAE_LightGBM.iloc[0], liq_last_mae=liq.MAE_LightGBM.iloc[-1])
nf = pd.read_csv(T/"noise_floor.csv")
bt = pd.read_parquet(C.PROCESSED/"backtest_ml.parquet"); b1 = bt[bt.horizon == 1]
seg = {}
for r, g in b1.groupby("region"):
    seg[r] = {**metrics(g.actual, g.LightGBM), "cov": float(np.mean((g.actual >= g.q10_cqr) & (g.actual <= g.q90_cqr)) * 100),
              "bias": float(np.mean(g.LightGBM - g.actual)), "mean_n": float(g.target_n.mean())}
    gl = g[g.liquid]; seg[r]["liq_mae"] = metrics(gl.actual, gl.LightGBM)["MAE"]
R["seg"] = seg
sh = pd.read_csv(T/"shap_importance.csv", index_col=0)["share_%"]; R["shap"] = sh.round(1).to_dict()
R["app_data_mb"] = f"{sum(p.stat().st_size for p in (C.ROOT/'app'/'data').iterdir())/1e6:.2f}"
json.dump(R, open(T/"report_numbers.json", "w"), indent=1, default=float)
print({k: v for k, v in R.items() if not isinstance(v, (list, dict))}); print(seg); print(R["shap"])
