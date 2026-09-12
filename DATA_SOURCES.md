# Data Sources

This log records where every dataset used in this project came from, when it
was accessed, and under what licence — required for Assessment 2 governance
and referenced in Section 3.14 (Ethics, Privacy and Security) of the report.

| Dataset | Source | Access date | Licence / terms | Notes |
|---|---|---|---|---|
| NSW property sales (bulk weekly/annual extracts) | NSW Valuer General, data.nsw.gov.au | [TEAM: fill in actual date] | NSW Government Open Data licence (attribution required) | Raw files kept locally only — not pushed to GitHub due to size (~180MB). See `database/schema.sql` for the `raw_sales` table structure they load into. |
| ABS Total Value of Dwellings | Australian Bureau of Statistics | [TEAM: fill in actual date] | Creative Commons Attribution 4.0 | Used as the independent state-level benchmark (`abs_benchmark` table / `ABS_NSW_benchmark_quarterly.csv`). |
| ABS Residential Property Price Indexes (archived) | Australian Bureau of Statistics | [TEAM: fill in actual date] | Creative Commons Attribution 4.0 | Historical context only, referenced in Assessment 1. |

## Why the raw files aren't in this repository

The raw NSW Valuer General weekly/annual archives total roughly 180MB across
hundreds of small zip files, and the full cleaned-sales export is ~78MB —
both well over what's practical to store in a plain Git repository. Instead:

- `database/schema.sql` documents the exact table structure the raw and
  cleaned data are loaded into.
- `data/NSW_cleaned_sales_SAMPLE_2000rows.csv` is a representative sample of
  the cleaned output, small enough to commit, so the shape of the data is
  visible without downloading everything.
- The acquisition script (see `src/`, once added) re-downloads the raw files
  directly from data.nsw.gov.au on request, so nothing is lost by leaving
  the raw archives out of version control.

## Personally identifiable information

No individual buyer/seller names are collected or stored — only property
address, sale price, date, and property attributes, which is itself public
record under the source licence (Section 3.14).
