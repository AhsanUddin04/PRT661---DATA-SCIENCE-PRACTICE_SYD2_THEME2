import sys, json, time; sys.path.insert(0, "src")
import numpy as np, pandas as pd
from prt661 import config as C, features as F, models as M
from prt661.evaluation import metrics
rng = np.random.default_rng(42)
fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
d = F.horizon_frame(fs, 1); d = d[d.target.notna() & (d.quarter >= "2014-01-01")]
pre = fs[(fs.quarter < "2024-07-01") & (fs.n_sales > 0)]
liq = pre.groupby("suburb").n_sales.mean(); liquid = set(liq[liq >= 20].index)
X = F.FEATURES + F.SEASONAL
tr = d[d.target_quarter <= "2022-04-01"]; va = d[(d.target_quarter >= "2022-07-01") & (d.target_quarter <= "2024-04-01") & d.suburb.isin(liquid)]
w = M.sample_weight(tr.target_n)
rows = []
def ev(name, model, params, fitkw):
    t=time.time(); model.fit(tr[X], tr.target, **fitkw); m = metrics(va.target, model.predict(va[X]))
    rows.append({"model": name, "params": json.dumps(params), **{k: round(v,3) for k,v in m.items()}, "sec": round(time.time()-t,1)})
    print(name, params, round(m["RMSE"],3), round(m["MAE"],3), flush=True)
for i in range(20):
    p = dict(learning_rate=float(rng.choice([0.01,0.02,0.03,0.05])), num_leaves=int(rng.choice([15,31,63])),
             min_child_samples=int(rng.choice([20,50,100,200])), n_estimators=int(rng.choice([300,600,1000])),
             colsample_bytree=float(rng.choice([0.5,0.7,0.9])), reg_lambda=float(rng.choice([0,1,5,20])),
             alpha=float(rng.choice([5.0,10.0,15.0,25.0])))
    ev("LightGBM", M.lightgbm(**p), p, {"sample_weight": w})
for i in range(14):
    p = dict(learning_rate=float(rng.choice([0.01,0.02,0.03,0.05])), max_depth=int(rng.choice([3,4,5,6,8])),
             min_child_weight=int(rng.choice([5,20,50,100])), n_estimators=int(rng.choice([300,600,1000])),
             colsample_bytree=float(rng.choice([0.5,0.7,0.9])), reg_lambda=float(rng.choice([1,5,20])),
             huber_slope=float(rng.choice([5.0,10.0,15.0,25.0])))
    ev("XGBoost", M.xgboost(**p), p, {"sample_weight": w})
for depth, leaf in [(8,50),(12,30),(16,20),(None,50)]:
    p = dict(max_depth=depth, min_samples_leaf=leaf)
    ev("Random forest", M.random_forest(**p), p, {"randomforestregressor__sample_weight": w})
for a in [1, 10, 100, 1000]:
    ev("Ridge", M.ridge(a), {"alpha": a}, {"ridge__sample_weight": w})
for eps in [1.35, 2.0]:
    ev("Huber regression", M.huber(eps), {"epsilon": eps}, {"huberregressor__sample_weight": w})
r = pd.DataFrame(rows); r.to_csv(C.TABLES/"tuning_hparams.csv", index=False)
best = r.sort_values("RMSE").groupby("model").head(1)
print(best[["model","params","RMSE","MAE","DirAcc"]].to_string())
json.dump({m: json.loads(p) for m, p in zip(best.model, best.params)}, open(C.MODELS/"best_params.json","w"), indent=1)
