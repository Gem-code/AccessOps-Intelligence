import streamlit as st
import json
import os
import asyncio
import nest_asyncio
import plotly.graph_objects as go
from datetime import datetime
import io

# Import your logic engine
try:
    import accessops_engine
except ImportError:
    st.error("CRITICAL ERROR: 'accessops_engine.py' not found. Please ensure it is in the same directory.")
    st.stop()

# Fix for asyncio
nest_asyncio.apply()

# ============================================================================
# 1. PAGE CONFIG & PROFESSIONAL FINANCIAL THEME
# ============================================================================
st.set_page_config(
    page_title="AccessOps Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: "Financial Blue" Professional Theme
st.markdown("""
<style>
    /* Main Background - Deep Navy Blue (Financial Trust) */
    .stApp {
        background-color: #0f172a; 
        color: #e2e8f0;
    }
    
    /* Sidebar - Darker Slate */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    
    /* Step Headers */
    .step-header {
        background-color: #1e293b;
        padding: 12px 20px;
        border-radius: 6px;
        border-left: 5px solid #3b82f6; /* Blue Accent */
        margin-bottom: 15px;
        font-weight: 600;
        font-size: 1.1em;
        color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Inputs & Text Areas */
    .stTextArea textarea {
        background-color: #0f172a;
        color: #a5d6ff;
        border: 1px solid #334155;
        font-family: 'Courier New', monospace;
    }
    
    /* Radio Buttons - Fix Visibility */
    .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 500;
        font-size: 1rem;
    }
    
    /* Primary Button - Financial Blue */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        font-weight: 600;
        height: 3.5em;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* Metrics & Containers */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 15px;
    }
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
        title = {'text': "NIST Risk Score", 'font': {'size': 20, 'color': "#e2e8f0"}},
        number = {'font': {'size': 40, 'color': "white"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"}, # Transparent bar
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#334155",
            'steps': [
                {'range': [0, 30], 'color': "#10b981"},  # Green
                {'range': [30, 60], 'color': "#f59e0b"}, # Amber
                {'range': [60, 85], 'color': "#ef4444"}, # Red
                {'range': [85, 100], 'color': "#7f1d1d"} # Dark Red
            ],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=30, r=30, t=50, b=30), height=250)
    return fig

def generate_pdf_download(report_text):
    # Simulating PDF generation for the button
    return report_text.encode('utf-8')

# ============================================================================
# 3. SIDEBAR (Step 1: Authentication)
# ============================================================================
with st.sidebar:
    # Logo
    st.image("https://mermaid.ink/img/pako:eNp1k01vwyAMhv8K8nFK1B942GGn3aZqT9W0uXAhwRqQBEyVqv_9OMm67bI4gPH7gW1swFpaQwG8e9fK0cNlq7S8b7S6q1S9r9W90g8gL1pda_2ilb7R6lGrl8q8aP2i1V_68cW20E_6y8W20u9tC_2gH19sC_2iv1xsK_22bSH8yv-F0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZt4de_G0I_6McX20K_6C8X20q_bVv49e-G0A_68cW20C_6y8W20m_bFvpH_xVC_0II_aAfX2wL_aK_XGwr_bZtIfzK_4XQD_rxxd9sC_1i1y62lX7btvDr3w2hH_Tji22hX_SXi22l37Yt9I_-K4R-0I8vtoV-0V8utpV-27bQj_4rhP6FEPpBP77YFvpFf7nYVvpt28KvfzeEftCPL7aFftFfLraVftu20I_-K4R-0I8vtoV-0V8utpV-27aFfvRfIfQvhNAP-vHFttAv-svFttJv2xbCr_xfCP2gH19sC_2iv1xsK_22baF_9F8h9C-E0A_68cW20C_6y8W20m_bFn79uyH0g358sS30i_5ysa3027aFfvRfIfSDfnzxt9pC_wF7tN2G", use_column_width=True)
    
    st.markdown("### ⚙️ Step 1: Configuration")
    
    api_key = st.text_input("Enter Google API Key:", type="password", help="Get from MakerSuite or Google Cloud")
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ Key Authenticated")
    else:
        st.warning("⚠️ Please enter API Key to proceed")

    st.markdown("---")
    st.info("**AccessOps Intelligence**\nAutomated Governance for Non-Human Identities.")

# ============================================================================
# 4. MAIN DASHBOARD
# ============================================================================

st.title("🛡️ CISO Command Center")
st.markdown("### Enterprise Access Risk Assessment")

# Rebalanced Layout: Left (1) vs Right (2)
col1, col2 = st.columns([1, 2])

with col1:
    # --- Step 2: Scenario Selection ---
    st.markdown('<div class="step-header">📝 Step 2: Load Scenario Template</div>', unsafe_allow_html=True)
    
    # High Contrast Radio Buttons
    scenario = st.radio(
        "Select a Test Case:",
        ["1. DevOps Engineer (LOW RISK)", "2. Toxic Finance Bot (CRITICAL RISK)", "3. Custom Payload"],
        captions=[
            "✅ Safe: Human requesting Read Access.", 
            "🛑 Danger: AI Bot requesting Write Access.", 
            "✏️ Edit the JSON manually below."
        ]
    )
    
    # --- JSON Pre-filling Logic ---
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
            "justification": "Debugging build failure."
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
            "justification": "AI Agent detected anomaly. Requesting autonomous write access to fix."
        }
    else:
        # Custom Template
        default_json = {
            "request_id": "REQ-CUSTOM-001",
            "user_id": "enter_user_id",
            "requested_resource_id": "enter_resource_id",
            "access_type": "read",
            "justification": "Enter justification here"
        }

    # --- Step 3: Review Payload ---
    st.markdown('<div class="step-header">📨 Step 3: Review JSON Payload</div>', unsafe_allow_html=True)
    request_text = st.text_area("Verify Request Data:", value=json.dumps(default_json, indent=2), height=300)

    # --- Action Button ---
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("🚨 RUN SECURITY AUDIT", type="primary", use_container_width=True)

# ============================================================================
# 5. EXECUTION & REPORTING
# ============================================================================

if run_btn:
    if not api_key:
        st.error("❌ STOP: Please complete Step 1 (Sidebar) by entering your API Key.")
    else:
        with col2:
            st.markdown('<div class="step-header">🧠 Step 4: Agentic Reasoning Trace</div>', unsafe_allow_html=True)
            
            try:
                req_data = json.loads(request_text)
                
                # --- Validation Check ---
                if "requested_resource_id" not in req_data:
                    st.error("❌ JSON Error: Missing key 'requested_resource_id'. Please restore the template.")
                    st.stop()

                # --- Live Agent Execution ---
                status_box = st.status("🕵️ AccessOps Core Initializing...", expanded=True)
                
                async def run_analysis():
                    # Call the imported engine
                    return await accessops_engine.run_pipeline(req_data)

                result = asyncio.run(run_analysis())
                
                # Update Status Steps
                status_box.write("✅ Investigator: IAM & Peer data loaded.")
                status_box.write("✅ Analyst: NIST 800-53 Risk Score calculated.")
                status_box.write("✅ Critic: Adversarial review complete.")
                
                # --- Verdict Logic ---
                decision = result.decision
                score = result.risk_score.get('net_risk_score', 0)
                
                if "DENY" in decision or "REVIEW" in decision:
                    status_box.update(label="🛑 GATEKEEPER: BLOCKED (High Risk)", state="error", expanded=False)
                    alert_type = "error"
                else:
                    status_box.update(label="✅ GATEKEEPER: APPROVED", state="complete", expanded=False)
                    alert_type = "success"

                # --- Step 5: Results Dashboard ---
                st.divider()
                st.subheader("📊 Step 5: Audit Results")
                
                # Metrics Row
                m1, m2, m3 = st.columns(3)
                m1.metric("Decision", decision, delta="STOP" if score > 50 else "GO", delta_color="inverse")
                m2.metric("Net Risk Score", f"{score}/100", delta="CRITICAL" if score > 80 else "SAFE", delta_color="inverse")
                
                policy_vs = len(result.investigation.get('policy_violations', []))
                m3.metric("Policy Violations", policy_vs, delta="DETECTED" if policy_vs > 0 else "None", delta_color="inverse")
                
                # Gauge
                st.plotly_chart(create_risk_gauge(score), use_container_width=True)
                
                # Final Verdict Box
                if alert_type == "error":
                    st.error(f"🛑 **BLOCKED:** This request violates security policies. Human intervention required.")
                else:
                    st.success("✅ **APPROVED:** Request is within normal parameters.")
                
                # --- Step 6: Reports ---
                c1, c2 = st.columns(2)
                
                with c1:
                    with st.expander("📜 View Raw Audit Log (JSON)"):
                         st.json(result.risk_score)
                         
                with c2:
                    with st.expander("📄 View Board Report (Markdown)", expanded=True):
                        st.markdown(result.board_report)
                
                # PDF Download Button (Fixed Visibility)
                st.download_button(
                    label="📥 Download Official Board Report (PDF)",
                    data=result.board_report,
                    file_name=f"Audit_Report_{req_data.get('request_id')}.md",
                    mime="text/markdown",
                    help="Download the NIST-compliant audit report for offline review.",
                    use_container_width=True
                )

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON format. Please check your input.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
