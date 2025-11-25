import streamlit as st
import json
import os
import asyncio
import nest_asyncio
import plotly.graph_objects as go
from datetime import datetime

# Import your logic engine
try:
    import accessops_engine
except ImportError:
    st.error("CRITICAL ERROR: 'accessops_engine.py' not found. Please ensure it is in the same directory.")
    st.stop()

# Fix for asyncio
nest_asyncio.apply()

# ============================================================================
# 1. PAGE CONFIG & STYLING (High Contrast)
# ============================================================================
st.set_page_config(
    page_title="AccessOps Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for visibility and "Steps" styling
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Step Headers */
    .step-header {
        background-color: #1f2937;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    /* JSON Input Area */
    .stTextArea textarea {
        background-color: #161b22;
        color: #a5d6ff;
        font-family: 'Courier New', monospace;
    }
    
    /* Sidebar Text Visibility */
    .stRadio label { color: #ffffff !important; font-weight: 600; }
    
    /* Success/Error/Info Boxes */
    .stAlert { font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. VISUAL HELPERS
# ============================================================================
def create_risk_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "NIST Risk Score", 'font': {'size': 20, 'color': "#ffffff"}},
        number = {'font': {'size': 40, 'color': "white"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 30], 'color': "#059669"},
                {'range': [30, 60], 'color': "#d97706"},
                {'range': [60, 85], 'color': "#dc2626"},
                {'range': [85, 100], 'color': "#7f1d1d"}
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=30, r=30, t=50, b=30), height=250)
    return fig

# ============================================================================
# 3. SIDEBAR (Configuration)
# ============================================================================
with st.sidebar:
    st.image("https://mermaid.ink/img/pako:eNp1k01vwyAMhv8K8nFK1B942GGn3aZqT9W0uXAhwRqQBEyVqv_9OMm67bI4gPH7gW1swFpaQwG8e9fK0cNlq7S8b7S6q1S9r9W90g8gL1pda_2ilb7R6lGrl8q8aP2i1V_68cW20E_6y8W20u9tC_2gH19sC_2iv1xsK_22bSH8yv-F0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZt4de_G0I_6McX20K_6C8X20q_bVv49e-G0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZtIfzK_4XQD_rxxd9sC_1i1y62lX7btvDr3w2hH_Tji22hX_SXi22l37Yt9I_-K4R-0I8vtoV-0V8utpV-27bQj_4rhP6FEPpBP77YFvpFf7nYVvpt28KvfzeEftCPL7aFftFfLraVftu20I_-K4R-0I8vtoV-0V8utpV-27aFfvRfIfQvhNAP-vHFttAv-svFttJv2xbCr_xfCP2gH19sC_2iv1xsK_22baF_9F8h9C-E0A_68cW20C_6y8W20m_bFn79uyH0g358sS30i_5ysa3027aFfvRfIfSDfnzxt9pC_wF7tN2G", use_column_width=True)
    
    st.markdown("### ⚙️ Step 1: Configuration")
    
    # API Key Input
    api_key = st.text_input("Enter Google API Key:", type="password", help="Required for Gemini 1.5 Flash")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ Key Loaded")
    else:
        st.warning("⚠️ Waiting for Key...")

    st.markdown("---")
    st.info("**About:** This system prevents 'Context Blindness' by using Agentic AI to evaluate non-human identity access requests.")

# ============================================================================
# 4. MAIN DASHBOARD
# ============================================================================

st.title("🚦 CISO Command Center")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown('<div class="step-header">📝 Step 2: Select a Scenario</div>', unsafe_allow_html=True)
    
    # SCENARIO TEMPLATES (Corrected Keys)
    scenario = st.radio(
        "Choose a Test Case to Pre-fill:",
        ["Toxic Finance Bot (CRITICAL)", "DevOps Engineer (LOW)", "Custom"],
        help="Click to load a pre-defined JSON payload."
    )
    
    # Logic to switch JSON based on selection
    if scenario == "Toxic Finance Bot (CRITICAL)":
        default_json = {
            "request_id": "REQ-TOXIC-001",
            "user_id": "svc_finops_auto_bot",
            "identity_type": "ai_agent",
            "job_title": "Automated Financial Ops",
            "department": "Finance Automation",
            "requested_resource_id": "prod_general_ledger_rw",  # FIXED KEY
            "requested_resource_name": "Production General Ledger",
            "access_type": "write",
            "system_criticality": "tier_1",
            "data_sensitivity": "restricted",
            "justification": "AI Agent detected anomaly. Requesting autonomous write access to fix."
        }
        st.caption("ℹ️ **Context:** A bot is asking for Write Access to the General Ledger. This violates SoD policies.")
        
    elif scenario == "DevOps Engineer (LOW)":
        default_json = {
            "request_id": "REQ-DEVOPS-005",
            "user_id": "eng_human_user",
            "identity_type": "human",
            "job_title": "Senior DevOps",
            "department": "Engineering",
            "requested_resource_id": "dev_logs_read",  # FIXED KEY
            "requested_resource_name": "Dev Logs",
            "access_type": "read",
            "system_criticality": "non_prod",
            "data_sensitivity": "internal",
            "justification": "Debugging build failure."
        }
        st.caption("ℹ️ **Context:** A human engineer requesting Read Access to logs. Low risk.")
    else:
        default_json = {}

    # Text Area
    st.markdown('<div class="step-header">📨 Step 3: Review JSON Payload</div>', unsafe_allow_html=True)
    request_text = st.text_area("Access Request Data:", value=json.dumps(default_json, indent=2), height=300)

    # Run Button
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚨 RUN SECURITY AUDIT", type="primary", use_container_width=True)

# ============================================================================
# 5. EXECUTION LOGIC
# ============================================================================

if run_btn:
    if not api_key:
        st.error("❌ STOP: You must enter a Google API Key in the Sidebar (Step 1).")
    else:
        with col2:
            st.markdown('<div class="step-header">🧠 Step 4: Agentic Reasoning Trace</div>', unsafe_allow_html=True)
            
            try:
                req_data = json.loads(request_text)
                
                # Check for the specific key that caused the error
                if "requested_resource_id" not in req_data:
                    st.error("❌ JSON Error: Missing key 'requested_resource_id'. The Engine needs this to check policies.")
                    st.stop()

                # Status Container
                status_box = st.status("🕵️ Agents Initializing...", expanded=True)
                
                # Async Execution Wrapper
                async def run_analysis():
                    status_box.write("🔍 Investigator: Fetching IAM & Peer Data...")
                    return await accessops_engine.run_pipeline(req_data)

                # Run!
                result = asyncio.run(run_analysis())
                
                # Update Status
                status_box.write("✅ Investigator: Context Loaded.")
                status_box.write("✅ Analyst: NIST 800-53 Risk Calculated.")
                status_box.write("✅ Critic: Peer Review Complete.")
                
                # Decision Logic
                decision = result.decision
                score = result.risk_score.get('net_risk_score', 0)
                
                if "DENY" in decision or "REVIEW" in decision:
                    status_box.update(label="🛑 GATEKEEPER: BLOCKED (High Risk)", state="error", expanded=False)
                    alert_type = "error"
                else:
                    status_box.update(label="✅ GATEKEEPER: APPROVED", state="complete", expanded=False)
                    alert_type = "success"

                # Results Dashboard
                st.divider()
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Decision", decision, delta="STOP" if score > 50 else "GO", delta_color="inverse")
                m2.metric("Net Risk Score", f"{score}/100", delta="CRITICAL" if score > 80 else "SAFE", delta_color="inverse")
                
                policy_vs = len(result.investigation.get('policy_violations', []))
                m3.metric("Policy Violations", policy_vs, delta="DETECTED" if policy_vs > 0 else "None", delta_color="inverse")
                
                # Gauge
                st.plotly_chart(create_risk_gauge(score), use_container_width=True)
                
                # Final Alert
                if alert_type == "error":
                    st.error(f"🛑 **BLOCKED:** This request violates security policies. See Report below.")
                else:
                    st.success("✅ **APPROVED:** Request is within normal parameters.")
                
                # Report
                with st.expander("📄 View Executive Audit Report", expanded=True):
                    st.markdown(result.board_report)

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format in text area.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
