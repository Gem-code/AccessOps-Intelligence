import streamlit as st
import pandas as pd
from datetime import datetime

def render_insights_page():
    st.markdown("### Analytics & Insights")

    hist = st.session_state.get("history", [])

    if not hist:
        st.info("Submit requests to populate analytics.")
        return

    # KPIs
    total = len(hist)
    high = sum(1 for h in hist if h["severity"] == "HIGH")
    med = sum(1 for h in hist if h["severity"] == "MEDIUM")
    low = total - high - med

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("High", high)
    c3.metric("Medium", med)
    c4.metric("Low", low)

    # Score trend
    df = pd.DataFrame([{
        "ts": datetime.fromisoformat(h["timestamp"]),
        "score": h["net_score"]
    } for h in hist])

    df = df.sort_values("ts")
    st.line_chart(df.set_index("ts")["score"])
