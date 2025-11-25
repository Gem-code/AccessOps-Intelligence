import streamlit as st
import asyncio
import json
import os
import io
import base64
import matplotlib.pyplot as plt
from math import pi
from datetime import datetime
import nest_asyncio

# Import your Logic Engine (Must be in the same folder)
try:
    import accessops_engine
except ImportError:
    st.error("CRITICAL: 'accessops_engine.py' not found. Please upload it.")
    st.stop()

# Apply Async Fix
nest_asyncio.apply()

# ============================================================================
# 1. VISUAL UTILITIES (The "Swag" Features)
# ============================================================================

def draw_risk_gauge(score):
    """Draws a speedometer-style gauge for risk score."""
    # Colors
    colors = ["#22C55E", "#F59E0B", "#EF4444"] # Green, Yellow, Red
    
    fig, ax = plt.subplots(figsize=(4, 2.5), subplot_kw={'projection': 'polar'})
    fig.patch.set_alpha(0) # Transparent background
    ax.set_theta_offset(pi)
    ax.set_theta_direction(-1)
    
    # Draw Arcs
    ax.barh(1, pi/3, left=0, height=0.5, color=colors[0])      # Low
    ax.barh(1, pi/3, left=pi/3, height=0.5, color=colors[1])   # Med
    ax.barh(1, pi/3, left=2*pi/3, height=0.5, color=colors[2]) # High
    
    # Draw Needle
    angle = (score / 100) * pi
    ax.arrow(angle, 0, 0, 1, width=0.05, head_width=0.15, head_length=0.2, fc='white', ec='black')
    
    # Clean up chart
    ax.set_ylim(0, 1.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines['polar'].set_visible(False)
    
    return fig

def generate_pdf_report(request_data, result):
    """Generates a professional PDF using ReportLab (Simplified from teammate)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib import colors
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    
    # Header
    c.setFillColorRGB(0.1, 0.1, 0.2) # Dark Blue
    c.rect(0, height-80, width, 80, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height-50, "AccessOps Intelligence Audit")
    
    # Content
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    y = height - 120
    
    # 1. Request Details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "1. Access Request Details")
    y -= 25
    c.setFont("Helvetica", 11)
    for key, val in request_data.items():
        c.drawString(50, y, f"{key}: {str(val)[:80]}") # Truncate long lines
        y -= 15
        
    y -= 20
    
    # 2. Risk Verdict
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "2. Automated Risk Verdict")
    y -= 25
    
    decision = result.get('decision', 'UNKNOWN')
    score = result.get('risk_score', {}).get('net_risk_score', 0)
    
    # Color badge
    if "DENY" in decision or "REVIEW" in decision:
        c.setFillColor(colors.red)
    else:
        c.setFillColor(colors.green)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"DECISION: {decision}")
    c.setFillColor(colors.black)
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Net Risk Score: {score}/100")
    
    # 3. Audit Trail (Cleaned)
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "3. Executive Summary")
    y -= 25
    c.setFont("Helvetica", 10)
    
    report_text = result.get('board_report', "No report generated.")
    # Simple text wrap for PDF
    lines = report_text.split('\n')
    for line in lines:
        if "###" in line: continue # Skip markdown headers
        if y < 50: 
            c.showPage()
            y = height - 50
        c.drawString(50, y, line.replace('*', '').replace('#', ''))
        y -= 14
        
    c.save()
    buffer.seek(0)
    return buffer

# ============================================================================
# 2. PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="AccessOps | CISO Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Dark Mode CSS
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0E1117; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #161B22; }
    
    /* Metrics */
    div[data-testid="metric-container"] {
        background-color: #21262D;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 8px;
    }
    
    /* Headers */
    h1, h2, h3 { color: #E6EDF3 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Success/Error Boxes */
    .stSuccess { background-color: rgba(35, 134, 54, 0.2); border: 1px solid #238636; }
    .stError { background-color: rgba(218, 54, 51, 0.2); border: 1px solid #DA3633; }
    
    /* Buttons */
    div.stButton > button {
        width: 100%;
        background-color: #238636;
        color: white;
        border: none;
        padding: 12px;
        font-size: 16px;
        font-weight: 600;
    }
    div.stButton > button:hover { background-color: #2EA043; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 3. SIDEBAR & CONFIG
# ============================================================================

with st.sidebar:
    # Logo (Using Mermaid Ink for reliability)
    st.image("https://mermaid.ink/img/pako:eNp1k01vwyAMhv8K8nFK1B942GGn3aZqT9W0uXAhwRqQBEyVqv_9OMm67bI4gPH7gW1swFpaQwG8e9fK0cNlq7S8b7S6q1S9r9W90g8gL1pda_2ilb7R6lGrl8q8aP2i1V_68cW20E_6y8W20u9tC_2gH19sC_2iv1xsK_22bSH8yv-F0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZt4de_G0I_6McX20K_6C8X20q_bVv49e-G0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZtIfzK_4XQD_rxxd9sC_1i1y62lX7btvDr3w2hH_Tji22hX_SXi22l37Yt9I_-K4R-0I8vtoV-0V8utpV-27bQj_4rhP6FEPpBP77YFvpFf7nYVvpt28KvfzeEftCPL7aFftFfLraVftu20I_-K4R-0I8vtoV-0V8utpV-27aFfvRfIfQvhNAP-vHFttAv-svFttJv2xbCr_xfCP2gH19sC_2iv1xsK_22baF_9F8h9C-E0A_68cW20C_6y8W20m_bFn79uyH0g358sS30i_5ysa3027aFfvRfIfSDfnzxt9pC_wF7tN2G", use_column_width=True)
    
    st.markdown("### ⚙️ System Configuration")
    
    # API Key handling
    api_key = st.text_input("Google API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    if not api_key:
        st.warning("⚠️ API Key Required")
    else:
        os.environ["GOOGLE_API_KEY"] = api_key # Set for engine to use
        st.success("🔑 System Secured")

    st.markdown("---")
    st.markdown("### 📂 Scenario Templates")
    
    # Scenario Templates (The Teammate's good idea, simplified)
    scenario = st.radio(
        "Select a Test Case:",
        ["Toxic Finance Bot (Critical)", "DevOps Engineer (Low Risk)", "Custom Payload"]
    )

# ============================================================================
# 4. MAIN DASHBOARD
# ============================================================================

st.title("🛡️ AccessOps Intelligence")
st.caption("Agentic Governance for Non-Human Identities")

# Data Prep based on Template
if scenario == "Toxic Finance Bot (Critical)":
    default_json = {
        "request_id": "REQ-TOXIC-001",
        "user_id": "svc_finops_auto_bot",
        "identity_type": "ai_agent",
        "resource": "prod_general_ledger_rw",
        "access_type": "write",
        "justification": "AI Agent detected anomaly. Requesting autonomous write access to fix."
    }
elif scenario == "DevOps Engineer (Low Risk)":
    default_json = {
        "request_id": "REQ-DEVOPS-99",
        "user_id": "eng_human_user",
        "identity_type": "human",
        "resource": "dev_logs_read",
        "access_type": "read",
        "justification": "Investigating debug logs in non-prod."
    }
else:
    default_json = {}

# Input Column
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📨 Incoming Access Request")
    request_text = st.text_area("JSON Payload", value=json.dumps(default_json, indent=2), height=250)
    
    run_btn = st.button("🚨 RUN RISK ASSESSMENT", type="primary")

# Execution Logic
if run_btn and api_key:
    try:
        req_data = json.loads(request_text)
        
        with col2:
            st.subheader("🧠 Agentic Reasoning Trace")
            status_container = st.status("🕵️ Investigator Agent: Gathering context...", expanded=True)
            
            # 1. Run the Engine
            # We wrap the async call here
            result = asyncio.run(accessops_engine.run_pipeline(req_data))
            
            # 2. Update UI Steps
            status_container.write("✅ Investigator: Context gathered (IAM, Peers, Logs)")
            status_container.write(f"✅ Analyst: Inherent Risk Score calculated.")
            status_container.write("✅ Critic: Audit review complete.")
            
            decision = result.decision
            score = result.risk_score.get('net_risk_score', 0)
            
            if "DENY" in decision or "REVIEW" in decision:
                status_container.update(label="🛑 Gatekeeper: BLOCKED High Risk Request", state="error", expanded=True)
            else:
                status_container.update(label="✅ Gatekeeper: Approved", state="complete", expanded=False)

        # ==========================
        # RESULTS AREA
        # ==========================
        st.divider()
        
        # Header
        r_col1, r_col2, r_col3 = st.columns([1, 1, 1])
        
        with r_col1:
            st.metric("Final Decision", decision, delta="STOP" if score > 50 else "GO", delta_color="inverse")
        
        with r_col2:
            st.metric("Net Risk Score", f"{score}/100", delta="Critical" if score > 80 else "Safe", delta_color="inverse")
            
        with r_col3:
            # The Visual Gauge
            st.pyplot(draw_risk_gauge(score), transparent=True)

        # The Report
        st.subheader("📄 Executive Audit Artifact (NIST 800-53)")
        with st.container():
            st.markdown(result.board_report)
            
        # PDF Download
        pdf_bytes = generate_pdf_report(req_data, {
            "decision": decision,
            "risk_score": result.risk_score,
            "board_report": result.board_report
        })
        
        st.download_button(
            label="⬇️ Download Official Audit PDF",
            data=pdf_bytes,
            file_name=f"Audit_Report_{req_data.get('request_id')}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Simulation Error: {e}")
        st.info("Make sure 'accessops_engine.py' is in the same folder.")

elif run_btn and not api_key:
    st.error("❌ Access Denied: Please enter Google API Key in the sidebar.")
