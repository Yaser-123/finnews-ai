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
print(f"🔌 PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
print("=" * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager - kept minimal for fastest port binding.
    Routers are loaded on-demand when first route is called.
    """
    print("\n✅ Lifespan started - port binding in progress...")
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

# CRITICAL: Routers are loaded on-demand to prevent Render timeout
# This flag tracks whether routers have been initialized
_routers_loaded = False

def load_routers_once():
    """Load routers on first request (lazy initialization)."""
    global _routers_loaded
    if _routers_loaded:
        return
    
    print("📦 Loading routers (on-demand)...")
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
        print("✅ All routers loaded!\n")
    except Exception as e:
        print(f"⚠️ Router loading error: {e}")
        import traceback
        traceback.print_exc()

print("⚡ Routers will lazy-load on first request")
print("🎯 This allows Render to detect open port immediately\n")

# CRITICAL: Define /health BEFORE middleware to avoid router loading on health checks
@app.get("/health")
def health():
    """Health check - always available without loading routers"""
    return {
        "status": "ok",
        "service": "finnews-ai",
        "version": "0.2.0"
    }

# Middleware to lazy-load routers on first non-health request
@app.middleware("http")
async def lazy_load_middleware(request, call_next):
    # Skip router loading for health check endpoint
    if request.url.path != "/health":
        load_routers_once()
    response = await call_next(request)
    return response

@app.get("/")
def root():
    """Serve the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(dashboard_path)

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
