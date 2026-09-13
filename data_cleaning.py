import pandas as pd
import numpy as np


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse the raw contract_date/settlement_date strings.

    The NSW Valuer General format is DD;MM;CCYY (e.g. '15;03;2023'), but a
    small number of records have unparseable/corrupted values, which we
    turn into NaT rather than raise on.
    """
    return pd.to_datetime(series, format="%d;%m;%Y", errors="coerce")


def clean_sales(raw_df: pd.DataFrame, price_floor: int = 10_000, iqr_multiplier: float = 1.5) -> tuple[pd.DataFrame, dict]:
    """Run the full cleaning pipeline described in report Section 3.4.

    Returns (cleaned_df, counts) where counts has keys:
        raw_total, corrupted_dates_removed, duplicates_removed,
        price_floor_removed, outliers_flagged, cleaned_total
    """
    counts = {"raw_total": len(raw_df)}
    df = raw_df.copy()

    # --- Rule 1: corrupted dates -------------------------------------
    df["contract_date"] = _parse_dates(df["contract_date"])
    df["settlement_date"] = _parse_dates(df["settlement_date"])
    before = len(df)
    df = df.dropna(subset=["contract_date"])
    counts["corrupted_dates_removed"] = before - len(df)

    # --- Rule 2: duplicate weekly re-publications ---------------------
    before = len(df)
    df = df.sort_values("download_datetime").drop_duplicates(subset=["dealing_number"], keep="first")
    counts["duplicates_removed"] = before - len(df)

    # --- Rule 3: price floor ------------------------------------------
    before = len(df)
    df = df[df["purchase_price"] >= price_floor]
    counts["price_floor_removed"] = before - len(df)

    # --- Derived field: price per sqm ---------------------------------
    df["price_per_sqm"] = np.where(
        (df["area"].notna()) & (df["area"] > 0),
        df["purchase_price"] / df["area"],
        np.nan,
    )

    # --- Rule 4: suburb-quarter outlier flagging (retained, not removed) ---
    # Implemented with groupby().transform() rather than groupby().apply() so
    # it works the same way across pandas versions (recent pandas releases
    # changed/removed how apply() handles the grouping columns).
    df["quarter"] = df["contract_date"].dt.to_period("Q").dt.start_time

    def _iqr_outlier_mask(s: pd.Series) -> pd.Series:
        valid = s.dropna()
        if len(valid) < 4:  # not enough points in this suburb-quarter for a meaningful IQR
            return pd.Series(False, index=s.index)
        q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
        return (s < lower) | (s > upper)

    df["is_outlier_flag"] = (
        df.groupby(["suburb", "postcode", "quarter"])["price_per_sqm"]
        .transform(_iqr_outlier_mask)
        .fillna(False)
        .astype(bool)
    )
    counts["outliers_flagged"] = int(df["is_outlier_flag"].sum())

    # --- Shape to match cleaned_sales schema ---------------------------
    cleaned = df[[
        "dealing_number", "district_code", "property_id", "suburb", "postcode",
        "contract_date", "settlement_date", "purchase_price", "area", "area_type",
        "price_per_sqm", "zoning", "is_outlier_flag",
    ]].reset_index(drop=True)

    counts["cleaned_total"] = len(cleaned)
    return cleaned, counts


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_cleaning.py <raw_sales_export.csv> [output.csv]")
        sys.exit(1)

    raw = pd.read_csv(sys.argv[1])
    cleaned_df, run_counts = clean_sales(raw)

    print("Cleaning summary:")
    for k, v in run_counts.items():
        print(f"  {k}: {v:,}")

    out_path = sys.argv[2] if len(sys.argv) > 2 else "cleaned_sales.csv"
    cleaned_df.to_csv(out_path, index=False)
    print(f"Wrote {len(cleaned_df):,} rows to {out_path}")
