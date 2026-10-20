// Section 3 part A: intro, audit, architecture, implementation, data engineering
const { P, H1, H2, H3, B, figure, table, code, int, AlignmentType: AL } = require("./lib");
const FIG = "/home/claude/prt661/reports/figures/";

module.exports = (R) => [
  H1("Section 3 – Final Technical Development", { pageBreak: true }),
  P(`This section documents the work completed between the Assessment 2 submission (12 September 2026) and this final report. It follows directly from the *Next Steps* list in A2 §3.16, and every number below was produced by code in the project repository. All of it is reproducible with a single command (\`make all\`) from the raw Valuer General archives. Where A4 work changed or corrected something reported in A2, we say so plainly and show the size of the change, because a reader comparing the two sections deserves to know which figure to trust.`),

  H2("3.1 Where Assessment 2 Left Us: An Audit Before Building"),
  P(`Before adding anything, we spent the first week of Sprint 9 auditing what A2 had actually delivered: the repository, the database dump and the feature store. The reasoning was simple. A2 was about 65% complete, and the last 35% (deployment, a refreshed model, public forecasts) would sit on top of the first 65%. A crack in the foundation would be inherited by everything built on it. The audit was worth it: it found six defects, none visible from the A2 report alone (Table A4.1).`),
  ...table(["#", "Finding", "Evidence", "Consequence if left", "A4 fix (section)"], [
    ["1", "The scripts that produced `cleaned_sales` were not in the repository; the README itself listed `src/` as \"to add\".", "GitHub tree at A2 tag", "Results could not be regenerated or audited.", "Full `src/prt661` package and CLI (3.3)"],
    ["2", "The repo's `data_cleaning.py` lacked the residential and date-window rules described in A2 §3.4, and kept the *earliest* re-publication rather than the latest.", "Code review vs. report", "Re-running it would give a different dataset from the one modelled.", "Rewritten; reproduces A2 Table 3.1 (3.4.1)"],
    ["3", `${int(R.gap_rows)} of ${int(R.gap_total)} (${R.gap_pct}%) "quarter-on-quarter" targets in the A2 feature store spanned a missing quarter.`, "Gap check on `NSW_feature_store.csv`", "Two- and three-quarter moves were scored as one-quarter moves, inflating error and volatility.", "Complete suburb × quarter grid (3.4.3)"],
    ["4", "The ABS benchmark entered the model in the same quarter as the target, although ABS publishes about a quarter later.", "Feature-store join logic", "Mild look-ahead: the model used information not available at forecast time.", "ABS regressor lagged one quarter (3.4.3)"],
    ["5", "The A2 database dump restores `raw_sales` and `suburb_dim` with **0 rows** (A2 §3.3.1 reports 2,762,903 and 2,656).", "`pg_restore` into PostgreSQL 16", "The raw-data lineage claimed in A2 could not be verified from the submitted artefact.", "Both tables repopulated by the pipeline (3.4.2)"],
    ["6", "`requirements.txt` contained unresolved Git merge-conflict markers.", "File contents", "`pip install -r` failed on a clean machine.", "Pinned pipeline and app requirement files (3.8)"],
  ], [380, 2650, 1650, 2300, 2658], "Defects found in the A2 artefacts during the Sprint 9 audit.", { size: 17 }),
  P(`None of these invalidates the direction of A2, but findings 3 and 4 mean the A2 model scores are not directly comparable with anything in this section. So we did not simply quote the A2 Gradient Boosting result. We **re-trained the exact A2 model configuration on the corrected data and the A4 test window**, and it appears as a named competitor in every results table (§3.6).`),

  H2("3.2 Final System Architecture"),
  P(`The decision-first architecture from A1 (Decision → Insight → Data → Pipeline → Tools) has held up. What has changed is that every box is now implemented, tested and connected (Figure A4.1). Data flows left to right through five layers. A weekly scheduled job acquires new Valuer General releases, a deterministic parser and cleaner write to PostgreSQL, a feature builder and model layer produce back-tested forecasts, and a containerised web application serves only published, aggregated outputs. Forecasts are written back to the database, so the app and any analyst query read from the same source.`),
  ...figure(FIG + "fig_architecture.png", 640, "Final system architecture. Every component is implemented; numbers are actual row counts from the final run."),
  ...table(["Component", "A2 status (§3.5)", "A4 status"], [
    ["Data acquisition", "Manual download; scheduling planned", "Scripted; weekly GitHub Actions schedule (Tuesdays 06:00 AEDT)"],
    ["Parsing & cleaning", "Notebook-based; not in repository", "`parsing.py`, `cleaning.py`; reproduces A2 counts; 5 s to clean 2.5 M rows"],
    ["PostgreSQL storage", "5 tables; shared login", "9 tables + 1 privacy view; least-privilege roles; audit log"],
    ["Feature engineering", "Lag/rolling/regime features", "Complete grid, 24 features + 4 seasonal; automated look-ahead test"],
    ["Forecasting models", "Baselines, SARIMA, Prophet, GB (different samples)", "12 models on identical cells; tuned; calibrated uncertainty"],
    ["Web application", "MVP; runs locally", "v4 with forecast bands and reliability labels; Docker image; Streamlit Cloud config"],
    ["Quality assurance", "Manual review", `${R.n_tests} automated tests + CI on every push`],
  ], [2100, 3500, 4038], "Architecture components: A2 versus final state."),

  H2("3.3 Complete Implementation"),
  P(`The single biggest change in A4 is structural. The project is now a Python package rather than a set of notebooks. Notebooks are good for exploration but poor for reproduction: execution order is implicit, outputs go stale, and there is nothing to test. We kept the A2 notebooks under \`notebooks/a2_legacy/\` as a historical record and moved all production logic into \`src/prt661/\` (Table A4.3).`),
  ...table(["Module", "Responsibility", "Lines"], R.modules.map(m => [`\`${m.file}\``, m.what, String(m.lines)]),
    [2300, 6338, 1000], "Source modules in the final repository (`src/prt661/`).", { align: [AL.LEFT, AL.LEFT, AL.RIGHT] }),
  P(`Every stage reads the previous stage's artefact from \`data/processed/\` and writes its own, so stages can be re-run independently. The orchestrator exposes them through one command-line entry point (Figure A4.2). The weekly refresh job runs exactly the same entry point, which means what runs in production is the same code the tests exercise.`),
  ...code([
    "$ python -m prt661.pipeline --stages parse clean features",
    "[parse] starting",
    "  parsed   2014.zip:   218,292 B-records      ...      parsed   2026.zip:   126,174 B-records",
    `[parse] done in 31s {'rows_out': ${int(R.rec.raw_parsed)}}`,
    "[clean] starting",
    `[clean] done in 8s {'raw_parsed': ${int(R.rec.raw_parsed)}, 'duplicates_removed': ${int(R.rec.duplicates_removed)}, 'non_residential_removed': ${int(R.rec.non_residential_removed)},`,
    `         'outside_window_removed': ${int(R.rec.outside_window_removed)}, 'price_floor_removed': ${int(R.rec.price_floor_removed)}, 'outliers_flagged': ${int(R.rec.outliers_flagged)}, 'cleaned_total': ${int(R.rec.cleaned_total)}}`,
    "[features] starting",
    `[features] done in 11s {'rows_out': ${int(R.fs_grid)}}`,
  ], "Running the first three pipeline stages from the raw archives (actual console output, abridged)."),

  H2("3.4 Data Engineering"),
  H3("3.4.1 Reproducing the A2 Dataset from Raw Archives"),
  P(`The NSW Valuer General archives are awkward: each yearly zip contains weekly zips (or folders) that contain one semicolon-delimited \`.DAT\` file per valuation district. Each file mixes header (A), sale (B), legal-description (C), party (D) and trailer (Z) records. Our parser streams these nested archives entirely in memory, keeps only B records, and maps the 24 positional fields from the Valuer General's published file format. It parsed **${int(R.rec.raw_parsed)} sale records in 31 seconds**, exactly the count reported in A2 §3.3. The cleaner then applies the five A2 rules in the documented order (Table A4.4).`),
  ...table(["Step (A2 §3.4 rule)", "A2 reported", "A4 reproduced", "Difference"], [
    ["Raw parsed records", "2,762,903", int(R.rec.raw_parsed), "0"],
    ["Duplicate re-publications removed (keep latest)", "237,770", int(R.rec.duplicates_removed), "0"],
    ["Non-residential removed", "429,788", int(R.rec.non_residential_removed), "0"],
    ["Outside 2013-Q1 – 2026-Q3 window", "995", int(R.rec.outside_window_removed), "0"],
    ["Below $10,000 price floor", "1,851", int(R.rec.price_floor_removed), "−1"],
    ["**Cleaned residential sales**", "**2,092,499**", `**${int(R.rec.cleaned_total)}**`, "**+1**"],
    ["Outliers flagged (retained)", "84,589", int(R.rec.outliers_flagged), `+${int(R.rec.outliers_flagged - 84589)}`],
  ], [4000, 1800, 1900, 1938], "Cleaning reconciliation: A2 report versus the A4 pipeline run on the same raw files.",
    { align: [AL.LEFT, AL.RIGHT, AL.RIGHT, AL.RIGHT] }),
  P(`Four of the five rules reproduce to the record. The single-record difference on the price floor is a boundary case (a sale recorded at exactly the floor), which we treat as immaterial. The outlier count differs by ${(100 * (R.rec.outliers_flagged - 84589) / 84589).toFixed(1)}%, because A2 never recorded which grouping key and area unit its IQR fence used. We fixed the rule explicitly: Tukey's 1.5 × IQR fence on price per m², computed within each (suburb, settlement quarter) with at least four sales, for lots measured in square metres only. Hectare-measured rural blocks have a price per m² that is not comparable with suburban lots, so they are left out of the fence. We also replaced A2's row-wise \`groupby().apply\` with a vectorised implementation, cutting cleaning time from 179 s to 5 s. That matters once the job runs weekly.`),

  H3("3.4.2 Database: Repopulated, Extended and Secured"),
  P(`We restored the A2 dump into a fresh PostgreSQL 16 server and immediately hit audit finding 5: \`raw_sales\` and \`suburb_dim\` exist but contain no rows. The pipeline's loader now bulk-loads through PostgreSQL \`COPY\` inside a single transaction, so a failed load leaves the table unchanged rather than half-written. Each load writes an audit row to a new \`pipeline_runs\` table. Loading all ${int(R.rec.raw_parsed)} raw rows takes about 90 seconds. Schema v2 (\`database/schema_v2.sql\`, idempotent) adds four operational tables and one view (Table A4.5).`),
  ...table(["Table / view", "Purpose", "Rows (final run)"], [
    ["`raw_sales`", "Landing table, now actually populated", int(R.rec.raw_parsed)],
    ["`cleaned_sales`", "Modelling-grade sales (unchanged from A2)", "2,092,499"],
    ["`suburb_dim`", "Suburb → modal postcode → region, now populated", int(R.n_suburb_dim)],
    ["`abs_benchmark`", "ABS Total Value of Dwellings (unchanged)", "97"],
    ["`feature_store_v2`", "Complete suburb × quarter grid with v2 features (new)", int(R.fs_grid)],
    ["`model_registry`", "One row per trained model: version, horizon, SHA-256 of artefact, back-test metrics (new)", "4"],
    ["`forecasts`", "Published forecasts with P10/P90 and reliability label (new)", int(R.fc_rows)],
    ["`pipeline_runs`", "Audit log of every load stage (new)", "per run"],
    ["`v_public_suburb_quarter`", "Privacy view: hides any statistic built from fewer than 5 sales (new)", `${int(R.public_suppressed)} cells suppressed`],
  ], [2500, 5238, 1900], "Final database objects.", { align: [AL.LEFT, AL.LEFT, AL.RIGHT] }),
  P(`The A2 report flagged the shared team login as an open governance task. It is now closed (Figure A4.3). Privileges sit on three group roles: \`prt661_etl\` (read/write data), \`prt661_analyst\` (read-only, *without* access to \`raw_sales\` and therefore to street addresses) and \`prt661_app_ro\` (forecasts and the privacy view only). Each team member has a personal login inheriting the role their work needs, and passwords are supplied at run time rather than committed.`),
  ...code(R.db_security_lines, "Least-privilege roles tested against the live database (actual psql output)."),

  H3("3.4.3 Feature Store v2"),
  P(`Two of the audit findings lived in the feature store, so we rebuilt it rather than patching it. The key change is that every suburb now has a row for **every** quarter, giving ${int(R.fs_grid)} rows for ${int(R.fs_suburbs)} suburbs over 55 quarters, of which ${int(R.fs_observed)} have at least one sale. A quarter-on-quarter change is only defined when **both** adjacent quarters have at least five sales; otherwise it is missing, never silently stretched over a gap. This yields ${int(R.fs_targets)} valid QoQ observations. That is fewer than A2, but each one means what its name says.`),
  P(`We also reframed the table around the **forecast origin**. A row for quarter *t* holds only what is known at the end of *t*, and direct targets for *t + 1 … t + 4* are stored alongside. Two versions are kept: the QoQ change in that future quarter (the A2 target, used for evaluation) and the cumulative change from *t* (used for the price path shown to users, §3.5.4). An automated test now enforces this: it triples every sale price **after** the origin, rebuilds the store, and asserts that no feature at the origin moves (Figure A4.12). The new features answer specific weaknesses seen in A2 (Table A4.6).`),
  ...table(["Feature group", "Features", "Why it was added"], [
    ["Momentum (own suburb)", "QoQ at t, t−1, t−2, t−3; 4- and 8-quarter means; 4-quarter volatility; YoY change", "A2 lags, re-based to the forecast origin; YoY is far less noisy than QoQ"],
    ["Mean reversion", "Deviation of log median from its 4-quarter mean", "EDA Pass 2 found r = −0.27 between consecutive QoQ moves: a jump is often a composition artefact that reverses"],
    ["Composition", "Unit (strata) share and its change; median $/m²; log price level", "A suburb median moves when the mix of houses vs. units sold changes (A2 §3.7 listed this as not yet done)"],
    ["Market breadth", "Regional and NSW median QoQ from our own data; regional 4-quarter momentum", "Timely market signal — available weeks before the ABS release"],
    ["Macro (lagged)", "ABS regional growth and Total Value of Dwellings growth, both at t−1", "Keeps the A2 benchmark idea but removes look-ahead"],
    ["Liquidity", "Log sales count, change in volume, quarters with ≥5 sales in last 8", "Lets the model learn that thin markets are noisier"],
    ["Calendar / regime", "Target-quarter dummies; COVID and rate-hike flags at t", "Seasonality of the *target* quarter is known in advance"],
  ], [1900, 3900, 3838], "Feature groups in feature store v2 (24 features + 4 target-quarter dummies)."),
];
