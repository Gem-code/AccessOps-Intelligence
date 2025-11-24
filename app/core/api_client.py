import requests
from core.configs import API_URL

def evaluate_access_request(payload):
    """
    Send access request payload to AccessOps Engine.
    Returns parsed JSON or error structure.
    """
    try:
        resp = requests.post(API_URL, json=payload, timeout=25)
        return resp.json()
    except Exception as e:
        return {
            "decision": "ERROR",
            "risk_score": {"severity_level": "UNKNOWN", "net_risk_score": 0},
            "board_report": f"API unreachable: {str(e)}"
        }
