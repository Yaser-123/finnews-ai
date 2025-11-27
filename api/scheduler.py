"""
Real-time ingestion scheduler for FinNews AI.

Provides background job scheduling for periodic RSS feed ingestion,
processing through the pipeline, and incremental indexing.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

# Import ingestion and database modules
from ingest.realtime import fetch_all, get_configured_feeds
from database import db
from vector_store.chroma_db import get_or_create_collection

load_dotenv()

logger = logging.getLogger(__name__)

# Router initialization
router = APIRouter()

# Global scheduler instance
scheduler = AsyncIOScheduler()

# Job statistics
job_stats = {
    "last_run": None,
    "last_run_time": None,
    "last_fetched": 0,
    "last_new": 0,
    "last_indexed": 0,
    "last_alerts": 0,
    "total_runs": 0,
    "last_error": None
}


async def run_pipeline_on_articles(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the pipeline on a list of articles (incremental processing).
    
    This is a simplified version that:
    1. Indexes articles into ChromaDB
    2. Extracts sentiment and sends alerts if conditions match
    
    For full pipeline processing, import and call agents directly.
    
    Args:
        articles: List of article dicts
    
    Returns:
        Dict with processing statistics
    """
    if not articles:
        return {"indexed": 0, "alerts_sent": 0}
    
    try:
        # Import agents lazily to avoid circular imports
        from agents.sentiment.agent import SentimentAgent
        from api.websocket.alerts import alert_manager
        
        # Analyze sentiment
        sentiment_agent = SentimentAgent()
        sentiment_articles = sentiment_agent.run(articles)
        
        # Index into ChromaDB
        collection = get_or_create_collection()
        
        documents = []
        metadatas = []
        ids = []
        
        for article in sentiment_articles:
            documents.append(article.get("text", ""))
            metadatas.append({
                "source": article.get("source", "unknown"),
                "published_at": article.get("published_at", ""),
                "sentiment": article.get("sentiment", {}).get("label", "neutral")
            })
            ids.append(str(article.get("id")))
        
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Indexed {len(documents)} articles into ChromaDB")
        
        # Send alerts for high-confidence sentiment
        alerts_sent = 0
        for article in sentiment_articles:
            sentiment = article.get("sentiment", {})
            label = sentiment.get("label", "neutral")
            score = sentiment.get("score", 0.0)
            
            # High-confidence positive
            if label == "positive" and score > 0.90:
                await alert_manager.send_alert(
                    level="BULLISH",
                    article_id=article.get("id"),
                    headline=article.get("title", article.get("text", "")[:100]),
                    sentiment=sentiment,
                    entities={},
                    summary=f"High-confidence positive sentiment detected (score: {score:.3f})"
                )
                alerts_sent += 1
            
            # High-confidence negative
            elif label == "negative" and score > 0.90:
                await alert_manager.send_alert(
                    level="HIGH_RISK",
                    article_id=article.get("id"),
                    headline=article.get("title", article.get("text", "")[:100]),
                    sentiment=sentiment,
                    entities={},
                    summary=f"High-confidence negative sentiment detected (score: {score:.3f})"
                )
                alerts_sent += 1
        
        return {
            "indexed": len(documents),
            "alerts_sent": alerts_sent
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to run pipeline on articles: {str(e)}")
        return {"indexed": 0, "alerts_sent": 0, "error": str(e)}


async def realtime_ingest_job():
    """
    Background job that fetches RSS feeds, saves new articles,
    runs pipeline, and indexes incrementally.
    
    This job runs periodically based on scheduler configuration.
    """
    start_time = datetime.now()
    
    try:
        logger.info("=" * 60)
        logger.info("Starting real-time ingestion job...")
        logger.info("=" * 60)
        
        # Step 1: Fetch feeds
        feeds = get_configured_feeds()
        articles = await fetch_all(feeds)
        fetched_count = len(articles)
        
        logger.info(f"📥 Fetched {fetched_count} articles from {len(feeds)} feeds")
        
        if not articles:
            logger.info("No articles fetched. Skipping processing.")
            job_stats.update({
                "last_run": start_time.isoformat(),
                "last_run_time": (datetime.now() - start_time).total_seconds(),
                "last_fetched": 0,
                "last_new": 0,
                "last_indexed": 0,
                "last_alerts": 0,
                "total_runs": job_stats["total_runs"] + 1,
                "last_error": None
            })
            return
        
        # Step 2: Save new articles to database
        new_ids = await db.save_new_articles(articles)
        new_count = len(new_ids)
        
        logger.info(f"💾 Saved {new_count} new articles to database")
        
        if new_count == 0:
            logger.info("No new articles. Skipping pipeline processing.")
            job_stats.update({
                "last_run": start_time.isoformat(),
                "last_run_time": (datetime.now() - start_time).total_seconds(),
                "last_fetched": fetched_count,
                "last_new": 0,
                "last_indexed": 0,
                "last_alerts": 0,
                "total_runs": job_stats["total_runs"] + 1,
                "last_error": None
            })
            return
        
        # Step 3: Filter to new articles only
        new_articles = [a for a in articles if a.get("id") in new_ids]
        
        # Step 4: Run pipeline on new articles
        pipeline_result = await run_pipeline_on_articles(new_articles)
        indexed_count = pipeline_result.get("indexed", 0)
        alerts_sent = pipeline_result.get("alerts_sent", 0)
        
        logger.info(f"🔍 Indexed {indexed_count} articles")
        logger.info(f"🚨 Sent {alerts_sent} alerts")
        
        # Update statistics
        end_time = datetime.now()
        job_stats.update({
            "last_run": start_time.isoformat(),
            "last_run_time": (end_time - start_time).total_seconds(),
            "last_fetched": fetched_count,
            "last_new": new_count,
            "last_indexed": indexed_count,
            "last_alerts": alerts_sent,
            "total_runs": job_stats["total_runs"] + 1,
            "last_error": None
        })
        
        logger.info("=" * 60)
        logger.info(f"✅ Ingestion job complete in {job_stats['last_run_time']:.2f}s")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ Ingestion job failed: {str(e)}")
        job_stats.update({
            "last_run": start_time.isoformat(),
            "last_run_time": (datetime.now() - start_time).total_seconds(),
            "last_error": str(e),
            "total_runs": job_stats["total_runs"] + 1
        })


# Request/Response models
class SchedulerStartRequest(BaseModel):
    interval_seconds: Optional[int] = None  # Default from env or 60


class SchedulerResponse(BaseModel):
    status: str
    message: str
    interval_seconds: Optional[int] = None
    next_run: Optional[str] = None


@router.post("/start", response_model=SchedulerResponse)
async def start_scheduler(request: Optional[SchedulerStartRequest] = None):
    """
    Start the real-time ingestion scheduler.
    
    Args:
        request: Optional request with interval_seconds
    
    Returns:
        Scheduler status
    """
    try:
        # Get interval from request, env, or default
        if request and request.interval_seconds:
            interval = request.interval_seconds
        else:
            interval = int(os.getenv("INGEST_INTERVAL", "60"))
        
        # Check if job already exists
        existing_job = scheduler.get_job("realtime_ingest_job")
        
        if existing_job:
            return SchedulerResponse(
                status="already_running",
                message="Scheduler is already running",
                interval_seconds=interval
            )
        
        # Add job with interval trigger
        scheduler.add_job(
            realtime_ingest_job,
            trigger=IntervalTrigger(seconds=interval),
            id="realtime_ingest_job",
            name="Real-time News Ingestion",
            replace_existing=True
        )
        
        # Start scheduler if not running
        if not scheduler.running:
            scheduler.start()
        
        logger.info(f"✅ Scheduler started with {interval}s interval")
        
        # Get next run time
        job = scheduler.get_job("realtime_ingest_job")
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
        
        return SchedulerResponse(
            status="started",
            message=f"Scheduler started successfully with {interval}s interval",
            interval_seconds=interval,
            next_run=next_run
        )
    
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start scheduler: {str(e)}"
        )


@router.post("/stop", response_model=SchedulerResponse)
async def stop_scheduler():
    """
    Stop the real-time ingestion scheduler.
    
    Returns:
        Scheduler status
    """
    try:
        existing_job = scheduler.get_job("realtime_ingest_job")
        
        if not existing_job:
            return SchedulerResponse(
                status="not_running",
                message="Scheduler is not running"
            )
        
        # Remove job
        scheduler.remove_job("realtime_ingest_job")
        
        logger.info("✅ Scheduler stopped")
        
        return SchedulerResponse(
            status="stopped",
            message="Scheduler stopped successfully"
        )
    
    except Exception as e:
        logger.error(f"❌ Failed to stop scheduler: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop scheduler: {str(e)}"
        )


@router.get("/status")
async def get_scheduler_status():
    """
    Get current scheduler status and statistics.
    
    Returns:
        Scheduler status with job statistics
    """
    try:
        job = scheduler.get_job("realtime_ingest_job")
        
        if job:
            next_run = job.next_run_time.isoformat() if job.next_run_time else None
            
            return {
                "running": True,
                "next_run": next_run,
                "stats": job_stats
            }
        else:
            return {
                "running": False,
                "next_run": None,
                "stats": job_stats
            }
    
    except Exception as e:
        logger.error(f"❌ Failed to get scheduler status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.get("/last_run")
async def get_last_run_stats():
    """
    Get statistics from the last ingestion run.
    
    Returns:
        Last run statistics
    """
    return job_stats


def init_scheduler():
    """Initialize the scheduler (called on app startup)."""
    # Auto-start if configured
    auto_start = os.getenv("AUTO_START_SCHEDULER", "false").lower() == "true"
    
    if auto_start:
        interval = int(os.getenv("INGEST_INTERVAL", "60"))
        
        scheduler.add_job(
            realtime_ingest_job,
            trigger=IntervalTrigger(seconds=interval),
            id="realtime_ingest_job",
            name="Real-time News Ingestion",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"✅ Scheduler auto-started with {interval}s interval")


def shutdown_scheduler():
    """Shutdown the scheduler (called on app shutdown)."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Scheduler shutdown complete")
