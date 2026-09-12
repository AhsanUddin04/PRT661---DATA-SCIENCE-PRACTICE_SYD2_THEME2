# Australian House Price Forecasting
## PRT661 Data Science Practice — Sydn2, Theme 2

Forecasting residential property prices across NSW using cleaned historical
sales data and machine-learning / time-series analysis, with forecast
uncertainty presented alongside every prediction so users can interpret
results responsibly rather than treating them as guarantees.

**Status:** Assessment 2 — Progress Report and Development.
Assessment 1 covered project proposal and design; this stage adds a real
database, a working data-cleaning pipeline, three backtested model families,
and a working web application.

---

## Repository structure

| Folder / file | What's in it |
|---|---|
| `reports/` | The combined Assessment 2 PDF (includes the full Assessment 1 report), and the working Word draft |
| `database/schema.sql` | PostgreSQL table definitions (`raw_sales`, `suburb_dim`, `abs_benchmark`, `cleaned_sales`, `feature_store`) |
| `data/` | Modelling-ready CSV exports: feature store, backtest results, ABS benchmark, and a small cleaned-sales sample |
| `webapp/` | The working Streamlit web app (`app.py`) and its own copy of the data it needs to run |
| `docs/` | Architecture diagram, workflow diagram, data sources log, task allocation, sprint/planning records, changelog |
| `src/` *(to add)* | Data acquisition, cleaning, feature-engineering and model-training scripts — **see note below** |
| `models/` *(to add)* | Saved trained model files, if/when exported — **see note below** |

### Two folders the team still needs to add

- **`src/`** — the actual Python scripts that produced everything in `data/`
  (acquisition, cleaning, feature engineering, model training/backtesting).
  These exist somewhere on a team member's machine or in notebooks — they
  need to be added here so the repository is genuinely reproducible, not
  just a place where outputs are stored.
- **`models/`** — if any trained model files were saved (e.g. a pickled
  Gradient Boosting model via `joblib`), add them here. If none were saved,
  a short note in this folder saying so is better than leaving it implied.

## Running the web app

```bash
cd webapp
pip install -r requirements.txt
streamlit run app.py
```
See `webapp/README.md` for deployment instructions (Streamlit Community
Cloud, free, ~2 minutes).

## Environment / reproducibility

- Python 3.10+
- Install everything with `pip install -r webapp/requirements.txt`
  (extend this file if `src/` scripts need extra packages such as
  `sqlalchemy`, `psycopg2`, `statsmodels`, `prophet`, or `scikit-learn`)
- Database: PostgreSQL — load `database/schema.sql` to recreate the schema

## Project objectives

- Acquire publicly available Australian property-sales and housing data.
- Store and manage the collected data using an appropriate database system.
- Process and prepare the data for analysis.
- Apply statistical and machine-learning forecasting techniques.
- Identify important property, regional and time-related characteristics.
- Develop visualisations to communicate historical trends and forecasts.
- Present forecast uncertainty to help users interpret predictions responsibly.

## Problem statement

Property prices do not change uniformly across Australia. This project
investigates whether government property-sales data, combined with ABS
information, can be used to predict dwelling-price changes one to four
quarters ahead with an acceptable level of accuracy — and to communicate
that accuracy honestly rather than as a single misleading headline number.

## Data sources

See `docs/DATA_SOURCES.md` for the full provenance and licence log.

- **Primary:** NSW Valuer General property-sales bulk data (data.nsw.gov.au)
- **Supporting:** ABS Total Value of Dwellings; archived ABS Residential
  Property Price Indexes

## Architecture

See `docs/architecture_diagram.svg` for the full data-flow diagram, and
Section 3.2 of the report for the detailed write-up.

## Team members

| Team Member | Role |
|---|---|
| Ahsan Uddin | Project Lead / Data Acquisition |
| Ferdous Anwar Anik | Data Engineer |
| Mohd Yah-Ya Raiyan | Data Analyst |
| Abrar Bin Khaiyum | Visualisation & Documentation Lead |

Full contribution detail: `docs/task_allocation.md`. Sprint-by-sprint
planning: `docs/project_planning.md`. Material project changes since
Assessment 1: `docs/CHANGELOG.md`.

## Project management

Jira is used to manage sprint tasks and progress (see
`docs/workflow_diagram.svg`); GitHub is used for source code, documentation,
data-source records, and version control.

## Risk and governance

Key risks — single-state pilot generalisability, non-arm's-length sale
records, structural market breaks (COVID-19, rate changes), and uneven team
contribution after a member's withdrawal — are tracked with mitigations in
report Section 3.13.

## References

Australian Bureau of Statistics. (2026). *Total value of dwellings*.
https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings

Australian Bureau of Statistics. (2021). *Residential property price
indexes: Eight capital cities (archived)*.
https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/residential-property-price-indexes-eight-capital-cities

NSW Government. (2026). *How to find property sales information*.
https://www.nsw.gov.au/housing-and-construction/land-values-nsw/how-to-find-property-sales-information
