import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Colour palette ────────────────────────────────────────────────────────────
C_BLUE    = "#2563EB"
C_RED     = "#EF4444"
C_GREEN   = "#16A34A"
C_AMBER   = "#D97706"
C_TEAL    = "#0D9488"
C_VIOLET  = "#7C3AED"
C_SLATE   = "#64748B"

CATEGORY_COLORS = {
    "Switch-up":   "#6366F1",
    "Edge-up SU":  "#0EA5E9",
    "Edge-up LU":  "#10B981",
    "Level-up":    "#F59E0B",
    "Step-up":     "#F97316",
    "Agent-up":    "#8B5CF6",
    "Pathway":     "#EC4899",
    "Unknown":     "#94A3B8",
}

UPFRONT_COLORS = {
    "Upfront":     C_GREEN,
    "Flexipay":    C_AMBER,
    "Non upfront": C_RED,
    "Unknown":     C_SLATE,
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


# ── KPI helper ────────────────────────────────────────────────────────────────

def kpi_cards(df: pd.DataFrame, total_enrollments: int) -> dict:
    total_refunds   = len(df)
    total_credit    = df["credit_note_amount"].sum()
    total_revenue   = df["net_revenue"].sum()
    refund_pct      = (total_refunds / total_enrollments * 100) if total_enrollments else 0
    avg_days        = df["days_enroll_to_refund_req"].dropna().mean()
    trial_pct       = (df["Refund request received in Trial Window"].str.lower().eq("yes").sum()
                       / total_refunds * 100) if total_refunds else 0
    return dict(
        total_refunds   = total_refunds,
        total_credit    = total_credit,
        total_revenue   = total_revenue,
        refund_pct      = refund_pct,
        avg_days_to_req = avg_days,
        trial_pct       = trial_pct,
    )


# ── 1. Refunds by Month ───────────────────────────────────────────────────────

def chart_refunds_by_month(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Refund Month", observed=True)
             .agg(count=("Hubspot id","count"),
                  credit=("credit_note_amount","sum"))
             .reset_index())
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=grp["Refund Month"].astype(str), y=grp["count"],
        name="# Refunds", marker_color=C_BLUE, opacity=0.85), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=grp["Refund Month"].astype(str), y=grp["credit"]/1000,
        name="Credit Note ($K)", mode="lines+markers",
        line=dict(color=C_RED, width=2.5), marker=dict(size=7)), secondary_y=True)
    fig.update_yaxes(title_text="# Refunds", secondary_y=False)
    fig.update_yaxes(title_text="Credit Note ($K)", secondary_y=True, showgrid=False)
    fig.update_layout(title="Monthly Refund Volume & Credit Value", **CHART_LAYOUT)
    return fig


# ── 2. Refund % by Quarter (enrollments base) ─────────────────────────────────

def chart_refund_pct_by_quarter(df_r: pd.DataFrame, df_o: pd.DataFrame) -> go.Figure:
    enroll_q = df_o.groupby("enrollment_quarter").size().rename("enrollments")
    refund_q  = df_r.groupby("enrollment_quarter").size().rename("refunds")
    merged = pd.concat([enroll_q, refund_q], axis=1).dropna(subset=["enrollments"])
    merged["refund_pct"] = (merged["refunds"].fillna(0) / merged["enrollments"] * 100).round(1)
    merged = merged.reset_index().sort_values("enrollment_quarter")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=merged["enrollment_quarter"], y=merged["refund_pct"],
        text=[f"{v}%" for v in merged["refund_pct"]],
        textposition="outside", marker_color=C_BLUE, opacity=0.85,
        name="Refund %"))
    fig.update_layout(title="Refund % by Enrollment Quarter", yaxis_title="Refund %", **CHART_LAYOUT)
    return fig


# ── 3. Refund by Country ──────────────────────────────────────────────────────

def chart_by_country(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Country").agg(
        count=("Hubspot id","count"),
        credit=("credit_note_amount","sum")).reset_index()
    grp["credit_k"] = (grp["credit"]/1000).round(1)
    fig = px.bar(grp, x="Country", y="count",
                 text=[f"${v}K" for v in grp["credit_k"]],
                 color="Country", color_discrete_sequence=[C_BLUE, C_TEAL, C_AMBER])
    fig.update_traces(textposition="outside")
    fig.update_layout(title="Refunds by Country", showlegend=False,
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── 4. BU Split ───────────────────────────────────────────────────────────────

def chart_bu_split(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("BU").agg(
        count=("Hubspot id","count"),
        credit=("credit_note_amount","sum")).reset_index()
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("# Refunds by BU","Credit Note by BU ($)"),
                        specs=[[{"type":"pie"},{"type":"pie"}]])
    fig.add_trace(go.Pie(labels=grp["BU"], values=grp["count"],
                         hole=0.45, marker_colors=[C_BLUE, C_AMBER],
                         textinfo="label+percent"), row=1, col=1)
    fig.add_trace(go.Pie(labels=grp["BU"], values=grp["credit"],
                         hole=0.45, marker_colors=[C_BLUE, C_AMBER],
                         textinfo="label+percent"), row=1, col=2)
    fig.update_layout(title="BU Split — Volume & Credit", **CHART_LAYOUT)
    return fig


# ── 5. Category breakdown ─────────────────────────────────────────────────────

def chart_category(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Category")
             .agg(count=("Hubspot id","count"),
                  credit=("credit_note_amount","sum"))
             .sort_values("count", ascending=True).reset_index())
    colors = [CATEGORY_COLORS.get(c, C_SLATE) for c in grp["Category"]]
    fig = go.Figure(go.Bar(
        y=grp["Category"], x=grp["count"],
        orientation="h", marker_color=colors,
        text=[f"${v/1000:.0f}K" for v in grp["credit"]],
        textposition="outside"))
    fig.update_layout(title="Refunds by Program Category",
                      xaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── 6. Course breakdown ───────────────────────────────────────────────────────

def chart_course(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Course")
             .agg(count=("Hubspot id","count"),
                  credit=("credit_note_amount","sum"))
             .sort_values("count", ascending=False).head(15).reset_index())
    fig = px.bar(grp, x="Course", y="count",
                 color="count",
                 color_continuous_scale=[[0, "#BFDBFE"], [1, C_BLUE]],
                 text=[f"${v/1000:.0f}K" for v in grp["credit"]])
    fig.update_traces(textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(title="Top Courses by Refund Volume",
                      yaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── 7. Payment mode ───────────────────────────────────────────────────────────

def chart_payment_mode(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Payment Mode")
             .agg(count=("Hubspot id","count"),
                  credit=("credit_note_amount","sum"))
             .sort_values("credit", ascending=True).reset_index())
    fig = go.Figure(go.Bar(
        y=grp["Payment Mode"], x=grp["credit"]/1000,
        orientation="h",
        marker=dict(color=grp["count"],
                    colorscale=[[0,"#BFDBFE"],[1,C_BLUE]],
                    showscale=True,
                    colorbar=dict(title="# Refunds", thickness=12)),
        text=[f"n={v}" for v in grp["count"]],
        textposition="outside"))
    fig.update_layout(title="Credit Note by Payment Mode ($K)",
                      xaxis_title="Credit Note ($K)", **CHART_LAYOUT)
    return fig


# ── 8. Upfront type comparison ────────────────────────────────────────────────

def chart_upfront_type(df: pd.DataFrame) -> go.Figure:
    col = "Upfront Payment / Non Upfront / Flexipay"
    grp = df.groupby(col).agg(
        count=("Hubspot id","count"),
        credit=("credit_note_amount","sum")).reset_index()
    grp.columns = ["type","count","credit"]
    colors = [UPFRONT_COLORS.get(t, C_SLATE) for t in grp["type"]]

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("# Refunds by Payment Type","Avg Credit Note ($)"))
    fig.add_trace(go.Bar(x=grp["type"], y=grp["count"],
                         marker_color=colors, showlegend=False,
                         text=grp["count"], textposition="outside"), row=1, col=1)
    avg_credit = grp["credit"] / grp["count"]
    fig.add_trace(go.Bar(x=grp["type"], y=avg_credit.round(0),
                         marker_color=colors, showlegend=False,
                         text=[f"${v:,.0f}" for v in avg_credit],
                         textposition="outside"), row=1, col=2)
    fig.update_layout(title="Upfront vs Flexipay vs Non-Upfront Analysis", **CHART_LAYOUT)
    return fig


# ── 9. Refund Category (reasons) ─────────────────────────────────────────────

def chart_refund_reasons(df: pd.DataFrame) -> go.Figure:
    grp = (df.groupby("Refund Category")
             .agg(count=("Hubspot id","count"),
                  credit=("credit_note_amount","sum"))
             .sort_values("count", ascending=True).reset_index())
    # colour gradient: more refunds = deeper red
    norm = (grp["count"] - grp["count"].min()) / (grp["count"].max() - grp["count"].min() + 1)
    colors = [f"rgba(239,{int(68 + 50*(1-n))},{int(68 + 50*(1-n))},{0.5+0.5*n})" for n in norm]

    fig = go.Figure(go.Bar(
        y=grp["Refund Category"], x=grp["count"],
        orientation="h", marker_color=colors,
        text=[f"${v/1000:.0f}K" for v in grp["credit"]],
        textposition="outside"))
    fig.update_layout(title="Refund Reasons — Frequency & Credit Value",
                      xaxis_title="# Refunds", **CHART_LAYOUT)
    return fig


# ── 10. Date-diff histograms ──────────────────────────────────────────────────

def chart_date_diffs(df: pd.DataFrame) -> go.Figure:
    pairs = [
        ("days_enroll_to_refund_req",   "Enrollment → Refund Request", C_BLUE),
        ("days_enroll_to_cohort_start", "Enrollment → Cohort Start",   C_TEAL),
        ("days_cohort_to_refund_req",   "Cohort Start → Refund Request", C_AMBER),
    ]
    fig = make_subplots(rows=1, cols=3, subplot_titles=[p[1] for p in pairs])
    for i, (col, label, color) in enumerate(pairs, 1):
        vals = df[col].dropna()
        fig.add_trace(go.Histogram(
            x=vals, nbinsx=20, name=label,
            marker_color=color, opacity=0.8,
            showlegend=False), row=1, col=i)
        fig.add_vline(x=vals.mean(), line_dash="dash",
                      line_color="#1E293B", row=1, col=i)
    fig.update_layout(title="Days Between Key Events (vertical line = mean)", **CHART_LAYOUT)
    return fig


# ── 11. Onboarding Status ─────────────────────────────────────────────────────

def chart_onboarding_status(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Onboarding Status").agg(
        count=("Hubspot id","count"),
        credit=("credit_note_amount","sum")).reset_index()
    fig = px.bar(grp, x="Onboarding Status", y="count",
                 color="Onboarding Status",
                 color_discrete_sequence=[C_BLUE, C_AMBER, C_RED, C_SLATE],
                 text="count")
    fig.update_traces(textposition="outside")
    fig.update_layout(title="Refunds by Onboarding Status",
                      yaxis_title="# Refunds", showlegend=False, **CHART_LAYOUT)
    return fig


# ── 12. Trial window ─────────────────────────────────────────────────────────

def chart_trial_window(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby("Refund request received in Trial Window").agg(
        count=("Hubspot id","count"),
        credit=("credit_note_amount","sum")).reset_index()
    grp.columns = ["trial","count","credit"]
    color_map = {"Yes": C_GREEN, "No": C_RED, "Unknown": C_SLATE}
    colors = [color_map.get(t, C_SLATE) for t in grp["trial"]]
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("# Refunds", "Credit Note ($K)"))
    fig.add_trace(go.Bar(x=grp["trial"], y=grp["count"],
                         marker_color=colors, text=grp["count"],
                         textposition="outside", showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=grp["trial"], y=grp["credit"]/1000,
                         marker_color=colors,
                         text=[f"${v:.0f}K" for v in grp["credit"]/1000],
                         textposition="outside", showlegend=False), row=1, col=2)
    fig.update_layout(title="Within Trial Window vs Outside",
                      xaxis_title="In Trial Window", **CHART_LAYOUT)
    return fig


# ── 13. New vs Alumni ─────────────────────────────────────────────────────────

def chart_new_vs_alumni(df: pd.DataFrame) -> go.Figure:
    grp = df.groupby(["Refund Month", "New / Alumni"], observed=True).size().reset_index(name="count")
    fig = px.bar(grp, x="Refund Month", y="count", color="New / Alumni",
                 barmode="group",
                 color_discrete_map={"New": C_BLUE, "Alumni": C_AMBER, "Unknown": C_SLATE})
    fig.update_layout(title="New vs Alumni Refunds by Month", **CHART_LAYOUT)
    return fig


# ── 14. Enrollment volume by month (onboarding) ───────────────────────────────

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
                         name="Refunds", marker_color=C_RED, opacity=0.8),
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
