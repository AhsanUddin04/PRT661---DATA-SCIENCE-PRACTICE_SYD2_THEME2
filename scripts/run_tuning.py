"""Hyper-parameter & design selection on a validation window that ENDS before the test window.
Train: target quarters <= 2022-Q2 | Validate: 2022-Q3 .. 2024-Q2 (8 quarters, h=1) | Test (untouched): 2024-Q3 .. 2026-Q2
"""
import sys, time, itertools; sys.path.insert(0, "src")
import pandas as pd
from prt661 import config as C, features as F, models as M
from prt661.evaluation import metrics

fs = pd.read_parquet(C.PROCESSED/"feature_store_v2.parquet")
d = F.horizon_frame(fs, 1)
d = d[d.target.notna() & (d.quarter >= "2014-01-01")]
pre = fs[(fs.quarter < "2024-07-01") & (fs.n_sales > 0)]
liq = pre.groupby("suburb").n_sales.mean(); liquid = set(liq[liq >= 20].index)
X_COLS = F.FEATURES + F.SEASONAL
tr = d[d.target_quarter <= "2022-04-01"]; va = d[(d.target_quarter >= "2022-07-01") & (d.target_quarter <= "2024-04-01")]
va_l = va[va.suburb.isin(liquid)]
print("train", len(tr), "valid(liquid)", len(va_l))
rows = []
def run(name, model, cols, train, y, w=None, **meta):
    t = time.time()
    model.fit(train[cols], y, **({"sample_weight": w} if w is not None and not hasattr(model, "steps") else
                                 ({f"{model.steps[-1][0]}__sample_weight": w} if w is not None else {})))
    p = model.predict(va_l[cols]); m = metrics(va_l.target, p)
    rows.append({"model": name, **meta, **{k: round(v, 3) for k, v in m.items()}, "sec": round(time.time()-t, 1)})
    print(rows[-1], flush=True)

# 1) design choices with a default LightGBM
for univ, wt, wins, obj in itertools.product(["all", "liquid"], [False, True], [False, True], ["l2", "huber"]):
    t = tr if univ == "all" else tr[tr.suburb.isin(liquid)]
    y = M.winsorise(t.target) if wins else t.target
    w = M.sample_weight(t.target_n) if wt else None
    run("LightGBM", M.lightgbm(objective=obj), X_COLS, t, y, w, universe=univ, weight=wt, winsor=wins, objective=obj)
pd.DataFrame(rows).to_csv(C.TABLES/"tuning_design.csv", index=False)
