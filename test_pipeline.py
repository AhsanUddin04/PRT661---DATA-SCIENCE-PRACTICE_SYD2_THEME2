"""Unit and integration tests for the A4 pipeline. Run: pytest -q"""
import io
import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from prt661 import cleaning, config as C, evaluation, features, models, parsing


# ------------------------------------------------------------------ parsing ---
def _dat(lines):
    return ("\n".join(lines) + "\n").encode("latin-1")


def test_parser_reads_nested_archives(tmp_path):
    b = "B;001;123;1;20240101 01:00;;;5;SMITH ST;TESTVILLE;2000;500;M;20231201;20231220;750000;R2;R;RESIDENCE;;;;;AB123;"
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as z:
        z.writestr("001_SALES_DATA_NNME_01012024.DAT", _dat(["A;RTSALEDATA;001;20240101 01:00;VALNET;", b,
                                                            "C;001;123;1;20240101 01:00;1/DP1;", "Z;3;1;0;0;"]))
    outer = tmp_path / "2024.zip"
    with zipfile.ZipFile(outer, "w") as z:
        z.writestr("2024/20240101.zip", inner.getvalue())
    df = parsing.coerce_types(parsing.parse_archive(outer, 2024))
    assert len(df) == 1
    r = df.iloc[0]
    assert r.suburb == "TESTVILLE" and r.purchase_price == 750000 and r.dealing_number == "AB123"
    assert r.settlement_date == pd.Timestamp("2023-12-20")


# ----------------------------------------------------------------- cleaning ---
def test_cleaning_rules_and_reconciliation(raw_df):
    raw = raw_df.copy()
    dup = raw.iloc[:20].copy(); dup["download_datetime"] += pd.Timedelta(days=7); dup["purchase_price"] += 1
    nonres = raw.iloc[20:35].copy(); nonres["nature_of_property"] = "V"; nonres["dealing_number"] += "V"
    old = raw.iloc[35:40].copy(); old["settlement_date"] = pd.Timestamp("1913-01-01"); old["dealing_number"] += "O"
    cheap = raw.iloc[40:47].copy(); cheap["purchase_price"] = 500.0; cheap["dealing_number"] += "C"
    raw = pd.concat([raw, dup, nonres, old, cheap], ignore_index=True)
    clean, n = cleaning.clean_sales(raw)
    assert n["duplicates_removed"] == 20
    assert n["non_residential_removed"] == 15
    assert n["outside_window_removed"] == 5
    assert n["price_floor_removed"] == 7
    removed = n["duplicates_removed"] + n["non_residential_removed"] + n["outside_window_removed"] + n["price_floor_removed"]
    assert n["raw_parsed"] - removed == n["cleaned_total"] == len(clean)
    # most recent re-publication kept
    kept = clean.set_index("dealing_number").loc[dup.dealing_number, "purchase_price"]
    assert (kept.values == dup.purchase_price.values).all()


def test_outliers_flagged_not_deleted(raw_df):
    raw = raw_df.copy()
    raw.loc[0, "purchase_price"] = 50_000_000
    clean, n = cleaning.clean_sales(raw)
    assert clean.loc[clean.dealing_number == raw.loc[0, "dealing_number"], "is_outlier_flag"].item()
    assert n["cleaned_total"] == len(raw)


# ----------------------------------------------------------------- features ---
@pytest.fixture
def fs(raw_df, monkeypatch):
    monkeypatch.setattr(features, "_load_abs", lambda: pd.DataFrame(
        {"quarter": pd.date_range("2017-01-01", "2024-01-01", freq="QS"),
         "median_price_house_sydney_qoq_pct": 1.0, "median_price_house_rest_nsw_qoq_pct": 2.0,
         "tvd_households_qoq_pct": 1.5}))
    clean, _ = cleaning.clean_sales(raw_df)
    return clean, features.build_feature_store(clean)


def test_grid_is_complete_and_qoq_never_spans_a_gap(fs, raw_df, monkeypatch):
    clean, _ = fs
    # delete one suburb-quarter entirely -> the next quarter's QoQ must be NaN, not a 2-quarter change
    gap_q = pd.Timestamp("2019-01-01")
    holed = clean[~((clean.suburb == "SUBURB0") & (clean.quarter == gap_q))]
    g = features.build_feature_store(holed)
    s0 = g[g.suburb == "SUBURB0"].set_index("quarter")
    assert s0.loc[gap_q, "n_sales"] == 0
    assert np.isnan(s0.loc[gap_q + pd.DateOffset(months=3), "qoq_pct_change"])
    assert g.groupby("suburb").size().nunique() == 1  # every suburb has every quarter


def test_partial_quarter_has_no_target(fs):
    _, g = fs
    last = g.quarter.max()
    assert g.loc[g.quarter == last, "qoq_pct_change"].isna().all()
    assert (g.loc[g.quarter == last, "is_partial_quarter"] == 1).all()


def test_features_do_not_look_ahead(fs):
    """Changing every sale AFTER the origin must not change any feature AT the origin."""
    clean, g = fs
    origin = pd.Timestamp("2020-01-01")
    future = clean.copy()
    future.loc[future.quarter > origin, "purchase_price"] *= 3
    g2 = features.build_feature_store(future)
    cols = [c for c in features.FEATURES if c not in ("state_qoq", "region_qoq")] + ["region_qoq", "state_qoq"]
    a = g[g.quarter == origin].set_index("suburb")[cols]
    b = g2[g2.quarter == origin].set_index("suburb")[cols]
    pd.testing.assert_frame_equal(a, b)
    # ...while the targets (which live in the future) do change
    assert not np.allclose(g[g.quarter == origin].target_h1, g2[g2.quarter == origin].target_h1)


def test_abs_regressor_is_lagged_one_quarter(fs):
    _, g = fs
    first_abs = pd.Timestamp("2017-01-01")
    row = g[g.quarter == first_abs]
    assert row.abs_region_growth_lag1.isna().all()  # Q1-2017 ABS value only usable from Q2-2017


# --------------------------------------------------------------- evaluation ---
def test_metrics_known_values():
    m = evaluation.metrics([1, -1, 2, 0.5], [1, 1, 2, 0.5])
    assert m["MAE"] == pytest.approx(0.5) and m["RMSE"] == pytest.approx(1.0)
    assert m["DirAcc"] == pytest.approx(75.0)


def test_interval_scores_coverage():
    s = evaluation.interval_scores([0, 1, 5], [-1, -1, -1], [1, 2, 2], alpha=0.2)
    assert s["coverage"] == pytest.approx(200 / 3)


def test_diebold_mariano_detects_better_model():
    rng = np.random.default_rng(1)
    y = rng.normal(size=500)
    good, bad = y + rng.normal(0, 0.3, 500), y + rng.normal(0, 1.0, 500)
    stat, p = evaluation.diebold_mariano(y, good, bad)
    assert stat < 0 and p < 0.01


def test_sample_weight_is_capped_sqrt():
    w = models.sample_weight(pd.Series([1, 4, 400]))
    assert np.allclose(w, [1, 2, 10])


# ---------------------------------------------------- reproduction of A2 ---
@pytest.mark.skipif(not (C.TABLES / "cleaning_reconciliation.json").exists(), reason="full data not present")
def test_full_run_reproduces_a2_table_3_1():
    n = json.load(open(C.TABLES / "cleaning_reconciliation.json"))
    assert n["raw_parsed"] == 2_762_903
    assert n["duplicates_removed"] == 237_770
    assert n["non_residential_removed"] == 429_788
    assert n["outside_window_removed"] == 995
    assert abs(n["price_floor_removed"] - 1_851) <= 1


@pytest.mark.skipif(not (C.PROCESSED / "forecasts.parquet").exists(), reason="forecasts not generated")
def test_published_forecasts_are_ordered_and_suppressed():
    fc = pd.read_parquet(C.PROCESSED / "forecasts.parquet")
    assert (fc.p10_pct <= fc.point_pct + 1e-9).all() and (fc.point_pct <= fc.p90_pct + 1e-9).all()
    assert fc.reliability.isin(["high", "medium", "low"]).all()
