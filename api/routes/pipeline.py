from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.dedup.agent import DeduplicationAgent
from agents.entity.agent import EntityAgent
from agents.sentiment.agent import SentimentAgent
from agents.llm.agent import LLMAgent
from agents.query.agent import QueryAgent

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


def run_pipeline_graph(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Orchestrate the multi-agent pipeline.
    
    Pipeline flow:
    1. Deduplication → remove duplicate articles
    2. Entity extraction → enrich with entities
    3. Sentiment analysis → analyze financial sentiment
    4. Indexing → store in vector database
    
    Args:
        articles: List of raw articles with id and text
        
    Returns:
        Dict with pipeline results and statistics
    """
    try:
        # Get agent instances
        dedup_agent, entity_agent, sentiment_agent, llm_agent, query_agent = get_agents()
        
        # Step 1: Deduplication
        dedup_result = dedup_agent.run(articles)
        unique_articles = dedup_result["unique_articles"]
        clusters = dedup_result["clusters"]
        
        # Step 2: Entity extraction
        enriched_articles = entity_agent.run(unique_articles)
        
        # Step 3: Sentiment analysis
        sentiment_articles = sentiment_agent.run(enriched_articles)
        
        # Step 4: LLM enrichment (optional - for logging/debugging)
        # Generate summaries for first 3 articles as demo
        if sentiment_articles and len(sentiment_articles) > 0:
            sample_summaries = llm_agent.run(sentiment_articles[:3], operation="summarize")
            # Store summaries in pipeline metadata (optional logging)
            _pipeline_status["last_summaries"] = sample_summaries
        
        # Step 5: Index into vector database
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
def run_pipeline():
    """
    Execute the full pipeline: ingest → dedup → entity → index.
    
    Returns:
        Pipeline execution summary with statistics
    """
    try:
        # Load demo articles
        articles = load_demo_articles()
        
        # Run the pipeline graph
        result = run_pipeline_graph(articles)
        
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
def query_articles(request: QueryRequest):
    """
    Query indexed articles using natural language.
    
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
        
        # Get query agent
        _, _, _, _, query_agent = get_agents()
        
        # Execute query
        result = query_agent.query(request.query, n_results=request.top_k)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )
