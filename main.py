from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from api.routes.pipeline import router as pipeline_router
from api.routes.stats import router as stats_router
from api.routes.llm import router as llm_router
from api.routes.analysis import router as analysis_router
from api.scheduler import router as scheduler_router, init_scheduler, shutdown_scheduler
from api.websocket.alerts import alert_manager
from database import db
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI app.
    Handles database initialization on startup and cleanup on shutdown.
    """
    print("🚀 Starting FinNews AI...")
    
    # Startup: Initialize database (non-blocking)
    try:
        print("📊 Initializing database...")
        db.init_db()
        print("✅ Database engine initialized")
        
        # Skip table creation and migrations on first startup to speed up
        # They will run on first API call instead
        print("⏭️  Skipping migrations on startup (will run on first request)")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {str(e)}")
        print("   App will continue without database persistence")
    
    # Skip scheduler on startup - user can enable via API if needed
    print("⏭️  Skipping scheduler on startup (enable via /scheduler/start API)")
    
    print("✅ FinNews AI started successfully!")
    
    yield
    
    # Shutdown: Stop scheduler
    try:
        shutdown_scheduler()
    except Exception as e:
        print(f"⚠️ Error shutting down scheduler: {str(e)}")
    
    # Shutdown: Close database connections
    try:
        await db.close_db()
    except Exception as e:
        print(f"⚠️ Error closing database: {str(e)}")

app = FastAPI(
    title="FinNews AI",
    description="Multi-agent financial news processing pipeline with semantic search and real-time ingestion",
    version="0.2.0",
    lifespan=lifespan
)

# Include routers
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(scheduler_router, prefix="/scheduler", tags=["Scheduler"])
app.include_router(stats_router, tags=["Dashboard"])  # No prefix, already has /stats
app.include_router(llm_router, prefix="/llm", tags=["LLM"])
app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])

@app.get("/")
def root():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(dashboard_path)

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
    await alert_manager.connect(websocket)
    try:
        # Keep connection alive and listen for client messages
        while True:
            await websocket.receive_text()
    except Exception:
        alert_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
