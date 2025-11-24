import streamlit as st
import pandas as pd

def render_history_page():
    st.markdown("### Access Request History")

    history = st.session_state.get("history", [])

    if not history:
        st.info("No history found.")
        return

    df = pd.DataFrame([{
        "timestamp": h["timestamp"],
        "request_id": h["request"]["request_id"],
        "user_id": h["request"]["user_id"],
        "resource": h["request"]["requested_resource_name"],
        "decision": h["decision"],
        "severity": h["severity"],
        "score": h["net_score"]
    } for h in history])

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button("Download CSV", data=csv, file_name="history.csv")
