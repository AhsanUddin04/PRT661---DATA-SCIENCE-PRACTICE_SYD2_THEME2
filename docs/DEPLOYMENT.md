# Deployment guide

## 1. Public web app (Streamlit Community Cloud — free, ~2 minutes)
1. Push this repository to GitHub (`main` branch).
2. Go to https://share.streamlit.io → **New app** → pick the repo, branch `main`, main file `app/app.py`.
3. Under *Advanced settings* set **Python 3.11** and requirements file `requirements-app.txt`.
4. Deploy. The app reads only `app/data/` — no secrets or database connection are needed.
5. Paste the public URL into README.md and the report's Evidence Locations table.

## 2. Docker (any host)
```bash
docker build -t prt661-app .
docker run -p 8501:8501 prt661-app      # http://localhost:8501
```
The image runs as a non-root user and contains no raw data and no credentials.

## 3. Activate CI and the weekly refresh
* Workflows live in `.github/workflows/`; they start running as soon as they are on GitHub.
* Add repository secret `DATABASE_URL` (Settings → Secrets → Actions) for the refresh job's DB load step
  (use the ETL role, never a superuser).
* Recommended branch protection on `main`: require 1 review and the `CI / test` check to pass.

## 4. Database
```bash
createdb prt661_housing
psql -d prt661_housing -f database/schema_a2.sql
psql -d prt661_housing -f database/schema_v2.sql
psql -d prt661_housing -v pw_ahsan=... -v pw_ferdous=... -v pw_raiyan=... -v pw_abrar=... -v pw_app=... \
     -f database/create_member_logins.sql
export DATABASE_URL=postgresql+psycopg2://ferdous_anik:...@localhost:5432/prt661_housing
python -m prt661.pipeline --stages load_db
```

## 5. Full reproduction from raw archives
```bash
pip install -r requirements.txt
python -m prt661.pipeline --stages acquire          # or place the 13 annual zips in data/raw/nsw/
make all                                            # parse → clean → features → back-test → forecast → report assets
```
Approximate run times (2 CPU cores): parse 30 s · clean 8 s · features 11 s · ML back-test ~90 min ·
SARIMA back-test ~2–3 h · Prophet sample ~30 min · forecast 3 min.
