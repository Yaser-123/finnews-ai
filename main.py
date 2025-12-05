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
print("✅ FastAPI app created - Uvicorn will bind port now!\n")

# Track if routers are loaded
_routers_loaded = False
_loading_started = False

def load_routers_sync():
    """Load routers synchronously in background thread"""
    global _routers_loaded
    if _routers_loaded:
        return
    
    print("📦 Background thread - loading routers now...")
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
        _routers_loaded = True
        print("✅ All routers loaded!")
    except Exception as e:
        print(f"⚠️ Router loading error: {e}")
        import traceback
        traceback.print_exc()

def trigger_router_loading():
    """Trigger router loading in background thread (non-blocking)"""
    global _loading_started
    if _loading_started:
        return
    _loading_started = True
    
    import threading
    thread = threading.Thread(target=load_routers_sync, daemon=True)
    thread.start()
    print("🔄 Started background router loading...")

@app.get("/")
def root():
    """Serve the dashboard HTML"""
    # Trigger router loading in background (non-blocking)
    trigger_router_loading()
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(dashboard_path)

@app.get("/health")
def health():
    """Health check - always available, triggers router loading"""
    # Trigger router loading in background on first health check
    trigger_router_loading()
    return {
        "status": "ok",
        "service": "finnews-ai",
        "version": "0.1",
        "routers_loaded": _routers_loaded
    }

@app.get("/api/loading-status")
def loading_status():
    """Check if routers are loaded"""
    return {
        "routers_loaded": _routers_loaded,
        "message": "Routers loading in background..." if not _routers_loaded else "All routers loaded!"
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
