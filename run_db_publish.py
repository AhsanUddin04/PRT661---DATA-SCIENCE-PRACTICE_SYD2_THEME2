"""Publish forecasts + model registry to PostgreSQL."""
import sys, os, json, time; sys.path.insert(0, "src")
import pandas as pd
from sqlalchemy import text
from prt661 import config as C, db
eng = db.engine(os.environ["DATABASE_URL"])
t = time.time(); fc = pd.read_parquet(C.PROCESSED/"forecasts.parquet"); n = db.load_forecasts(eng, fc); db.log_run(eng, "publish_forecasts", t, "ok", len(fc), n)
reg = json.load(open(C.MODELS/"model_registry.json")); bp = json.load(open(C.MODELS/"best_params.json"))["LightGBM"]
with eng.begin() as c:
    c.execute(text("TRUNCATE model_registry"))
    for r in reg:
        c.execute(text("""INSERT INTO model_registry (model_name, model_version, horizon, target, trained_through, artefact_path,
            artefact_sha256, params_json, backtest_json, is_champion) VALUES (:n,:v,:h,:t,:d,:p,:s,CAST(:pj AS JSONB),CAST(:bj AS JSONB),TRUE)"""),
            dict(n=r["model_name"], v=r["model_version"], h=r["horizon"], t=r["target"], d=r["trained_through"], p=r["artefact_path"],
                 s=r["artefact_sha256"], pj=json.dumps(bp), bj=json.dumps({"n_train": r["n_train"], "cqr_margin": r["cqr_margin"]})))
with eng.connect() as c:
    print(c.execute(text("select model_name, horizon, trained_through, left(artefact_sha256,12) from model_registry order by horizon")).fetchall())
    print("forecasts:", c.execute(text("select count(*) from forecasts")).scalar())
