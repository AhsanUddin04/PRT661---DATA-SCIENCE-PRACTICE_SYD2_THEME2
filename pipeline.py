"""One-command pipeline orchestrator.

    python -m prt661.pipeline                # every stage, end to end
    python -m prt661.pipeline --from features --to forecast
    python -m prt661.pipeline --stages acquire parse clean   # weekly refresh job

Each stage reads the previous stage's artefact from data/processed/, so stages
can be re-run independently and the run is deterministic given the raw files.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date

import pandas as pd

from . import config as C

STAGES = ["acquire", "parse", "clean", "features", "load_db", "backtest", "forecast", "app_data"]


def stage_acquire():
    from . import acquisition
    acquisition.download_nsw_weekly(date(date.today().year, 1, 1), date.today(), output_dir=str(C.RAW_NSW / str(date.today().year)))
    acquisition.download_abs_total_value_of_dwellings(output_dir=str(C.EXTERNAL / "abs_xlsx"))


def stage_parse():
    from . import parsing
    df = parsing.parse_all(C.RAW_NSW)
    df.to_parquet(C.PROCESSED / "raw_sales.parquet", index=False)
    return {"rows_out": len(df)}


def stage_clean():
    from . import cleaning
    raw = pd.read_parquet(C.PROCESSED / "raw_sales.parquet")
    clean, counts = cleaning.clean_sales(raw)
    clean.to_parquet(C.PROCESSED / "cleaned_sales.parquet", index=False)
    json.dump(counts, open(C.TABLES / "cleaning_reconciliation.json", "w"), indent=1)
    return counts


def stage_features():
    from . import features
    fs = features.build_feature_store(pd.read_parquet(C.PROCESSED / "cleaned_sales.parquet"))
    fs.to_parquet(C.PROCESSED / "feature_store_v2.parquet", index=False)
    return {"rows_out": len(fs)}


def stage_load_db():
    from . import db
    eng = db.engine()
    db.run_sql_file(eng, C.ROOT / "database" / "schema_v2.sql")
    out = {}
    for stage, loader, f in [("raw_sales", db.load_raw_sales, "raw_sales.parquet"),
                             ("feature_store_v2", db.load_feature_store_v2, "feature_store_v2.parquet"),
                             ("suburb_dim", db.load_suburb_dim, "feature_store_v2.parquet")]:
        t = time.time(); n = loader(eng, pd.read_parquet(C.PROCESSED / f)); db.log_run(eng, f"load_{stage}", t, "ok", None, n)
        out[stage] = n
    fc = C.PROCESSED / "forecasts.parquet"
    if fc.exists():
        out["forecasts"] = db.load_forecasts(eng, pd.read_parquet(fc))
    return out


def stage_backtest():
    from . import backtest
    fs = pd.read_parquet(C.PROCESSED / "feature_store_v2.parquet")
    preds, log = backtest.run(fs, best_params=json.load(open(C.MODELS / "best_params.json")))
    preds.to_parquet(C.PROCESSED / "backtest_ml.parquet", index=False)
    return {"rows_out": len(preds)}


def stage_forecast():
    from . import forecast
    fs = pd.read_parquet(C.PROCESSED / "feature_store_v2.parquet")
    fc, reg = forecast.train_and_forecast(fs, json.load(open(C.MODELS / "best_params.json")))
    fc.to_parquet(C.PROCESSED / "forecasts.parquet", index=False)
    json.dump(reg, open(C.MODELS / "model_registry.json", "w"), indent=1)
    return {"rows_out": len(fc)}


def stage_app_data():
    import runpy
    runpy.run_path(str(C.ROOT / "scripts" / "build_app_data.py"), run_name="__main__")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", nargs="*", choices=STAGES)
    ap.add_argument("--from", dest="start", choices=STAGES, default="parse")
    ap.add_argument("--to", dest="end", choices=STAGES, default="app_data")
    a = ap.parse_args(argv)
    todo = a.stages or STAGES[STAGES.index(a.start): STAGES.index(a.end) + 1]
    for s in todo:
        if s == "load_db" and not os.environ.get("DATABASE_URL"):
            print("  [skip] load_db — DATABASE_URL not set"); continue
        t = time.time()
        print(f"[{s}] starting", flush=True)
        res = globals()[f"stage_{s}"]()
        print(f"[{s}] done in {time.time() - t:.0f}s {res or ''}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
