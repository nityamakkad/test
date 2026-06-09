import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Colour palette ─────────────────────────────────────────────────────────
C_BLUE   = "#2563EB"
C_RED    = "#EF4444"
C_GREEN  = "#16A34A"
C_AMBER  = "#D97706"
C_TEAL   = "#0D9488"
C_SLATE  = "#64748B"

UPFRONT_COLORS = {
    "Upfront":     C_GREEN,
    "Flexipay":    C_AMBER,
    "Non upfront": C_RED,
    "Unknown":     C_SLATE,
    "Not Updated": C_SLATE,
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

def _apply(fig):
    fig.update_layout(**CHART_LAYOUT)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
    return fig


# ── KPI ────────────────────────────────────────────────────────────────────

def kpi_cards(df: pd.DataFrame, total_enrollments: int) -> dict:
    total_refunds = len(df)
    total_revenue = df["net_revenue"].sum()
    refund_pct    = (total_refunds / total_enrollments * 100) if total_enrollments else 0
    # Median — not mean; mean is skewed by 4 enrollments from 2024/2025
    avg_days      = df["days_enroll_to_refund_req"].dropna().median()
    trial_pct     = (df["Refund request received in Trial Window"]
                     .str.strip().str.lower().eq("yes").sum()
                     / total_refunds * 100) if total_refunds else 0
    return dict(
        total_refunds   = total_refunds,
        total_revenue   = total_revenue,
        refund_pct      = refund_pct,
        avg_days_to_req = avg_days,
        trial_pct       = trial_pct,
    )


# ── SECTION 1 ─────────────────────────────────────────────────────────────

def chart_quarterly_enroll_vs_refund(df_r: pd.DataFrame, df_o: pd.DataFrame) -> go.Figure:
    enr = df_o.groupby("enrollment_quarter").size().rename("enrollments").reset_index()
    ref = df_r.groupby("enrollment_quarter").size().rename("refunds").reset_index()
    merged = enr.merge(ref, on="enrollment_quarter", how="left").fillna({"refunds": 0})
    merged["refunds"] = merged["refunds"].astype(int)
    merged = merged[merged["enrollment_quarter"].notna()].sort_values("enrollment_quarter")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["enrollment_quarter"], y=merged["enrollments"],
        name="Enrollments", marker_color="#BFDBFE", opacity=0.9,
        text=merged["enrollments"], textposition="outside"))
    fig.add_trace(go.Bar(
        x=merged["enrollment_quarter"], y=merged["refunds"],
        name="Refunds", marker_color=C_RED, opacity=0.85,
        text=merged["refunds"], textposition="outside"))
    fig.update_layout(title="Enrollments vs Refund Count by Quarter",
                      barmode="group", yaxis_title="Count", **CHART_LAYOUT)
    return fig


def chart_monthly_refund_line(df: pd.DataFrame) -> go.Figure:
    month_order = ["Jan - 26","Feb - 26","Mar - 26","Apr - 26","May - 26","Jun - 26"]
    grp = df.groupby("Refund Month", observed=True).size().rename("count").reset_index()
    grp["Refund Month"] = pd.Categorical(
        grp["Refund Month"].astype(str), categories=month_order, ordered=True)
    grp = grp.sort_values("Refund Month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=grp["Refund Month"].astype(str), y=grp["count"],
        mode="lines+markers+text",
        text=grp["count"], textposition="top center",
        line=dict(color=C_BLUE, width=2.5),
        marker=dict(size=8, color=C_BLUE),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
        name="# Refunds"))
    fig.update_layout(title="Monthly Refund Count",
                      yaxis_title="# Refunds", xaxis_title="Refund Month",
                      **CHART_LAYOUT)
    return fig


# ── SECTION 2 ─────────────────────────────────────────────────────────────

def chart_enrollments_vs_refunds(df_o: pd.DataFrame, df_r: pd.DataFrame) -> go.Figure:
    enr = df_o.groupby("enrollment_month").size().rename("enrollments").reset_index()
    ref = df_r.groupby("enrollment_month").size().rename("refunds").reset_index()
    merged = enr.merge(ref, on="enrollment_month", how="left").fillna({"refunds": 0})
    merged["refund_pct"] = (merged["refunds"] / merged["enrollments"] * 100).round(1)
    merged = merged[merged["enrollment_month"].notna()].sort_values("enrollment_month")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=merged["enrollment_month"], y=merged["enrollments"],
                         name="Enrollments", marker_color="#BFDBFE", opacity=0.9),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=merged["enrollment_month"], y=merged["refunds"],
                         name="Refunds", marker_color=C_RED, opacity=0.85),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=merged["enrollment_month"], y=merged["refund_pct"],
                             name="Refund %", mode="lines+markers",
                             line=dict(color="#1E293B", width=2), marker=dict(size=6)),
                  secondary_y=True)
    fig.update_yaxes(title_text="Count", secondary_y=False)
    fig.update_yaxes(title_text="Refund %", secondary_y=True, showgrid=False)
    fig.update_layout(title="Enrollments vs Refunds by Month (Enrollment Cohort)",
                      barmode="overlay", **CHART_LAYOUT)
    return fig


# ── SECTION 3 — BU ────────────────────────────────────────────────────────

def chart_bu_count_pie(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("BU").size().reset_index(name="count")
    fig = go.Figure(go.Pie(
        labels=grp["BU"], values=grp["count"],
        hole=0.45, marker_colors=[C_BLUE, C_AMBER],
        textinfo="label+percent+value"))
    fig.update_layout(title="Refund Count by BU", **CHART_LAYOUT)
    return fig


def chart_bu_amount_pie(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("BU").agg(amount=("amount_refunded","sum")).reset_index()
    fig = go.Figure(go.Pie(
        labels=grp["BU"], values=grp["amount"],
        hole=0.45, marker_colors=[C_BLUE, C_AMBER],
        textinfo="label+percent",
        hovertemplate="%{label}: $%{value:,.0f}<extra></extra>"))
    fig.update_layout(title="Total Amount Refunded by BU ($)", **CHART_LAYOUT)
    return fig


def chart_category(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Category")
             .agg(count=("Hubspot id","count"),
                  amount=("amount_refunded","sum"))
             .sort_values("count", ascending=True).reset_index())
    fig = go.Figure(go.Bar(
        y=grp["Category"], x=grp["count"],
        orientation="h", marker_color=C_BLUE, opacity=0.85,
        text=[f"${v:,.0f}" for v in grp["amount"]],
        textposition="outside"))
    fig.update_layout(title="Refunds by Program Category",
                      xaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


def chart_course(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Course")
             .agg(count=("Hubspot id","count"),
                  amount=("amount_refunded","sum"))
             .sort_values("count", ascending=False).head(15).reset_index())
    fig = px.bar(grp, x="Course", y="count",
                 color="count",
                 color_continuous_scale=[[0,"#BFDBFE"],[1,C_BLUE]],
                 text=[f"${v/1000:.0f}K" for v in grp["amount"]])
    fig.update_traces(textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(title="Top Courses by Refund Volume ($ = amount refunded)",
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── SECTION 4 — PAYMENT ───────────────────────────────────────────────────

def chart_upfront_count(df: pd.DataFrame) -> go.Figure:
    col = "Upfront Payment / Non Upfront / Flexipay"
    grp = df.groupby(col).size().reset_index(name="count")
    grp.columns = ["type","count"]
    colors = [UPFRONT_COLORS.get(t, C_SLATE) for t in grp["type"]]
    fig = go.Figure(go.Bar(
        x=grp["type"], y=grp["count"],
        marker_color=colors,
        text=grp["count"], textposition="outside"))
    fig.update_layout(title="Refund Count by Payment Type",
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


def chart_upfront_amount(df: pd.DataFrame) -> go.Figure:
    col = "Upfront Payment / Non Upfront / Flexipay"
    grp = df.groupby(col).agg(amount=("amount_refunded","sum")).reset_index()
    grp.columns = ["type","amount"]
    colors = [UPFRONT_COLORS.get(t, C_SLATE) for t in grp["type"]]
    fig = go.Figure(go.Bar(
        x=grp["type"], y=grp["amount"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in grp["amount"]],
        textposition="outside"))
    fig.update_layout(title="Total Amount Refunded by Payment Type ($)",
                      yaxis_title="Amount Refunded ($)", **CHART_LAYOUT)
    return fig


def chart_payment_mode(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Payment Mode")
             .agg(count=("Hubspot id","count"),
                  amount=("amount_refunded","sum"))
             .sort_values("amount", ascending=True).reset_index())
    fig = go.Figure(go.Bar(
        y=grp["Payment Mode"], x=grp["amount"],
        orientation="h",
        marker=dict(color=grp["count"],
                    colorscale=[[0,"#BFDBFE"],[1,C_BLUE]],
                    showscale=True,
                    colorbar=dict(title="# Refunds", thickness=12)),
        text=[f"n={v}" for v in grp["count"]],
        textposition="outside"))
    fig.update_layout(title="Amount Refunded by Payment Mode (colour = count)",
                      xaxis_title="Amount Refunded ($)", **CHART_LAYOUT)
    return fig


# ── SECTION 5 — REFUND REASONS ────────────────────────────────────────────

def chart_refund_reasons(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Refund Category")
             .agg(count=("Hubspot id","count"),
                  amount=("amount_refunded","sum"))
             .sort_values("count", ascending=True).reset_index())
    norm = (grp["count"] - grp["count"].min()) / (grp["count"].max() - grp["count"].min() + 1)
    colors = [f"rgba(239,{int(68+50*(1-n))},{int(68+50*(1-n))},{0.5+0.5*n})" for n in norm]
    fig = go.Figure(go.Bar(
        y=grp["Refund Category"], x=grp["count"],
        orientation="h", marker_color=colors,
        text=[f"${v:,.0f}" for v in grp["amount"]],
        textposition="outside"))
    fig.update_layout(title="Refund Reasons — Count & Amount Refunded ($)",
                      xaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── SECTION 6 — TIMING ────────────────────────────────────────────────────

def chart_days_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram: days from enrollment to refund request."""
    vals = df["days_enroll_to_refund_req"].dropna()
    median_val = vals.median()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=vals, nbinsx=25,
        marker_color=C_BLUE, opacity=0.8, name="# Refunds"))
    fig.add_vline(x=median_val, line_dash="dash", line_color=C_RED, line_width=2,
                  annotation_text=f"Median: {median_val:.0f}d",
                  annotation_position="top right")
    fig.update_layout(title="Days: Enrollment → Refund Request",
                      xaxis_title="Days", yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


def chart_days_buckets(df: pd.DataFrame) -> go.Figure:
    """Bucketed bar: enrollment → refund request in bands."""
    vals = df["days_enroll_to_refund_req"].dropna()
    bins   = [-1, 7, 14, 30, 60, 10000]
    labels = ["0–7 days", "8–14 days", "15–30 days", "31–60 days", "60+ days"]
    bucketed = pd.cut(vals, bins=bins, labels=labels)
    grp = bucketed.value_counts().reindex(labels).reset_index()
    grp.columns = ["bucket","count"]
    bucket_colors = [C_RED, "#F97316", C_AMBER, C_TEAL, C_SLATE]
    fig = go.Figure(go.Bar(
        x=grp["bucket"], y=grp["count"],
        marker_color=bucket_colors,
        text=grp["count"], textposition="outside"))
    fig.update_layout(title="Enrollment → Request (Bucketed)",
                      xaxis_title="Days After Enrollment",
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


def chart_cohort_to_request_buckets(df: pd.DataFrame) -> go.Figure:
    """Bucketed bar: cohort start → refund request.
    Negative = refunded before cohort started (enrolled for future cohort).
    Positive = refunded after cohort started.
    """
    vals = df["days_cohort_to_refund_req"].dropna()
    bins   = [-10000, -1, 7, 14, 30, 60, 10000]
    labels = ["Before cohort started", "0-7 days", "8-14 days", "15-30 days", "31-60 days", "60+ days"]
    bucketed = pd.cut(vals, bins=bins, labels=labels)
    grp = bucketed.value_counts().reindex(labels).reset_index()
    grp.columns = ["bucket","count"]
    bucket_colors = [C_SLATE, C_RED, "#F97316", C_AMBER, C_TEAL, "#6366F1"]
    fig = go.Figure(go.Bar(
        x=grp["bucket"], y=grp["count"],
        marker_color=bucket_colors,
        text=grp["count"], textposition="outside"))
    fig.update_layout(
        title="Cohort Start → Request (Bucketed)",
        xaxis_title="Days After Cohort Start (negative = before cohort)",
        yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── SECTION 7 — REGION / OB / LEARNER ────────────────────────────────────

def chart_by_country(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Country").agg(
        count=("Hubspot id","count"),
        amount=("amount_refunded","sum")).reset_index()
    fig = px.bar(grp, x="Country", y="count",
                 text=[f"${v/1000:.0f}K" for v in grp["amount"]],
                 color="Country",
                 color_discrete_sequence=[C_BLUE, C_TEAL, C_AMBER])
    fig.update_traces(textposition="outside")
    fig.update_layout(title="Refunds by Country ($ = amount refunded)",
                      showlegend=False, yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


def chart_onboarding_status(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Onboarding Status").agg(
        count=("Hubspot id","count"),
        amount=("amount_refunded","sum")).reset_index()
    fig = px.bar(grp, x="Onboarding Status", y="count",
                 color="Onboarding Status",
                 color_discrete_sequence=[C_BLUE, C_AMBER, C_RED, C_SLATE],
                 text="count")
    fig.update_traces(textposition="outside")
    fig.update_layout(title="Refunds by Onboarding Status",
                      yaxis_title="# Refunds", showlegend=False, **CHART_LAYOUT)
    return fig


def chart_new_vs_alumni(df: pd.DataFrame) -> go.Figure:
    month_order = ["Jan - 26","Feb - 26","Mar - 26","Apr - 26","May - 26","Jun - 26"]
    grp = df.groupby(["Refund Month","New / Alumni"], observed=True).size().reset_index(name="count")
    fig = px.bar(grp, x="Refund Month", y="count", color="New / Alumni",
                 barmode="group",
                 color_discrete_map={"New":C_BLUE,"Alumni":C_AMBER,"Unknown":C_SLATE,"Not Updated":C_SLATE})
    fig.update_layout(title="New vs Alumni Refunds by Month", **CHART_LAYOUT)
    return fig


def chart_trial_window(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Refund request received in Trial Window").agg(
        count=("Hubspot id","count")).reset_index()
    grp.columns = ["trial","count"]
    color_map = {"Yes":C_GREEN,"No":C_RED,"Unknown":C_SLATE,"Not Updated":C_SLATE}
    colors = [color_map.get(t, C_SLATE) for t in grp["trial"]]
    fig = go.Figure(go.Bar(
        x=grp["trial"], y=grp["count"],
        marker_color=colors,
        text=grp["count"], textposition="outside"))
    fig.update_layout(title="Refund Request Within Trial Window",
                      xaxis_title="In Trial Window",
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── SECTION — ELIGIBLE AS PER REFUND POLICY ──────────────────────────────

def chart_eligible_policy(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Eligible as per refund policy").agg(
        count=("Hubspot id","count"),
        amount=("amount_refunded","sum")).reset_index()
    grp.columns = ["eligible","count","amount"]
    color_map = {"Yes":C_GREEN,"No":C_RED,"Not Updated":C_SLATE}
    colors = [color_map.get(e, C_SLATE) for e in grp["eligible"]]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("# Refunds by Policy Eligibility",
                                        "Amount Refunded by Policy Eligibility ($)"))
    fig.add_trace(go.Bar(x=grp["eligible"], y=grp["count"],
                         marker_color=colors, text=grp["count"],
                         textposition="outside", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=grp["eligible"], y=grp["amount"],
                         marker_color=colors,
                         text=[f"${v:,.0f}" for v in grp["amount"]],
                         textposition="outside", showlegend=False), row=1, col=2)
    fig.update_layout(title="Eligible as per Refund Policy", **CHART_LAYOUT)
    return fig
