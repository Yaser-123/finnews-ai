from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os
import asyncio

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.dedup.agent import DeduplicationAgent
from agents.entity.agent import EntityAgent
from agents.sentiment.agent import SentimentAgent
from agents.llm.agent import LLMAgent
from agents.query.agent import QueryAgent

# Database imports
from database import db

# Router initialization
router = APIRouter()

# Global state for lazy-loaded agents and pipeline status
_agents = {
    "dedup": None,
    "entity": None,
    "sentiment": None,
    "llm": None,
    "query": None
}

_pipeline_status = {
    "status": "not run",
    "last_run": None
}


def get_agents():
    """Lazy-load agents on first use (singleton pattern)."""
    if _agents["dedup"] is None:
        try:
            _agents["dedup"] = DeduplicationAgent(threshold=0.80)
            _agents["entity"] = EntityAgent()
            _agents["sentiment"] = SentimentAgent()
            _agents["llm"] = LLMAgent()
            _agents["query"] = QueryAgent()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize agents: {str(e)}"
            )
    return _agents["dedup"], _agents["entity"], _agents["sentiment"], _agents["llm"], _agents["query"]


def load_demo_articles() -> List[Dict[str, Any]]:
    """Load demo articles from ingest module."""
    try:
        from ingest.demo_data import get_demo_articles
        return get_demo_articles()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load demo articles: {str(e)}"
        )


async def run_pipeline_graph(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrate the multi-agent pipeline with database persistence.
    
    Pipeline flow:
    1. Ingest → save articles to database
    2. Deduplication → remove duplicate articles
    3. Entity extraction → enrich with entities
    4. Sentiment analysis → analyze financial sentiment
    5. Indexing → store in vector database
    
    Args:
        articles: List of raw articles with id and text
        
    Returns:
        Dict with pipeline results and statistics
    """
    try:
        # Get agent instances
        dedup_agent, entity_agent, sentiment_agent, llm_agent, query_agent = get_agents()
        
        # Step 1: Save raw articles to database
        await db.save_articles(articles)
        
        # Step 2: Deduplication
        dedup_result = dedup_agent.run(articles)
        unique_articles = dedup_result["unique_articles"]
        clusters = dedup_result["clusters"]
        
        # Save dedup results to database
        await db.save_dedup_results(dedup_result)
        
        # Step 3: Entity extraction
        enriched_articles = entity_agent.run(unique_articles)
        
        # Save entities to database
        for article in enriched_articles:
            if "entities" in article:
                await db.save_entities(article["id"], article["entities"])
        
        # Step 4: Sentiment analysis
        sentiment_articles = sentiment_agent.run(enriched_articles)
        
        # Save sentiment to database
        for article in sentiment_articles:
            if "sentiment" in article:
                await db.save_sentiment(article["id"], article["sentiment"])
        
        # Step 5: LLM enrichment (optional - for logging/debugging)
        # Generate summaries for first 3 articles as demo
        if sentiment_articles and len(sentiment_articles) > 0:
            sample_summaries = llm_agent.run(sentiment_articles[:3], operation="summarize")
            # Store summaries in pipeline metadata (optional logging)
            _pipeline_status["last_summaries"] = sample_summaries
        
        # Step 6: Index into vector database
        query_agent.index_articles(sentiment_articles)
        
        return {
            "status": "ok",
            "total_input": len(articles),
            "unique_count": len(unique_articles),
            "clusters_count": len(clusters),
            "indexed_count": len(sentiment_articles),
            "clusters": clusters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    query: str
    matched_entities: Dict[str, List[str]]
    results: List[Dict[str, Any]]


@router.post("/run")
async def run_pipeline():
    """
    Execute the full pipeline: ingest → dedup → entity → sentiment → index.
    Persists results to PostgreSQL database.
    
    Returns:
        Pipeline execution summary with statistics
    """
    try:
        # Load demo articles
        articles = load_demo_articles()
        
        # Run the pipeline graph (now async with DB writes)
        result = await run_pipeline_graph(articles)
        
        # Update global status
        _pipeline_status["status"] = "completed"
        _pipeline_status["last_run"] = result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in pipeline: {str(e)}"
        )


@router.get("/status")
def get_pipeline_status():
    """
    Get the status of the last pipeline run.
    
    Returns:
        Status information including counts and timestamp
    """
    if _pipeline_status["status"] == "not run":
        return {
            "status": "not run",
            "message": "Pipeline has not been executed yet. Call POST /pipeline/run first."
        }
    
    return _pipeline_status["last_run"]


@router.post("/query")
async def query_articles(request: QueryRequest):
    """
    Query indexed articles using natural language.
    Logs query to database.
    
    Args:
        request: Query request with query text and optional top_k
        
    Returns:
        Query results with matched entities and ranked articles
    """
    try:
        # Ensure pipeline has been run
        if _pipeline_status["status"] == "not run":
            raise HTTPException(
                status_code=400,
                detail="Pipeline must be run first. Call POST /pipeline/run to index articles."
            )
        
        # Get agents
        _, _, _, llm_agent, query_agent = get_agents()
        
        # Optional: Expand query using LLM
        expanded = None
        try:
            expansion_result = llm_agent.expand_query({"query": request.query})
            expanded = expansion_result.get("expanded")
        except Exception as e:
            # Continue without expansion if LLM fails
            pass
        
        # Execute query
        result = query_agent.query(request.query, n_results=request.top_k)
        
        # Save query log to database
        await db.save_query_log(
            query=request.query,
            expanded_query=expanded,
            result_count=len(result.get("results", []))
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )
