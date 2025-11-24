from datetime import datetime

def generate_request_id(prefix):
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

ROLE_TEMPLATES = {
    "AI Agent — Anomaly": {
        "request_id": generate_request_id("AI-ANOM"),
        "user_id": "svc_finops_auto_bot",
        "identity_type": "ai_agent",
        "job_title": "Automated Financial Ops",
        "department": "Finance Automation",
        "requested_resource_id": "prod_general_ledger_rw",
        "requested_resource_name": "Production General Ledger",
        "access_type": "write",
        "system_criticality": "tier_1",
        "data_sensitivity": "restricted",
        "justification": "AI detected anomaly requiring correction"
    },

    "Finance Manager — Escalation": {
        "request_id": generate_request_id("FM-ESC"),
        "user_id": "finance_mgr",
        "identity_type": "human_user",
        "job_title": "Finance Manager",
        "department": "Finance",
        "requested_resource_id": "prod_general_ledger_rw",
        "requested_resource_name": "Production General Ledger",
        "access_type": "write",
        "system_criticality": "tier_1",
        "data_sensitivity": "confidential",
        "justification": "Emergency reconciliation after outage"
    }
}
