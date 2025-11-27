from fastapi import FastAPI
import uvicorn
from api.routes.pipeline import router as pipeline_router

app = FastAPI(
    title="FinNews AI",
    description="Multi-agent financial news processing pipeline with semantic search",
    version="0.1.0"
)

# Include pipeline router
app.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "finnews-ai",
        "version": "0.1"
    }

@app.post("/run_graph")
def run_graph():
    return {"message": "Graph execution placeholder - use /pipeline/run for full pipeline"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
