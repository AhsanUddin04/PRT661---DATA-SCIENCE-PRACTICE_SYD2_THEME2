"""Cleaning pipeline (A2 §3.4) — now covering every rule, in the documented order.

The A2 repository version of this module omitted two rules that the report
described (residential-only filter and analysis-window restriction) and
de-duplicated on the *earliest* download rather than the most recent one.
Both are corrected here; the counts reproduce Table 3.1 of the A2 report.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def iqr_outlier_flag(df: pd.DataFrame, keys: list[str], col: str, k: float = 1.5,
                     min_n: int = 4) -> pd.Series:
    """Vectorised Tukey fence per group (≈60x faster than groupby.apply on 2M rows)."""
    g = df.groupby(keys, sort=False)[col]
    stats = g.quantile([0.25, 0.75]).unstack()
    stats.columns = ["q1", "q3"]
    stats["n"] = g.count()
    m = df[keys].merge(stats, left_on=keys, right_index=True, how="left")
    iqr = m["q3"] - m["q1"]
    out = ((df[col].values < (m["q1"] - k * iqr).values) |
           (df[col].values > (m["q3"] + k * iqr).values)) & (m["n"].values >= min_n)
    return pd.Series(np.asarray(out, dtype=bool), index=df.index)


def clean_sales(raw: pd.DataFrame,
                price_floor: int = C.PRICE_FLOOR,
                iqr_multiplier: float = C.IQR_MULTIPLIER,
                window=(C.WINDOW_START, C.WINDOW_END)) -> tuple[pd.DataFrame, dict]:
    """Return (cleaned_df, reconciliation_counts)."""
    counts = {"raw_parsed": len(raw)}
    df = raw

    # 1. Weekly re-publication duplicates: keep the most recent copy per dealing
    before = len(df)
    df = (df.sort_values(["download_datetime", "sale_counter"])
            .drop_duplicates(subset="dealing_number", keep="last"))
    counts["duplicates_removed"] = before - len(df)

    # 2. Residential dwellings only
    before = len(df)
    df = df[df["nature_of_property"].str.strip() == C.RESIDENTIAL_CODE]
    counts["non_residential_removed"] = before - len(df)

    # 3. Analysis window on settlement date (also drops unparseable/mistyped dates)
    before = len(df)
    lo, hi = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    df = df[df["settlement_date"].between(lo, hi)]
    counts["outside_window_removed"] = before - len(df)

    # 4. Nominal / non-arm's-length proxy
    before = len(df)
    df = df[df["purchase_price"] >= price_floor]
    counts["price_floor_removed"] = before - len(df)

    df = df.copy()
    # price per sqm only where land area is recorded in square metres (A4: hectare
    # lots are rural blocks whose $/sqm is not comparable, so they are left NaN)
    df["price_per_sqm"] = np.where(
        (df["area"] > 0) & (df["area_type"].str.strip() == "M"),
        df["purchase_price"] / df["area"], np.nan)
    df["quarter"] = df["settlement_date"].dt.to_period("Q").dt.start_time
    # A4 addition: dwelling type from the strata lot field (strata lot => unit/apartment)
    df["is_strata"] = df["strata_lot_number"].fillna("").astype(str).str.strip().ne("")

    # 5. Outliers are flagged, never deleted (Tukey 1.5xIQR within suburb-quarter, n>=4)
    df["is_outlier_flag"] = iqr_outlier_flag(df, ["suburb", "quarter"], "price_per_sqm", iqr_multiplier)
    counts["outliers_flagged"] = int(df["is_outlier_flag"].sum())
    counts["cleaned_total"] = len(df)
    counts["total_removed"] = counts["raw_parsed"] - counts["cleaned_total"]
    keep = ["dealing_number", "district_code", "property_id", "suburb", "postcode",
            "contract_date", "settlement_date", "purchase_price", "area", "area_type",
            "price_per_sqm", "zoning", "is_strata", "quarter", "is_outlier_flag"]
    return df[keep].reset_index(drop=True), counts
