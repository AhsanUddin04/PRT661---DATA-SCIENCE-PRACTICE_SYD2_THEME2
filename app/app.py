"""NSW Suburb Price Outlook — PRT661 Sydn2-Theme2 web application (v4).

Reads only the published, privacy-filtered artefacts in app/data/ (built by
scripts/build_app_data.py), so the app never touches raw sale records.
Run locally:   streamlit run app/app.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
st.set_page_config(page_title="NSW Suburb Price Outlook", page_icon="🏠", layout="wide")

INK, MUTED, GRID = "#1C2430", "#5B6472", "#E6E9EF"
BLUE, BAND, ORANGE, GREEN = "#2A5BD7", "rgba(42,91,215,0.16)", "#D9822B", "#1F9E89"


@st.cache_data
def load():
    hist = pd.read_parquet(DATA / "history.parquet")
    fc = pd.read_parquet(DATA / "forecasts.parquet")
    lb = pd.read_csv(DATA / "leaderboard.csv")
    byh = pd.read_csv(DATA / "metrics_by_horizon.csv")
    cov = pd.read_csv(DATA / "interval_coverage.csv")
    meta = json.load(open(DATA / "meta.json"))
    region = pd.read_parquet(DATA / "region_history.parquet")
    return hist, fc, lb, byh, cov, meta, region


hist, fc, lb, byh, cov, meta, region = load()


def style(fig, h=360):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=8, b=8), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(color=MUTED, size=12), legend=dict(orientation="h", y=-0.2),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor=GRID))
    return fig


st.markdown("## NSW Suburb Price Outlook")
st.caption(f"Forecasts from the last complete quarter ({meta['anchor_quarter']}) · model v{meta['model_version']} · "
           f"data: NSW Valuer General bulk sales ({meta['n_sales_used']:,} cleaned residential sales) and ABS.")

tab_fc, tab_mkt, tab_acc, tab_gov = st.tabs(["Suburb forecast", "Market overview", "Model accuracy", "Data & governance"])

# ----------------------------------------------------------------- forecast ---
with tab_fc:
    suburbs = sorted(fc.suburb.unique())
    default = suburbs.index("PARRAMATTA") if "PARRAMATTA" in suburbs else 0
    c1, c2 = st.columns([2, 3])
    sub = c1.selectbox("Suburb", suburbs, index=default)
    f = fc[fc.suburb == sub].sort_values("horizon")
    h = hist[hist.suburb == sub].sort_values("quarter")
    rel = f.reliability.iloc[0]
    colour = {"high": GREEN, "medium": ORANGE, "low": "#C0392B"}[rel]
    c2.markdown(f"<div style='padding-top:28px'>Forecast reliability: <b style='color:{colour}'>{rel.upper()}</b> "
                f"&nbsp;·&nbsp; {int(h.n_sales.tail(4).mean())} sales per quarter on average (last year)</div>",
                unsafe_allow_html=True)

    k = st.columns(4)
    k[0].metric(f"Median price, {meta['anchor_quarter']}", f"${f.anchor_price.iloc[0]:,.0f}")
    k[1].metric("Central forecast in 1 year", f"${f.point_price.iloc[-1]:,.0f}", f"{f.point_pct.iloc[-1]:+.1f}%")
    k[2].metric("Low case (10th pct)", f"${f.p10_price.iloc[-1]:,.0f}", f"{f.p10_pct.iloc[-1]:+.1f}%")
    k[3].metric("High case (90th pct)", f"${f.p90_price.iloc[-1]:,.0f}", f"{f.p90_pct.iloc[-1]:+.1f}%")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h.quarter, y=h.median_price, name="Observed median", line=dict(color=INK, width=2)))
    xq = [pd.Timestamp(meta["anchor_quarter_date"])] + list(pd.to_datetime(f.target_quarter))
    a = f.anchor_price.iloc[0]
    fig.add_trace(go.Scatter(x=xq + xq[::-1], y=[a] + list(f.p90_price) + (list(f.p10_price) + [a])[::-1],
                             fill="toself", fillcolor=BAND, line=dict(width=0), mode="lines", hoverinfo="skip", name="80% range (P10–P90)"))
    fig.add_trace(go.Scatter(x=xq, y=[a] + list(f.point_price), name="Central forecast",
                             line=dict(color=BLUE, width=2.5, dash="dot"), mode="lines+markers"))
    st.plotly_chart(style(fig, 400), use_container_width=True)

    hz = byh[byh.model == meta["champion"]].set_index("horizon")
    st.info(f"**How much to trust this.** In back-testing over the last eight quarters, the model's typical error "
            f"for a single suburb was about ±{hz.loc[1, 'MAE']:.0f} percentage points one quarter ahead. "
            f"The shaded band is calibrated so that roughly 8 in 10 outcomes fall inside it "
            f"(achieved: {meta['cum_coverage']:.0f}%). Suburb medians move with the *mix* of homes sold, so a single "
            f"quarter can jump or fall sharply without the value of any one home changing. Treat this as a guide, "
            f"not a valuation.")
    tbl = f[["target_quarter", "point_price", "p10_price", "p90_price", "point_pct"]].copy()
    tbl.columns = ["Quarter", "Central ($)", "Low P10 ($)", "High P90 ($)", "Change vs now (%)"]
    tbl["Quarter"] = pd.to_datetime(tbl["Quarter"]).dt.to_period("Q").astype(str)
    st.dataframe(tbl.style.format({"Central ($)": "{:,.0f}", "Low P10 ($)": "{:,.0f}", "High P90 ($)": "{:,.0f}",
                                   "Change vs now (%)": "{:+.1f}"}), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------- market ---
with tab_mkt:
    fig = go.Figure()
    for r, col, name in [("sydney", BLUE, "Greater Sydney"), ("rest_nsw", GREEN, "Rest of NSW")]:
        s = region[region.region == r]
        fig.add_trace(go.Scatter(x=s.quarter, y=s.median_price, name=name, line=dict(color=col, width=2)))
    st.markdown("**Median residential sale price by region (our cleaned Valuer General data)**")
    st.plotly_chart(style(fig, 340), use_container_width=True)
    st.markdown("**Strongest and weakest 12-month outlooks** (high-reliability suburbs only)")
    h4 = fc[(fc.horizon == 4) & (fc.reliability == "high")].sort_values("point_pct")
    c1, c2 = st.columns(2)
    fmt = {"point_pct": "{:+.1f}%", "p10_pct": "{:+.1f}%", "p90_pct": "{:+.1f}%", "anchor_price": "${:,.0f}"}
    cols = ["suburb", "anchor_price", "point_pct", "p10_pct", "p90_pct"]
    c1.dataframe(h4.tail(10)[cols][::-1].style.format(fmt), hide_index=True, use_container_width=True)
    c2.dataframe(h4.head(10)[cols].style.format(fmt), hide_index=True, use_container_width=True)

# ----------------------------------------------------------------- accuracy ---
with tab_acc:
    st.markdown("**Walk-forward back-test: every model forecasts the same suburb-quarters** "
                f"({meta['test_window']}, liquid suburbs, 1 quarter ahead)")
    st.dataframe(lb.style.format({"RMSE": "{:.2f}", "MAE": "{:.2f}", "R2": "{:.3f}", "DirAcc": "{:.1f}"}),
                 hide_index=True, use_container_width=True)
    fig = go.Figure()
    for m, col in [(meta["champion"], BLUE), ("A2 Gradient Boosting", ORANGE), ("Naive persistence", MUTED)]:
        s = byh[byh.model == m]
        fig.add_trace(go.Bar(x=s.horizon.astype(str), y=s.MAE, name=m, marker_color=col))
    fig.update_layout(barmode="group", xaxis_title="Horizon (quarters ahead)", yaxis_title="MAE (pp)")
    st.plotly_chart(style(fig, 320), use_container_width=True)
    st.markdown("**Uncertainty band calibration** (target 80%)")
    st.dataframe(cov, hide_index=True, use_container_width=True)

# --------------------------------------------------------------- governance ---
with tab_gov:
    st.markdown("**Data lineage (rows at each stage, reproduced from the raw archives)**")
    st.dataframe(pd.DataFrame(meta["reconciliation"]), hide_index=True, use_container_width=True)
    st.markdown(
        "- Statistics built from fewer than **5 sales** are never displayed.\n"
        "- No individual sale, address or owner is shown anywhere in this app.\n"
        "- Every forecast carries an uncertainty band and a reliability label.\n"
        "- Sources: NSW Valuer General Property Sales Information (CC BY 4.0); ABS Total Value of Dwellings (CC BY 4.0).\n"
        "- This tool is a research prototype, not financial advice or a property valuation.")
