// Build the Assessment 4 additions (cover + Sections 2-4) as a .docx
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Footer, AlignmentType, PageNumber, LevelFormat, HeadingLevel } = require("docx");
const L = require("./lib");
const { P, H2, f1, f2 } = L;
const { cover, section2, section4 } = require("./s2_s4");

const R = JSON.parse(fs.readFileSync("/home/claude/prt661/reports/tables/report_numbers.json", "utf8"));
const PAGES = fs.existsSync(__dirname + "/pages.json") ? JSON.parse(fs.readFileSync(__dirname + "/pages.json")) : { s1: "2–33", s2: "34", s3: "35–", s4: "" };
R.pg = PAGES;
R.submit_date = "October 2026";

// ---- derived narrative strings --------------------------------------------------
const dm = Object.fromEntries(R.dm.map(d => [d.vs, d]));
const p = x => x < 0.001 ? "p < 0.001" : `p = ${x.toFixed(3)}`;
R.dm_text = `LightGBM is significantly more accurate than every baseline and than SARIMA (${p(dm.SARIMA.p_abs)}). It is also significantly better than the A2 model (${p(dm["A2 Gradient Boosting"].p_sq)} on squared error, ${p(dm["A2 Gradient Boosting"].p_abs)} on absolute error) and than Ridge (${p(dm.Ridge.p_abs)}): the A4 improvement over A2 is small but not luck. Against Random Forest and XGBoost there is no detectable difference (${p(dm["Random forest"].p_abs)} and ${p(dm.XGBoost.p_abs)}). The ensemble is marginally better on absolute error (${p(dm["Ensemble (LGBM+XGB+RF)"].p_abs)}) but not on squared error (${p(dm["Ensemble (LGBM+XGB+RF)"].p_sq)}). For a 0.03 pp MAE gain at three times the training cost, we kept LightGBM as the production model and logged the ensemble as the leading candidate for the next release.`;
const s = R.shap;
R.shap_text = `One feature dominates: **deviation of the suburb's median from its own four-quarter trend accounts for ${f1(s.dev_from_trend)}% of total attribution**, and its effect is strongly negative. When a suburb's median sits well above its recent trend, the model forecasts a fall, and vice versa. This is the mean reversion that EDA Pass 2 detected as a negative autocorrelation (A2 §3.6.2), now learned explicitly. It also explains A2's apparent paradox that the lagged QoQ change was both negatively correlated with the target and the most important GB feature. Year-on-year change (${f1(s.yoy_pct_change)}%), the eight-quarter mean (${f1(s.qoq_roll8_mean)}%) and the price level (${f1(s.log_price)}%; dearer suburbs grew slightly less) come next. Market-wide signals (ABS growth lagged, regional momentum, NSW median) together contribute about ${f1(s.abs_tvd_growth_lag1 + s.region_qoq_roll4 + s.abs_region_growth_lag1 + s.state_qoq + s.region_qoq)}%. The composition features we added for A4 (unit share and its change) contribute a modest ${f1(s.strata_share + s.strata_share_change)}%, and calendar seasonality almost nothing, consistent with A2's STL finding that seasonality explains only 0.4% of variance.`;

const s3a = require("./s3a")(R), s3b = require("./s3b")(R), s3c = require("./s3c")(R);

const refs = [
  "Australian Bureau of Statistics. (2026). *Total value of dwellings, Australia* (Cat. No. 6432.0). https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings/latest-release",
  "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324",
  "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. In *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). https://doi.org/10.1145/2939672.2939785",
  "Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics, 13*(3), 253–263. https://doi.org/10.1080/07350015.1995.10524599",
  "Harvey, D., Leybourne, S., & Newbold, P. (1997). Testing the equality of prediction mean squared errors. *International Journal of Forecasting, 13*(2), 281–291. https://doi.org/10.1016/S0169-2070(96)00719-4",
  "Huber, P. J. (1964). Robust estimation of a location parameter. *The Annals of Mathematical Statistics, 35*(1), 73–101. https://doi.org/10.1214/aoms/1177703732",
  "Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts. https://otexts.com/fpp3/",
  "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems, 30*, 3146–3154.",
  "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems, 30*, 4765–4774.",
  "Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model cards for model reporting. In *Proceedings of the Conference on Fairness, Accountability, and Transparency* (pp. 220–229). https://doi.org/10.1145/3287560.3287596",
  "New South Wales Government. (2026). *Property sales information* [Data set]. NSW Valuer General. https://valuation.property.nsw.gov.au/embed/propertySalesInformation",
  "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.",
  "Romano, Y., Patterson, E., & Candès, E. (2019). Conformalized quantile regression. *Advances in Neural Information Processing Systems, 32*, 3543–3553.",
  "Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In *Proceedings of the 9th Python in Science Conference* (pp. 92–96). https://doi.org/10.25080/Majora-92bf1922-011",
  "Taylor, S. J., & Letham, B. (2018). Forecasting at scale. *The American Statistician, 72*(1), 37–45. https://doi.org/10.1080/00031305.2017.1380080",
];
const references = [H2("References (Assessment 4)"),
  ...refs.map(r => new Paragraph({ children: L.runs(r, { size: 21 }), indent: { left: 567, hanging: 567 }, spacing: { after: 80 }, alignment: AlignmentType.LEFT }))];

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
  children: [new TextRun({ font: L.FONT, size: 18, color: "666666", children: ["PRT661 Sydn2–Theme2 · Assessment 4 · "] })] })] });

const doc = new Document({
  creator: "Sydn2 – Theme 2", title: "PRT661 Assessment 4 – Final Professional Report",
  styles: {
    default: { document: { run: { font: L.FONT, size: L.BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: L.FONT, color: "1F3864" }, paragraph: { spacing: { before: 120, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: L.FONT, color: "1F3864" }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: L.FONT, color: "2E5597" }, paragraph: { spacing: { before: 140, after: 60 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 500, hanging: 260 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 500, hanging: 300 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    children: cover(R),
  }, {
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 },
      pageNumbers: { start: 34 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ font: L.FONT, size: 18, color: "666666", text: "PRT661 Sydn2–Theme2 · Assessment 4 · page " }),
                 new TextRun({ font: L.FONT, size: 18, color: "666666", children: [PageNumber.CURRENT] })] })] }) },
    children: [...section2(R), ...s3a, ...s3b, ...s3c, ...references, ...section4(R)],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/claude/prt661/reports/PRT661_A4_additions.docx", buf);
  console.log("written");
});
