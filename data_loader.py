import pandas as pd
import numpy as np


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _parse_money(series: pd.Series) -> pd.Series:
    """Convert comma-formatted money strings like '8,500' to float. Blanks → NaN."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace({"nan": np.nan, "": np.nan, "None": np.nan})
        .astype(float)
    )


def _parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=False)


def _quarter_label(dt_series: pd.Series) -> pd.Series:
    """
    IK quarter definition:
      Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec
    Returns label like 'Q1-26'.
    """
    q = dt_series.dt.month.map(
        {1: "Q1", 2: "Q1", 3: "Q1",
         4: "Q2", 5: "Q2", 6: "Q2",
         7: "Q3", 8: "Q3", 9: "Q3",
         10: "Q4", 11: "Q4", 12: "Q4"}
    )
    yr = dt_series.dt.year.astype("Int64").astype(str).str[-2:]
    return q + "-" + yr


# ──────────────────────────────────────────────
# REFUND DATA
# ──────────────────────────────────────────────

def load_refund(path: str = "data/refund_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)

    # ── Date columns ──────────────────────────
    df["enrollment_date"]     = _parse_date(df["Date of Receipt"])
    df["cohort_start_date"]   = _parse_date(df["Cohort Start Date"])
    df["refund_request_date"] = _parse_date(df["Refund Request Date  by learner"])
    df["refund_date"]         = _parse_date(df["Refund Date"])

    # ── Money columns ─────────────────────────
    for col, alias in [
        ("Net Revenue",       "net_revenue"),
        ("Amount refunded",   "amount_refunded"),
        ("Credit Note Amount","credit_note_amount"),
        ("Amount Credited",   "amount_credited"),
        ("Flexipay Drop Amount",    "flexipay_drop_amount"),
        ("Non Upfront Drop Amount", "non_upfront_drop_amount"),
    ]:
        df[alias] = _parse_money(df[col])

    # ── Derived date-diff columns (in days) ───
    df["days_enroll_to_refund_req"]  = (df["refund_request_date"] - df["enrollment_date"]).dt.days
    df["days_enroll_to_cohort_start"]= (df["cohort_start_date"]   - df["enrollment_date"]).dt.days
    df["days_cohort_to_refund_req"]  = (df["refund_request_date"] - df["cohort_start_date"]).dt.days

    # ── Quarter / Month labels ─────────────────
    df["refund_quarter"]    = _quarter_label(df["refund_date"])
    df["enrollment_quarter"]= _quarter_label(df["enrollment_date"])
    df["enrollment_month"]  = df["enrollment_date"].dt.to_period("M").astype(str)

    # ── Normalise categorical strings ─────────
    str_cols = [
        "BU", "Category", "Course", "Country", "Payment Mode",
        "Upfront Payment / Non Upfront / Flexipay",
        "New / Alumni", "Refund Category", "Onboarding Status",
        "Refund request received in Trial Window",
        "Refund Month", "Student Retained / Dropped - For Retention",
    ]
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({"nan": "Unknown", "": "Unknown"})

    # keep Refund Month as a sortable label
    month_order = ["Jan - 26","Feb - 26","Mar - 26","Apr - 26","May - 26","Jun - 26"]
    df["Refund Month"] = pd.Categorical(df["Refund Month"], categories=month_order, ordered=True)

    return df


# ──────────────────────────────────────────────
# ONBOARDING DATA
# ──────────────────────────────────────────────

def load_onboarding(path: str = "data/onboarding_data.csv") -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df["enrollment_date"] = _parse_date(df["Deposit Paid Date"])
    df["enrollment_month"]  = df["enrollment_date"].dt.to_period("M").astype(str)
    df["enrollment_quarter"]= _quarter_label(df["enrollment_date"])
    # normalise status
    df["Status"] = df["Status"].astype(str).str.strip().replace({"nan": "Unknown", "": "Unknown"})
    return df
