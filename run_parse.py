import sys, time; sys.path.insert(0, "src")
from prt661 import config as C, parsing
t=time.time()
df = parsing.parse_all(C.RAW_NSW)
print("TOTAL B-records:", len(df), "in", round(time.time()-t), "s")
df.to_parquet(C.PROCESSED/"raw_sales.parquet", index=False)
