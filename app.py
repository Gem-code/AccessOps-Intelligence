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
    st.error("CRITICAL ERROR: 'accessops_engine.py' not found. Please ensure it is in the same directory.")
    st.stop()

# Allow asyncio.run inside Streamlit
nest_asyncio.apply()

# ---------------------------------------------------------------------
# 1. PAGE CONFIG & LIGHT THEME
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="AccessOps Intelligence – CISO Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Light, enterprise-style theme overrides
st.markdown(
    """
<style>
    .stApp {
        background-color: #f3f4f6;  /* light gray */
        color: #111827;             /* near-black text */
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }

    section[data-testid="stSidebar"] {
        background-color: #e5e7eb;  /* slightly darker sidebar */
        border-right: 1px solid #d1d5db;
    }

    .step-header {
        background-color: #e5e7eb;
        padding: 10px 16px;
        border-radius: 8px;
        border-left: 4px solid #2563eb;
        margin-bottom: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        color: #111827;
    }

    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.1rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid rgba(148,163,184,0.9);
        background-color: #e5e7eb;
        color: #111827;
    }

    .stTextArea textarea {
        background-color: #ffffff;
        color: #111827;
        border: 1px solid #d1d5db;
        font-family: "JetBrains Mono", Menlo, Monaco, Consolas, "Courier New", monospace;
        font-size: 0.8rem;
    }

    .stRadio label {
        color: #111827 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    div.stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: #f9fafb;
        border-radius: 999px;
        border: none;
        font-weight: 600;
        height: 3rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.8rem;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
        transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
    }

    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        padding: 10px 12px;
    }

    button[data-baseweb="tab"] {
        background-color: #e5e7eb !important;
        border-radius: 999px !important;
        border: 1px solid transparent !important;
        padding: 0.3rem 0.9rem !important;
        margin-right: 0.3rem !important;
        font-size: 0.8rem !important;
        color: #374151 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-color: #2563eb !important;
        background-color: #dbeafe !important;
        color: #1e3a8a !important;
    }

    .trace-card {
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        padding: 0.75rem 1rem;
        background-color: #ffffff;
        font-size: 0.8rem;
    }

    .caption-sm {
        font-size: 0.7rem;
        color: #6b7280;
    }

    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #6b7280;
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
            title={"text": "Net Risk Score", "font": {"size": 18, "color": "#111827"}},
            number={"font": {"size": 32, "color": "#111827"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#4b5563"},
                "bar": {"color": "rgba(0,0,0,0)"},
                "bgcolor": "#ffffff",
                "borderwidth": 1,
                "bordercolor": "#e5e7eb",
                "steps": [
                    {"range": [0, 30], "color": "#bbf7d0"},
                    {"range": [30, 60], "color": "#fef3c7"},
                    {"range": [60, 85], "color": "#fed7aa"},
                    {"range": [85, 100], "color": "#fecaca"},
                ],
                "threshold": {
                    "line": {"color": "#111827", "width": 4},
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
# 3. SIDEBAR – STEP 1: AUTH / CONFIG
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ AccessOps Intelligence")
    st.caption(
        "Agentic risk engine for **Non-Human Identities**.\n"
        "This UI exposes the full pipeline: investigation, scoring, critique, gatekeeper, and board report."
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Step 1: Runtime Configuration")

    api_key = st.text_input(
        "Google API Key (for local / MakerSuite):",
        type="password",
        help="For local API-key runs. In Cloud Run, Vertex AI uses the service account.",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API key set for this session.")
    else:
        st.info("Using default Vertex / GCP identity from `accessops_engine.py`.")

    st.markdown("---")
    st.markdown("#### 🧪 Demo Scenarios")
    st.markdown(
        """
- **DevOps Engineer (LOW RISK)** – Human requesting read-only access to Dev logs.
- **Toxic Finance Bot (CRITICAL)** – AI bot trying to write to Production General Ledger.
- **Custom Payload** – Paste any request JSON you want to test.
"""
    )

    st.markdown("---")
    st.markdown("#### 📓 Judge Runbook")
    st.caption(
        "1. Ensure Step 1 API Key is set (or Vertex identity is configured).\n"
        "2. Choose a scenario and inspect the JSON.\n"
        "3. Run the audit.\n"
        "4. Use tabs: **Executive**, **Signals**, **Context**, **Agent Trace**, **Raw JSON**.\n"
        "5. Export the board packet as Markdown or PDF."
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
# 5. INPUT PANEL – STEP 2 / STEP 3
# ---------------------------------------------------------------------
input_col, output_col = st.columns([1.05, 1.45])

with input_col:
    # Step 2 – Scenario
    st.markdown('<div class="step-header">📝 Step 2 – Select Scenario</div>', unsafe_allow_html=True)

    scenario = st.radio(
        "Select a pre-defined test case:",
        # DevOps LOW first, Critical second (as requested)
        ["DevOps Engineer (LOW RISK)", "Toxic Finance Bot (CRITICAL RISK)", "Custom Payload"],
        captions=[
            "Human engineer requesting read-only access to non-production logs.",
            "AI service account attempting unauthorized write access to General Ledger.",
            "Bring your own JSON body.",
        ],
    )

    # Step 3 – JSON payload
    if "DevOps" in scenario:
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
    elif "Toxic" in scenario:
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

    st.markdown('<div class="step-header">📨 Step 3 – Review / Edit JSON Payload</div>', unsafe_allow_html=True)
    st.caption("This JSON is passed into the ADK / Vortex agentic pipeline.")
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
            "Required keys:\n"
            "- `request_id`\n"
            "- `user_id`\n"
            "- `requested_resource_id`\n"
            "- `access_type`"
        )

# ---------------------------------------------------------------------
# 6. EXECUTION & OUTPUT
# ---------------------------------------------------------------------
pipeline_result: Optional["accessops_engine.PipelineResult"] = None

if run_btn:
    with output_col:
        st.markdown('<div class="step-header">🧠 Step 4 – Agentic Reasoning Trace</div>', unsafe_allow_html=True)

        if not api_key:
            st.warning(
                "You can run with Vertex / service account only, but if you intended to use an API key, "
                "please complete **Step 1 – Runtime Configuration** in the sidebar."
            )

        # Parse JSON
        try:
    req_data = json.loads(request_text)
except json.JSONDecodeError:
    st.error("❌ Invalid JSON – please correct syntax (double quotes, commas, etc.).")
else:
    missing = [k for k in ["request_id", "user_id", "requested_resource_id", "access_type"] if k not in req_data]
    if missing:
        st.error(f"❌ Missing required key(s): {', '.join(missing)}.")
    else:
        missing = [k for k in ["request_id", "user_id", "requested_resource_id", "access_type"] if k not in req_data]

