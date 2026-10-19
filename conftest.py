import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _raw_rows(n_suburbs=6, n_quarters=20, per_q=12, seed=0):
    rng = np.random.default_rng(seed)
    rows, deal = [], 0
    quarters = pd.date_range("2018-01-01", periods=n_quarters, freq="QS")
    for s in range(n_suburbs):
        base = 600_000 * (1 + 0.2 * s)
        for qi, q in enumerate(quarters):
            for _ in range(per_q):
                deal += 1
                price = base * (1.01 ** qi) * rng.lognormal(0, 0.15)
                rows.append(dict(district_code="001", property_id=deal, sale_counter=1,
                                 download_datetime=q + pd.Timedelta(days=40), suburb=f"SUBURB{s}",
                                 postcode=2000 + s if s < 3 else 2800 + s, area=500.0, area_type="M",
                                 contract_date=q + pd.Timedelta(days=5), settlement_date=q + pd.Timedelta(days=30),
                                 purchase_price=float(round(price)), zoning="R2", nature_of_property="R",
                                 primary_purpose="RESIDENCE", strata_lot_number="", dealing_number=f"D{deal}",
                                 house_number="1", street_name="TEST ST", source_file="t", source_year_archive=2020))
    return pd.DataFrame(rows)


@pytest.fixture
def raw_df():
    return _raw_rows()
