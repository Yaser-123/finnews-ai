from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import sys

# Configure matplotlib to avoid font cache building at startup
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
os.environ['MPLBACKEND'] = 'Agg'

# Print startup diagnostic
print("=" * 60)
print("🚀 FinNews AI - Initializing FastAPI (port binding first)...")
print("=" * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager - MUST be empty for instant port binding.
    Routers will be loaded on first request.
    """
    print("\n✅ Lifespan started - port will bind now!")
    yield
    
    # Shutdown cleanup
    print("\n🛑 Shutting down FinNews AI...")
    try:
        from api.scheduler import shutdown_scheduler
        shutdown_scheduler()
        print("✅ Scheduler stopped")
    except Exception as e:
        print(f"⚠️ Scheduler shutdown error: {e}")
    
    try:
        from database import db
        await db.close_db()
        print("✅ Database closed")
    except Exception as e:
        print(f"⚠️ Database shutdown error: {e}")

# Create app IMMEDIATELY - this allows port binding
print("🌐 Creating FastAPI app (instant)...")
app = FastAPI(
    title="FinNews AI",
    description="Multi-agent financial news processing pipeline with semantic search and real-time ingestion",
    version="0.2.0",
    lifespan=lifespan
)
print("✅ FastAPI app created!\n")

# Load all routers immediately for localhost development
print("📦 Loading routers...")
try:
    from api.routes.pipeline import router as pipeline_router
    from api.scheduler import router as scheduler_router
    from api.routes.stats import router as stats_router
    from api.routes.llm import router as llm_router
    from api.routes.analysis import router as analysis_router
    
    app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
    app.include_router(scheduler_router, prefix="/scheduler", tags=["Scheduler"])
    app.include_router(stats_router, tags=["Dashboard"])
    app.include_router(llm_router, prefix="/llm", tags=["LLM"])
    app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
    print("✅ All routers loaded!\n")
except Exception as e:
    print(f"⚠️ Router loading error: {e}")
    import traceback
    traceback.print_exc()

@app.get("/")
def root():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(dashboard_path)

@app.get("/health")
def health():
    """Health check - always available"""
    return {
        "status": "ok",
        "service": "finnews-ai",
        "version": "0.2.0"
    }

@app.post("/run_graph")
def run_graph():
    return {"message": "Graph execution placeholder - use /pipeline/run for full pipeline"}

@app.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trading alerts.
    
    Broadcasts alerts for:
    - HIGH_RISK: Negative sentiment > 0.90
    - BULLISH: Positive sentiment > 0.90
    - REGULATORY_UPDATE: RBI/policy/inflation mentions
    - EARNINGS_UPDATE: Profit/growth mentions
    """
    # Lazy-load alert manager only when WebSocket connects
    from api.websocket.alerts import alert_manager
    
    await alert_manager.connect(websocket)
    try:
        # Keep connection alive and listen for client messages
        while True:
            await websocket.receive_text()
    except Exception:
        alert_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
