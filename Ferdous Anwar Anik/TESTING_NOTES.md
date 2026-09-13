# How these scripts were tested

`data_cleaning.py` and `data_loading.py` were verified end-to-end before
being added to this repo, not just checked for valid syntax:

## data_cleaning.py
Tested against a synthetic 520-row raw dataset with real defects injected
on purpose: 10 corrupted dates, 20 duplicate re-publications, 15 sales
under the $10,000 floor, and 8 extreme-price outliers in one suburb.
Verified that:
- exactly 10 corrupted-date rows were removed
- exactly 20 duplicate rows were removed (by `dealing_number`)
- exactly 15 under-floor rows were removed
- the injected outliers were **flagged**, not deleted, and remained in the
  output with `is_outlier_flag = True`
- the output columns exactly match the `cleaned_sales` table shape in
  `schema.sql`

## data_loading.py
Tested against a **real, running PostgreSQL 16 instance** with the actual
`schema.sql` loaded (not a mock or SQLite substitute):
- loaded 500 raw rows into `raw_sales`, queried the count back — matched
- ran the cleaned rows through `load_cleaned_sales`, queried the count
  back — matched
- ran the exact same load a second time to confirm the `ON CONFLICT ...
  DO UPDATE` upsert logic works — row count stayed the same instead of
  duplicating, confirming re-running the pipeline is safe

## What to do before your real run
Set `DATABASE_URL` to point at your actual database:
```bash
export DATABASE_URL="postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>"
```
Then run, e.g.:
```bash
python data_loading.py path/to/raw_sales_export.csv
```
