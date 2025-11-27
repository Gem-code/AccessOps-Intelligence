# -------------------------------------------------------------
#  ACCESSOPS — CISO COMMAND CENTER  (UI + CLEAN STRUCTURE)
#  Full redesigned UI with animations, cards, transitions,
#  responsive layout, and blue cyber-security theme.
# -------------------------------------------------------------

import os
import json
import asyncio
import io
from datetime import datetime, timezone

import nest_asyncio
import streamlit as st
from streamlit_monaco import st_monaco
import plotly.graph_objects as go

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------

st.set_page_config(
    page_title="AccessOps Decision Engine — CISO Suite",
    page_icon="🛡️",
    layout="wide",
)

nest_asyncio.apply()

# -----------------------------------------------------
# GLOBAL THEME + ANIMATED UI
# -----------------------------------------------------

st.markdown(
    """
<style>

    /* Base app background */
    .stApp {
        background: #0d1117 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Fade-in animation for all cards */
    .fade-card {
        animation: fadeIn 0.6s ease-out;
    }

    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* Hover lift on cards */
    .card {
        transition: all 0.22s ease-out;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(59,130,246,0.25);
    }

    /* Gradient headers */
    .section-header {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        padding: 12px 18px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 12px;
        font-size: 1rem;
        color: #f8fafc;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    /* Header banner */
    .hero {
        padding: 28px;
        border-radius: 14px;
        background: linear-gradient(90deg, #1e3a8a, #1e40af);
        box-shadow: 0 8px 32px rgba(30,64,175,0.35);
        margin-bottom: 30px;
        animation: fadeIn 0.8s ease-out;
    }

    /* Buttons */
    div.stButton > button {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white !important;
        border-radius: 999px;
        border: none;
        padding: 0.75rem 1.6rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        transition: all 0.22s ease-out;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(37,99,235,0.45);
    }

    /* Text areas */
    .stTextArea textarea {
        background: #0f172a !important;
        color: #f1f5f9 !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px;
    }

    /* Monaco editor wrapper */
    .monaco-editor {
        border: 1px solid #1e293b;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 8px 18px rgba(0,0,0,0.35);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #111827 !important;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }

</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------
# HERO BANNER
# -----------------------------------------------------

st.markdown(
    """
<div class="hero">
    <h1 style="margin:0; color:white; font-size:32px; font-weight:700;">
        🛡️ AccessOps Decision Engine — CISO Command Center
    </h1>
    <p style="margin-top:8px; color:#dbeafe; font-size:17px;">
        Automated Identity Adjudication • Governance • Zero-Trust • NIST 800-53
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------
# LOAD ENGINE (your original import stays unchanged)
# -----------------------------------------------------

try:
    import accessops_engine
except ImportError:
    st.error("CRITICAL ERROR: accessops_engine.py missing.")
    st.stop()

engine = accessops_engine.AccessOpsEngine()

# -----------------------------------------------------
#  LAYOUT: 3 STEP PANELS
# -----------------------------------------------------

col1, col2 = st.columns([1.2, 1.8])

# =====================================================
#  STEP 1 — INPUTS
# =====================================================

with col1:
    st.markdown('<div class="section-header">Step 1 — User & Access Inputs</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card fade-card">', unsafe_allow_html=True)

        user_json = st.text_area("User Profile (JSON):", height=200)
        access_json = st.text_area("Access Package (JSON):", height=200)

        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
#  STEP 2 — POLICY & CODE EDITOR
# =====================================================

with col2:
    st.markdown('<div class="section-header">Step 2 — Policy & Evaluation Logic</div>', unsafe_allow_html=True)

    st.markdown('<div class="card fade-card">', unsafe_allow_html=True)

    st.write("### Policy YAML")
    policy_yaml = st.text_area("Paste Policy YAML", height=250)

    st.write("### Decision Logic (Python)")
    decision_python = st_monaco(
        value=engine.default_decision_logic(),
        language="python",
        height="350px",
        theme="vs-dark",
    )

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
#  STEP 3 — RUN PIPELINE
# =====================================================

st.markdown('<div class="section-header">Step 3 — Run Access Evaluation</div>', unsafe_allow_html=True)

run_col1, run_col2 = st.columns([1, 1])

with run_col1:
    run_pipeline = st.button("🚀 Run Access Pipeline")

with run_col2:
    st.caption("Runs full parsing → policy ingestion → decision → adjudication → risk model")

# -----------------------------------------------------
#  PROCESS ACTION
# -----------------------------------------------------

result = None

if run_pipeline:
    try:
        user = json.loads(user_json)
        access = json.loads(access_json)

        with st.spinner("Running pipeline..."):
            decision_obj = engine.load_custom_decision_logic(decision_python)
            result = engine.run_pipeline(
                user=user,
                access=access,
                policy_yaml=policy_yaml,
                decision_class=decision_obj,
            )

        st.success("Pipeline executed successfully.")

    except Exception as e:
        st.error(f"Error: {e}")

# -----------------------------------------------------
#  RESULTS
# -----------------------------------------------------

if result:

    # ---------------------- SUMMARY CARD ------------------------
    st.markdown(
        """
        <div class="section-header">
            Final Access Decision — Summary
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card fade-card">', unsafe_allow_html=True)

    cols = st.columns(3)

    cols[0].metric("Decision", result["decision"].upper())
    cols[1].metric("Confidence", f"{result['confidence']}%")
    cols[2].metric("Risk Score", result["risk_score"])

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------- GAUGE CHART ------------------------
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=result["risk_score"],
            title={"text": "Risk Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "rgba(59,130,246,0.9)"},
            },
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------- RAW OUTPUT ------------------------
    st.markdown(
        '<div class="section-header">Raw Output</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card fade-card">', unsafe_allow_html=True)
    st.json(result)
    st.markdown('</div>', unsafe_allow_html=True)
