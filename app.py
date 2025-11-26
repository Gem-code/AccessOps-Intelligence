import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import nest_asyncio
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# 0. ENGINE WIRING
# ---------------------------------------------------------------------
try:
    import accessops_engine  # must be in same directory
except ImportError:
    st.error("CRITICAL ERROR: `accessops_engine.py` not found. Please ensure it is in the same directory.")
    st.stop()

# Allow asyncio.run inside Streamlit
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

# Custom CSS – “financial blue” + subtle cards
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

    /* Text areas */
    .stTextArea textarea {
        background-color: #020617;
        color: #e5e7eb;
        border: 1px solid #1f2937;
        font-family: "JetBrains Mono", "Source Code Pro", Menlo, Monaco, Consolas, "Courier New", monospace;
        font-size: 0.8rem;
    }

    /* Radio labels */
    .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* Primary button */
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

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #020617;
        border-radius: 10px;
        border: 1px solid #1f2937;
        padding: 10px 12px;
    }

    /* Tabs */
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

    /* Code-like blocks */
    .trace-card {
        border-radius: 10px;
        border: 1px solid #1f2937;
        padding: 0.75rem 1rem;
        background-color: #020617;
        font-size: 0.8rem;
    }

    /* Small caption text */
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
# 2. VISUAL HELPERS
# ---------------------------------------------------------------------
def create_risk_gauge(score: float) -> go.Figure:
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
                "bar": {"color": "rgba(0,0,0,0)"},  # transparent bar, we rely on steps
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


# ---------------------------------------------------------------------
# 3. SIDEBAR – RUNBOOK & CONFIG
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ AccessOps Intelligence")
    st.caption(
        "Agentic risk engine for **Non-Human Identities**.\n"
        "Use the templates to simulate toxic AI agents vs. safe human engineers."
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Runtime Configuration")

    api_key = st.text_input(
        "Optional: Google API key",
        type="password",
        help="For local testing with MakerSuite / API-key flows. Vertex AI mode is configured in `accessops_engine.py`.",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("API key loaded into environment.")
    else:
        st.info("Vertex AI config is used by default (see `accessops_engine.py`).")

    st.markdown("---")
    st.markdown("#### 🧪 Demo Scenarios")
    st.markdown(
        """
- **Toxic Finance Bot** – AI agent requesting write access to **Production General Ledger** (should be blocked).
- **DevOps Engineer** – Human requesting read-only access to **Dev logs** (should pass).
- **Custom Payload** – Paste your own JSON request body.
"""
    )

    st.markdown("---")
    st.markdown("#### 📓 Judge Notes")
    st.caption(
        "1. Load a scenario.\n"
        "2. Review/modify JSON.\n"
        "3. Run the audit.\n"
        "4. Inspect **Executive Overview**, **Risk Signals**, and **Agent Trace**."
    )

# ---------------------------------------------------------------------
# 4. HEADER
# ---------------------------------------------------------------------
left_header, right_header = st.columns([1.4, 1])

with left_header:
    st.title("CISO Command Center – AccessOps Intelligence")
    st.markdown(
        "Real-time, agentic **access risk adjudication** for AI agents & humans "
        "backed by NIST 800-53 and SoD policies."
    )

with right_header:
    st.markdown("<div class='section-label'>TODAY</div>", unsafe_allow_html=True)
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
# 5. INPUT LAYOUT (SCENARIO + PAYLOAD)
# ---------------------------------------------------------------------
input_col, output_col = st.columns([1.1, 1.4])

with input_col:
    # Step 1 – Scenario Selector
    st.markdown("<div class='step-header'>📝 Step 1 – Select Scenario</div>", unsafe_allow_html=True)
    scenario = st.radio(
        "Choose a test case:",
        ["Toxic Finance Bot (CRITICAL)", "DevOps Engineer (LOW RISK)", "Custom Payload"],
        captions=[
            "AI agent attempting **write** access to Production General Ledger.",
            "Senior DevOps engineer requesting **read** access to dev logs.",
            "Paste your own JSON with `requested_resource_id`, `access_type`, etc.",
        ],
    )

    # Step 2 – Prefill JSON
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
    st.caption("This is the request body sent into the agentic risk engine.")
    request_text = st.text_area(
        "Access request JSON",
        value=json.dumps(default_json, indent=2),
        height=340,
    )

    col_run, col_help = st.columns([2, 1])
    with col_run:
        run_btn = st.button("🚨 Run Security Audit", use_container_width=True)
    with col_help:
        st.caption(
            "Must include:\n"
            "- `request_id`\n"
            "- `user_id`\n"
            "- `requested_resource_id`\n"
            "- `access_type`"
        )

# ---------------------------------------------------------------------
# 6. EXECUTION & OUTPUT PANEL
# ---------------------------------------------------------------------
pipeline_result: Optional["accessops_engine.PipelineResult"] = None

if run_btn:
    with output_col:
        st.markdown("<div class='step-header'>🧠 Step 3 – Agentic Reasoning Trace</div>", unsafe_allow_html=True)

        try:
            req_data = json.loads(request_text)
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON – please check syntax. (Tip: use `\"` for keys/strings and commas between fields.)")
        else:
            if "requested_resource_id" not in req_data:
                st.error("❌ Missing key `requested_resource_id` – required by the engine.")
            elif "request_id" not in req_data:
                st.error("❌ Missing key `request_id` – required for session tracing.")
            else:
                status_box = st.status("🕵️ Investigator Agent: Gathering IAM / SIEM context …", expanded=True)
                status_box.write("Connecting to AccessOps engine…")

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
                    # Status updates
                    status_box.write("✅ Investigator – IAM, entitlements & peer baselines loaded.")
                    status_box.write("✅ Severity Analyst – NIST 800-53 risk score computed.")
                    status_box.write("✅ Risk Critic – Internal audit challenge completed.")
                    status_box.write("✅ Gatekeeper – Authorization decision generated.")
                    status_box.write("✅ Board Reporter – Executive summary prepared.")

                    decision = pipeline_result.decision
                    score = safe_get(pipeline_result.risk_score, "net_risk_score", 0)
                    severity = safe_get(pipeline_result.risk_score, "severity_level", "UNKNOWN")
                    investigation = pipeline_result.investigation or {}
                    policy_violations = safe_get(investigation, "policy_violations", []) or []

                    if "DENY" in decision or "REVIEW" in decision:
                        status_box.update(
                            label="🛑 Gatekeeper: Blocked / Requires Human",
                            state="error",
                            expanded=False,
                        )
                        decision_state = "error"
                    else:
                        status_box.update(
                            label="✅ Gatekeeper: Auto-approved",
                            state="complete",
                            expanded=False,
                        )
                        decision_state = "success"

                    # -----------------------------------------------------------------
                    # 7. OUTPUT STRUCTURE – TABS
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
                            delta="STOP" if score and score > 50 else "GO",
                            delta_color="inverse",
                        )
                        m2.metric(
                            "Net Risk Score",
                            f"{score or 0}/100",
                            delta=severity or "N/A",
                            delta_color="inverse",
                        )
                        m3.metric(
                            "Policy Violations",
                            len(policy_violations),
                            delta="Detected" if policy_violations else "None",
                            delta_color="inverse",
                        )

                        st.plotly_chart(create_risk_gauge(float(score or 0)), use_container_width=True)

                        if decision_state == "error":
                            st.error(
                                "🛑 **BLOCKED / ESCALATE** – This access request breaches SoD / NIST guardrails. "
                                "See Risk Signals & Board Report for details."
                            )
                        else:
                            st.success(
                                "✅ **APPROVED / WITHIN GUARDRAILS** – Risk is within the defined policy envelope."
                            )

                        st.markdown("#### 📄 Executive Audit Report")
                        st.caption("Auto-generated board report suitable for regulators, auditors and risk committees.")
                        st.markdown(pipeline_result.board_report, unsafe_allow_html=True)

                        st.download_button(
                            label="📥 Download Audit Report (Markdown)",
                            data=pipeline_result.board_report,
                            file_name=f"Audit_Report_{req_data.get('request_id', 'UNKNOWN')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                    # --- Risk Signals Tab -------------------------------------------
                    with signals_tab:
                        st.markdown("#### 🚦 Risk Factor Analysis")

                        risk_signals = safe_get(investigation, "risk_signals", {}) or {}
                        if not risk_signals:
                            st.info("No structured `risk_signals` object returned. Showing raw investigation instead.")
                            st.json(investigation)
                        else:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Binary Risk Signals**")
                                for key, val in risk_signals.items():
                                    emoji = "🔴" if bool(val) else "🟢"
                                    label = key.replace("_", " ").title()
                                    st.markdown(format_badge(label, emoji), unsafe_allow_html=True)

                            with col_b:
                                st.markdown("**High-Level Interpretation**")
                                high_flags = [k for k, v in risk_signals.items() if v]
                                if not high_flags:
                                    st.success("No critical risk flags raised by the investigator.")
                                else:
                                    st.error(
                                        "The following risk levers are raised: "
                                        + ", ".join(k.replace("_", " ") for k in high_flags)
                                    )

                            st.markdown("---")
                            st.markdown("**Risk Scoring JSON (Analyst Output)**")
                            st.json(pipeline_result.risk_score)

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
                            st.json(up or {"note": "No profile details returned."})

                            st.markdown("**Current Entitlements (WHAT THEY ALREADY HAVE)**")
                            st.json(ent or {"note": "No entitlement data returned."})

                        with c2:
                            st.markdown("**Peer Baseline (NORM)**")
                            st.json(peer or {"note": "No peer baseline returned."})

                            st.markdown("**Recent Activity (BEHAVIOR)**")
                            st.json(act or {"note": "No SIEM activity returned."})

                        st.markdown("---")
                        st.markdown("#### 📜 Policy Violations")
                        if not policy_violations:
                            st.success("No explicit policy violations detected for this request.")
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
                            st.info("No execution trace returned from engine.")
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
                        st.json(pipeline_result.risk_score)
                        st.markdown("---")
                        st.markdown("**Gatekeeper Decision JSON**")
                        st.json({"decision": pipeline_result.decision})
                        st.markdown("---")
                        st.markdown("**Execution Trace**")
                        st.json(pipeline_result.execution_trace)

else:
    # If not run yet, show a placeholder in the output panel
    with output_col:
        st.info(
            "👈 Configure a scenario and JSON payload, then click **“Run Security Audit”** "
            "to see the full agentic risk pipeline and board-ready report."
        )
