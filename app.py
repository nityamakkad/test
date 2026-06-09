"""
IK Refund Analysis Dashboard
Production-ready Streamlit app.
Run: streamlit run app.py
"""

import json
import os
import pandas as pd
import streamlit as st

from data_loader import load_refund, load_onboarding
from charts import (
    kpi_cards,
    chart_refunds_by_month,
    chart_refund_pct_by_quarter,
    chart_by_country,
    chart_bu_split,
    chart_category,
    chart_course,
    chart_payment_mode,
    chart_upfront_type,
    chart_refund_reasons,
    chart_date_diffs,
    chart_onboarding_status,
    chart_trial_window,
    chart_new_vs_alumni,
    chart_enrollments_vs_refunds,
)
import insights as ins

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="IK Refund Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Global font */
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

  /* KPI cards */
  .kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .kpi-label { font-size: 12px; color: #64748B; letter-spacing: 0.05em; text-transform: uppercase; }
  .kpi-value { font-size: 26px; font-weight: 700; color: #1E293B; margin: 4px 0; }
  .kpi-sub   { font-size: 11px; color: #94A3B8; }

  /* Section headers */
  .section-header {
    font-size: 17px; font-weight: 600; color: #1E293B;
    border-left: 4px solid #2563EB;
    padding-left: 10px; margin: 28px 0 14px 0;
  }

  /* Reading note / insight box */
  .insight-box {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 13.5px;
    color: #334155;
    line-height: 1.7;
    margin-bottom: 16px;
  }
  .insight-box ul { margin: 0; padding-left: 18px; }
  .insight-box li { margin-bottom: 5px; }

  /* Warning / maturity note */
  .warn-box {
    background: #FFFBEB; border: 1px solid #FCD34D;
    border-radius: 8px; padding: 10px 14px;
    font-size: 13px; color: #92400E; margin-bottom: 12px;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] { background: #F8FAFC; }
  .sidebar-title { font-size: 18px; font-weight: 700; color: #1E293B; margin-bottom: 4px; }
  .sidebar-sub   { font-size: 11px; color: #94A3B8; margin-bottom: 16px; }

  /* Hide streamlit branding */
  #MainMenu, footer { visibility: hidden; }
  header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOAD
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading data…")
def get_data():
    df_r = load_refund("data/refund_data.csv")
    df_o = load_onboarding("data/onboarding_data.csv")
    return df_r, df_o


df_raw, df_onboard = get_data()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="sidebar-title">🔍 Filters</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Applied to all charts</div>', unsafe_allow_html=True)
    st.divider()

    def multiselect_filter(label, series, key):
        opts = sorted([x for x in series.unique() if x not in ("", "Unknown", "nan")])
        opts_with_unknown = opts + (["Unknown"] if series.isin(["Unknown"]).any() else [])
        return st.multiselect(label, options=opts_with_unknown,
                              default=opts_with_unknown, key=key)

    sel_country    = multiselect_filter("🌍 Country / Region",
                                        df_raw["Country"], "country")
    sel_bu         = multiselect_filter("🏢 Business Unit (BU)",
                                        df_raw["BU"], "bu")
    sel_category   = multiselect_filter("📂 Program Category",
                                        df_raw["Category"], "category")
    sel_course     = multiselect_filter("🎓 Course",
                                        df_raw["Course"], "course")
    sel_payment    = multiselect_filter("💳 Payment Mode",
                                        df_raw["Payment Mode"], "payment_mode")
    sel_upfront    = multiselect_filter("📦 Upfront / Flexipay / Non-Upfront",
                                        df_raw["Upfront Payment / Non Upfront / Flexipay"],
                                        "upfront")
    sel_month      = multiselect_filter("📅 Refund Month",
                                        df_raw["Refund Month"].astype(str), "month")
    sel_new_alumni = multiselect_filter("👤 New / Alumni",
                                        df_raw["New / Alumni"], "new_alumni")
    sel_ob_status  = multiselect_filter("✅ Onboarding Status",
                                        df_raw["Onboarding Status"], "ob_status")
    sel_trial      = multiselect_filter("⏱️ Refund in Trial Window",
                                        df_raw["Refund request received in Trial Window"],
                                        "trial")

    st.divider()
    st.caption("Quarter definition: Q1=Jan–Mar, Q2=Apr–Jun, Q3=Jul–Sep, Q4=Oct–Dec")
    st.caption("*Agentic/IP column coming soon — add column AD to source sheet*")


# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────

df = df_raw.copy()
if sel_country:    df = df[df["Country"].isin(sel_country)]
if sel_bu:         df = df[df["BU"].isin(sel_bu)]
if sel_category:   df = df[df["Category"].isin(sel_category)]
if sel_course:     df = df[df["Course"].isin(sel_course)]
if sel_payment:    df = df[df["Payment Mode"].isin(sel_payment)]
if sel_upfront:    df = df[df["Upfront Payment / Non Upfront / Flexipay"].isin(sel_upfront)]
if sel_month:      df = df[df["Refund Month"].astype(str).isin(sel_month)]
if sel_new_alumni: df = df[df["New / Alumni"].isin(sel_new_alumni)]
if sel_ob_status:  df = df[df["Onboarding Status"].isin(sel_ob_status)]
if sel_trial:      df = df[df["Refund request received in Trial Window"].isin(sel_trial)]

total_enrollments = len(df_onboard)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("## 📊 IK Refund Analysis Dashboard")
st.markdown(
    f"<span style='color:#64748B;font-size:13px;'>"
    f"Source: <code>refund_data.csv</code> · <code>onboarding_data.csv</code> · "
    f"Filters applied · Showing <b>{len(df)}</b> of <b>{len(df_raw)}</b> refund records"
    f"</span>",
    unsafe_allow_html=True,
)

if len(df) == 0:
    st.warning("No records match the current filters. Please adjust your selection.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────

kpi = kpi_cards(df, total_enrollments)

c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, label, value, sub in [
    (c1, "Total Refunds",       f"{kpi['total_refunds']}",              "drops in period"),
    (c2, "Credit Note Value",   f"${kpi['total_credit']:,.0f}",         "total written off"),
    (c3, "Gross Revenue at Risk",f"${kpi['total_revenue']:,.0f}",       "net rev of refunded"),
    (c4, "Refund Rate",         f"{kpi['refund_pct']:.1f}%",            "of all enrollments"),
    (c5, "Avg Days to Request", f"{kpi['avg_days_to_req']:.0f} days"
                                 if not pd.isna(kpi['avg_days_to_req']) else "—",
                                "enrollment → request"),
    (c6, "In Trial Window",     f"{kpi['trial_pct']:.0f}%",             "refunds within trial"),
]:
    with col:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — OVERVIEW TRENDS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">① Monthly & Quarterly Trends</div>',
            unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])
with col_a:
    st.plotly_chart(chart_refunds_by_month(df), use_container_width=True)
with col_b:
    st.plotly_chart(chart_refund_pct_by_quarter(df, df_onboard), use_container_width=True)

st.markdown(
    '<div class="warn-box">⚠️ <b>Maturity note:</b> Jun-26 refund data is still accruing — '
    'the refund rate for this month will rise as more requests come in. '
    'Use Apr–May 2026 as the most mature comparison window.</div>',
    unsafe_allow_html=True,
)

# AI insight
with st.expander("🔮 AI Insights — Trend Analysis", expanded=True):
    monthly_stats = df.groupby("Refund Month", observed=True).agg(
        count=("Hubspot id","count"), credit=("credit_note_amount","sum")
    ).to_json()
    with st.spinner("Generating insights…"):
        text = ins.insight_overview(monthly_stats)
    bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
    st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — ENROLLMENTS vs REFUNDS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">② Enrollment Base & Refund Rate</div>',
            unsafe_allow_html=True)
st.plotly_chart(chart_enrollments_vs_refunds(df_onboard, df),
                use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SEGMENTATION
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">③ Segmentation — BU, Category, Course</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.plotly_chart(chart_bu_split(df), use_container_width=True)
with col2:
    st.plotly_chart(chart_category(df), use_container_width=True)

st.plotly_chart(chart_course(df), use_container_width=True)

with st.expander("🔮 AI Insights — Course & Segment Risk", expanded=False):
    course_stats = df.groupby("Course").agg(
        count=("Hubspot id","count"), credit=("credit_note_amount","sum")
    ).to_json()
    with st.spinner("Generating insights…"):
        text = ins.insight_course(course_stats)
    bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
    st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — PAYMENT TYPE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">④ Payment Type Analysis</div>',
            unsafe_allow_html=True)

col3, col4 = st.columns([1, 1])
with col3:
    st.plotly_chart(chart_upfront_type(df), use_container_width=True)
with col4:
    st.plotly_chart(chart_payment_mode(df), use_container_width=True)

with st.expander("🔮 AI Insights — Payment Type Risk", expanded=False):
    pay_stats = df.groupby("Upfront Payment / Non Upfront / Flexipay").agg(
        count=("Hubspot id","count"),
        avg_credit=("credit_note_amount","mean"),
        total_credit=("credit_note_amount","sum")
    ).to_json()
    with st.spinner("Generating insights…"):
        text = ins.insight_payment_type(pay_stats)
    bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
    st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — REFUND REASONS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑤ Why Are Students Refunding?</div>',
            unsafe_allow_html=True)

st.plotly_chart(chart_refund_reasons(df), use_container_width=True)

with st.expander("🔮 AI Insights — Refund Reasons", expanded=False):
    reason_stats = df.groupby("Refund Category").agg(
        count=("Hubspot id","count"), credit=("credit_note_amount","sum")
    ).to_json()
    with st.spinner("Generating insights…"):
        text = ins.insight_reasons(reason_stats)
    bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
    st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — DATE DIFFERENCE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑥ Timing Analysis — Days Between Key Events</div>',
            unsafe_allow_html=True)

st.plotly_chart(chart_date_diffs(df), use_container_width=True)

# Summary stats table
dd_cols = ["days_enroll_to_refund_req", "days_enroll_to_cohort_start", "days_cohort_to_refund_req"]
dd_labels = ["Enroll → Refund Request", "Enroll → Cohort Start", "Cohort Start → Refund Request"]
stats_df = pd.DataFrame({
    "Metric": dd_labels,
    "Mean": [df[c].mean() for c in dd_cols],
    "Median": [df[c].median() for c in dd_cols],
    "Min": [df[c].min() for c in dd_cols],
    "Max": [df[c].max() for c in dd_cols],
    "Blanks": [df[c].isna().sum() for c in dd_cols],
}).set_index("Metric").round(1)
st.dataframe(stats_df, use_container_width=True)

with st.expander("🔮 AI Insights — Timing Patterns", expanded=False):
    diff_stats = stats_df.to_json()
    with st.spinner("Generating insights…"):
        text = ins.insight_date_diffs(diff_stats)
    bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
    html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
    st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — COHORT & REGIONAL BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑦ Region, Onboarding Status & Learner Type</div>',
            unsafe_allow_html=True)

col5, col6 = st.columns([1, 1])
with col5:
    st.plotly_chart(chart_by_country(df), use_container_width=True)
with col6:
    st.plotly_chart(chart_onboarding_status(df), use_container_width=True)

col7, col8 = st.columns([1, 1])
with col7:
    st.plotly_chart(chart_new_vs_alumni(df), use_container_width=True)
with col8:
    st.plotly_chart(chart_trial_window(df), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — RAW DATA TABLE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑧ Filtered Data Table</div>',
            unsafe_allow_html=True)

display_cols = [
    "Hubspot id", "Cohort", "BU", "Category", "Course",
    "Country", "Upfront Payment / Non Upfront / Flexipay",
    "Payment Mode", "net_revenue", "credit_note_amount",
    "Refund Category", "Refund Month",
    "days_enroll_to_refund_req", "days_cohort_to_refund_req",
    "Refund request received in Trial Window",
    "Onboarding Status", "New / Alumni",
]
show_cols = [c for c in display_cols if c in df.columns]
st.dataframe(
    df[show_cols].rename(columns={
        "Upfront Payment / Non Upfront / Flexipay": "Payment Type",
        "net_revenue": "Net Revenue ($)",
        "credit_note_amount": "Credit Note ($)",
        "days_enroll_to_refund_req": "Days: Enroll→Request",
        "days_cohort_to_refund_req": "Days: Cohort→Request",
        "Refund request received in Trial Window": "In Trial Window",
    }),
    use_container_width=True,
    height=350,
)

csv_data = df[show_cols].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download filtered data as CSV",
                   data=csv_data,
                   file_name="ik_refund_filtered.csv",
                   mime="text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    "<span style='font-size:11px;color:#94A3B8;'>"
    "IK Refund Dashboard · Data: Google Sheets export · "
    "Add column AD (Agentic/IP) to source sheet to unlock Program filter · "
    "Built with Streamlit + Plotly"
    "</span>",
    unsafe_allow_html=True,
)
