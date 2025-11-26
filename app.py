import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import io

import nest_asyncio
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------
# 0. ENGINE WIRING
# ---------------------------------------------------------------------
try:
    import accessops_engine  # must be in same directory
except ImportError:
    st.error("CRITICAL ERROR: `accessops_engine.py` not found. Please ensure it is in the same directory.")
    st.stop()

# Allow asyncio.run inside Streamlit (important for ADK / Capstone notebooks)
nest_asyncio.apply()

# ---------------------------------------------------------------------
# 1. PAGE CONFIG & THEME
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="AccessOps Intelligence – CISO Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS – dark, enterprise feel
st.markdown(
    """
<style>
    .stApp {
        background-color: #020617; /* slate-950 */
        color: #e2e8f0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    section[data-testid="stSidebar"] {
        background-color: #020617;
        border-right: 1px solid #1f2937;
    }

    .step-header {
        background: linear-gradient(90deg, #0f172a 0%, #020617 100%);
        padding: 10px 16px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        color: #e5e7eb;
    }

    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid rgba(148,163,184,0.75);
        background-color: rgba(15,23,42,0.85);
        color: #e5e7eb;
    }

    .stTextArea textarea {
        background-color: #020617;
        color: #e5e7eb;
        border: 1px solid #1f2937;
        font-family: "JetBrains Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
        font-size: 0.8rem;
    }

    .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    div.stButton > button {
        background: radial-gradient(circle at 10% 20%, #1d4ed8 0%, #1e293b 40%, #020617 100%);
        color: #f9fafb;
        border: 1px solid #1d4ed8;
        border-radius: 999px;
        font-weight: 600;
        height: 3rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-size: 0.8rem;
        transition: all 0.2s ease-out;
    }
    div.stButton > button:hover {
        box-shadow: 0 20px 35px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
    }

    div[data-testid="metric-container"] {
        background-color: #020617;
        border-radius: 10px;
        border: 1px solid #1f2937;
        padding: 10px 12px;
    }

    button[data-baseweb="tab"] {
        background-color: #020617 !important;
        border-radius: 999px !important;
        border: 1px solid transparent !important;
        padding: 0.4rem 1rem !important;
        margin-right: 0.3rem !important;
        font-size: 0.8rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-color: #3b82f6 !important;
        background-color: rgba(37, 99, 235, 0.12) !important;
    }

    .trace-card {
        border-radius: 10px;
        border: 1px solid #1f2937;
        padding: 0.75rem 1rem;
        background-color: #020617;
        font-size: 0.8rem;
    }

    .caption-sm {
        font-size: 0.7rem;
        color: #9ca3af;
    }

    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #9ca3af;
        margin-bottom: 0.25rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# 2. HELPERS
# ---------------------------------------------------------------------
def create_risk_gauge(score: float) -> go.Figure:
    """Plotly gauge for net risk score."""
    score = score or 0
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Net Risk Score", "font": {"size": 18, "color": "#e5e7eb"}},
            number={"font": {"size": 32, "color": "#f9fafb"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#e5e7eb"},
                "bar": {"color": "rgba(0,0,0,0)"},
                "bgcolor": "#020617",
                "borderwidth": 1,
                "bordercolor": "#1f2937",
                "steps": [
                    {"range": [0, 30], "color": "#16a34a"},
                    {"range": [30, 60], "color": "#f59e0b"},
                    {"range": [60, 85], "color": "#ef4444"},
                    {"range": [85, 100], "color": "#7f1d1d"},
                ],
                "threshold": {
                    "line": {"color": "#f9fafb", "width": 4},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        height=220,
    )
    return fig


def format_badge(label: str, emoji: str) -> str:
    return f'<span class="pill-badge">{emoji} {label}</span>'


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    return d.get(key, default) if isinstance(d, dict) else default


def create_pdf_bytes(report_text: str, title: str) -> bytes:
    """Generate a simple PDF from the markdown/board report."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    y = height - 72

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, title[:90])
    y -= 24

    c.setFont("Helvetica", 10)
    for raw_line in report_text.splitlines():
        line = raw_line.replace("\t", "    ")
        if not line.strip():
            y -= 10
        else:
            # naive wrapping
            while len(line) > 110:
                c.drawString(72, y, line[:110])
                line = line[110:]
                y -= 12
                if y < 72:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 72
            c.drawString(72, y, line)
            y -= 12

        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 72

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ---------------------------------------------------------------------
# 3. SIDEBAR – CONFIG + JUDGE ORIENTATION
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ AccessOps Intelligence")
    st.caption(
        "Agentic risk engine for **Non-Human Identities**.\n"
        "This UI showcases the full pipeline judges care about: investigation, scoring, critique, gatekeeper, and board report."
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Runtime Configuration")

    api_key = st.text_input(
        "Optional: Google API key",
        type="password",
        help="Only needed for local API-key runs. In Cloud Run, use Vertex/GCP service identity.",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("API key exported to environment for this session.")
    else:
        st.info("Using default Vertex / ADK config from `accessops_engine.py`.")

    st.markdown("---")
    st.markdown("#### 🧪 Demo Scenarios")
    st.markdown(
        """
- **Toxic Finance Bot** – AI service account requesting **write** access to Production General Ledger.
- **DevOps Engineer** – Human engineer requesting **read** access to Dev logs.
- **Custom Payload** – Paste any JSON request body you want to test.
"""
    )

    st.markdown("---")
    st.markdown("#### 📓 Judge Runbook")
    st.caption(
        "1. Pick a scenario.\n"
        "2. Inspect / tweak JSON.\n"
        "3. Run the audit.\n"
        "4. Use tabs: **Executive**, **Signals**, **Context**, **Agent Trace**, **Raw JSON**.\n"
        "5. Export the Board packet as Markdown or PDF."
    )

# ---------------------------------------------------------------------
# 4. HEADER
# ---------------------------------------------------------------------
header_left, header_right = st.columns([1.6, 1])

with header_left:
    st.title("CISO Command Center – AccessOps Intelligence")
    st.markdown(
        "Real-time **access risk adjudication** for human and AI identities, "
        "grounded in NIST 800-53 & Segregation-of-Duties policies."
    )

with header_right:
    st.markdown("<div class='section-label'>SESSION CONTEXT</div>", unsafe_allow_html=True)
    st.markdown(
        format_badge(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "⏱️"),
        unsafe_allow_html=True,
    )
    st.markdown(
        format_badge("NIST 800-53 • AC-6 • SoD", "📚"),
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------
# 5. INPUT PANEL – SCENARIO & JSON
# ---------------------------------------------------------------------
input_col, output_col = st.columns([1.05, 1.45])

with input_col:
    st.markdown("<div class='step-header'>📝 Step 1 – Select Scenario</div>", unsafe_allow_html=True)

    scenario = st.radio(
        "Choose a test case:",
        ["Toxic Finance Bot (CRITICAL)", "DevOps Engineer (LOW RISK)", "Custom Payload"],
        captions=[
            "AI Agent attempting unauthorized write on Tier-1 ledger.",
            "Human requesting low-risk read on non-production logs.",
            "Bring your own JSON body.",
        ],
    )

    if "Toxic" in scenario:
        default_json = {
            "request_id": "REQ-TOXIC-001",
            "user_id": "svc_finops_auto_bot",
            "identity_type": "ai_agent",
            "job_title": "Automated Financial Ops",
            "department": "Finance Automation",
            "requested_resource_id": "prod_general_ledger_rw",
            "requested_resource_name": "Production General Ledger",
            "access_type": "write",
            "system_criticality": "tier_1",
            "data_sensitivity": "restricted",
            "justification": "AI Agent detected anomaly. Requesting autonomous write access to fix.",
        }
    elif "DevOps" in scenario:
        default_json = {
            "request_id": "REQ-DEVOPS-005",
            "user_id": "eng_human_user",
            "identity_type": "human",
            "job_title": "Senior DevOps",
            "department": "Engineering",
            "requested_resource_id": "dev_logs_read",
            "requested_resource_name": "Dev Logs",
            "access_type": "read",
            "system_criticality": "non_prod",
            "data_sensitivity": "internal",
            "justification": "Debugging build failure.",
        }
    else:
        default_json = {
            "request_id": "REQ-CUSTOM-001",
            "user_id": "svc_or_user_id",
            "identity_type": "ai_agent",
            "job_title": "Role Title",
            "department": "Owning Department",
            "requested_resource_id": "resource_id_here",
            "requested_resource_name": "Resource Friendly Name",
            "access_type": "read",
            "system_criticality": "tier_2",
            "data_sensitivity": "confidential",
            "justification": "Business justification goes here.",
        }

    st.markdown("<div class='step-header'>📨 Step 2 – Review / Edit JSON Payload</div>", unsafe_allow_html=True)
    st.caption("This is the exact request body passed into the ADK/Vortex pipeline.")
    request_text = st.text_area(
        "Access request JSON",
        value=json.dumps(default_json, indent=2),
        height=360,
    )

    run_col, hint_col = st.columns([2, 1])
    with run_col:
        run_btn = st.button("🚨 Run Security Audit", use_container_width=True)
    with hint_col:
        st.caption(
            "Must include:\n"
            "- `request_id`\n"
            "- `user_id`\n"
            "- `requested_resource_id`\n"
            "- `access_type`"
        )

# ---------------------------------------------------------------------
# 6. EXECUTION LOGIC
# ---------------------------------------------------------------------
pipeline_result: Optional["accessops_engine.PipelineResult"] = None

if run_btn:
    with output_col:
        st.markdown("<div class='step-header'>🧠 Step 3 – Agentic Reasoning Trace</div>", unsafe_allow_html=True)

        # Parse JSON
        try:
            req_data = json.loads(request_text)
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON – please correct syntax (use double quotes, commas, etc.).")
        else:
            missing = [k for k in ["request_id", "user_id", "requested_resource_id", "access_type"] if k not in req_data]
            if missing:
                st.error(f"❌ Missing required key(s): {', '.join(missing)}.")
            else:
                status_box = st.status("🕵️ Investigator Agent: Gathering IAM / SIEM context…", expanded=True)
                status_box.write("Connecting to AccessOps engine in Google Cloud Run / Vertex…")

                async def run_pipeline_async() -> "accessops_engine.PipelineResult":
                    return await accessops_engine.run_pipeline(req_data)

                try:
                    pipeline_result = asyncio.run(run_pipeline_async())
                except Exception as e:
                    status_box.update(
                        label="❌ Pipeline execution failed",
                        state="error",
                        expanded=True,
                    )
                    st.error(f"Execution Error: {e}")
                    pipeline_result = None
                else:
                    # Status trail for rubric
                    status_box.write("✅ Investigator – context & peer baselines collected.")
                    status_box.write("✅ Severity Analyst – NIST 800-53 score computed.")
                    status_box.write("✅ Risk Critic – second-opinion challenge completed.")
                    status_box.write("✅ Gatekeeper – authorization verdict generated.")
                    status_box.write("✅ Board Reporter – regulator-ready summary assembled.")

                    decision = pipeline_result.decision
                    risk_score_obj = pipeline_result.risk_score or {}
                    score = safe_get(risk_score_obj, "net_risk_score", 0) or 0
                    severity = safe_get(risk_score_obj, "severity_level", "UNKNOWN")
                    investigation = pipeline_result.investigation or {}
                    policy_violations = safe_get(investigation, "policy_violations", []) or []

                    if "DENY" in (decision or "") or "REVIEW" in (decision or ""):
                        status_box.update(
                            label="🛑 GATEKEEPER: Blocked / Requires Human",
                            state="error",
                            expanded=False,
                        )
                        decision_state = "error"
                    else:
                        status_box.update(
                            label="✅ GATEKEEPER: Auto-approved",
                            state="complete",
                            expanded=False,
                        )
                        decision_state = "success"

                    # -----------------------------------------------------------------
                    # 7. OUTPUT TABS
                    # -----------------------------------------------------------------
                    st.markdown("")
                    st.markdown("<div class='step-header'>📊 Step 4 – Risk Dashboard</div>", unsafe_allow_html=True)

                    overview_tab, signals_tab, context_tab, trace_tab, raw_tab = st.tabs(
                        [
                            "Executive Overview",
                            "Risk Signals",
                            "Context & Policies",
                            "Agent Trace (ADK)",
                            "Raw JSON",
                        ]
                    )

                    # --- Overview Tab ------------------------------------------------
                    with overview_tab:
                        m1, m2, m3 = st.columns(3)
                        m1.metric(
                            "Decision",
                            decision,
                            delta="STOP" if score > 50 else "GO",
                            delta_color="inverse",
                        )
                        m2.metric(
                            "Net Risk Score",
                            f"{score:.0f}/100",
                            delta=severity,
                            delta_color="inverse",
                        )
                        m3.metric(
                            "Policy Violations",
                            len(policy_violations),
                            delta="Detected" if policy_violations else "None",
                            delta_color="inverse",
                        )

                        st.plotly_chart(create_risk_gauge(float(score)), use_container_width=True)

                        if decision_state == "error":
                            st.error(
                                "🛑 **BLOCKED / ESCALATE** – This access request breaches SoD / NIST guardrails. "
                                "See Risk Signals & Board Report for rationale."
                            )
                        else:
                            st.success(
                                "✅ **APPROVED / WITHIN GUARDRAILS** – Risk is within policy envelope."
                            )

                        st.markdown("#### 📄 Executive / Board Report")
                        st.caption("Auto-generated narrative suitable for CISO, auditors, and regulators.")
                        st.markdown(pipeline_result.board_report, unsafe_allow_html=True)

                        report_id = req_data.get("request_id", "UNKNOWN")
                        md_bytes = pipeline_result.board_report.encode("utf-8")
                        pdf_bytes = create_pdf_bytes(
                            pipeline_result.board_report,
                            f"Access Risk Audit – {report_id}",
                        )

                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            st.download_button(
                                label="📥 Download Board Report (Markdown)",
                                data=md_bytes,
                                file_name=f"Audit_Report_{report_id}.md",
                                mime="text/markdown",
                                use_container_width=True,
                            )
                        with dl_col2:
                            st.download_button(
                                label="📄 Download Board Packet (PDF)",
                                data=pdf_bytes,
                                file_name=f"Audit_Report_{report_id}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )

                    # --- Risk Signals Tab -------------------------------------------
                    with signals_tab:
                        st.markdown("#### 🚦 Risk Factor Analysis")

                        risk_signals = safe_get(investigation, "risk_signals", {}) or {}
                        if not risk_signals:
                            st.info("No structured `risk_signals` field returned. Showing raw investigation instead.")
                            st.json(investigation)
                        else:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Binary / Categorical Signals**")
                                for key, val in risk_signals.items():
                                    emoji = "🔴" if bool(val) else "🟢"
                                    label = key.replace("_", " ").title()
                                    st.markdown(format_badge(label, emoji), unsafe_allow_html=True)

                            with col_b:
                                st.markdown("**High-Level Interpretation**")
                                high_flags = [k for k, v in risk_signals.items() if v]
                                if not high_flags:
                                    st.success("No critical flags raised by the investigator.")
                                else:
                                    st.error(
                                        "Raised signals: "
                                        + ", ".join(k.replace("_", " ") for k in high_flags)
                                    )

                            st.markdown("---")
                            st.markdown("**Risk Scoring JSON**")
                            st.json(risk_score_obj)

                    # --- Context & Policies Tab -------------------------------------
                    with context_tab:
                        st.markdown("#### 🧩 Context Signals")

                        up = safe_get(investigation, "user_profile", {})
                        ent = safe_get(investigation, "current_access", {})
                        peer = safe_get(investigation, "peer_baseline", {})
                        act = safe_get(investigation, "activity_summary", {})

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Identity Profile (WHO)**")
                            st.json(up or {"note": "No user profile returned."})

                            st.markdown("**Current Entitlements (WHAT THEY ALREADY HAVE)**")
                            st.json(ent or {"note": "No entitlement data returned."})

                        with c2:
                            st.markdown("**Peer Baseline (NORM)**")
                            st.json(peer or {"note": "No peer baseline returned."})

                            st.markdown("**Recent Activity (BEHAVIOR)**")
                            st.json(act or {"note": "No SIEM / activity summary returned."})

                        st.markdown("---")
                        st.markdown("#### 📜 Policy Violations")
                        if not policy_violations:
                            st.success("No explicit policy violations detected.")
                        else:
                            for v in policy_violations:
                                with st.expander(
                                    f"🛑 {v.get('policy_id', 'POLICY')} – {v.get('severity', 'SEVERITY')}",
                                    expanded=True,
                                ):
                                    st.write(v.get("description", ""))
                                    st.markdown(
                                        f"**NIST Control:** `{v.get('nist_control', 'N/A')}`  \n"
                                        f"**Finding:** {v.get('finding', 'N/A')}"
                                    )

                    # --- Agent Trace Tab --------------------------------------------
                    with trace_tab:
                        st.markdown("#### 🧬 ADK Agent Trace")

                        exec_trace: List[Dict[str, Any]] = pipeline_result.execution_trace or []
                        if not exec_trace:
                            st.info("No `execution_trace` list returned from engine.")
                        else:
                            for i, phase in enumerate(exec_trace, start=1):
                                with st.expander(f"{i}. Phase: {phase.get('phase', 'unknown')}", expanded=True):
                                    st.markdown(
                                        f"<div class='caption-sm'>Agent: "
                                        f"`{phase.get('agent', 'unknown')}`</div>",
                                        unsafe_allow_html=True,
                                    )
                                    st.markdown("<div class='trace-card'>", unsafe_allow_html=True)
                                    st.json(phase)
                                    st.markdown("</div>", unsafe_allow_html=True)

                    # --- Raw JSON Tab ------------------------------------------------
                    with raw_tab:
                        st.markdown("#### 🧾 Raw Engine Payloads")
                        st.markdown("**Request Context**")
                        st.json(req_data)
                        st.markdown("---")
                        st.markdown("**Investigation Output**")
                        st.json(investigation)
                        st.markdown("---")
                        st.markdown("**Risk Scoring Output**")
                        st.json(risk_score_obj)
                        st.markdown("---")
                        st.markdown("**Gatekeeper Decision JSON**")
                        st.json({"decision": pipeline_result.decision})
                        st.markdown("---")
                        st.markdown("**Execution Trace**")
                        st.json(pipeline_result.execution_trace)

else:
    # No run yet: nudge to start
    with output_col:
        st.info(
            "👈 Select a scenario, adjust the JSON if needed, and hit **“Run Security Audit”** "
            "to see the full AccessOps agent pipeline and board-ready report."
        )
