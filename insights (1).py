"""
AI-powered insight generation using OpenAI API.
API key is injected from app.py via st.secrets.
"""

import requests
import streamlit as st

MODEL   = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"
API_KEY = ""  # Set from app.py: insights.API_KEY = api_key


def _call_openai(prompt: str) -> str:
    try:
        resp = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": MODEL,
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a sharp data analyst at an edtech company called Interview Kickstart. "
                            "You receive summary statistics about student refunds and write 3-4 concise, "
                            "non-obvious, actionable insights as bullet points. "
                            "Be specific — use numbers from the data. "
                            "Don't state the obvious. Flag risks or patterns worth acting on. "
                            "Output plain bullet points only, no headers, no bold, no preamble."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=20,
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Insight generation unavailable: {e}"


@st.cache_data(ttl=300, show_spinner=False)
def insight_overview(stats: str) -> str:
    return _call_openai(
        f"Monthly refund volume and credit note data:\n{stats}\n"
        "Give 4 sharp insights about what the trend reveals."
    )

@st.cache_data(ttl=300, show_spinner=False)
def insight_payment_type(stats: str) -> str:
    return _call_openai(
        f"Refund breakdown by payment type:\n{stats}\n"
        "Give 3 insights on risk differences and what IK should act on."
    )

@st.cache_data(ttl=300, show_spinner=False)
def insight_reasons(stats: str) -> str:
    return _call_openai(
        f"Refund reasons and credit values:\n{stats}\n"
        "Give 3 insights: most financially damaging reasons, preventable ones, patterns to flag."
    )

@st.cache_data(ttl=300, show_spinner=False)
def insight_course(stats: str) -> str:
    return _call_openai(
        f"Refund counts and credit by course:\n{stats}\n"
        "Give 3 insights about which courses have disproportionate refund issues and why."
    )
