import os
import json
import asyncio
import io
from datetime import datetime, timezone
from typing import Any, Dict, List

import nest_asyncio
import plotly.graph_objects as go
import streamlit as st
from streamlit_monaco import st_monaco 

# One-time session timestamp in UTC 
session_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ---------------------------------------------------------------------
# 0. ENGINE WIRING
# ---------------------------------------------------------------------
try:
    import accessops_engine
except ImportError:
    st.error("CRITICAL ERROR: 'accessops_engine.py' not found. Please ensure it is in the same directory.")
    st.stop()

# Allow re-entrant event loop for Streamlit
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

st.markdown(
    """
<style>
    .stApp {
        background-color: #f3f4f6;
        color: #111827;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #e5e7eb;
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
# 2. SESSION STATE (PERSIST LATEST RESULT)
# ---------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state["result"] = None
    st.session_state["req_data"] = None
    st.session_state["error_msg"] = None

# ---------------------------------------------------------------------
# 3. HELPERS
# ---------------------------------------------------------------------
def create_risk_gauge(score: float) -> go.Figure:
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

def create_pdf_bytes(board_report_md: str, title: str) -> bytes:
    """
    Generate a Board Report PDF that closely matches the Streamlit UI:
      - Title: AccessOps Board Report – <REQ-ID>
      - 🛡 Executive Board Report heading + paragraph
      - 🚦 Risk Factor Analysis (NIST/COBIT) table
        * Status column uses per-row "traffic light" status (🔴 / 🟡 / 🟢)
      - 📋 Recommended Management Action (supports numbered list OR single paragraph)

    This version uses ReportLab Platypus so it plays nicely with the rest of the app.
    """

    import io
    from reportlab.lib.pagesizes import LETTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()

    # Styles roughly matching UI
    h_title = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=12,
    )
    h_section = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceAfter=10,
    )
    body = ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=10,
    )

    story = []

    # ------------------------------------------------------------------
    # 0. Top title ("AccessOps Board Report – REQ-XXX")
    # ------------------------------------------------------------------
    story.append(Paragraph(title, h_title))
    story.append(Spacer(1, 6))

    lines = board_report_md.splitlines()

    # ------------------------------------------------------------------
    # 1. Executive Board Report (🛡 heading + paragraph)
    # ------------------------------------------------------------------
    story.append(Paragraph("🛡 Executive Board Report", h_section))

    exec_summary_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "Executive Board Report" in line:
            # consume following non-empty lines until blank or next heading
            i += 1
            while i < len(lines):
                l = lines[i].strip()
                if not l:
                    break
                # skip markdown headings
                if l.startswith("#"):
                    break
                exec_summary_lines.append(l)
                i += 1
            break
        i += 1

    if exec_summary_lines:
        exec_text = " ".join(exec_summary_lines)
        story.append(Paragraph(exec_text, body))
        story.append(Spacer(1, 12))

    # ------------------------------------------------------------------
    # 2. Risk Factor Analysis (🚦 heading + table)
    # ------------------------------------------------------------------
    story.append(Paragraph("🚦 Risk Factor Analysis (NIST/COBIT)", h_section))

    headers = []
    rows = []

    i = 0
    while i < len(lines):
        if "| Status" in lines[i] and "Risk Component" in lines[i]:
            # header row
            header_cells = [c.strip() for c in lines[i].strip().split("|") if c.strip()]
            headers = header_cells
            # skip separator row
            i += 2
            # data rows
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().split("|") if c.strip()]
                rows.append(cells)
                i += 1
            break
        i += 1

    # Clean markdown from data cells (remove **)
    cleaned_rows = []
    for r in rows:
        cleaned_rows.append([cell.replace("**", "") for cell in r])

    # Table rendering: Status column shows traffic-light status
    if headers and cleaned_rows:
        col_widths = [0.6 * inch, 2.1 * inch, 3.0 * inch]
        table_data = [headers] + cleaned_rows

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        ts = TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )

        # Status column colors (per-row)
        for row_idx in range(1, len(table_data)):
            status_cell = table_data[row_idx][0]
            status_str = str(status_cell).strip()
            # Map emojis / words to colors
            if "🔴" in status_str or "HIGH" in status_str.upper() or "CRIT" in status_str.upper():
                fill = colors.red
            elif "🟡" in status_str or "MED" in status_str.upper():
                fill = colors.yellow
            elif "🟠" in status_str or "ORANGE" in status_str.upper():
                fill = colors.orange
            else:
                # default LOW/green
                fill = colors.green
            ts.add("BACKGROUND", (0, row_idx), (0, row_idx), fill)
            ts.add("TEXTCOLOR", (0, row_idx), (0, row_idx), colors.white)
            ts.add("ALIGN", (0, row_idx), (0, row_idx), "CENTER")

        t.setStyle(ts)
        story.append(t)
        story.append(Spacer(1, 12))

    # ------------------------------------------------------------------
    # 3. Recommended Management Action (📋 heading + body)
    # ------------------------------------------------------------------
    story.append(Paragraph("📋 Recommended Management Action", h_section))

    actions_raw = []
    i = 0
    while i < len(lines):
        if "Recommended Management Action" in lines[i]:
            i += 1
            while i < len(lines):
                l = lines[i].strip()
                if not l:
                    i += 1
                    continue
                # stop if we hit another markdown heading (unlikely at end)
                if l.startswith("#"):
                    break
                actions_raw.append(l)
                i += 1
            break
        i += 1

    if actions_raw:
        # Determine if we have numbered list items like "1. text"
        numbered = all(
            (len(l) > 2 and l[0].isdigit() and l[1] in {".", ")"})
            for l in actions_raw
        )
        if numbered:
            # Render each as its own numbered paragraph
            for l in actions_raw:
                # strip leading "1. " or "1) "
                parts = l.split(" ", 1)
                if len(parts) == 2 and parts[0][0].isdigit():
                    text = parts[1]
                else:
                    text = l
                story.append(Paragraph(text, body))
        else:
            # Treat as a single paragraph (e.g. DevOps LOW-risk example)
            combined = " ".join(actions_raw)
            story.append(Paragraph(combined, body))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes




    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "h1",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=12,
        leading=22,
    )
    h2 = ParagraphStyle(
        "h2",
        parent=styles["Heading2"],
        fontSize=15,
        spaceAfter=10,
        leading=20,
    )
    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
    )

    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=50, rightMargin=50)
    story = []

    # Title
    story.append(Paragraph("<b>AccessOps Board Report</b>", h1))
    story.append(Spacer(1, 6))

    # EXECUTIVE SUMMARY
    story.append(Paragraph("🛡️ <b>Executive Board Report</b>", h2))
    story.append(Paragraph(executive_summary, body))
    story.append(Spacer(1, 12))

    # RISK FACTOR ANALYSIS
    story.append(Paragraph("🚦 <b>Risk Factor Analysis (NIST/COBIT)</b>", h2))

    table_data = [["Status", "Risk Component", "Audit Note"]]
    for row in risk_rows:
        table_data.append([row[0], row[1], row[2]])

    table = Table(table_data, colWidths=[60, 170, 230])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    risk_rows = [
    ("🔴", "Inherent Risk", "Score: TBD"),
    ("🟡", "Control Effectiveness", "API Quota Exceeded"),
    ("🔴", "Compliance Gaps", "TBD"),
    ("🔴", "Net Risk Score", "PENDING")
]
    
def run_pipeline_sync(request_context: Dict[str, Any]):
    """
    Helper to run the async pipeline from Streamlit safely.
    Uses the existing event loop or creates one if needed.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(accessops_engine.run_pipeline(request_context))


# ---------------------------------------------------------------------
# 4. SIDEBAR – STEP 1: RUNTIME CONFIG
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ AccessOps Intelligence")
    st.caption(
        "Agentic risk engine for **Non-Human Identities**.\n"
        "UI exposes investigation, scoring, critique, gatekeeper & board report."
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Step 1 – Runtime Configuration")

    api_key = st.text_input(
        "Add Gemini API key to start AccessOps.",
        type="password",
        help="For local / MakerSuite runs. In Cloud Run, Vertex AI uses service account auth.",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API key set for this session.")
    else:
        st.info("Using default Vertex / GCP identity from backend config.")

    st.markdown("---")
    st.markdown("#### 🧪 Demo Scenarios")
    st.markdown(
        """
- **DevOps Engineer (LOW RISK)** – Human requesting read-only access to Dev logs.
- **Toxic Finance Bot (CRITICAL)** – AI bot asking to write to Production General Ledger.
- **Custom Scenario** – Paste or edit any JSON access request you want to test.
"""
    )

    st.markdown("---")
    st.markdown("#### 📓 AccessOps Runbook")
    st.caption(
        "1. Add Gemini API key to start AccessOps.\n"
        "2. Select or build a scenario & inspect JSON.\n"
        "3. Run Security Audit.\n"
        "4. Expand to view: Executive Overview, Risk Indicators, Context & POlicies, Agent Trace (ADK), Raw JSON.\n"
        "5. Generate board report."
        "6. Download board report and audit log."
    )

# ---------------------------------------------------------------------
# 5. HEADER
# ---------------------------------------------------------------------
# ----------- Top Header Row With Logo (Balanced) -------------

col1, col2 = st.columns([3, 1])  # wider left column, narrower right

with col1:
    st.markdown(
        """
        <h1 style='margin-top: 10px; margin-bottom: -5px;'>
            CISO Command Center — AccessOps Intelligence
        </h1>
        <p style='font-size: 18px; color: #444; margin-top: 0;'>
            Real-time access risk adjudication for human and AI identities,
            grounded in NIST 800-53 and Segregation-of-Duties policies.
        </p>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
<style>
.logo-container {
    width: 110%;            /* adjust width as needed */
    height: 145x;         
    overflow: hidden;      
    border-radius: 8px;   
    margin-top: 5px;
    margin-right: auto;
    margin-left: -40px;     /* pushes container to the right */
}

.logo-container img {
    width: 100%;           /* image fills container */
    height: 100%;          
    object-fit: cover;     
    display: block;        
}
</style>

<div class="logo-container">
    <img src="https://raw.githubusercontent.com/Gem-code/AccessOps-Intelligence/refs/heads/master/AccessOps-AI_SecurityShield_Header_Image.png"
         alt="AccessOps Intelligence Header">
</div>
        """,
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.markdown("### 🕒 Session Context")
    st.info(f"**UTC:** {session_timestamp}")
    st.success("NIST 800-53 • AC-6 • SoD")

# Create a narrower container for the expander
with st.container():
    st.markdown("""
        <style>
        .narrow-expander .streamlit-expander {
            width: 20% !important;      /* adjust width */
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Apply custom class
    st.markdown('<div class="narrow-expander">', unsafe_allow_html=True)

    with st.expander("🧩 Why this matters"):
        st.markdown(
            "- Most modern breaches involve some form of identity or access failure.\n"
            "- AI agents can request powerful access at machine speed, often outside traditional IAM workflows.\n"
            "- AccessOps Intelligence makes those AI and human access decisions **explainable, auditable and policy-aligned**."
        )

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("")

# ---------------------------------------------------------------------
# 6. INPUT PANEL – STEP 2 & 3
# ---------------------------------------------------------------------
input_col, output_col = st.columns([1.05, 1.45])

with input_col:
    # Step 2 – Scenario
    st.markdown('<div class="step-header">📝 Step 2 – Select/Build AccessOps Scenario</div>', unsafe_allow_html=True)
    scenario = st.radio(
        "Select/Build AccessOps Scenario",
        ["DevOps Engineer (LOW RISK)", "Toxic Finance Bot (CRITICAL RISK)", "Custom Scenario"],
        captions=[
            "Human requesting read-only access to non-production logs.",
            "AI service account attempting write access to Production General Ledger.",
            "Paste or edit any JSON access request.",
        ],
    )

    # Prefill JSON
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

    # Step 3 – JSON payload
    st.markdown('<div class="step-header">📨 Step 3 – Review / Edit JSON Payload</div>', unsafe_allow_html=True)
    st.caption("This JSON is passed into the ADK / Vortex agentic pipeline.")
    
    # Monaco editor with JSON syntax highlighting (no key argument)
    request_text = st_monaco(
        value=json.dumps(default_json, indent=2),
        language="json",
        theme="vs-light",
        height="280px",
    )

    
    run_col, hint_col = st.columns([2, 1])
    with run_col:
        run_btn = st.button("🚨 Run Security Audit", use_container_width=True)
    with hint_col:
        st.markdown("**Required keys**")
        st.markdown(
            f"{format_badge('request_id','🔑')} "
            f"{format_badge('user_id','👤')} "
            f"{format_badge('requested_resource_id','📦')} "
            f"{format_badge('access_type','🔐')}",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------
# 7. RUN PIPELINE (STORE IN SESSION STATE)
# ---------------------------------------------------------------------
if run_btn:
    try:
        req_data = json.loads(request_text)
    except json.JSONDecodeError:
        st.session_state["result"] = None
        st.session_state["req_data"] = None
        st.session_state["error_msg"] = (
            "❌ The access request is not valid JSON. "
            "Please check commas, quotes and brackets and try again."
        )
    else:
        missing = [k for k in ["request_id", "user_id", "requested_resource_id", "access_type"] if k not in req_data]
        if missing:
            st.session_state["result"] = None
            st.session_state["req_data"] = None
            st.session_state["error_msg"] = (
                "❌ The following required fields are missing in the JSON: "
                + ", ".join(missing)
                + ". Please add them and re-run."
            )
        else:
            try:
                result = run_pipeline_sync(req_data)
            except Exception as e:
                st.session_state["result"] = None
                st.session_state["req_data"] = None
                st.session_state["error_msg"] = (
                    "⚠️ Something went wrong while running the risk engine. "
                    "This is a system issue, not your request. "
                    "If it keeps happening, please share this code with the engineering team:\n\n"
                    f"`{type(e).__name__}: {e}`"
                )
            else:
                st.session_state["result"] = result
                st.session_state["req_data"] = req_data
                st.session_state["error_msg"] = None

# ---------------------------------------------------------------------
# 8. RENDER OUTPUT (PERSISTS ACROSS INTERACTIONS)
# ---------------------------------------------------------------------
with output_col:
    st.markdown('<div class="step-header">🧠 Step 4 – Agentic Reasoning Trace</div>', unsafe_allow_html=True)

    error_msg = st.session_state.get("error_msg")
    result = st.session_state.get("result")
    req_data = st.session_state.get("req_data")

    if error_msg:
        st.error(error_msg)
    elif result is None or req_data is None:
        st.info(
            "👈 Complete **Step 1 – Runtime Configuration** in the sidebar if needed, "
            "then choose a scenario and click **Run Security Audit** to view the full pipeline."
        )
    else:
        # ---------------- Safely extract backend fields ----------------
        decision = getattr(result, "decision", "UNKNOWN")
        risk_score_obj: Dict[str, Any] = getattr(result, "risk_score", {}) or {}
        investigation: Dict[str, Any] = getattr(result, "investigation", {}) or {}
        board_report: str = getattr(result, "board_report", "No board report returned.")
        execution_trace: List[Dict[str, Any]] = getattr(result, "execution_trace", []) or []

        score = risk_score_obj.get("net_risk_score", 0) or 0
        severity = risk_score_obj.get("severity_level") or risk_score_obj.get("severity_label", "UNKNOWN")

        # Normalise policy violations to list[dict]
        raw_pv = investigation.get("policy_violations", []) or []
        if not isinstance(raw_pv, list):
            raw_pv = [raw_pv]
        policy_violations: List[Dict[str, Any]] = []
        for v in raw_pv:
            if isinstance(v, dict):
                policy_violations.append(v)
            else:
                policy_violations.append(
                    {"policy_id": "UNKNOWN", "description": str(v), "severity": "N/A"}
                )

        # Decision banner (for on-screen view)
        if "DENY" in decision.upper() or "REVIEW" in decision.upper():
            decision_state = "error"
        else:
            decision_state = "success"

        st.markdown(
            f"<div class='caption-sm'>Last evaluated request: "
            f"<code>{req_data.get('request_id', 'UNKNOWN')}</code></div>",
            unsafe_allow_html=True,
        )

        # ---------- Multi-Agent Status summary ----------
        agent_counts: Dict[str, int] = {}
        for phase in execution_trace:
            agent_name = phase.get("agent") or phase.get("phase") or "unknown_agent"
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1

        st.markdown(
            "**Multi-Agent Security Council:** "
            "1️⃣ Investigator → 2️⃣ Severity Analyst → 3️⃣ Critic → 4️⃣ Gatekeeper → 5️⃣ Narrator"
        )

        if agent_counts:
            st.markdown("#### 🤖 Multi-Agent Status")
            cols = st.columns(min(len(agent_counts), 4))
            items = list(agent_counts.items())
            for idx, (agent_name, count) in enumerate(items):
                col = cols[idx % len(cols)]
                with col:
                    pretty_name = agent_name.replace("_", " ").title()
                    st.markdown(
                        f"{format_badge(pretty_name, '✅')}<br>"
                        f"<span class='caption-sm'>{count} events</span>",
                        unsafe_allow_html=True,
                    )

        # ---------------------- TABS (Step 5) ---------------------------
        st.markdown("")
        st.markdown('<div class="step-header">📊 Step 5 – Risk Dashboard</div>', unsafe_allow_html=True)

        overview_tab, signals_tab, context_tab, trace_tab, raw_tab = st.tabs(
            [
                "Executive Overview",
                "Risk Indicators",
                "Context & Policies",
                "Agent Trace (ADK)",
                "Raw JSON",
            ]
        )

        st.markdown("""
        <style>

        /* Shrink metric label */
        div[data-testid="stMetricLabel"] {
            font-size: 20px !important;
        }

        /* Shrink main metric value */
        div[data-testid="stMetricValue"] {
            font-size: 20px !important;
            font-weight: 600 !important;
        }

        /* Shrink delta text (GO/STOP/DETECTED) */
        div[data-testid="stMetricDelta"] {
            font-size: 20px !important;
        }

        </style>
        """, unsafe_allow_html=True)

        # Executive Overview
        with overview_tab:
            m1, m2, m3 = st.columns(3)
            m1.metric("Decision", decision, delta="STOP" if score > 50 else "GO", delta_color="inverse")
            m2.metric(
                "Net Risk Score",
                f"{score:.0f}/100",
                delta=severity,
                delta_color="inverse",
            )
            m3.metric(
                "Policy Violations",
                len(policy_violations),
                delta="DETECTED" if policy_violations else "None",
                delta_color="inverse",
            )

            st.plotly_chart(create_risk_gauge(float(score)), use_container_width=True)

            if decision_state == "error":
                st.error(
                    "🛑 **BLOCKED / ESCALATE** – This access request breaches SoD / NIST guardrails. "
                    "See Risk Indicators & Board Report for detailed rationale."
                )
            else:
                st.success(
                    "✅ **APPROVED / WITHIN GUARDRAILS** – Risk is within the defined policy envelope."
                )

            st.caption(
                "Mapped to **NIST 800-53** controls (AC-6, IA-5, AU-6) and Segregation-of-Duties policies."
            )
            # Normalize heading: change "Executive Audit Summary" -> "Executive Board Report"
            normalized_board_report = board_report or "No board report returned."
            normalized_board_report = normalized_board_report.replace(
                "Executive Audit Summary", "Executive Board Report", 1
            )
            
            # --- Executive / Board Report (collapsed by default to keep layout compact) ---
            st.markdown("#### 📄 Executive / Board Report")
            
            # Clear, accurate preview label
            st.caption("Preview: ### 🛡️ Board and Audit Reports")
            
            with st.expander("View full Board Report", expanded=False):
                # Use the normalized version so the heading says "Executive Board Report"
                st.markdown(normalized_board_report, unsafe_allow_html=True)
            
                # --- Download buttons: Board Report first, then Audit Log ---
                report_id = req_data.get("request_id", "UNKNOWN")
            
                pdf_bytes = create_pdf_bytes(
                    normalized_board_report,  # <- use normalized text in the PDF as well
                    f"AccessOps Board Report – {report_id}",
                )
            
                audit_log = {
                    "request": req_data,
                    "decision": decision,
                    "risk_score": risk_score_obj,
                    "investigation": investigation,
                    "execution_trace": execution_trace,
                }
                audit_log_md = "```json\n" + json.dumps(audit_log, indent=2) + "\n```"
                audit_log_bytes = audit_log_md.encode("utf-8")
            
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    st.download_button(
                        label="📊 Board Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"Board_Report_{report_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                with dl_col2:
                    st.download_button(
                        label="📄 Audit Log Report (Markdown)",
                        data=audit_log_bytes,
                        file_name=f"Audit_Log_{report_id}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            
            # Architecture diagram (Data Flow) – also in an expander, closed by default
            with st.expander("📦 End-to-End AccessOps Pipeline (Architecture Diagram)", expanded=False):
                try:
                    st.image("data_flow.png", use_column_width=True)
                except Exception:
                    st.info("Architecture diagram PNG not found in repository (data_flow.png).")

        # Risk Indicators 
        with signals_tab:
            st.markdown("#### 🚦 Risk Factor Analysis")
            risk_signals = investigation.get("risk_signals", {}) or {}
            if not isinstance(risk_signals, dict) or not risk_signals:
                st.info(
                    "The engine did not return structured Risk Indicators  for this run. "
                    "Showing the full investigation details instead."
                )
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
                        st.success("No critical risk flags raised by the investigator.")
                    else:
                        st.error(
                            "Raised signals: "
                            + ", ".join(k.replace("_", " ") for k in high_flags)
                        )

                st.markdown("---")
                st.markdown("**Risk Scoring JSON**")
                st.json(risk_score_obj)

        # Context & Policies
        with context_tab:
            st.markdown("#### 🧩 Context Signals")
            up = investigation.get("user_profile", {})
            ent = investigation.get("current_access", {})
            peer = investigation.get("peer_baseline", {})
            act = investigation.get("activity_summary", {})

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
                    policy_id = v.get("policy_id", "POLICY")
                    severity_v = v.get("severity", "SEVERITY")
                    with st.expander(f"🛑 {policy_id} – {severity_v}", expanded=True):
                        st.write(v.get("description", ""))
                        st.markdown(
                            f"**NIST Control:** `{v.get('nist_control', 'N/A')}`  \n"
                            f"**Finding:** {v.get('finding', 'N/A')}"
                        )

            # Gatekeeper deterministic logic diagram
            with st.expander("🚦 Gatekeeper Safety Logic (Deterministic Controls)", expanded=False):
                try:
                    st.image("gatekeeper_logic.png", use_column_width=True)
                except Exception:
                    st.info(
                        "Gatekeeper diagram PNG not found in repository "
                        "(5. Decision Logic Flow (Gatekeeper).png)."
                    )

        # Agent Trace
        with trace_tab:
            st.markdown("#### 🧬 ADK Agent Trace")
            if not execution_trace:
                st.info(
                    "No detailed agent trace was returned for this request. "
                    "You can still review the decision, risk score and board report."
                )
            else:
                for i, phase in enumerate(execution_trace, start=1):
                    phase_name = phase.get("phase", "unknown")
                    agent_name = phase.get("agent", "unknown")
                    with st.expander(f"{i}. Phase: {phase_name}", expanded=True):
                        st.markdown(
                            f"<div class='caption-sm'>Agent: `{agent_name}`</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown("<div class='trace-card'>", unsafe_allow_html=True)
                        st.json(phase)
                        st.markdown("</div>", unsafe_allow_html=True)

            # Toxic scenario interaction diagram
            with st.expander("🧪 Multi-Agent Sequence Diagram (Toxic Scenario)", expanded=False):
                try:
                    st.image("agent_sequence_toxic.png", use_column_width=True)
                except Exception:
                    st.info(
                        "Sequence diagram PNG not found in repository "
                        '(2. Agent Interaction Sequence (The "Toxic" Scenario).png).'
                    )

        # Raw JSON
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
            st.json({"decision": decision})
            st.markdown("---")
            st.markdown("**Execution Trace**")
            st.json(execution_trace)
