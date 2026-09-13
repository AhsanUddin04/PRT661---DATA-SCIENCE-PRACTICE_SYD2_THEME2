"""
data_loading.py

Purpose: load raw and cleaned data into the PostgreSQL tables defined in
database/schema.sql (raw_sales, suburb_dim, abs_benchmark, cleaned_sales,
feature_store).

Set the connection string via an environment variable rather than hardcoding
credentials:
    export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/prt661_housing"
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

DB_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://prt661:prt661@localhost:5432/prt661_housing",
)


def get_engine(dsn: str = DB_DSN):
    return create_engine(dsn)


def load_raw_sales(df: pd.DataFrame, engine=None, if_exists: str = "append") -> int:
    """Load raw NSW Valuer General records into raw_sales.

    sale_id is auto-generated (BIGSERIAL) so it's dropped from the frame
    before loading if present.
    """
    engine = engine or get_engine()
    df = df.drop(columns=["sale_id"], errors="ignore")
    df.to_sql("raw_sales", engine, if_exists=if_exists, index=False, method="multi", chunksize=1000)
    return len(df)


def load_abs_benchmark(df: pd.DataFrame, engine=None, if_exists: str = "append") -> int:
    """Load the ABS Total Value of Dwellings series into abs_benchmark."""
    engine = engine or get_engine()
    df.to_sql("abs_benchmark", engine, if_exists=if_exists, index=False, method="multi", chunksize=1000)
    return len(df)


def load_cleaned_sales(df: pd.DataFrame, engine=None) -> int:
    """Upsert cleaned records into cleaned_sales (dealing_number is the
    primary key, so re-running this after a re-clean updates existing rows
    instead of erroring on the duplicate key).
    """
    engine = engine or get_engine()
    cols = list(df.columns)
    insert_cols = ", ".join(cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    update_cols = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "dealing_number")

    upsert_sql = text(f"""
        INSERT INTO cleaned_sales ({insert_cols})
        VALUES ({placeholders})
        ON CONFLICT (dealing_number) DO UPDATE SET {update_cols}
    """)

    records = df.to_dict(orient="records")
    with engine.begin() as conn:
        for i in range(0, len(records), 1000):
            conn.execute(upsert_sql, records[i:i + 1000])
    return len(records)


def load_feature_store(df: pd.DataFrame, engine=None) -> int:
    """Upsert engineered features into feature_store (composite primary key:
    suburb, postcode, quarter).
    """
    engine = engine or get_engine()
    cols = list(df.columns)
    insert_cols = ", ".join(cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    update_cols = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in ("suburb", "postcode", "quarter"))

    upsert_sql = text(f"""
        INSERT INTO feature_store ({insert_cols})
        VALUES ({placeholders})
        ON CONFLICT (suburb, postcode, quarter) DO UPDATE SET {update_cols}
    """)

    records = df.to_dict(orient="records")
    with engine.begin() as conn:
        for i in range(0, len(records), 1000):
            conn.execute(upsert_sql, records[i:i + 1000])
    return len(records)


def row_counts(engine=None) -> dict:
    """Quick sanity check: row counts for every table, useful after a load."""
    engine = engine or get_engine()
    tables = ["raw_sales", "suburb_dim", "abs_benchmark", "cleaned_sales", "feature_store"]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    return counts


if __name__ == "__main__":
    import sys
    from data_cleaning import clean_sales

    if len(sys.argv) < 2:
        print("Usage: python data_loading.py <raw_sales_export.csv>")
        sys.exit(1)

    engine = get_engine()
    raw_df = pd.read_csv(sys.argv[1])

    print(f"Loading {len(raw_df):,} raw records...")
    load_raw_sales(raw_df, engine)

    print("Cleaning...")
    cleaned_df, counts = clean_sales(raw_df)
    for k, v in counts.items():
        print(f"  {k}: {v:,}")

    print(f"Loading {len(cleaned_df):,} cleaned records...")
    load_cleaned_sales(cleaned_df, engine)

    print("\nRow counts by table:")
    for table, n in row_counts(engine).items():
        print(f"  {table}: {n:,}")
