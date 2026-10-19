"""Central configuration for the PRT661 Sydn2-Theme2 forecasting pipeline.

Every threshold that changes a number in the report lives here, so a reviewer
can see (and the CHANGELOG can record) exactly which rule produced which count.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("PRT661_ROOT", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"
RAW_NSW = DATA / "raw" / "nsw"
PROCESSED = DATA / "processed"
EXTERNAL = DATA / "external"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"

ABS_CSV = EXTERNAL / "ABS_NSW_benchmark_quarterly.csv"

# ---- cleaning rules (Assessment 2, Section 3.4 — unchanged) -----------------
WINDOW_START = "2013-01-01"
WINDOW_END = "2026-09-30"
PRICE_FLOOR = 10_000
IQR_MULTIPLIER = 1.5
RESIDENTIAL_CODE = "R"

# ---- feature store ------------------------------------------------------------
COVID_START, COVID_END = "2020-01-01", "2021-10-01"
RATE_HIKE_START, RATE_HIKE_END = "2022-04-01", "2023-10-01"
# Sydney Greater Capital City postcode ranges (approximation flagged in A2 §3.7)
SYDNEY_POSTCODE_RANGES = [(2000, 2234), (2555, 2574), (2740, 2786)]

# ---- modelling ----------------------------------------------------------------
LIQUID_MIN_MEAN_SALES = 20      # A2 definition of a "liquid" suburb
MIN_SALES_FOR_TARGET = 5        # A4: suburb-quarters with <5 sales are not scored
N_TEST_QUARTERS = 8             # walk-forward window (identical for every model)
HORIZONS = (1, 2, 3, 4)
INTERVAL_ALPHA = 0.20           # 10th–90th percentile band (80% nominal coverage)
RANDOM_STATE = 42

# Privacy: never publish a suburb-quarter statistic built from fewer sales
MIN_CELL_SIZE_PUBLISH = 5

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://prt661_app@localhost:5432/prt661_housing"
)

for _p in (PROCESSED, MODELS, FIGURES, TABLES):
    _p.mkdir(parents=True, exist_ok=True)
