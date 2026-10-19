import sys, json; sys.path.insert(0, "src")
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
from prt661 import config as C, forecast
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
fc, reg = forecast.train_and_forecast(fs, json.load(open(C.MODELS/"best_params.json")))
fc.to_parquet(C.PROCESSED/"forecasts.parquet", index=False)
json.dump(reg, open(C.MODELS/"model_registry.json","w"), indent=1)
print(len(fc), fc.suburb.nunique(), fc.reliability.value_counts().to_dict())
print(fc.groupby("horizon")[["point_pct","p10_pct","p90_pct"]].median().round(2))
print(fc[fc.suburb=="PARRAMATTA"].round(1).to_string())
