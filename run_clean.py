import sys, time, json; sys.path.insert(0, "src")
import pandas as pd
from prt661 import config as C, cleaning
raw = pd.read_parquet(C.PROCESSED/"raw_sales.parquet")
t=time.time()
clean, counts = cleaning.clean_sales(raw)
print(json.dumps(counts, indent=1), round(time.time()-t),"s")
clean.to_parquet(C.PROCESSED/"cleaned_sales.parquet", index=False)
json.dump(counts, open(C.TABLES/"cleaning_reconciliation.json","w"), indent=1)
print(clean.is_strata.mean(), clean.suburb.nunique(), clean.quarter.min(), clean.quarter.max())
