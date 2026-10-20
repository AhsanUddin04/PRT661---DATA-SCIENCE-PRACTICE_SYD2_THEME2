// Cover, Section 2 (one-page update summary) and Section 4 (individual pages)
const { Paragraph, TextRun, AlignmentType, ImageRun } = require("docx");
const { P, H1, H2, H3, B, PB, table, runs, int, f1, f2, FONT, AlignmentType: AL } = require("./lib");

const GH = "https://github.com/AhsanUddin04/PRT661---DATA-SCIENCE-PRACTICE_SYD2_THEME2";
const JIRA = "https://prt661.atlassian.net/jira/software/projects/KAN/boards/2";

const center = (t, size, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: o.after ?? 120, before: o.before ?? 0 },
  children: [new TextRun({ text: t, font: FONT, size, bold: o.bold, color: o.color })] });

const cover = (R) => [
  center("PRT661", 40, { bold: true, before: 1200 }),
  center("DATA SCIENCE PRACTICE", 32, { bold: true }),
  center("Assessment 4 – Final Professional Report (40%)", 30, { before: 200, after: 80 }),
  center("Forecasting NSW Suburb House Prices from Government Sales Data", 26, { color: "1F4E8C", after: 500 }),
  center("Submitted by: Sydn2 – Theme 2", 24, { bold: true, after: 200 }),
  ...table(["Student Name", "Student ID", "Campus"], [
    ["Ahsan Uddin", "S386288", "Sydney"], ["Ferdous Anwar Anik", "S388272", "Sydney"],
    ["Abrar Bin Khaiyum", "S395453", "Sydney"], ["Mohd Yah Ya Raiyan", "S390934", "Sydney"]],
    [3600, 2400, 2400], null, { size: 22 }),
  center("Submitted to: Reem Sherif, Lecturer", 22, { before: 300, after: 60 }),
  center("Charles Darwin University (Sydney Campus) · Faculty of Science & Technology", 22, { after: 60 }),
  center(R.submit_date, 22, { after: 400 }),
  P("**How this document is organised.** As required by the Assessment 4 brief, this single PDF shows the whole evolution of the project:", { align: AL.LEFT }),
  ...table(["Section", "Content", "Pages"], [
    ["Section 1", "Complete Assessment 2 submission, unchanged: the Assessment 1 report, the A2 Project Update Summary, A2 Technical Development and the A2 individual pages (with its own table of contents)", R.pg.s1],
    ["Section 2", "Final Project Update Summary: changes since Assessment 2, team contributions, evidence locations", R.pg.s2],
    ["Section 3", "Final Technical Development: the work completed since Assessment 2 (§3.1–3.13 and references)", R.pg.s3],
    ["Section 4", "Individual Work and Contribution Summary: one page per student", R.pg.s4],
  ], [1400, 6738, 1500], null, { size: 20 }),
  P("Page numbers refer to the page counter of the PDF viewer. Figures and tables added in Assessment 4 are numbered *A4.n* to keep them distinct from the A2 numbering.", { size: 20, align: AL.LEFT }),
];

const section2 = (R) => [
  H1("Section 2 – Final Project Update Summary"),
  P(`Since A2 the project has gone from a working prototype to a reproducible, tested and deployable forecasting system, and its headline accuracy now rests on a fair, like-for-like evaluation.`, { size: 21, after: 60 }),
  H3("2.1 Changes Since Assessment 2"),
  ...table(["Area", "Previous state (A2)", "Current state (A4)", "Justification"], [
    ["Reproducibility", "Notebooks + outputs; cleaning code missing from repo", "`src/prt661` package; `make all` rebuilds everything from raw zips; A2 counts reproduced", "Audit found the repo could not regenerate its own data"],
    ["Data engineering", "QoQ targets spanned gaps (9.5%); ABS used same-quarter", "Complete suburb×quarter grid; ABS lagged 1 qtr; 24 features incl. composition", "Remove mislabelled targets and look-ahead"],
    ["Database", "raw_sales / suburb_dim empty in dump; shared login", `Repopulated (${int(R.rec.raw_parsed)} raw rows); 4 new tables; per-member least-privilege roles`, "Lineage and A2 governance gap"],
    ["Machine learning", "1 tuned-by-hand GB; models compared on different samples", `12 models on identical cells; tuned on a separate validation window; LightGBM champion (MAE ${f2(R.champ_mae)} pp)`, "Fair comparison; A2 next step"],
    ["Uncertainty", "Ad-hoc ±12 pp cap and decay", `Conformalised P10–P90 bands, ${f1(R.cov_h1)}–${f1(R.cov_h4)}% coverage vs 80% target`, "Promised in A2 §3.1; replaces heuristics"],
    ["Evaluation", "RMSE/MAE only", "+ R², directional accuracy, Diebold–Mariano tests, segment & liquidity analysis, SHAP", "Show where and why the model works"],
    ["Deployment", "Local Streamlit MVP", "App v4 (bands, reliability), Docker, CI, weekly scheduled refresh", "A2 §3.16 next steps"],
    ["Governance", "CHANGELOG, Jira", "Model registry with artefact hashes, model card, privacy view, security matrix", "Traceability and privacy by design"],
  ], [1300, 2350, 3600, 2388], null, { size: 16 }),
  H3("2.2 Team Contribution Summary"),
  ...table(["Team member", "Major contributions since Assessment 2"], [
    ["Ahsan Uddin", "Project coordination and Jira; acquisition module and weekly scheduled-refresh workflow; repository restructure and CI workflow; requirements fix"],
    ["Ferdous Anwar Anik", "Sprint 9 audit; raw-archive parser and corrected cleaning module (A2 reproduction); PostgreSQL schema v2, COPY loader, audit log and least-privilege roles; feature store v2 and look-ahead tests"],
    ["Mohd Yah Ya Raiyan", "Hyper-parameter tuning; common-window back-test of 12 models; SARIMA/Prophet re-run; CQR uncertainty; Diebold–Mariano, liquidity and SHAP analysis"],
    ["Abrar Bin Khaiyum", "Web app v4 and app-data publishing step; Dockerfile and Streamlit Cloud configuration; model card and documentation; report consolidation"],
  ], [2100, 7538], null, { size: 17 }),
  H3("2.3 Evidence Locations"),
  ...table(["Evidence", "Repository location"], [
    ["Source code, tests, CI/CD", `[GitHub repository](${GH}) → \`src/prt661/\`, \`tests/\`, \`.github/workflows/\``],
    ["Sprint backlog and task ownership", `[Jira board KAN](${JIRA}) — Sprint 9 and 10 epics`],
    ["Database schema, roles", "`database/schema_v2.sql`, `database/create_member_logins.sql`"],
    ["Results tables and figures", "`reports/tables/`, `reports/figures/` (regenerated by `scripts/make_report_assets.py`)"],
    ["Models and registry", "`models/*.joblib`, `models/model_registry.json`, DB table `model_registry`"],
    ["Deployment artefacts", "`app/`, `Dockerfile`, `requirements-app.txt`"],
    ["Documentation", "`README.md`, `docs/` (CHANGELOG, MODEL_CARD, DATA_SOURCES, SECURITY_AND_PRIVACY, DEPLOYMENT)"],
  ], [3000, 6638], null, { size: 17 }),
];

const PLACE = "[INSERT SCREENSHOT: Individual Capstone Project name, completion status, score, and completion date & time]";

function person(name, id, contrib, links, reflection) {
  return [
    new Paragraph({ heading: "Heading2", pageBreakBefore: (person.n || 0) > 0, spacing: { before: 0, after: 80 }, children: [new TextRun({ text: `4.${person.n = (person.n || 0) + 1} ${name}`, font: FONT })] }),
    P(`**Student ID:** ${id}`, { after: 60 }),
    H3("Individual Capstone Project Completion Evidence"),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 }, border: {
      top: { style: "dashed", size: 6, color: "999999", space: 6 }, bottom: { style: "dashed", size: 6, color: "999999", space: 6 },
      left: { style: "dashed", size: 6, color: "999999", space: 6 }, right: { style: "dashed", size: 6, color: "999999", space: 6 } },
      children: [new TextRun({ text: PLACE, font: FONT, size: 20, italics: true, color: "888888" })] }),
    new Paragraph({ spacing: { after: 3200 }, children: [] }),
    H3("Individual Project Contribution (since Assessment 2)"),
    P(contrib),
    ...links.map(l => B(l)),
    H3("Professional Reflection"),
    P(reflection),
  ];
}

const section4 = (R) => {
  person.n = 0;
  const L = (label, path) => `[${label}](${GH}/${path})`;
  return [
    H1("Section 4 – Individual Work and Contribution Summary", { pageBreak: true }),
    ...person("Ahsan Uddin", "S386288",
      "I continued as project lead and owned acquisition and automation. I adapted the acquisition script into the package, wrote the weekly scheduled-refresh workflow that runs the pipeline every Tuesday after the Valuer General's release, restructured the repository around `src/`, `tests/` and `docs/`, wrote the CI workflow, and replaced the broken `requirements.txt`. I also ran Sprint 9–10 planning in Jira and the weekly stand-ups.",
      [L("Acquisition module", "blob/main/src/prt661/acquisition.py") + " · " + L("Weekly refresh workflow", "blob/main/.github/workflows/weekly_refresh.yml") + " · " + L("CI workflow", "blob/main/.github/workflows/ci.yml"),
       `[Jira Sprint 9–10 epics](${JIRA}) · [Commit history](${GH}/commits/main)`],
      "The most significant work this phase was turning a manual process into a scheduled one. The hard part was not the cron line but making the job safe to run unattended: it had to skip the two-hour back-test, fail loudly, and only publish if the tests passed. Coordinating four people through an audit that found defects in our own earlier work also needed care. We agreed early to treat findings as process issues rather than anyone's fault, and that kept the team moving. My contribution made sure the system keeps working after we stop touching it, which is what moves the project from coursework to something deployable."),
    ...person("Ferdous Anwar Anik", "S388272",
      "I led the Sprint 9 audit and the data-engineering rebuild. I wrote the nested-archive parser that reproduces A2's 2,762,903 raw records, corrected the cleaning module so it reproduces A2 Table 3.1, and vectorised outlier flagging (179 s → 5 s). I designed schema v2 (model registry, forecasts, audit log, privacy view), wrote the transactional COPY loader that repopulated `raw_sales` and `suburb_dim`, and implemented the least-privilege roles. I rebuilt the feature store on a complete grid with the lagged ABS regressor, and wrote the look-ahead and reconciliation tests.",
      [L("parsing.py", "blob/main/src/prt661/parsing.py") + " · " + L("cleaning.py", "blob/main/src/prt661/cleaning.py") + " · " + L("features.py", "blob/main/src/prt661/features.py") + " · " + L("db.py", "blob/main/src/prt661/db.py"),
       L("schema_v2.sql", "blob/main/database/schema_v2.sql") + " · " + L("tests", "blob/main/tests/test_pipeline.py") + ` · [Jira tasks](${JIRA})`],
      "The most significant thing I did was find that 9.5% of our own QoQ targets spanned a missing quarter. It was an uncomfortable discovery, because the A2 feature store was my work. The fix itself was simple; deciding to rebuild rather than patch, and then proving the new store had no look-ahead, took longer. Writing a test that deliberately corrupts future data taught me more about leakage than any lecture had. Because modelling and the app both sit on this layer, getting it right was what allowed the rest of the team to trust the numbers in this report. It also gave us a reproducible baseline, so any later change can be checked against known counts."),
    ...person("Mohd Yah Ya Raiyan", "S390934",
      "I led modelling and evaluation. I set up the validation design (separate tuning and test windows), ran the design and hyper-parameter search, and built the walk-forward back-test that scores 12 models on identical suburb-quarters across four horizons. That included re-running SARIMA and Prophet and reproducing the A2 Gradient Boosting model. I implemented conformalised quantile regression for the P10–P90 bands and the statistical evaluation: Diebold–Mariano tests, the liquidity analysis, segment errors and SHAP.",
      [L("backtest.py", "blob/main/src/prt661/backtest.py") + " · " + L("models.py", "blob/main/src/prt661/models.py") + " · " + L("evaluation.py", "blob/main/src/prt661/evaluation.py"),
       L("Results tables", "tree/main/reports/tables") + " · " + L("SHAP script", "blob/main/scripts/run_explain.py") + ` · [Jira tasks](${JIRA})`],
      "The most important result I produced is also the most humbling: once models were compared fairly, the gap between them was much smaller than A2 suggested, and most of the remaining error is sampling noise in suburb medians. My main challenge was resisting the urge to keep tuning on the test set. Fixing the validation window first and evaluating the test window once made the final numbers believable, even when they were less impressive than A2's. A second challenge was compute: the SARIMA re-run alone took over two hours, so I had to plan runs carefully. Calibrating the uncertainty bands was the contribution I am proudest of, because it turns an honest-but-noisy forecast into something a user can actually act on."),
    ...person("Abrar Bin Khaiyum", "S395453",
      "I rebuilt the web application around forecasts with calibrated bands and reliability labels, and designed the publishing step that exports only aggregated, suppressed data to the app. I wrote the Dockerfile (non-root, health-checked) and the Streamlit Cloud configuration, and produced the model card, deployment guide and README. I consolidated this final report.",
      [L("app.py", "blob/main/app/app.py") + " · " + L("build_app_data.py", "blob/main/scripts/build_app_data.py") + " · " + L("Dockerfile", "blob/main/Dockerfile"),
       L("Model card", "blob/main/docs/MODEL_CARD.md") + " · " + L("Deployment guide", "blob/main/docs/DEPLOYMENT.md") + ` · [Jira tasks](${JIRA})`],
      "The most significant work was redesigning the app so that uncertainty comes first: the shaded band, the reliability label and a plain-English accuracy note now sit beside every number. The technical challenge was keeping the app small and safe. Moving it from database access to a set of published files removed both the credential problem and the risk of leaking sale-level data. Writing the report taught me how much easier communication becomes when the evidence is reproducible: every figure here can be regenerated, so I could write with confidence. Working on deployment also showed me that most of the effort in a data product goes into the parts users never see: packaging, privacy rules and clear explanations."),
  ];
};

module.exports = { cover, section2, section4 };
