import sys, json; sys.path.insert(0, "src")
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
from prt661 import config as C, backtest
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
bp = json.load(open(C.MODELS/"best_params.json"))
preds, log = backtest.run(fs, best_params=bp)
preds.to_parquet(C.PROCESSED/"backtest_ml.parquet", index=False)
pd.DataFrame(log).to_csv(C.TABLES/"backtest_fold_log.csv", index=False)
print("done", len(preds))
