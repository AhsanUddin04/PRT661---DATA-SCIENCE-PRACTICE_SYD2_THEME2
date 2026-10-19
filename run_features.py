import sys, time; sys.path.insert(0, "src")
import pandas as pd
from prt661 import config as C, features as F
t=time.time()
clean = pd.read_parquet(C.PROCESSED/"cleaned_sales.parquet")
fs = F.build_feature_store(clean)
fs.to_parquet(C.PROCESSED/"feature_store_v2.parquet", index=False)
obs = fs[fs.n_sales>0]
print("grid rows", len(fs), "observed suburb-quarters", len(obs), "suburbs", fs.suburb.nunique(), round(time.time()-t),"s")
print("valid qoq targets", fs.qoq_pct_change.notna().sum())
print(fs[F.FEATURES].describe().T[["count","mean","std"]].round(2))
