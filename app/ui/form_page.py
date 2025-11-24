import streamlit as st
from datetime import datetime
import requests
from streamlit_lottie import st_lottie


from core.api_client import evaluate_access_request
from core.state_manager import save_history_entry
from core.roles import ROLE_TEMPLATES
from core.configs import CRITICALITY_PRESETS, SENSITIVITY_PRESETS
from core.gauge import draw_small_gauge
from core.pdf_generator import make_pdf


# ---------------------------------------------------------
#   LOTTIE: SAFE, EMBEDDED ROTATING LOADER (No JS errors)
# ---------------------------------------------------------
thinking_anim = {
    "v": "5.5.1",
    "fr": 30,
    "ip": 0,
    "op": 150,
    "w": 200,
    "h": 200,
    "nm": "processing",
    "ddd": 0,
    "assets": [],
    "layers": [
        {
            "ddd": 0,
            "ind": 1,
            "ty": 4,
            "nm": "loader",
            "sr": 1,
            "ks": {
                "o": {"a": 0, "k": 100},
                "r": {"a": 1, "k": [{"t": 0, "s": 0}, {"t": 150, "s": 360}]},
                "p": {"a": 0, "k": [100, 100]},
                "a": {"a": 0, "k": [0, 0]},
                "s": {"a": 0, "k": [100, 100, 100]}
            },
            "shapes": [
                {
                    "ty": "gr",
                    "it": [
                        {"d": 1, "ty": "el", "s": {"a": 0, "k": [120, 120]}, "p": {"a": 0, "k": [0, 0]}},
                        {"ty": "st", "c": {"a": 0, "k": [0.1, 0.4, 0.9, 1]}, "w": {"a": 0, "k": 10}},
                        {"ty": "tr", "p": {"a": 0, "k": [0, 0]}}
                    ]
                }
            ],
            "ip": 0,
            "op": 150,
            "st": 0
        }
    ]
}


# ---------------------------------------------------------
#   TEMPLATE CARDS (Streamlit-safe buttons + CSS styling)
# ---------------------------------------------------------

TEMPLATE_UI = {
    "AI Agent — Anomaly": {
        "icon": "🤖",
        "desc": "Auto-detected anomaly requiring production access",
        "bg": "#dbeafe",
    },
    "Finance Manager — Escalation": {
        "icon": "👨‍💼",
        "desc": "Privileged access for emergency reconciliation",
        "bg": "#fef3c7",
    },
    "Developer — Debug": {
        "icon": "🧑‍💻",
        "desc": "Temporary admin access for debugging",
        "bg": "#dcfce7",
    }
}


# ---------------------------------------------------------
#   FORM PAGE MAIN RENDER FUNCTION
# ---------------------------------------------------------
def render_form_page():

    st.markdown("## Choose a Template")

    # Columns for horizontal layout — auto wraps to vertical on mobile
    cols = st.columns(len(TEMPLATE_UI))

    # Template card buttons
    for (role, meta), col in zip(TEMPLATE_UI.items(), cols):
        with col:

            btn = st.button(
                f"{meta['icon']}  {role}\n{meta['desc']}",
                key=f"tmpl_{role}",
                help=f"Apply template: {role}",
            )
            # Style overrides for this specific button ID
            st.markdown(
                f"""
                <style>
                button[kind="secondary"]{{
                    background-color: {meta['bg']} !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

            if btn:
                st.session_state["prefill"] = ROLE_TEMPLATES[role]
                st.success(f"Template applied: {role}")
                st.rerun()

    st.markdown("---")

    # Prefill data
    pre = st.session_state.get("prefill", {})

    # ---------------------------------------------------------
    #   ACCESS REQUEST FORM
    # ---------------------------------------------------------
    with st.form("access_request_form"):

        col1, col2 = st.columns(2)

        with col1:
            request_id = st.text_input(
                "Request ID",
                pre.get("request_id", f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
            )
            user_id = st.text_input("User ID", pre.get("user_id", ""))
            identity_type = st.selectbox(
                "Identity Type",
                ["ai_agent", "human_user", "service_account"],
                index=0 if pre.get("identity_type") == "ai_agent" else 1
            )
            job_title = st.text_input("Job Title", pre.get("job_title", ""))

        with col2:
            department = st.text_input("Department", pre.get("department", ""))
            requested_resource_id = st.text_input(
                "Resource ID",
                pre.get("requested_resource_id", "")
            )
            requested_resource_name = st.text_input(
                "Resource Name",
                pre.get("requested_resource_name", "")
            )
            access_type = st.selectbox(
                "Access Type",
                ["read", "write", "admin"],
                index=1 if pre.get("access_type") == "write" else 0
            )

        c1, c2 = st.columns(2)

        with c1:
            system_criticality = st.selectbox(
                "System Criticality",
                CRITICALITY_PRESETS,
                index=CRITICALITY_PRESETS.index(pre.get("system_criticality", "tier_1"))
            )

        with c2:
            data_sensitivity = st.selectbox(
                "Data Sensitivity",
                SENSITIVITY_PRESETS,
                index=SENSITIVITY_PRESETS.index(pre.get("data_sensitivity", "restricted"))
            )

        justification = st.text_area("Justification", pre.get("justification", ""))

        submit = st.form_submit_button("Submit Request 🚀")

    # ===========================================================
    #                     FORM SUBMITTED
    # ===========================================================
    if submit:

        # Build payload
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

        # ---------------------------------------------------------
        #   SAFE LOTTIE LOADER (NO "destroy" JS errors)
        # ---------------------------------------------------------
        with st.spinner("Evaluating request…"):
            placeholder = st.empty()
            with placeholder:
                st_lottie(thinking_anim, height=80)

            response = evaluate_access_request(payload)

            placeholder.empty()

        # ---------------------------------------------------------
        #   Extract response
        # ---------------------------------------------------------
        decision = response.get("decision", "UNKNOWN")
        rs = response.get("risk_score", {})
        severity = rs.get("severity_level", "UNKNOWN")
        score = rs.get("net_risk_score", 0)
        report = response.get("board_report", "")

        card_class = (
            "success-card" if severity == "LOW"
            else "warn-card" if severity == "MEDIUM"
            else "danger-card"
        )

        # ---------------------------------------------------------
        #   RESULT + GAUGE IN SINGLE ROW
        # ---------------------------------------------------------
        col1, col2 = st.columns([1.3, 1])

        with col1:
            st.markdown(f"""
            <div class='result-card {card_class}'>
                <h3>📊 Access Evaluation Result</h3>
                <p><strong>Decision:</strong> {decision}</p>
                <p><strong>Risk Severity:</strong> {severity}</p>
                <p><strong>Net Risk Score:</strong> {score}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='gauge-wrapper'>", unsafe_allow_html=True)
            st.pyplot(draw_small_gauge(score), clear_figure=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        #   Executive Report
        # ---------------------------------------------------------
        if report:
            st.markdown("### 📘 Executive Board Report")
            st.markdown(f"<div class='card'>{report}</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        #   Save to history
        # ---------------------------------------------------------
        save_history_entry({
            "timestamp": datetime.utcnow().isoformat(),
            "request": payload,
            "decision": decision,
            "severity": severity,
            "net_score": score,
            "board_report": report,
        })

        # ---------------------------------------------------------
        #   PDF Download
        # ---------------------------------------------------------
        pdf_data = make_pdf(payload, response, gauge_fig=draw_small_gauge(score))

        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_data,
            file_name=f"AccessOps_Report_{request_id}.pdf",
            mime="application/pdf"
        )
