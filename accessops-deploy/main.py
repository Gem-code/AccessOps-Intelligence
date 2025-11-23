from fastapi import FastAPI, HTTPException
from accessops_engine import run_pipeline

app = FastAPI(title="AccessOps Intelligence API")

@app.get("/")
def home():
    return {"message": "AccessOps Intelligence is running", "status": "healthy"}

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
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
