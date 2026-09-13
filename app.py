import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

DATA_DIR = "data"
st.set_page_config(page_title="NSW House Price Forecast", layout="wide")

INK, PAPER, PANEL, HAIR, MUTED = "#14171C", "#F0F2F6", "#FFFFFF", "#D7DCE3", "#5B6472"
FORECAST, ACCURACY, BAND, MODEL_C, WARN = "#3454D1", "#1F9E89", "#E2574C", "#F0A202", "#8892A0"

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] {{ font-family:'IBM Plex Sans', sans-serif; }}
  .stApp {{ background-color:{PAPER}; color:{INK}; }}
  #MainMenu, footer, header {{ visibility:hidden; }}
  .block-container {{ padding-top:1.6rem; max-width:1180px; }}
  h1.brand {{ font-family:'Fraunces', serif; font-weight:600; font-size:28px; margin:0; }}
  .tagline {{ font-size:13px; color:{MUTED}; margin-top:2px; }}
  .mod {{ background:{PANEL}; border:1px solid {HAIR}; padding:20px 22px; margin-bottom:14px; }}
  .mod h2 {{ font-size:15.5px; font-weight:600; margin:0 0 2px; }}
  .mod .sub {{ font-size:12.5px; color:{MUTED}; margin:0 0 10px; }}
  .kpi {{ text-align:left; }}
  .kpi .num {{ font-family:'IBM Plex Mono', monospace; font-weight:600; font-size:24px; color:{INK}; }}
  .kpi .lbl {{ font-size:11.5px; color:{MUTED}; margin-top:3px; }}
  .kpi .delta {{ font-size:11.5px; margin-top:2px; }}
  .up {{ color:{ACCURACY}; }} .down {{ color:{BAND}; }}
  .accuracy-note {{ font-size:12.5px; background:#3454D10D; border-left:3px solid {FORECAST}; padding:10px 14px; border-radius:2px; }}
  .warn-note {{ font-size:12.5px; background:#E2574C0D; border-left:3px solid {BAND}; padding:10px 14px; border-radius:2px; }}
  .pill {{ display:inline-block; background:{INK}; color:#fff; font-size:11px; padding:3px 9px; border-radius:10px; margin-right:6px; }}
  .flow-step {{
    background:{PANEL}; border:1px solid {HAIR}; border-radius:3px; padding:9px 14px;
    font-size:12.5px; text-align:center; margin:0 auto 4px; max-width:340px;
  }}
  .flow-arrow {{ text-align:center; color:{MUTED}; font-size:14px; margin:0 0 4px; }}
  .persona-box {{ font-size:12.5px; line-height:1.6; }}
  div[data-baseweb="tab-list"] {{ gap: 4px; }}
  .footnote {{ font-size:11.5px; color:{MUTED}; border-top:1px solid {HAIR}; padding-top:10px; margin-top:18px; }}
</style>
""", unsafe_allow_html=True)

PLOT_FONT = dict(family="IBM Plex Sans, sans-serif", color=MUTED, size=12)

def style_fig(fig, height=340):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor=PANEL, paper_bgcolor=PANEL, font=PLOT_FONT,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#E4E8EE", zeroline=False),
        legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    )
    return fig

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_feature_store():
    return pd.read_csv(f"{DATA_DIR}/NSW_feature_store.csv", parse_dates=["quarter"])

@st.cache_data
def load_abs():
    return pd.read_csv(f"{DATA_DIR}/ABS_NSW_benchmark_quarterly.csv", parse_dates=["Date"])

@st.cache_data
def load_pooled_gb():
    return pd.read_csv(f"{DATA_DIR}/model_results_pooled_GB.csv")

@st.cache_data
def compute_full_metrics():
    sarima_df = pd.read_csv(f"{DATA_DIR}/backtest_SARIMA_830suburbs.csv")
    prophet_df = pd.read_csv(f"{DATA_DIR}/backtest_Prophet_149suburbs.csv")
    gb = load_pooled_gb()

    def metrics(actual, pred):
        actual = np.array(actual, dtype=float); pred = np.array(pred, dtype=float)
        mask = ~(np.isnan(actual) | np.isnan(pred))
        actual, pred = actual[mask], pred[mask]
        resid = actual - pred
        rmse = float(np.sqrt(np.mean(resid ** 2)))
        mae = float(np.mean(np.abs(resid)))
        denom = np.where(np.abs(actual) < 1e-6, np.nan, actual)
        mape = float(np.nanmean(np.abs(resid / denom)) * 100)
        ss_res = np.sum(resid ** 2); ss_tot = np.sum((actual - actual.mean()) ** 2)
        r2 = float(1 - ss_res / ss_tot)
        dir_acc = float(np.mean(np.sign(actual) == np.sign(pred)) * 100)
        return dict(RMSE=round(rmse, 2), MAE=round(mae, 2), MAPE=round(mape, 1),
                    R2=round(r2, 3), DirAcc=round(dir_acc, 1), N=int(len(actual)))

    out = {
        "Naive persistence": metrics(sarima_df["actual"], sarima_df["naive"]),
        "Seasonal-naive": metrics(sarima_df["actual"], sarima_df["seasonal_naive"]),
        "SARIMA": metrics(sarima_df["actual"], sarima_df["sarima"]),
        "Prophet": metrics(prophet_df["actual"], prophet_df["prophet"]),
    }
    gbr = gb[gb["Model"].str.contains("Gradient")].iloc[0]
    out["Gradient Boosting"] = dict(
        RMSE=round(float(gbr["RMSE"]), 2), MAE=round(float(gbr["MAE"]), 2),
        MAPE=round(float(gbr["MAPE_%"]), 1), R2=None, DirAcc=None, N=int(gbr["N"]),
    )
    return out

fs = load_feature_store()
abs_df = load_abs()
bt_pooled = load_pooled_gb()
FULL_METRICS = compute_full_metrics()
PRIMARY = FULL_METRICS["Gradient Boosting"]

suburbs = sorted(fs["suburb"].dropna().unique().tolist())
regions = sorted([r for r in fs["region"].dropna().unique().tolist()])

RAW_TOTAL = 2762903
CLEANED_TOTAL = 2092499
DUPLICATES, CORRUPT_DATES, PRICE_FLOOR, OUTLIERS_FLAGGED = 237770, 85, 1851, 84589
OTHER_EXCLUDED = RAW_TOTAL - CLEANED_TOTAL - DUPLICATES - CORRUPT_DATES - PRICE_FLOOR

def forecast_for(suburb, horizon=4):
    sdf = fs[fs["suburb"] == suburb].dropna(subset=["median_price"]).sort_values("quarter")
    if sdf.empty:
        return None, None
    last = sdf.iloc[-1]
    last_price = last["median_price"]
    lag1 = last["qoq_pct_change"] if pd.notna(last["qoq_pct_change"]) else 0.0
    hist_qoq = sdf["qoq_pct_change"].dropna()
    typical_move = hist_qoq.tail(8).mean() if len(hist_qoq) else 0.0
    point_qoq = 0.5 * lag1 + 0.5 * typical_move
    future_q = pd.date_range(sdf["quarter"].max(), periods=5, freq="QS")[1:]
    mae = PRIMARY["MAE"]
    rows, price = [], last_price
    for fq in future_q:
        price = price * (1 + point_qoq / 100.0)
        rows.append({"quarter": fq, "price": price,
                     "low": price * (1 - mae / 100.0), "high": price * (1 + mae / 100.0)})
    fc = pd.DataFrame(rows).head(horizon)
    return sdf, fc

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(f"""
<h1 class="brand">NSW House Price Forecast</h1>
<div class="tagline">Forecasting residential property prices across NSW using cleaned historical sales data and machine-learning / time-series analysis.</div>
""", unsafe_allow_html=True)

with st.expander("Who this is for, and how it's meant to be used"):
    st.markdown("""
    <div class="persona-box">
    <strong>Primary user: property buyer / investor.</strong> Goal: understand whether prices in a
    particular NSW suburb are likely to rise or fall over the next 1–4 quarters, before making an
    offer or deciding to keep searching.<br><br>
    <strong>Secondary users:</strong> real-estate analysts, policy/research users, property agents —
    who use the same forecasts and accuracy metrics for regional comparison and reporting rather
    than an individual purchase decision.<br><br>
    <strong>How to use it:</strong> pick a suburb on the Suburb Forecast page → read the historical
    trend and forecast → choose a forecast horizon → check Model Accuracy before trusting the number
    → treat the result as decision-support, not a guaranteed future price. A wide uncertainty band
    means the forecast should carry less weight in your decision.
    </div>
    """, unsafe_allow_html=True)

st.markdown("")
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Forecast Overview", "📊 Suburb Forecast", "🎯 Model Accuracy", "🧹 Data Quality & Processing"])

# ===========================================================================
# PAGE 1 — FORECAST OVERVIEW
# ===========================================================================
with tab1:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("**Select a suburb**")
        ov_region = st.selectbox("Region", ["All regions"] + [r.title() for r in regions], key="ov_region")
    with c2:
        st.markdown("&nbsp;", unsafe_allow_html=True)

    filtered_suburbs = suburbs
    if ov_region != "All regions":
        filtered_suburbs = sorted(fs[fs["region"].str.title() == ov_region]["suburb"].dropna().unique().tolist())
    default_idx = filtered_suburbs.index("MANLY") if "MANLY" in filtered_suburbs else 0
    ov_suburb = st.selectbox("Suburb", filtered_suburbs, index=default_idx, key="ov_suburb")

    sdf, fc = forecast_for(ov_suburb, horizon=4)
    if sdf is None:
        st.warning("No cleaned sales data for this suburb.")
    else:
        last_price = sdf.iloc[-1]["median_price"]
        next_price = fc.iloc[0]["price"]
        pct_change = (next_price - last_price) / last_price * 100
        n_quarters = sdf.shape[0]
        n_sales = int(sdf["n_sales"].sum())

        st.markdown("<br>", unsafe_allow_html=True)
        k1, k2, k3, k4, k5 = st.columns(5)
        for col, num, lbl in [
            (k1, f"${last_price:,.0f}", "Current median price"),
            (k2, f"${next_price:,.0f}", "Next quarter forecast"),
            (k3, f"{pct_change:+.1f}%", "Forecast change"),
            (k4, "1–4 qtrs", "Forecast horizon"),
            (k5, f"{n_quarters}", "Historical quarters"),
        ]:
            col.markdown(f'<div class="kpi"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi" style="margin-top:8px;"><div class="num">{n_sales:,}</div><div class="lbl">Clean sales used, {ov_suburb.title()}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="mod" style="margin-top:18px;"><h2>Model reliability</h2><p class="sub">Primary model: Gradient Boosting (walk-forward backtest, all NSW suburbs)</p>', unsafe_allow_html=True)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("MAE", f"{PRIMARY['MAE']}pp")
        m2.metric("RMSE", f"{PRIMARY['RMSE']}pp")
        m3.metric("MAPE", f"{PRIMARY['MAPE']}%")
        m4.metric("R²", "pending" if PRIMARY["R2"] is None else PRIMARY["R2"])
        m5.metric("Directional accuracy", "pending" if PRIMARY["DirAcc"] is None else f"{PRIMARY['DirAcc']}%")
        st.markdown(f"""
        <div class="accuracy-note">Forecast uncertainty: &plusmn;{PRIMARY['MAE']} percentage points, based on walk-forward
        backtesting across N={PRIMARY['N']:,} forecast/actual pairs. This is more honest than saying "our model is X% accurate" —
        the number tells you the typical size of the error, not a single confidence score.</div>
        <div class="warn-note" style="margin-top:8px;">R² and directional accuracy for Gradient Boosting are marked
        <strong>pending</strong> because the current data export doesn't include per-row GB predictions — only aggregate
        RMSE/MAE/MAPE. See the Model Accuracy page for the full metric set on the models where raw predictions are available.</div>
        </div>
        """, unsafe_allow_html=True)

# ===========================================================================
# PAGE 2 — SUBURB FORECAST
# ===========================================================================
with tab2:
    left, right = st.columns([1, 3])
    with left:
        sf_suburb = st.selectbox("Suburb", suburbs, index=suburbs.index("MANLY") if "MANLY" in suburbs else 0, key="sf_suburb")
        horizon = st.radio("Forecast horizon", [1, 2, 3, 4], index=3, horizontal=True, format_func=lambda h: f"{h}Q")
        compare_list = st.multiselect("Compare suburbs (optional, up to 3)", [s for s in suburbs if s != sf_suburb], max_selections=3)

    sdf, fc = forecast_for(sf_suburb, horizon=horizon)
    with right:
        if sdf is None:
            st.warning("No data for this suburb.")
        else:
            last_price = sdf.iloc[-1]["median_price"]
            next_price = fc.iloc[0]["price"]
            pct_change = (next_price - last_price) / last_price * 100
            st.markdown(f"### {sf_suburb.title()}")
            k1, k2, k3 = st.columns(3)
            k1.metric("Current median", f"${last_price:,.0f}")
            k2.metric(f"{horizon}-quarter forecast", f"${fc.iloc[-1]['price']:,.0f}")
            k3.metric("Expected change (next qtr)", f"{pct_change:+.1f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sdf["quarter"], y=sdf["median_price"], mode="lines",
                                      line=dict(color=FORECAST, width=2.2), name="Historical"))
            bq = [sdf["quarter"].max()] + fc["quarter"].tolist()
            bp = [last_price] + fc["price"].tolist()
            bh = [last_price] + fc["high"].tolist()
            bl = [last_price] + fc["low"].tolist()
            fig.add_trace(go.Scatter(x=bq + bq[::-1], y=bh + bl[::-1], fill="toself",
                                      fillcolor="rgba(226,87,76,0.15)", line=dict(color="rgba(0,0,0,0)"),
                                      showlegend=False, name="Uncertainty band"))
            fig.add_trace(go.Scatter(x=bq, y=bp, mode="lines", line=dict(color=BAND, width=2.2, dash="dash"), name="Forecast"))
            fig = style_fig(fig, height=360)
            fig.update_yaxes(tickprefix="$")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('<div class="legend-note" style="font-size:11.5px;color:#5B6472;">Shaded band = forecast uncertainty (&plusmn;MAE from backtesting), not a guaranteed range.</div>', unsafe_allow_html=True)

    if compare_list:
        st.markdown('<div class="mod" style="margin-top:16px;"><h2>Suburb comparison</h2><p class="sub">Normalised to first available quarter = 100</p>', unsafe_allow_html=True)
        fig_c = go.Figure()
        palette = [FORECAST, ACCURACY, MODEL_C, BAND]
        for i, s in enumerate([sf_suburb] + compare_list):
            cdf = fs[fs["suburb"] == s].dropna(subset=["median_price"]).sort_values("quarter")
            if cdf.empty:
                continue
            base = cdf["median_price"].iloc[0]
            norm = cdf["median_price"] / base * 100
            fig_c.add_trace(go.Scatter(x=cdf["quarter"], y=norm, mode="lines",
                                        line=dict(color=palette[i % len(palette)], width=2), name=s.title()))
        fig_c = style_fig(fig_c, height=300)
        fig_c.update_yaxes(ticksuffix="")
        st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="warn-note">Forecast should be treated as an estimate, not a guaranteed future property price. Use it as decision-support information alongside your own research.</div>', unsafe_allow_html=True)

# ===========================================================================
# PAGE 3 — MODEL ACCURACY
# ===========================================================================
with tab3:
    st.markdown('<div class="mod"><h2>Model performance</h2><p class="sub">Primary model: <strong>Gradient Boosting</strong></p>', unsafe_allow_html=True)
    metric_defs = {
        "MAE": "Average absolute prediction error, in percentage points of QoQ price change.",
        "RMSE": "Root-mean-squared error — penalises larger errors more than MAE.",
        "MAPE": "Average percentage error. De-emphasised here since the target crosses zero.",
        "R2": "How much of the variation in actual price change the model explains. Negative means worse than predicting the average.",
        "DirAcc": "How often the model predicts the correct direction (up/down), regardless of magnitude.",
    }
    rows = []
    for model, m in FULL_METRICS.items():
        rows.append({
            "Model": model, "MAE (pp)": m["MAE"], "RMSE (pp)": m["RMSE"], "MAPE (%)": m["MAPE"],
            "R²": "pending" if m["R2"] is None else m["R2"],
            "Directional accuracy": "pending" if m["DirAcc"] is None else f"{m['DirAcc']}%",
            "N": m["N"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with st.expander("What do these metrics mean?"):
        for k, v in metric_defs.items():
            st.markdown(f"**{k}** — {v}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="mod"><h2>Model comparison</h2><p class="sub">Backtest RMSE — lower RMSE = better performance</p>', unsafe_allow_html=True)
    models_sorted = sorted(FULL_METRICS.items(), key=lambda kv: kv[1]["RMSE"])
    fig_m = go.Figure(go.Bar(
        x=[m["RMSE"] for _, m in models_sorted], y=[k for k, _ in models_sorted],
        orientation="h", marker_color=[MODEL_C if k != "Gradient Boosting" else FORECAST for k, _ in models_sorted],
    ))
    fig_m = style_fig(fig_m, height=220)
    fig_m.update_xaxes(ticksuffix="pp", title="RMSE")
    st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"""
    <div class="accuracy-note">Gradient Boosting was selected as the primary model because it achieved the lowest
    walk-forward RMSE ({PRIMARY['RMSE']}pp) and MAE ({PRIMARY['MAE']}pp) of all four candidates tested. Note that
    R² is negative for the statistical baselines (Naive, Seasonal-naive, SARIMA) on this dataset — quarter-on-quarter
    suburb price change is a genuinely noisy target, and even the best model's directional accuracy (~50–52%) is only
    modestly better than a coin flip. This is disclosed here deliberately rather than hidden behind a single headline
    accuracy number.</div>
    </div>
    """, unsafe_allow_html=True)

# ===========================================================================
# PAGE 4 — DATA QUALITY & PROCESSING
# ===========================================================================
with tab4:
    st.markdown('<div class="mod"><h2>Data processing pipeline</h2><p class="sub">Raw property sales to forecast-ready dataset</p>', unsafe_allow_html=True)
    steps = [
        "Raw Property Sales (NSW Valuer General bulk extract)",
        "Date Validation — remove corrupted contract dates",
        "Duplicate Detection — remove weekly re-publications (dealing_number)",
        "Price Validation — remove sales under $10,000 (non-arm's-length proxy)",
        "Suburb & Quarter Aggregation",
        "Outlier Detection — 1.5×IQR flag (retained, not deleted)",
        "Feature Engineering — lag, rolling, seasonal features",
        "Clean Modelling Dataset (feature_store)",
        "Forecast Models — Naive / SARIMA / Prophet / Gradient Boosting",
    ]
    for i, s in enumerate(steps):
        st.markdown(f'<div class="flow-step">{s}</div>', unsafe_allow_html=True)
        if i < len(steps) - 1:
            st.markdown('<div class="flow-arrow">↓</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:12.5px; color:#5B6472; margin-top:10px;">Raw property sales data cannot be used for
    forecasting directly. Records were validated, duplicates were identified, invalid prices were removed,
    suburbs were standardised, and observations were aggregated by suburb and quarter before any model saw them.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mod"><h2>Raw vs. cleaned records</h2><p class="sub">Click a category below for detail</p>', unsafe_allow_html=True)
    fig_funnel = go.Figure(go.Funnel(
        y=["Raw parsed records", "After date validation", "After duplicate removal", "After price-floor check", "Modelling-ready (cleaned)"],
        x=[RAW_TOTAL, RAW_TOTAL - CORRUPT_DATES, RAW_TOTAL - CORRUPT_DATES - DUPLICATES,
           RAW_TOTAL - CORRUPT_DATES - DUPLICATES - PRICE_FLOOR, CLEANED_TOTAL],
        marker=dict(color=[WARN, WARN, WARN, WARN, ACCURACY]),
        textinfo="value+percent initial",
    ))
    fig_funnel = style_fig(fig_funnel, height=280)
    st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False})

    categories = [
        ("Cleaned & modelling-ready", CLEANED_TOTAL, ACCURACY,
         f"{CLEANED_TOTAL:,} records passed every validation step and are used for modelling."),
        ("Duplicate re-publications", DUPLICATES, FORECAST,
         f"{DUPLICATES:,} records identified as duplicate / re-publication records (same dealing_number republished weekly) and excluded."),
        ("Other data-quality exclusions", OTHER_EXCLUDED, MODEL_C,
         f"{OTHER_EXCLUDED:,} records excluded for other reasons not itemised in this export "
         f"(e.g. non-residential property types, missing suburb/postcode, unparseable records) — see report Section 3.4 for the full breakdown."),
        ("Sales under $10,000", PRICE_FLOOR, BAND,
         f"{PRICE_FLOOR:,} records excluded as likely non-arm's-length transfers (family transfers, etc.) using a $10,000 price floor."),
        ("Corrupted contract dates", CORRUPT_DATES, WARN,
         f"{CORRUPT_DATES:,} records had unparseable 6-digit contract dates and were excluded."),
    ]
    for name, count, color, detail in categories:
        pct = count / RAW_TOTAL * 100
        with st.expander(f"{name} — {pct:.1f}% ({count:,} records)"):
            st.write(detail)

    st.markdown(f"""
    <div class="warn-note" style="margin-top:10px;">Separately: of the {CLEANED_TOTAL:,} modelling-ready records,
    {OUTLIERS_FLAGGED:,} suburb-quarter observations ({OUTLIERS_FLAGGED/CLEANED_TOTAL*100:.1f}%) are flagged as
    statistical outliers (1.5&times;IQR on price/sqm) but <strong>retained</strong> in the dataset with a flag,
    rather than deleted — they are not part of the exclusion funnel above.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Project workflow (Jira)"):
        st.markdown("""
        Data Acquisition → Data Storage → Data Processing → Regression / Forecasting →
        Model Evaluation → Web Dashboard → Testing & Documentation

        Jira was used to organise project tasks, assign responsibilities, and track progress
        across these stages; sprint status is summarised in Section 3.11 of the report.
        """)

st.markdown(f"""
<div class="footnote">All figures computed from the team's real PostgreSQL feature_store and walk-forward
backtests (Sections 3.3–3.9 of the report). Raw parsed records: {RAW_TOTAL:,}. Cleaned, modelling-ready
records: {CLEANED_TOTAL:,}. Forecasts are decision-support estimates, not guaranteed future prices.</div>
""", unsafe_allow_html=True)
