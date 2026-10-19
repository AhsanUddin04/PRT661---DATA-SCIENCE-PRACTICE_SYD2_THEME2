"""PostgreSQL loading via COPY (fast, transactional) with an audit trail.

Replaces A2's row-by-row ``to_sql`` loader. Each stage writes a row to
``pipeline_runs`` so the database itself records what was loaded and when.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine, text

from . import config as C


def engine(url: str | None = None):
    return create_engine(url or C.DATABASE_URL, future=True)


def run_sql_file(eng, path) -> None:
    raw = eng.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(open(path).read())
        raw.commit()
    finally:
        raw.close()


def copy_df(eng, df: pd.DataFrame, table: str, truncate: bool = True) -> int:
    """Bulk-load a DataFrame with COPY inside one transaction (all-or-nothing)."""
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)
    cols = ",".join(df.columns)
    raw = eng.raw_connection()
    try:
        with raw.cursor() as cur:
            if truncate:
                cur.execute(f"TRUNCATE {table}")
            cur.copy_expert(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    return len(df)


def log_run(eng, stage: str, started: float, status: str, rows_in=None, rows_out=None, details=None):
    with eng.begin() as con:
        con.execute(text(
            "INSERT INTO pipeline_runs (stage, started_at, finished_at, status, rows_in, rows_out, details_json) "
            "VALUES (:s, :a, :b, :st, :ri, :ro, CAST(:d AS JSONB))"),
            dict(s=stage, a=datetime.fromtimestamp(started, timezone.utc), b=datetime.now(timezone.utc),
                 st=status, ri=rows_in, ro=rows_out, d=json.dumps(details or {}, default=str)))


def load_raw_sales(eng, raw: pd.DataFrame) -> int:
    cols = ["district_code", "property_id", "sale_counter", "download_datetime", "house_number",
            "street_name", "suburb", "postcode", "area", "area_type", "contract_date", "settlement_date",
            "purchase_price", "zoning", "nature_of_property", "primary_purpose", "dealing_number",
            "source_file", "source_year_archive"]
    d = raw[cols].copy()
    for c in ("property_id", "sale_counter", "postcode", "purchase_price"):
        d[c] = d[c].astype("Int64")
    d["download_datetime"] = d["download_datetime"].dt.strftime("%Y-%m-%d %H:%M")
    for c in ("contract_date", "settlement_date"):
        d[c] = d[c].dt.strftime("%Y-%m-%d")
    return copy_df(eng, d, "raw_sales")


def load_suburb_dim(eng, fs: pd.DataFrame) -> int:
    d = (fs.dropna(subset=["postcode"]).drop_duplicates("suburb")[["suburb", "postcode", "region"]]
           .assign(postcode=lambda x: x.postcode.astype(int)))
    return copy_df(eng, d, "suburb_dim")


def load_feature_store_v2(eng, fs: pd.DataFrame) -> int:
    cols = ["suburb", "quarter", "postcode", "region", "n_sales", "median_price", "median_price_per_sqm",
            "strata_share", "qoq_pct_change", "yoy_pct_change", "region_qoq", "state_qoq",
            "abs_region_growth_lag1", "is_partial_quarter"]
    d = fs[cols].copy()
    d["postcode"] = d["postcode"].astype("Int64")
    d["quarter"] = d["quarter"].dt.strftime("%Y-%m-%d")
    return copy_df(eng, d, "feature_store_v2")


def load_forecasts(eng, fc: pd.DataFrame) -> int:
    d = fc.copy()
    for c in ("origin_quarter", "target_quarter"):
        d[c] = pd.to_datetime(d[c]).dt.strftime("%Y-%m-%d")
    return copy_df(eng, d, "forecasts")
