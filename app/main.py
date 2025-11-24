import streamlit as st
import requests
import json

# -------------------------
#   PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="AccessOps — Enterprise Access Evaluation",
    page_icon="🛡️",
    layout="wide"
)

# -------------------------
#   CUSTOM ENTERPRISE CSS
# -------------------------
st.markdown("""
<style>

body {
    font-family: 'Inter', sans-serif;
}

.big-title {
    font-size: 32px;
    font-weight: 700;
    color: #1A1A1A;
}

.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-top: 25px;
    margin-bottom: 10px;
}

.card {
    background: #FFFFFF;
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #E6E6E6;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
}

.result-card {
    background: #F8FAFC;
    padding: 25px;
    border-left: 6px solid #0078FF;
    border-radius: 10px;
    margin-top: 20px;
    font-size: 16px;
}

.success-card {
    border-left: 6px solid #22C55E !important;
}

.warn-card {
    border-left: 6px solid #EAB308 !important;
}

.danger-card {
    border-left: 6px solid #EF4444 !important;
}

.hidden-json {
    display: none;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
#   TITLE
# -------------------------
st.markdown("<div class='big-title'>🛡️ AccessOps Intelligence — Enterprise Access Evaluator</div>", unsafe_allow_html=True)
st.write("A polished enterprise interface for evaluating access requests using your AccessOps multi-agent system.")


# -------------------------
#   API CONFIG
# -------------------------
API_URL = "https://accessops-intel-584977353084.us-central1.run.app/evaluate"


# -------------------------
#   FORM UI
# -------------------------
st.markdown("<div class='section-title'>Access Request Form</div>", unsafe_allow_html=True)

with st.container():
    with st.form("enterprise_form"):
        col1, col2 = st.columns(2)

        with col1:
            request_id = st.text_input("Request ID", "CAPSTONE-DEMO-001")
            user_id = st.text_input("User ID", "svc_finops_auto_bot")
            identity_type = st.selectbox("Identity Type", ["ai_agent", "human_user", "service_account"])
            job_title = st.text_input("Job Title", "Automated Financial Ops")

        with col2:
            department = st.text_input("Department", "Finance Automation")
            requested_resource_id = st.text_input("Resource ID", "prod_general_ledger_rw")
            requested_resource_name = st.text_input("Resource Name", "Production General Ledger")
            access_type = st.selectbox("Access Type", ["read", "write", "admin"], index=1)

        colA, colB = st.columns(2)
        with colA:
            system_criticality = st.selectbox("System Criticality", ["tier_1", "tier_2", "tier_3"], index=0)

        with colB:
            data_sensitivity = st.selectbox("Data Sensitivity", ["public", "internal", "confidential", "restricted"], index=3)

        justification = st.text_area("Justification", "AI detected anomaly")

        submit_btn = st.form_submit_button("Submit Request 🚀")


# -------------------------
#   SUBMIT HANDLER
# -------------------------
if submit_btn:
    payload = {
        "request_id": request_id,
        "user_id": user_id,
        "identity_type": identity_type,
        "job_title": job_title,
        "department": department,
        "requested_resource_id": requested_resource_id,
        "requested_resource_name": requested_resource_name,
        "access_type": access_type,
        "system_criticality": system_criticality,
        "data_sensitivity": data_sensitivity,
        "justification": justification
    }

    with st.spinner("Evaluating access request…"):
        try:
            response = requests.post(API_URL, json=payload)
            data = response.json()
        except Exception as e:
            st.error(f"❌ Unable to reach AccessOps Engine: {str(e)}")
            st.stop()

    # -------------------------
    #   DISPLAY SUMMARY ONLY
    # -------------------------
    decision = data.get("decision", "UNKNOWN")
    risk_score = data.get("risk_score", {})
    report = data.get("board_report", "")

    severity = risk_score.get("severity_level", "UNKNOWN")
    net_score = risk_score.get("net_risk_score", "--")

    # Decide card color class
    if severity == "LOW":
        card_class = "success-card"
    elif severity == "MEDIUM":
        card_class = "warn-card"
    else:
        card_class = "danger-card"

    # Result Summary Card
    st.markdown(f"""
    <div class='result-card {card_class}'>
        <h3>📊 Access Evaluation Result</h3>
        <p><strong>Decision:</strong> {decision}</p>
        <p><strong>Risk Severity:</strong> {severity}</p>
        <p><strong>Net Risk Score:</strong> {net_score}</p>
    </div>
    """, unsafe_allow_html=True)

    # Executive Summary
    if report:
        st.markdown("<div class='section-title'>📘 Executive Summary</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            {report}
        </div>
        """, unsafe_allow_html=True)

