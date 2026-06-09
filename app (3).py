"""
IK Refund Analysis Dashboard
Production-ready Streamlit app.
Run: streamlit run app.py
"""

import os
import pandas as pd
import numpy as np
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

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="IK Refund Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

  .dash-title {
    font-size: 32px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.5px;
    text-decoration: underline;
    text-underline-offset: 6px;
    text-decoration-color: #2563EB;
    margin-bottom: 2px;
  }

  .kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    height: 100%;
  }
  .kpi-label { font-size: 11px; color: #64748B; letter-spacing: 0.06em; text-transform: uppercase; }
  .kpi-value { font-size: 24px; font-weight: 700; color: #1E293B; margin: 6px 0 4px 0; }
  .kpi-sub   { font-size: 11px; color: #94A3B8; }

  .section-header {
    font-size: 17px; font-weight: 600; color: #1E293B;
    border-left: 4px solid #2563EB;
    padding-left: 10px; margin: 28px 0 14px 0;
  }

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

  .warn-box {
    background: #FFFBEB; border: 1px solid #FCD34D;
    border-radius: 8px; padding: 10px 14px;
    font-size: 13px; color: #92400E; margin-bottom: 12px;
  }

  .calc-note {
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 8px; padding: 10px 14px;
    font-size: 12.5px; color: #1E40AF; margin-bottom: 12px;
  }

  section[data-testid="stSidebar"] { background: #F8FAFC; }
  #MainMenu, footer { visibility: hidden; }
  header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOAD
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading data…")
def get_data():
    df_r = load_refund("refund_data.csv")
    df_o = load_onboarding("onboarding_data.csv")
    return df_r, df_o

df_raw, df_onboard = get_data()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔍 Filters")
    st.caption("Applied to all charts and KPIs")
    st.divider()

    def multiselect_filter(label, series, key):
        # Convert everything to string, treat blanks as "Not Updated"
        clean = series.astype(str).str.strip()
        clean = clean.replace({"nan": "Not Updated", "": "Not Updated", "None": "Not Updated"})
        all_opts = sorted(clean.unique().tolist())
        return st.multiselect(label, options=all_opts, default=all_opts, key=key), clean

    # Month filter (refund month)
    month_order = ["Jan - 26", "Feb - 26", "Mar - 26", "Apr - 26", "May - 26", "Jun - 26"]
    avail_months = [m for m in month_order if m in df_raw["Refund Month"].astype(str).values]
    sel_month = st.multiselect("📅 Refund Month", options=avail_months,
                               default=avail_months, key="month")

    # Quarter filter (derived from refund date)
    avail_quarters = sorted(df_raw["refund_quarter"].dropna().unique().tolist())
    sel_quarter = st.multiselect("🗓️ Refund Quarter", options=avail_quarters,
                                 default=avail_quarters, key="quarter")

    st.divider()

    sel_country,  _c1 = multiselect_filter("🌍 Country / Region",   df_raw["Country"],  "country")
    sel_bu,       _c2 = multiselect_filter("🏢 Business Unit",       df_raw["BU"],       "bu")
    sel_category, _c3 = multiselect_filter("📂 Program Category",    df_raw["Category"], "category")
    sel_course,   _c4 = multiselect_filter("🎓 Course",              df_raw["Course"],   "course")
    sel_payment,  _c5 = multiselect_filter("💳 Payment Mode",        df_raw["Payment Mode"], "payment_mode")
    sel_upfront,  _c6 = multiselect_filter("📦 Payment Type",
                                           df_raw["Upfront Payment / Non Upfront / Flexipay"], "upfront")
    sel_new_alumni, _c7 = multiselect_filter("👤 New / Alumni",      df_raw["New / Alumni"], "new_alumni")
    sel_ob_status,  _c8 = multiselect_filter("✅ Onboarding Status", df_raw["Onboarding Status"], "ob_status")
    sel_trial,      _c9 = multiselect_filter("⏱️ In Trial Window",
                                             df_raw["Refund request received in Trial Window"], "trial")

    st.divider()
    st.caption("Q1=Jan–Mar · Q2=Apr–Jun · Q3=Jul–Sep · Q4=Oct–Dec")


# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────

def apply_str_filter(df, col, sel):
    clean = df[col].astype(str).str.strip().replace(
        {"nan": "Not Updated", "": "Not Updated", "None": "Not Updated"})
    return df[clean.isin(sel)]

df = df_raw.copy()

# Month & Quarter filters
if sel_month:
    df = df[df["Refund Month"].astype(str).isin(sel_month)]
if sel_quarter:
    df = df[df["refund_quarter"].isin(sel_quarter)]

# All other filters
df = apply_str_filter(df, "Country",   sel_country)
df = apply_str_filter(df, "BU",        sel_bu)
df = apply_str_filter(df, "Category",  sel_category)
df = apply_str_filter(df, "Course",    sel_course)
df = apply_str_filter(df, "Payment Mode", sel_payment)
df = apply_str_filter(df, "Upfront Payment / Non Upfront / Flexipay", sel_upfront)
df = apply_str_filter(df, "New / Alumni",        sel_new_alumni)
df = apply_str_filter(df, "Onboarding Status",   sel_ob_status)
df = apply_str_filter(df, "Refund request received in Trial Window", sel_trial)

# Filter onboarding by same month/quarter selection for enrollment KPI
df_onboard_filtered = df_onboard.copy()
if sel_month:
    month_map = {
        "Jan - 26": "2026-01", "Feb - 26": "2026-02", "Mar - 26": "2026-03",
        "Apr - 26": "2026-04", "May - 26": "2026-05", "Jun - 26": "2026-06"
    }
    selected_periods = [month_map[m] for m in sel_month if m in month_map]
    if selected_periods:
        df_onboard_filtered = df_onboard_filtered[
            df_onboard_filtered["enrollment_month"].isin(selected_periods)]

if sel_quarter:
    df_onboard_filtered = df_onboard_filtered[
        df_onboard_filtered["enrollment_quarter"].isin(sel_quarter)]

total_enrollments = len(df_onboard_filtered)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="dash-title">📊 IK Refund Analysis Dashboard</div>',
            unsafe_allow_html=True)
st.markdown(
    f"<span style='color:#64748B;font-size:13px;'>"
    f"Source: <code>refund_data.csv</code> · <code>onboarding_data.csv</code> · "
    f"Showing <b>{len(df)}</b> of <b>{len(df_raw)}</b> refund records"
    f"</span>",
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

if len(df) == 0:
    st.warning("No records match the current filters. Please adjust your selection.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────

kpi = kpi_cards(df, total_enrollments)

# Parse amount_refunded properly (it's money with commas in raw data, already cleaned in loader)
total_refunded_amt = df["amount_refunded"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)

kpi_data = [
    (c1, "Total Refunds",        f"{kpi['total_refunds']}",
         "drops in selected period"),
    (c2, "Total Enrollments",    f"{total_enrollments:,}",
         "deposits paid in period"),
    (c3, "Refund Rate",          f"{kpi['refund_pct']:.1f}%",
         "refunds ÷ enrollments"),
    (c4, "Total Refunded Amt",   f"${total_refunded_amt:,.0f}",
         "actual cash refunded"),
    (c5, "Avg Days to Request",
         f"{kpi['avg_days_to_req']:.0f} days" if not pd.isna(kpi['avg_days_to_req']) else "—",
         "enrollment → refund request"),
    (c6, "In Trial Window",      f"{kpi['trial_pct']:.0f}%",
         "refunds within trial"),
]

for col, label, value, sub in kpi_data:
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

# Calculation transparency note
st.markdown(
    '<div class="calc-note">'
    '📐 <b>How metrics are calculated:</b> '
    'Refund Rate = refund records ÷ enrollments (Deposit Paid Date) for the same period · '
    'Avg Days to Request = Refund Request Date by learner − Date of Receipt (enrollment date) · '
    'Total Refunded Amt = sum of "Amount refunded" column (actual cash returned, not credit note)'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — TRENDS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">① Monthly & Quarterly Trends</div>',
            unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(chart_refunds_by_month(df), use_container_width=True)
with col_b:
    st.plotly_chart(chart_refund_pct_by_quarter(df, df_onboard), use_container_width=True)

st.markdown(
    '<div class="warn-box">⚠️ <b>Maturity note:</b> Jun-26 refund data is still accruing — '
    'refund rate for this month will rise as more requests come in. '
    'Use Apr–May 2026 as the most mature comparison window.</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — ENROLLMENT BASE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">② Enrollment Base & Refund Rate by Month</div>',
            unsafe_allow_html=True)
st.plotly_chart(chart_enrollments_vs_refunds(df_onboard_filtered, df),
                use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SEGMENTATION
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">③ Segmentation — BU, Category, Course</div>',
            unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(chart_bu_split(df), use_container_width=True)
with col2:
    st.plotly_chart(chart_category(df), use_container_width=True)

st.plotly_chart(chart_course(df), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — PAYMENT TYPE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">④ Payment Type Analysis</div>',
            unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(chart_upfront_type(df), use_container_width=True)
with col4:
    st.plotly_chart(chart_payment_mode(df), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — REFUND REASONS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑤ Why Are Students Refunding?</div>',
            unsafe_allow_html=True)
st.plotly_chart(chart_refund_reasons(df), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — DATE DIFFERENCE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑥ Timing Analysis — Days Between Key Events</div>',
            unsafe_allow_html=True)

st.markdown(
    '<div class="calc-note">'
    '📐 <b>How days are calculated:</b><br>'
    '• <b>Enrollment → Refund Request:</b> "Refund Request Date by learner" − "Date of Receipt" (enrollment date)<br>'
    '• <b>Enrollment → Cohort Start:</b> "Cohort Start Date" − "Date of Receipt"<br>'
    '• <b>Cohort Start → Refund Request:</b> "Refund Request Date by learner" − "Cohort Start Date"<br>'
    'All in calendar days. Blank dates are excluded from averages and shown as "Blanks" in the table below.'
    '</div>',
    unsafe_allow_html=True,
)

st.plotly_chart(chart_date_diffs(df), use_container_width=True)

dd_cols   = ["days_enroll_to_refund_req", "days_enroll_to_cohort_start", "days_cohort_to_refund_req"]
dd_labels = ["Enrollment → Refund Request", "Enrollment → Cohort Start", "Cohort Start → Refund Request"]
stats_df  = pd.DataFrame({
    "Metric":  dd_labels,
    "Mean":    [df[c].mean()   for c in dd_cols],
    "Median":  [df[c].median() for c in dd_cols],
    "Min":     [df[c].min()    for c in dd_cols],
    "Max":     [df[c].max()    for c in dd_cols],
    "Blanks":  [df[c].isna().sum() for c in dd_cols],
}).set_index("Metric").round(1)
st.dataframe(stats_df, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — REGION / ONBOARDING / LEARNER TYPE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑦ Region, Onboarding Status & Learner Type</div>',
            unsafe_allow_html=True)

col5, col6 = st.columns(2)
with col5:
    st.plotly_chart(chart_by_country(df), use_container_width=True)
with col6:
    st.plotly_chart(chart_onboarding_status(df), use_container_width=True)

col7, col8 = st.columns(2)
with col7:
    st.plotly_chart(chart_new_vs_alumni(df), use_container_width=True)
with col8:
    st.plotly_chart(chart_trial_window(df), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — AI INSIGHTS  (requires OPENAI_API_KEY in Streamlit secrets)
# ─────────────────────────────────────────────────────────────────────────────

api_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, "secrets") else ""

if api_key:
    import insights as ins
    ins.API_KEY = api_key

    st.markdown('<div class="section-header">⑧ AI-Generated Insights</div>',
                unsafe_allow_html=True)
    st.caption("Powered by Claude · Refreshes when filters change")

    col_i1, col_i2 = st.columns(2)

    with col_i1:
        with st.expander("📈 Trend & Volume Insights", expanded=True):
            stats = df.groupby("Refund Month", observed=True).agg(
                count=("Hubspot id","count"), credit=("credit_note_amount","sum")
            ).to_json()
            with st.spinner("Analysing trends…"):
                text = ins.insight_overview(stats)
            bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
            html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
            st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)

        with st.expander("💳 Payment Type Insights", expanded=False):
            stats = df.groupby("Upfront Payment / Non Upfront / Flexipay").agg(
                count=("Hubspot id","count"),
                total_credit=("credit_note_amount","sum")
            ).to_json()
            with st.spinner("Analysing payment types…"):
                text = ins.insight_payment_type(stats)
            bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
            html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
            st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)

    with col_i2:
        with st.expander("🎓 Course Risk Insights", expanded=True):
            stats = df.groupby("Course").agg(
                count=("Hubspot id","count"), credit=("credit_note_amount","sum")
            ).to_json()
            with st.spinner("Analysing courses…"):
                text = ins.insight_course(stats)
            bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
            html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
            st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)

        with st.expander("⚠️ Refund Reason Insights", expanded=False):
            stats = df.groupby("Refund Category").agg(
                count=("Hubspot id","count"), credit=("credit_note_amount","sum")
            ).to_json()
            with st.spinner("Analysing reasons…"):
                text = ins.insight_reasons(stats)
            bullets = [l.strip().lstrip("•-").strip() for l in text.strip().split("\n") if l.strip()]
            html = "<ul>" + "".join(f"<li>{b}</li>" for b in bullets if b) + "</ul>"
            st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="section-header">⑧ AI-Generated Insights</div>',
                unsafe_allow_html=True)
    st.info(
        "💡 **To enable AI insights:** Go to Streamlit Cloud → your app → "
        "**Settings → Secrets** and add:\n\n"
        "```\nOPENAI_API_KEY = \"your-key-here\"\n```\n\n"
        "Get your key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)",
        icon="🔑",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — RAW DATA TABLE
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-header">⑨ Filtered Data Table</div>',
            unsafe_allow_html=True)

display_cols = [
    "Hubspot id", "Cohort", "BU", "Category", "Course",
    "Country", "Upfront Payment / Non Upfront / Flexipay",
    "Payment Mode", "net_revenue", "amount_refunded", "credit_note_amount",
    "Refund Category", "Refund Month",
    "days_enroll_to_refund_req", "days_cohort_to_refund_req",
    "Refund request received in Trial Window",
    "Onboarding Status", "New / Alumni",
]
show_cols = [c for c in display_cols if c in df.columns]
st.dataframe(
    df[show_cols].rename(columns={
        "Upfront Payment / Non Upfront / Flexipay": "Payment Type",
        "net_revenue":          "Net Revenue ($)",
        "amount_refunded":      "Amount Refunded ($)",
        "credit_note_amount":   "Credit Note ($)",
        "days_enroll_to_refund_req":  "Days: Enroll→Request",
        "days_cohort_to_refund_req":  "Days: Cohort→Request",
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

st.divider()
st.markdown(
    "<span style='font-size:11px;color:#94A3B8;'>"
    "IK Refund Dashboard · Data: Google Sheets export · "
    "Add column AD (Agentic/IP) to refund sheet to unlock that filter · "
    "Built with Streamlit + Plotly"
    "</span>",
    unsafe_allow_html=True,
)
