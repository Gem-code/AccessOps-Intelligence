import streamlit as st
import requests
import json

st.set_page_config(page_title="AccessOps Request Form", page_icon="📝", layout="wide")

st.title("📝 AccessOps Intelligence — Access Request Evaluator")

API_URL = "https://accessops-intel-584977353084.us-central1.run.app/evaluate"

st.subheader("Enter Access Request Details")

with st.form("access_request_form"):

    request_id = st.text_input("Request ID", "CAPSTONE-DEMO-001")
    user_id = st.text_input("User ID", "svc_finops_auto_bot")
    
    identity_type = st.selectbox(
        "Identity Type",
        ["ai_agent", "human_user", "service_account"],
        index=0
    )

    job_title = st.text_input("Job Title", "Automated Financial Ops")
    department = st.text_input("Department", "Finance Automation")

    requested_resource_id = st.text_input("Resource ID", "prod_general_ledger_rw")
    requested_resource_name = st.text_input("Resource Name", "Production General Ledger")

    access_type = st.selectbox("Access Type", ["read", "write", "admin"], index=1)

    system_criticality = st.selectbox(
        "System Criticality",
        ["tier_1", "tier_2", "tier_3"],
        index=0
    )

    data_sensitivity = st.selectbox(
        "Data Sensitivity",
        ["public", "internal", "confidential", "restricted"],
        index=3
    )

    justification = st.text_area("Justification", "AI detected anomaly")

    submit_button = st.form_submit_button("Submit Request 🚀")

if submit_button:
    st.subheader("📤 Sending Request…")

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

    st.code(json.dumps(payload, indent=2), language="json")

    try:
        response = requests.post(API_URL, json=payload)
        response_data = response.json()

        st.success("Response Received Successfully!")
        st.subheader("📥 API Response")
        st.code(json.dumps(response_data, indent=2), language="json")

        if "board_report" in response_data:
            st.subheader("📊 Executive Board Report")
            st.markdown(response_data["board_report"])

    except Exception as e:
        st.error(f"❌ Error communicating with server: {str(e)}")
