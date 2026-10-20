# Security, privacy and ethics controls

| Risk | Control | Where |
|---|---|---|
| Re-identification of individual sales | Public outputs aggregate to suburb-quarter; cells with <5 sales suppressed | `v_public_suburb_quarter`, `config.MIN_CELL_SIZE_PUBLISH`, app |
| Over-broad database access | Group roles + personal logins; analysts cannot read `raw_sales` (addresses); app role reads only forecasts & public view | `database/schema_v2.sql`, `create_member_logins.sql` |
| Credentials in Git | Passwords supplied at run time (`psql -v`), `DATABASE_URL` via env / GitHub Secrets; `.env` git-ignored | CI, `.gitignore` |
| Silent corruption on load | COPY in a single transaction (all-or-nothing); every stage logged to `pipeline_runs` | `db.py` |
| Misleading forecasts | Every forecast shows a calibrated P10–P90 band and a reliability label; plain-language accuracy note; "not a valuation" disclaimer | app, `forecast.py` |
| Look-ahead bias | Automated test perturbs future data and asserts features at the origin are unchanged | `tests/test_pipeline.py` |
| Container compromise | App image runs as non-root user, contains no raw data and no DB credentials | `Dockerfile` |
| Licence compliance | NSW VG and ABS data used under CC BY 4.0 with attribution in app footer and report | `docs/DATA_SOURCES.md` |
