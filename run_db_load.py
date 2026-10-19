import sys, time, os; sys.path.insert(0, "src")
import pandas as pd
from sqlalchemy import text
from prt661 import config as C, db
eng = db.engine(os.environ["DATABASE_URL"])
db.run_sql_file(eng, C.ROOT/"database"/"schema_v2.sql")
for stage, loader, path in [("load_raw_sales", db.load_raw_sales, "raw_sales.parquet"),
                            ("load_feature_store_v2", db.load_feature_store_v2, "feature_store_v2.parquet")]:
    t = time.time(); df = pd.read_parquet(C.PROCESSED/path); n = loader(eng, df)
    db.log_run(eng, stage, t, "ok", len(df), n); print(stage, n, round(time.time()-t,1), "s")
t=time.time(); fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet"); n=db.load_suburb_dim(eng, fs); db.log_run(eng,"load_suburb_dim",t,"ok",None,n); print("suburb_dim", n)
with eng.connect() as c:
    for tname in ["raw_sales","suburb_dim","abs_benchmark","cleaned_sales","feature_store","feature_store_v2","pipeline_runs"]:
        print(f"{tname:18s}", c.execute(text(f"select count(*) from {tname}")).scalar())
