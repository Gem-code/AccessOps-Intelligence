import streamlit as st
from datetime import datetime

from core.api_client import evaluate_access_request
from core.state_manager import save_history_entry
from core.roles import ROLE_TEMPLATES
from core.configs import CRITICALITY_PRESETS, SENSITIVITY_PRESETS
from core.gauge import draw_risk_gauge
from core.pdf_generator import make_pdf

def render_form_page():
    st.markdown("### Submit Access Request")

    role = st.selectbox("Role Template", ["(none)"] + list(ROLE_TEMPLATES.keys()))

    if st.button("Apply Template"):
        if role != "(none)":
            st.session_state["prefill"] = ROLE_TEMPLATES[role]
            st.success(f"Applied template: {role}")

    pre = st.session_state.get("prefill", {})

    with st.form("req_form"):
        col1, col2 = st.columns(2)

        with col1:
            request_id = st.text_input("Request ID", pre.get("request_id", f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"))
            user_id = st.text_input("User ID", pre.get("user_id", ""))

            identity_type = st.selectbox("Identity Type",
                ["ai_agent", "human_user", "service_account"],
                index=0 if pre.get("identity_type") == "ai_agent" else 1
            )

            job_title = st.text_input("Job Title", pre.get("job_title", ""))

        with col2:
            department = st.text_input("Department", pre.get("department", ""))
            requested_resource_id = st.text_input("Resource ID", pre.get("requested_resource_id", ""))
            requested_resource_name = st.text_input("Resource Name", pre.get("requested_resource_name", ""))
            access_type = st.selectbox("Access Type", ["read", "write", "admin"])

        c1, c2 = st.columns(2)
        with c1:
            system_criticality = st.selectbox("System Criticality", CRITICALITY_PRESETS)
        with c2:
            data_sensitivity = st.selectbox("Data Sensitivity", SENSITIVITY_PRESETS)

        justification = st.text_area("Justification", pre.get("justification", ""))

        submit = st.form_submit_button("Submit Evaluation 🚀")

    if submit:
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

        response = evaluate_access_request(payload)

        # Show card
        severity = response["risk_score"].get("severity_level", "UNKNOWN")
        score = response["risk_score"].get("net_risk_score", 0)
        decision = response.get("decision")

        st.markdown("---")
        st.markdown(f"### Result: **{decision}**")
        st.markdown(f"**Severity:** {severity}")
        st.markdown(f"**Score:** {score}")

        st.pyplot(draw_risk_gauge(score))

        save_history_entry({
            "timestamp": datetime.utcnow().isoformat(),
            "request": payload,
            "decision": decision,
            "severity": severity,
            "net_score": score,
            "board_report": response.get("board_report", "")
        })

        pdf_bytes = make_pdf(payload, response)
        st.download_button("Download PDF Report", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
