"""Publish the small, privacy-filtered artefacts the web app reads (app/data/)."""
import sys, json; sys.path.insert(0, "src")
import pandas as pd
from prt661 import config as C
A = C.ROOT / "app" / "data"; A.mkdir(parents=True, exist_ok=True)
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
fc = pd.read_parquet(C.PROCESSED/"forecasts.parquet")
ok = (fs.n_sales >= C.MIN_CELL_SIZE_PUBLISH) & (fs.is_partial_quarter == 0) & fs.suburb.isin(fc.suburb)
fs.loc[ok, ["suburb", "quarter", "n_sales", "median_price"]].to_parquet(A/"history.parquet", index=False)
fc.to_parquet(A/"forecasts.parquet", index=False)
clean = pd.read_parquet(C.PROCESSED/"cleaned_sales.parquet", columns=["suburb", "quarter", "purchase_price", "is_outlier_flag"])
reg = fs.drop_duplicates("suburb").set_index("suburb").region
clean = clean[~clean.is_outlier_flag]; clean["region"] = clean.suburb.map(reg)
r = clean.groupby(["region", "quarter"]).purchase_price.median().rename("median_price").reset_index()
r = r[(r.quarter >= "2014-01-01") & (r.quarter < fs.quarter.max())]
r.to_parquet(A/"region_history.parquet", index=False)
lb = pd.read_csv(C.TABLES/"leaderboard_h1_liquid.csv")[["model", "RMSE", "MAE", "R2", "DirAcc", "N"]]
lb.to_csv(A/"leaderboard.csv", index=False)
pd.read_csv(C.TABLES/"metrics_by_horizon.csv").to_csv(A/"metrics_by_horizon.csv", index=False)
cv = pd.read_csv(C.TABLES/"interval_coverage.csv")
cv[["horizon", "cqr_coverage", "cqr_width", "raw_coverage", "N"]].round(1).rename(columns={
    "cqr_coverage": "Coverage % (calibrated)", "cqr_width": "Mean width (pp)", "raw_coverage": "Coverage % (uncalibrated)"}
    ).to_csv(A/"interval_coverage.csv", index=False)
rec = json.load(open(C.TABLES/"cleaning_reconciliation.json"))
cumcov = json.load(open(C.TABLES/"cumulative_coverage.json"))["overall_coverage"] if (C.TABLES/"cumulative_coverage.json").exists() else 80.0
anchor = fc.origin_quarter.iloc[0]
meta = {"anchor_quarter": str(pd.Period(anchor, "Q")), "anchor_quarter_date": str(pd.Timestamp(anchor).date()),
        "model_version": fc.model_version.iloc[0], "n_sales_used": rec["cleaned_total"], "champion": "LightGBM",
        "test_window": "2024-Q3 to 2026-Q2", "cum_coverage": cumcov,
        "reconciliation": [{"Stage": k.replace("_", " "), "Rows": f"{v:,}"} for k, v in rec.items()]}
json.dump(meta, open(A/"meta.json", "w"), indent=1)
print({p.name: round(p.stat().st_size/1e6, 2) for p in A.iterdir()})
