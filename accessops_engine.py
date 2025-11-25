"""
AccessOps Intelligence - Kaggle-Compatible Version
Fixes the Tool import error by using standard ADK function declarations
"""

import os
import json
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ============================================================================
# SECTION 1: MOCK DATA
# ============================================================================

def load_mock_data():
    """Simulates database lookups"""
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
                "description": "Segregation of Duties: No automated bot shall have Write access to Production Ledger",
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


# ============================================================================
# SECTION 2: TOOL FUNCTIONS (Plain Python - ADK will auto-convert)
# ============================================================================

def get_user_profile(user_id: str) -> str:
    """
    Fetch user's HR profile from identity management system.
    
    Args:
        user_id: Unique identifier for the user/agent
        
    Returns:
        JSON string containing job_title, department, tenure_months
    """
    data = load_mock_data()
    profile = data["users"].get(user_id, {"error": f"User {user_id} not found"})
    return json.dumps(profile, indent=2)


def get_current_entitlements(user_id: str) -> str:
    """
    Retrieve all resources currently granted to user.
    
    Args:
        user_id: Unique identifier
        
    Returns:
        JSON string with list of entitlements
    """
    data = load_mock_data()
    entitlements = data["entitlements"].get(user_id, [])
    return json.dumps({"entitlements": entitlements}, indent=2)


def get_peer_baseline(job_title: str, department: str) -> str:
    """
    Get statistical baseline of access for similar roles.
    
    Args:
        job_title: Job role
        department: Department name
        
    Returns:
        JSON string with typical_access and write_access_rate
    """
    data = load_mock_data()
    key = f"{job_title}|{department}"
    baseline = data["peer_baseline"].get(key, {
        "typical_access": ["read_only"],
        "write_access_rate": 0.05
    })
    return json.dumps(baseline, indent=2)


def check_policy_violations(user_id: str, job_title: str, requested_resource_id: str, access_type: str) -> str:
    """
    Check if access request violates organizational policies.
    
    Returns:
        JSON string with policy_violations list
    """
    data = load_mock_data()
    violations = []
    
    # Check if request violates SoD policy
    if "general_ledger" in requested_resource_id and access_type == "write":
        if "bot" in user_id.lower() or "svc_" in user_id:
            violations.append({
                "policy_id": "POL-SOD-001",
                "description": "SoD: No automated bot shall have Write access to Production Ledger",
                "severity": "CRITICAL",
                "nist_control": "AC-6 (Least Privilege)",
                "finding": f"AI Agent '{user_id}' requesting write access to financial system"
            })
    
    return json.dumps({"policy_violations": violations}, indent=2)


def get_activity_logs(user_id: str) -> str:
    """
    Retrieve recent high-risk actions from SIEM.
    
    Returns:
        JSON string with recent_high_risk_actions
    """
    data = load_mock_data()
    logs = data["activity_logs"].get(user_id, {"recent_high_risk_actions": []})
    return json.dumps(logs, indent=2)


# ============================================================================
# SECTION 3: AGENT CREATION
# ============================================================================

def create_agents(llm_model: Gemini) -> Dict[str, LlmAgent]:
    """Create all agents with proper tool bindings."""
    
    # Investigator - calls tools to gather context
    investigator = LlmAgent(
        model=llm_model,
        name="context_investigator",
        description="Gathers all context signals by calling IAM/SIEM tools",
        instruction="""
        You are an enterprise access risk investigator. Your job:
        
        1. Call get_user_profile(user_id) to understand WHO is requesting
        2. Call get_current_entitlements(user_id) to see what they have now
        3. Call get_peer_baseline(job_title, department) to check if request is normal
        4. Call check_policy_violations(user_id, job_title, resource_id, access_type) for compliance
        5. Call get_activity_logs(user_id) to check for anomalies
        
        Output JSON with these exact keys:
        {
          "user_profile": <dict>,
          "current_access": <list>,
          "peer_baseline": <dict>,
          "policy_violations": <list>,
          "activity_summary": <dict>,
          "risk_signals": {
            "privilege_escalation": <bool>,
            "outside_peer_norms": <bool>,
            "policy_violation_found": <bool>,
            "ai_agent_scope_mismatch": <bool>
          }
        }
        
        Call ALL tools. Do not skip any.
        """,
        tools=[
            get_user_profile,
            get_current_entitlements,
            get_peer_baseline,
            check_policy_violations,
            get_activity_logs
        ]
    )
    
    # Severity Analyst - calculates NIST-based risk score
    severity_analyst = LlmAgent(
        model=llm_model,
        name="severity_analyst",
        description="Calculates risk scores using NIST 800-53 framework",
        instruction="""
        You are a Senior Risk Analyst applying NIST 800-53 AC-6 (Least Privilege).
        
        Calculate:
        1. Inherent Risk (0-100): Base risk of the permission
           - Admin to Tier-1 = 90-100
           - Write to restricted = 70-90
           - Read to confidential = 40-60
        
        2. Compensating Factors (each reduces risk):
           - MFA enabled: -10
           - Time-bound access: -15
           - Peer-certified: -10
        
        3. Control Failures: Map to NIST codes
        
        4. Net Risk = Inherent - Compensating
        
        5. Severity: LOW (0-30), MEDIUM (31-60), HIGH (61-85), CRITICAL (86-100)
        
        Output JSON with keys: inherent_risk_score, compensating_factors, 
        control_failures, net_risk_score, severity_level, confidence
        """,
        tools=[]
    )
    
    # Critic - challenges the analyst's score
    critic = LlmAgent(
        model=llm_model,
        name="risk_critic",
        description="Challenges risk assessments to prevent false positives",
        instruction="""
        You are the Internal Auditor. Review the Severity Analyst's score.
        
        Challenge by asking:
        - Did they consider emergency/on-call justification?
        - Are there compensating controls they missed?
        - Is this too conservative for the system criticality?
        
        Output JSON:
        {
          "critique_valid": <bool>,
          "critique_reasoning": <string>,
          "suggested_adjustment": <string>
        }
        
        Be skeptical but fair.
        """,
        tools=[]
    )
    
    # Gatekeeper - makes authorization decision
    gatekeeper = LlmAgent(
        model=llm_model,
        name="gatekeeper",
        description="Makes final authorization decision",
        instruction="""
        You are the Gatekeeper. Decide based on risk score:
        
        RULES:
        - CRITICAL → DENY + Require CISO
        - HIGH + Policy Violation → PENDING_HUMAN_REVIEW
        - HIGH + No violations → PENDING_MANAGER_REVIEW
        - MEDIUM + Controls → AUTO_APPROVE
        - LOW → AUTO_APPROVE
        
        Output JSON:
        {
          "decision": "AUTO_APPROVE | PENDING_HUMAN_REVIEW | DENY",
          "reasoning": <string>,
          "required_approvers": [<list or null>],
          "expires_in_hours": <int or null>
        }
        """,
        tools=[]
    )
    
    # Narrator - generates board report
    narrator = LlmAgent(
        model=llm_model,
        name="board_reporter",
        description="Generates executive summary",
        instruction="""
        You are a CISO reporting to the Board.
        
        Generate Markdown with this structure:
        
        ### 🛡️ Executive Audit Summary
        [1-2 sentences on governance impact]
        
        ### 🚦 Risk Factor Analysis (NIST/COBIT)
        | Status | Risk Component | Audit Note |
        | :---: | :--- | :--- |
        | 🔴 | **Inherent Risk** | Score: X |
        | 🟡 | **Control Effectiveness** | [factors] |
        | 🔴 | **Compliance Gaps** | [NIST codes] |
        | 🛑 | **Net Risk Score** | **[LEVEL]** |
        
        ### 📋 Recommended Management Action
        [Specific steps]
        
        Use emojis: 🔴 (high), 🟡 (medium), 🟢 (low), 🛑 (stop), ✅ (approved)
        """,
        tools=[]
    )
    
    return {
        "investigator": investigator,
        "analyst": severity_analyst,
        "critic": critic,
        "gatekeeper": gatekeeper,
        "narrator": narrator
    }


# ============================================================================
# SECTION 4: EXECUTION HELPER
# ============================================================================

async def execute_agent_with_trace(
    agent: LlmAgent,
    prompt: str,
    session_service: InMemorySessionService,
    session_id: str
) -> Dict[str, Any]:
    """Execute agent and return response with execution trace."""
    
    runner = Runner(
        agent=agent,
        app_name="accessops-intel",
        session_service=session_service
    )
    
    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )
    
    events = runner.run_async(
        user_id="demo-user",
        session_id=session_id,
        new_message=content
    )
    
    tool_calls = []
    responses = []
    
    try:
        async for event in events:
            # Track tool calls
            if hasattr(event, 'tool_calls') and event.tool_calls:
                for tc in event.tool_calls:
                    tool_calls.append({
                        "tool": tc.name if hasattr(tc, 'name') else str(tc),
                        "args": tc.args if hasattr(tc, 'args') else {}
                    })
            
            # Collect final response
            if event.is_final_response():
                if event.content and event.content.parts:
                    text = "".join(
                        getattr(p, "text", "") 
                        for p in event.content.parts 
                        if hasattr(p, "text")
                    )
                    responses.append(text)
    
    except Exception as e:
        print(f"⚠️ Error during agent execution: {e}")
        return {
            "response": {"error": str(e)},
            "tool_calls": tool_calls,
            "raw_output": ""
        }
    
    # Parse JSON from response
    final_text = "\n".join(responses)
    try:
        result = json.loads(final_text)
    except json.JSONDecodeError:
        # Extract JSON from markdown blocks
        start = final_text.find("{")
        end = final_text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                result = json.loads(final_text[start:end])
            except:
                result = {"raw_text": final_text}
        else:
            result = {"raw_text": final_text}
    
    return {
        "response": result,
        "tool_calls": tool_calls,
        "raw_output": final_text
    }


# ============================================================================
# SECTION 5: MAIN PIPELINE
# ============================================================================

@dataclass
class PipelineResult:
    """Container for pipeline results."""
    request_id: str
    decision: str
    risk_score: Dict[str, Any]
    investigation: Dict[str, Any]
    board_report: str
    execution_trace: List[Dict[str, Any]]


async def run_pipeline(request_context: Dict[str, Any]) -> PipelineResult:
    """Main orchestration - executes all agents in sequence."""
    
    print(f"🚀 Starting Pipeline for {request_context['request_id']}")
    
    # Initialize session
    session_service = InMemorySessionService()
    session_id = f"session-{request_context['request_id']}"
    await session_service.create_session(
        app_name="accessops-intel",
        user_id="demo-user",
        session_id=session_id
    )
    
    # Configure LLM with explicit API key
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=2,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504]
    )
    
  # Use Vertex AI instead of API key
    llm_model = Gemini(
        model="gemini-2.0-flash-001",
        vertexai=True,
        project="accessops-intel",
        location="us-central1",
        retry_options=retry_config
    )
    
    agents = create_agents(llm_model)
    execution_trace = []
    
    # PHASE 1: Investigation
    print("\n🔍 PHASE 1: Context Investigation")
    investigation_prompt = f"""
    Investigate this access request:
    
    {json.dumps(request_context, indent=2)}
    
    User ID: {request_context['user_id']}
    Resource: {request_context['requested_resource_id']}
    Access Type: {request_context['access_type']}
    Job Title: {request_context.get('job_title', 'Unknown')}
    Department: {request_context.get('department', 'Unknown')}
    
    Call ALL tools to gather complete context.
    """
    
    investigation = await execute_agent_with_trace(
        agent=agents["investigator"],
        prompt=investigation_prompt,
        session_service=session_service,
        session_id=session_id
    )
    
    print(f"   ✓ Tools called: {[tc['tool'] for tc in investigation['tool_calls']]}")
    execution_trace.append({
        "phase": "investigation",
        "agent": "investigator",
        "tool_calls": investigation["tool_calls"]
    })
    
    # PHASE 2: Risk Scoring
    print("\n📊 PHASE 2: Risk Scoring (NIST 800-53)")
    scoring_prompt = f"""
    Calculate risk for this investigation:
    
    Context: {json.dumps(investigation['response'], indent=2)}
    Request: {json.dumps(request_context, indent=2)}
    """
    
    initial_score = await execute_agent_with_trace(
        agent=agents["analyst"],
        prompt=scoring_prompt,
        session_service=session_service,
        session_id=session_id  # FIXED: Use same session
    )
    
    print(f"   ✓ Score: {initial_score['response'].get('net_risk_score', 'N/A')}")
    execution_trace.append({
        "phase": "scoring",
        "agent": "severity_analyst",
        "score": initial_score["response"]
    })
    
    # PHASE 3: Critique
    print("\n🧐 PHASE 3: Internal Audit Review")
    critique_prompt = f"""
    Review this assessment:
    
    Investigation: {json.dumps(investigation['response'], indent=2)}
    Score: {json.dumps(initial_score['response'], indent=2)}
    """
    
    critique = await execute_agent_with_trace(
        agent=agents["critic"],
        prompt=critique_prompt,
        session_service=session_service,
        session_id=session_id  # FIXED: Use same session
    )
    
    final_score = initial_score["response"]
    if critique["response"].get("critique_valid"):
        print(f"   ⚠️ Critique: {critique['response'].get('critique_reasoning', '')[:100]}...")
    
    execution_trace.append({
        "phase": "critique",
        "agent": "critic",
        "critique": critique["response"]
    })
    
    # PHASE 4: Gatekeeper
    print("\n🚦 PHASE 4: Authorization")
    gatekeeper_prompt = f"""
    Make authorization decision:
    
    Risk: {json.dumps(final_score, indent=2)}
    Context: {json.dumps(investigation['response'], indent=2)}
    """
    
    decision = await execute_agent_with_trace(
        agent=agents["gatekeeper"],
        prompt=gatekeeper_prompt,
        session_service=session_service,
        session_id=session_id  # FIXED: Use same session
    )
    
    decision_type = decision["response"].get("decision", "PENDING_HUMAN_REVIEW")
    print(f"   ✓ Decision: {decision_type}")
    
    if decision_type in ["DENY", "PENDING_HUMAN_REVIEW"]:
        print("   🛑 STOP! Human intervention required")
    
    execution_trace.append({
        "phase": "authorization",
        "agent": "gatekeeper",
        "decision": decision["response"]
    })
    
    # PHASE 5: Board Report
    print("\n📝 PHASE 5: Executive Report")
    report_prompt = f"""
    Generate Board report:
    
    Investigation: {json.dumps(investigation['response'], indent=2)}
    Risk: {json.dumps(final_score, indent=2)}
    Decision: {json.dumps(decision['response'], indent=2)}
    """
    
    report = await execute_agent_with_trace(
        agent=agents["narrator"],
        prompt=report_prompt,
        session_service=session_service,
        session_id=session_id  # FIXED: Use same session
    )
    
    board_report = report["response"].get("markdown_report", report["raw_output"])
    print("   ✓ Report generated")
    
    return PipelineResult(
        request_id=request_context["request_id"],
        decision=decision_type,
        risk_score=final_score,
        investigation=investigation["response"],
        board_report=board_report,
        execution_trace=execution_trace
    )


# ============================================================================
# SECTION 6: MAIN EXECUTION
# ============================================================================

async def main():
    """Test harness."""
    
    toxic_request = {
        "request_id": "REQ-AI-CRITICAL-001",
        "user_id": "svc_finops_auto_bot",
        "identity_type": "ai_agent",
        "job_title": "Automated Financial Ops",
        "department": "Finance Automation",
        "requested_resource_id": "prod_general_ledger_rw",
        "requested_resource_name": "Production General Ledger",
        "access_type": "write",
        "system_criticality": "tier_1",
        "data_sensitivity": "restricted",
        "justification": "AI detected anomaly. Requesting write access."
    }
    
    result = await run_pipeline(toxic_request)
    
    # Save outputs
    with open("final_report.json", "w") as f:
        json.dump({
            "request_id": result.request_id,
            "decision": result.decision,
            "risk_score": result.risk_score,
            "investigation": result.investigation,
            "execution_trace": result.execution_trace
        }, f, indent=2)
    
    with open("board_report.md", "w") as f:
        f.write(result.board_report)
    
    print("\n" + "="*60)
    print("   🛡️  EXECUTION COMPLETE")
    print("="*60)
    print(f"Decision: {result.decision}")
    print(f"Risk Score: {result.risk_score.get('net_risk_score', 'N/A')}")
    print(f"\nFiles: final_report.json, board_report.md")
    
    # DISPLAY BOARD REPORT IN NOTEBOOK
    print("\n" + "="*60)
    print("   📊 BOARD REPORT PREVIEW")
    print("="*60)
    
    try:
        from IPython.display import display, Markdown
        display(Markdown(result.board_report))
    except ImportError:
        # If not in Jupyter/Kaggle, just print
        print("\n" + result.board_report)
    
    return result


# Run in Kaggle
if __name__ == "__main__":
    asyncio.run(main())
