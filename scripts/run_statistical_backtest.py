"""Re-run SARIMA and Prophet for all liquid suburbs on the A4 common walk-forward window."""
import sys, time; sys.path.insert(0, "src")
from multiprocessing import Pool
import pandas as pd
from prt661 import config as C
from prt661.statistical import backtest_suburb

which = sys.argv[1]  # sarima | prophet
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
pre = fs[(fs.quarter < "2024-07-01") & (fs.n_sales > 0)]
liq = pre.groupby("suburb").n_sales.mean(); liquid = liq[liq >= C.LIQUID_MIN_MEAN_SALES].index
test_q = pd.date_range("2024-07-01", "2026-04-01", freq="QS")
origins = pd.date_range(test_q[0] - pd.DateOffset(months=12), test_q[-1] - pd.DateOffset(months=3), freq="QS")
if which == "prophet":  # Prophet is ~10x slower: stratified 150-suburb sample, as in A2
    reg = fs.drop_duplicates("suburb").set_index("suburb").region.reindex(liquid)
    liquid = pd.Index(reg.groupby(reg).sample(75, random_state=42).index if reg.value_counts().min() >= 75
                      else reg.sample(150, random_state=42).index)
jobs = [(s, g.set_index("quarter")["qoq_pct_change"], origins, which)
        for s, g in fs[fs.suburb.isin(liquid)].groupby("suburb")]
t = time.time()
with Pool(2) as p:
    res = [r for chunk in p.imap_unordered(backtest_suburb, jobs, chunksize=4) for r in chunk]
out = pd.DataFrame(res)
out = out[out.target_quarter.isin(test_q)]
out.to_parquet(C.PROCESSED/f"backtest_{which}.parquet", index=False)
print(which, len(jobs), "suburbs", len(out), "forecasts", round(time.time()-t), "s")
