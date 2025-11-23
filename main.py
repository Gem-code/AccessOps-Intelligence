from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from accessops_engine import run_pipeline
import os

app = FastAPI(title="AccessOps Intelligence API")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the UI dashboard"""
    try:
        with open("index.html", "r") as f:
            return f.read()
    except:
        return "<h1>AccessOps Intelligence API</h1><p>UI not found. API is running at /evaluate</p>"

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/evaluate")
async def evaluate(request: dict):
    try:
        result = await run_pipeline(request)
        return {
            "request_id": result.request_id,
            "decision": result.decision,
            "risk_score": result.risk_score,
            "board_report": result.board_report,
            "execution_trace": result.execution_trace
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
