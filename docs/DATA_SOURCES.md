# Data sources and provenance

| Dataset | Publisher / URL | Accessed | Licence | Used as |
|---|---|---|---|---|
| NSW Property Sales Information — bulk annual archives 2014–2025 and weekly archives 2026 (to 31 Aug 2026) | NSW Valuer General, https://valuation.property.nsw.gov.au/embed/propertySalesInformation | 6 Sep 2026 | CC BY 4.0 (attribution: © State of NSW, Valuer General) | Primary record-level source (`raw_sales`, 2,762,903 records) |
| Total Value of Dwellings, Australia (cat. 6432.0), tables 643201 & 643202 | Australian Bureau of Statistics | 6 Sep 2026 | CC BY 4.0 | State/region benchmark (`abs_benchmark`, 97 quarters); used lagged one quarter |
| Residential Property Price Indexes (archived, to Dec 2021) | Australian Bureau of Statistics | Aug 2026 | CC BY 4.0 | Historical context only (A1) |

Raw archives are not committed (≈180 MB). `python -m prt661.pipeline --stages acquire` re-downloads
them; `data/raw/` and `data/processed/` are git-ignored. No buyer or vendor names exist in the source files.
