// Section 3 part C: deployment, readiness, governance, ethics, limitations, future work
const { P, H2, H3, B, figure, table, code, int, f1, AlignmentType: AL } = require("./lib");
const FIG = "/home/claude/prt661/reports/figures/";

module.exports = (R) => [
  H2("3.8 Deployment"),
  P(`A2 ended with a working app that ran only on a team member's laptop. For A4 we treated deployment as an engineering problem with three separate concerns: what the app is allowed to see, how it is packaged, and how it stays current.`),
  H3("3.8.1 The Web Application (v4)"),
  P(`The app was rebuilt around the forecasting output rather than the back-test tables. Its main page (Figure A4.10) shows, for any of the ${int(R.fc_suburbs)} suburbs with enough recent sales, the observed median price history, a four-quarter central forecast, the calibrated P10–P90 band as a shaded fan, and a reliability label (high/medium/low) based on recent sales volume and band width. Below the chart, a plain-language note states the typical back-tested error and explains *why* a suburb median can jump for reasons unrelated to any one home's value. We added it because, during our own review of the A2 app, we kept reading large forecast swings as market calls when they were usually a change in the mix of homes sold. Three further tabs cover the regional market, model accuracy and data lineage.`),
  ...figure(FIG + "fig_app_forecast.png", 600, `Web application v4, Suburb Forecast page (live screenshot, Parramatta). The shaded fan is the conformalised P10–P90 band from §3.5.4.`),
  P(`A deliberate design decision is that **the app never connects to the database or to sale-level data**. A publishing step (\`scripts/build_app_data.py\`) exports five small, already-aggregated files to \`app/data/\` (${R.app_data_mb} MB in total), applying the five-sale suppression rule on the way out. This shrinks the attack surface to near zero, makes the app start in about two seconds, and means a deployed copy cannot leak an address even if misconfigured.`),
  ...figure(FIG + "fig_app_accuracy.png", 560, "Model Accuracy tab: the same leaderboard and horizon comparison reported in §3.6, generated from the back-test tables."),
  H3("3.8.2 Packaging, Continuous Integration and Scheduling"),
  ...table(["Artefact", "What it does", "Status"], [
    ["`Dockerfile`", "Python 3.11-slim image with only the five app dependencies; runs as a non-root user; health check on Streamlit's `/_stcore/health`", "Written and reviewed"],
    ["`requirements-app.txt`", "Minimal runtime for Streamlit Community Cloud (the A2-recommended host)", "Tested locally"],
    ["`.github/workflows/ci.yml`", "On every push/PR: install pinned deps, lint with ruff, run the test suite, apply both schema files to a throw-away PostgreSQL 16 service (twice, to prove idempotence)", "Ready to activate on push"],
    ["`.github/workflows/weekly_refresh.yml`", "Every Tuesday 06:00 AEDT (after the Valuer General's Monday release): acquire → parse → clean → features → forecast → publish → load DB → test; commits refreshed app data, which triggers a Streamlit Cloud redeploy", "Ready to activate on push"],
    ["`Makefile` / pipeline CLI", "`make all` reproduces every number in this report from raw archives", "Run end-to-end for this report"],
  ], [2700, 5100, 1838], "Deployment artefacts."),
  P(`The full pipeline run is not free. The statistical back-test dominates (about two hours on two CPU cores, almost all of it SARIMA and Prophet fitting). So the weekly job deliberately **excludes** the back-test: it re-trains and re-forecasts, which takes a few minutes, and the back-test is re-run at each tagged release. This keeps the published model and its quoted accuracy in step without paying for a full evaluation every week.`),

  H2("3.9 Deployment Readiness"),
  P(`We assessed readiness against a short checklist we would apply to any analytics product going in front of non-technical users (Table A4.14). Our honest summary: the system is **ready for a supervised public pilot** but not for unsupervised production use. The two gaps are organisational rather than technical: the workflows have to be pushed to the team's GitHub to go live, and there is no named owner for the weekly job after the semester ends.`),
  ...table(["Criterion", "Evidence", "Ready?"], [
    ["Reproducible from raw data", "Pipeline reproduces A2 Table 3.1 to within one record (§3.4.1)", "Yes"],
    ["Automated tests pass", `${R.n_tests} tests, including look-ahead and suppression tests (Figure A4.12)`, "Yes"],
    ["Accuracy known and published", "Common-window back-test, shown in the app", "Yes"],
    ["Uncertainty calibrated", `CQR bands hit ${f1(R.cov_h1)}–${f1(R.cov_h4)}% coverage against an 80% target`, "Yes"],
    ["Privacy controls enforced in code", "Suppression view, app reads aggregates only, role tests (Figure A4.3)", "Yes"],
    ["Model versioned and traceable", "`model_registry` with SHA-256 of each artefact; CHANGELOG", "Yes"],
    ["Monitoring & alerting", "Pipeline audit log exists; no automated drift alert yet", "Partial"],
    ["Live public URL", "Config complete; requires push to team GitHub + Streamlit Cloud connect (~2 min)", "Pending team action"],
    ["Operational owner after semester", "Not assigned", "No"],
  ], [3000, 5338, 1300], "Deployment readiness assessment."),
  ...code(R.pytest_lines, "Automated test suite (actual pytest output). The look-ahead test perturbs all post-origin sales and asserts the features at the origin are unchanged."),

  H2("3.10 Governance"),
  P(`Governance in A2 was mostly process: Jira epics, pull requests, a CHANGELOG. In A4 we pushed it into the artefacts themselves, so that the system enforces the rules rather than relying on people to remember them.`),
  B(`**Model registry.** Every trained model is a row in \`model_registry\` with its version, horizon, the date it was trained through, its hyper-parameters, its back-test metrics and the SHA-256 hash of the saved file. Whatever produced a published forecast can be identified exactly.`),
  B(`**Selection discipline.** Hyper-parameters were chosen on a validation window that closes before the test window opens (§3.5.2), and the test window was evaluated once. The champion (LightGBM) was fixed from the validation results, and the rule is recorded in \`docs/MODEL_CARD.md\`, so the test leaderboard could not quietly steer model choice.`),
  B(`**Change control.** \`docs/CHANGELOG.md\` records every data-rule, schema, feature and model change with its effect on reported numbers, including all six audit findings. We recommend branch protection on \`main\` (one required review, CI must pass) as a repository setting; the steps are in \`docs/DEPLOYMENT.md\`.`),
  B(`**Documentation as deliverable.** A model card (intended use, out-of-scope uses, metrics by segment, caveats; after Mitchell et al., 2019), a data-sources log with access dates and licences, and a security and privacy control matrix all ship in \`docs/\`.`),
  P(`**Team process.** Sprints 9 and 10 kept the A2 cadence: two-week sprints mirrored as Jira epics, a weekly stand-up on Teams, and a pull request per task with one reviewer. Table A4.15 shows final sprint status. The ten-sprint plan from A1 is complete except the optional second-state extension, which we deliberately descoped in Sprint 9 to protect the audit and evaluation work.`),
  ...table(["Sprint", "Focus", "Status"], [
    ["1–8", "Business understanding → data → EDA → models → back-test (A1/A2)", "Complete"],
    ["9", "Audit of A2 artefacts; reproducible package; DB v2 and roles; feature store v2; tuning", "Complete"],
    ["10", "Common-window back-test; uncertainty calibration; app v4; CI/CD; final report", "Complete"],
    ["Stretch", "Second state (VIC) for generalisability", "Descoped (see §3.13)"],
  ], [1100, 6738, 1800], "Final sprint status."),

  H2("3.11 Ethics, Privacy and Security"),
  P(`The data is public under CC BY 4.0, but "public" is not the same as "harmless". Valuer General records include street addresses and exact prices. Combined with a suburb and a quarter, a thin market can make an "aggregate" effectively disclose one household's sale. Our controls are layered, so that no single mistake exposes anything:`),
  B(`**Minimum cell size.** No statistic built from fewer than five sales is ever published. This is enforced in the database view, in the app-data export and by a test. It suppresses ${int(R.public_suppressed)} suburb-quarters.`),
  B(`**Least privilege.** Only the ETL role can read addresses; the app role can read forecasts and the privacy view only (Figure A4.3). The app image contains no credentials and no sale-level data.`),
  B(`**No false precision.** Every forecast carries a calibrated band and a reliability label, low-liquidity suburbs are labelled *low* rather than hidden, and the app states plainly that it is not a valuation or financial advice.`),
  B(`**Fairness across places.** We checked whether the model serves regional NSW worse than Sydney. Overall it does not: one-quarter-ahead MAE is ${f1(R.seg.rest_nsw.MAE)} pp for regional suburbs and ${f1(R.seg.sydney.MAE)} pp for Sydney, and band coverage is ${f1(R.seg.rest_nsw.cov)}% and ${f1(R.seg.sydney.cov)}%. Among liquid suburbs, regional forecasts are actually *more* accurate (${f1(R.seg.rest_nsw.liq_mae)} vs ${f1(R.seg.sydney.liq_mae)} pp), plausibly because Sydney medians mix houses and apartments far more. Both regions show a small negative bias (forecasts ${f1(Math.min(-R.seg.rest_nsw.bias, -R.seg.sydney.bias))}–${f1(Math.max(-R.seg.rest_nsw.bias, -R.seg.sydney.bias))} pp below outcomes on average) because the test window was a period of strong growth. We publish these segment results in the model card rather than averaging them away.`),
  B(`**Secrets and supply chain.** Credentials come from environment variables and GitHub Secrets, \`.env\` is git-ignored, and all dependencies are pinned to the versions used to produce this report.`),
  P(`One ethical risk we cannot fully engineer away is **misuse as a buy/sell signal**. A forecast that suburb X will rise could, at scale, become self-fulfilling or be used in marketing. We mitigate this with framing (ranges first, central value second; "guide, not valuation"), and the model card lists investment advice and automated lending decisions as out of scope.`),

  H2("3.12 Limitations"),
  B(`**The noise floor is real.** A suburb median from 20 sales has substantial sampling error, so a large part of each QoQ move is unforecastable composition noise (§3.7). Our forecasts are best read as *direction and range*, not a point estimate.`),
  B(`**One state.** NSW only. The pipeline is config-driven, but other states publish in different formats and under different terms, so generalisability is untested.`),
  B(`**Region proxy.** Sydney vs rest-of-NSW is still assigned by postcode range, not the ABS GCCSA correspondence, and suburbs are matched by name, so boundary changes over 2014–2026 are not tracked.`),
  B(`**No macro drivers.** Interest rates, credit growth and population flows are absent: sourcing, aligning and lagging these series correctly was out of scope for the project window. The model will therefore react to a rate shock only after it shows up in sales.`),
  B(`**Test window.** Eight quarters (2024-Q3 to 2026-Q2) is a reasonable but single regime. The model has not been tested through a sharp downturn.`),

  H2("3.13 Future Improvements"),
  B(`**Repeat-sales or hedonic index per suburb.** Tracking the same properties over time (property_id is in the data) would strip out composition noise and could cut the noise floor substantially. This is the single most promising next step.`),
  B(`**Hierarchical forecasting.** Reconciling suburb, region and state forecasts (e.g. MinT; Hyndman & Athanasopoulos, 2021) so they add up coherently and borrow strength across levels.`),
  B(`**Macro features and scenario mode.** Add the RBA cash rate and ABS lending indicators, and let users ask "what if rates rise 50 bp?" with the band widening accordingly.`),
  B(`**Drift monitoring.** Compare each new quarter's realised errors and band coverage with the back-test and alert when they leave the expected range.`),
  B(`**Second state and SA2 geography.** Victoria's Valuer-General data, and the ABS postcode-to-SA2 correspondence to replace the postcode-range region proxy.`),
];
