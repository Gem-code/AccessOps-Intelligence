"""
AccessOps Intelligence - SIMPLE, WORKING VERSION
No fancy CSS, no complex layouts - JUST WORKS
"""

import streamlit as st
import json
import os
import asyncio
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, List

# Import your backend (adjust path if needed)
try:
    from google.adk.agents import LlmAgent
    from google.adk.models.google_llm import Gemini
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
except ImportError:
    st.error("⚠️ Google ADK not installed. Check requirements.txt")
    st.stop()

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="AccessOps Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# ============================================================================
# SIMPLE CSS - NO FANCY STUFF
# ============================================================================

st.markdown("""
<style>
    .stApp {
        background: #0e1117;
        color: #e2e8f0;
    }
    h1, h2, h3 {
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MOCK DATA & TOOLS (FROM YOUR BACKEND)
# ============================================================================

def load_mock_data():
    return {
        "users": {
            "svc_finops_auto_bot": {
                "user_id": "svc_finops_auto_bot",
                "job_title": "Automated Financial Ops",
                "department": "Finance Automation",
                "tenure_months": 12,
                "identity_type": "ai_agent"
            }
        },
        "entitlements": {
            "svc_finops_auto_bot": ["finance_read_only", "report_viewer"]
        },
        "peer_baseline": {
            "Automated Financial Ops|Finance Automation": {
                "typical_access": ["read_only", "report_generation"],
                "write_access_rate": 0.0
            }
        },
        "policies": {
            "POL-SOD-001": {
                "description": "No automated bot shall have Write access to Production Ledger",
                "resource_pattern": "*general_ledger*",
                "allowed_roles": ["CFO", "Controller"],
                "severity": "CRITICAL"
            }
        },
        "activity_logs": {
            "svc_finops_auto_bot": {
                "lookback_days": 30,
                "recent_high_risk_actions": ["API Call: POST /ledger/update (Blocked)"]
            }
        }
    }

def get_user_profile(user_id: str) -> str:
    data = load_mock_data()
    profile = data["users"].get(user_id, {"error": f"User {user_id} not found"})
    return json.dumps(profile, indent=2)

def get_current_entitlements(user_id: str) -> str:
    data = load_mock_data()
    entitlements = data["entitlements"].get(user_id, [])
    return json.dumps({"entitlements": entitlements}, indent=2)

def get_peer_baseline(job_title: str, department: str) -> str:
    data = load_mock_data()
    key = f"{job_title}|{department}"
    baseline = data["peer_baseline"].get(key, {"typical_access": ["read_only"], "write_access_rate": 0.05})
    return json.dumps(baseline, indent=2)

def check_policy_violations(user_id: str, job_title: str, requested_resource_id: str, access_type: str) -> str:
    data = load_mock_data()
    violations = []
    if "general_ledger" in requested_resource_id and access_type == "write":
        if "bot" in user_id.lower() or "svc_" in user_id:
            violations.append({
                "policy_id": "POL-SOD-001",
                "description": "SoD: No automated bot shall have Write access to Production Ledger",
                "severity": "CRITICAL",
                "nist_control": "AC-6",
                "finding": f"AI Agent '{user_id}' requesting write access to financial system"
            })
    return json.dumps({"policy_violations": violations}, indent=2)

def get_activity_logs(user_id: str) -> str:
    data = load_mock_data()
    logs = data["activity_logs"].get(user_id, {"recent_high_risk_actions": []})
    return json.dumps(logs, indent=2)

# ============================================================================
# AGENT CREATION (SIMPLIFIED)
# ============================================================================

def create_simple_agent(llm_model):
    """Create one investigator agent with all tools"""
    investigator = LlmAgent(
        model=llm_model,
        name="investigator",
        description="Access risk investigator",
        instruction="Investigate this access request by calling all 5 tools. Return findings as JSON.",
        tools=[
            get_user_profile,
            get_current_entitlements,
            get_peer_baseline,
            check_policy_violations,
            get_activity_logs
        ]
    )
    return investigator

# ============================================================================
# SIMPLE PIPELINE
# ============================================================================

@dataclass
class SimpleResult:
    decision: str
    risk_score: int
    findings: Dict[str, Any]
    duration: float

async def run_simple_pipeline(request_data: Dict[str, Any]) -> SimpleResult:
    """Simplified pipeline - just investigator + basic risk calc"""
    
    start_time = time.time()
    
    # Initialize
    session_service = InMemorySessionService()
    session_id = f"session-{int(time.time())}"
    await session_service.create_session(
        app_name="accessops-intel",
        user_id="user",
        session_id=session_id
    )
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key required")
    
    llm_model = Gemini(model="gemini-1.5-flash", api_key=api_key)
    agent = create_simple_agent(llm_model)
    
    # Run investigation
    runner = Runner(agent=agent, session_service=session_service, app_name="accessops-intel")
    
    prompt = f"Investigate this access request: {json.dumps(request_data, indent=2)}"
    
    raw_output = ""
    async for event in runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message={"text": prompt}
    ):
        if hasattr(event, 'content') and event.content:
            raw_output += str(event.content)
    
    # Simple risk calculation
    risk_score = 50  # Default
    if "bot" in request_data.get("user_id", "").lower():
        risk_score += 30
    if request_data.get("access_type") == "write":
        risk_score += 20
    
    decision = "BLOCKED" if risk_score >= 80 else "APPROVED"
    
    duration = time.time() - start_time
    
    return SimpleResult(
        decision=decision,
        risk_score=risk_score,
        findings={"raw_output": raw_output},
        duration=duration
    )

# ============================================================================
# STREAMLIT UI
# ============================================================================

st.title("🛡️ AccessOps Intelligence")
st.subheader("Enterprise Security Platform")

# SIDEBAR
with st.sidebar:
    st.header("🔑 API Key")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ Configured")
    else:
        st.warning("⚠️ Enter key")

# MAIN AREA
st.markdown("---")
st.header("🧪 Test Scenario")

st.info("Testing: Rogue bot requesting WRITE to Production Ledger")

# Quick stats
col1, col2, col3 = st.columns(3)
col1.metric("Expected Risk", "95/100")
col2.metric("Decision", "BLOCKED")
col3.metric("Policy", "POL-SOD-001")

# JSON input (simple)
toxic_scenario = {
    "request_id": "REQ-001",
    "user_id": "svc_finops_auto_bot",
    "access_type": "write",
    "requested_resource_id": "prod_general_ledger_rw"
}

with st.expander("Edit JSON"):
    request_json = st.text_area("Request:", value=json.dumps(toxic_scenario, indent=2), height=150)

# THE BUTTON
st.markdown("---")
if st.button("🚨 RUN SECURITY AUDIT", use_container_width=True):
    
    if not api_key:
        st.error("❌ Enter API key in sidebar!")
        st.stop()
    
    try:
        request_data = json.loads(request_json)
    except:
        st.error("❌ Invalid JSON")
        st.stop()
    
    with st.spinner("🔄 Running audit..."):
        try:
            result = asyncio.run(run_simple_pipeline(request_data))
            
            st.success("✅ Audit complete!")
            
            # Results
            if result.decision == "BLOCKED":
                st.error(f"# 🛑 {result.decision}")
            else:
                st.success(f"# ✅ {result.decision}")
            
            st.metric("Risk Score", f"{result.risk_score}/100")
            st.write(f"Duration: {result.duration:.2f}s")
            
            with st.expander("See findings"):
                st.json(result.findings)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
