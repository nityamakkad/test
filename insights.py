"""
AI-powered insight generation using Anthropic API.
Each function receives a small stats dict and returns bullet-point insights.
Results are cached per session so we don't re-call on every filter change.
"""

import json
import requests
import streamlit as st


MODEL = "claude-sonnet-4-20250514"
API_URL = "https://api.anthropic.com/v1/messages"


def _call_claude(prompt: str) -> str:
    """Call Anthropic API and return the text response."""
    try:
        resp = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={
                "model": MODEL,
                "max_tokens": 1000,
                "system": (
                    "You are a sharp data analyst at an edtech company called Interview Kickstart. "
                    "You receive summary statistics about student refunds and write 3–4 concise, "
                    "non-obvious, actionable insights as bullet points. "
                    "Be specific — use numbers from the data. "
                    "Don't state the obvious. Flag risks or patterns worth acting on. "
                    "Output plain bullet points, no headers, no markdown bold, no preamble."
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"• Insight generation unavailable: {e}"


@st.cache_data(ttl=300, show_spinner=False)
def insight_overview(stats: str) -> str:
    return _call_claude(
        f"Here are overall refund stats for the filtered dataset:\n{stats}\n"
        "Give 4 sharp insights about what this data reveals."
    )


@st.cache_data(ttl=300, show_spinner=False)
def insight_payment_type(stats: str) -> str:
    return _call_claude(
        f"Refund breakdown by payment type (Upfront / Flexipay / Non-Upfront):\n{stats}\n"
        "Give 3 insights focusing on risk differences between payment types and what IK should act on."
    )


@st.cache_data(ttl=300, show_spinner=False)
def insight_reasons(stats: str) -> str:
    return _call_claude(
        f"Top refund reasons and their credit note values:\n{stats}\n"
        "Give 3 insights: which reasons are most financially damaging, which are preventable, "
        "and any patterns worth flagging."
    )


@st.cache_data(ttl=300, show_spinner=False)
def insight_course(stats: str) -> str:
    return _call_claude(
        f"Refund counts and credit values broken down by course:\n{stats}\n"
        "Give 3 insights about which courses have disproportionate refund issues and possible causes."
    )


@st.cache_data(ttl=300, show_spinner=False)
def insight_date_diffs(stats: str) -> str:
    return _call_claude(
        f"Distribution stats for days between key events (enrollment→request, cohort start→request):\n{stats}\n"
        "Give 3 insights about what the timing patterns reveal — early vs late refund behaviour, "
        "trial window compliance, and any red flags."
    )


def build_stats(df, groupby_col, value_cols) -> str:
    """Helper: summarise a grouped dataframe to a JSON string for the prompt."""
    grp = df.groupby(groupby_col)[value_cols].sum()
    return grp.to_json(indent=2)
