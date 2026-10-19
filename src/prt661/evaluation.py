"""Forecast accuracy metrics and significance tests."""
from __future__ import annotations

import numpy as np
from scipy import stats


def metrics(actual, pred, weights=None) -> dict:
    a = np.asarray(actual, float); p = np.asarray(pred, float)
    m = ~(np.isnan(a) | np.isnan(p))
    a, p = a[m], p[m]
    e = a - p
    out = {
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "MAE": float(np.mean(np.abs(e))),
        "MedAE": float(np.median(np.abs(e))),
        "R2": float(1 - np.sum(e ** 2) / np.sum((a - a.mean()) ** 2)),
        "DirAcc": float(np.mean(np.sign(a) == np.sign(p)) * 100),
        "N": int(m.sum()),
    }
    if weights is not None:
        w = np.asarray(weights, float)[m]
        out["wMAE"] = float(np.sum(w * np.abs(e)) / np.sum(w))
    return out


def diebold_mariano(actual, pred_a, pred_b, h: int = 1, power: int = 2) -> tuple[float, float]:
    """DM test (Harvey-Leybourne-Newbold small-sample correction).
    Negative statistic => model A more accurate than B."""
    a = np.asarray(actual, float); pa = np.asarray(pred_a, float); pb = np.asarray(pred_b, float)
    m = ~(np.isnan(a) | np.isnan(pa) | np.isnan(pb))
    d = np.abs(a[m] - pa[m]) ** power - np.abs(a[m] - pb[m]) ** power
    n = len(d)
    dbar = d.mean()
    gamma = [np.mean((d[k:] - dbar) * (d[: n - k] - dbar)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    dm = dbar / np.sqrt(var)
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = dm * hln
    p = 2 * stats.t.sf(np.abs(stat), df=n - 1)
    return float(stat), float(p)


def interval_scores(actual, lo, hi, alpha: float = 0.2) -> dict:
    a = np.asarray(actual, float); lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    m = ~(np.isnan(a) | np.isnan(lo) | np.isnan(hi))
    a, lo, hi = a[m], lo[m], hi[m]
    cover = (a >= lo) & (a <= hi)
    width = hi - lo
    # Winkler / interval score (lower is better)
    score = width + (2 / alpha) * ((lo - a) * (a < lo) + (a - hi) * (a > hi))
    return {"coverage": float(cover.mean() * 100), "mean_width": float(width.mean()),
            "median_width": float(np.median(width)), "interval_score": float(score.mean()), "N": int(m.sum())}
