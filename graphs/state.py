"""
State models for LangGraph workflows in FinNews AI.

Defines the state structure for:
- Pipeline workflow (ingestion → dedup → entities → sentiment → LLM → indexing)
- Query workflow (parse → expand → search → rerank → format)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PipelineState(BaseModel):
    """
    State model for the main processing pipeline.
    
    Tracks articles through each stage:
    1. Ingestion
    2. Deduplication
    3. Entity extraction
    4. Sentiment analysis
    5. LLM enrichment
    6. Vector indexing
    """
    # Raw input articles
    articles: List[Dict[str, Any]] = Field(default_factory=list, description="Raw input articles")
    
    # After deduplication
    unique_articles: List[Dict[str, Any]] = Field(default_factory=list, description="Unique articles after deduplication")
    clusters: List[Dict[str, Any]] = Field(default_factory=list, description="Deduplication cluster information")
    
    # Enrichment data (keyed by article ID)
    entities: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Extracted entities per article")
    sentiment: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Sentiment analysis per article")
    
    # LLM outputs
    llm_outputs: Dict[str, Any] = Field(default_factory=dict, description="LLM-generated summaries and insights")
    
    # Status flags
    index_done: bool = Field(default=False, description="Whether articles have been indexed")
    timestamp: Optional[str] = Field(default=None, description="Pipeline execution timestamp")
    
    # Statistics
    stats: Dict[str, Any] = Field(default_factory=dict, description="Pipeline statistics")
    
    class Config:
        arbitrary_types_allowed = True


class QueryState(BaseModel):
    """
    State model for the query processing workflow.
    
    Tracks query through stages:
    1. Query parsing
    2. LLM expansion
    3. Semantic search
    4. Result reranking
    5. Response formatting
    """
    # Input query
    query: str = Field(..., description="Original user query")
    
    # Query expansion
    expanded_query: Optional[str] = Field(default=None, description="LLM-expanded query")
    
    # Entity matching
    matched_entities: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Entities extracted from query (companies, sectors, regulators)"
    )
    
    # Search results
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Raw search results")
    
    # Reranked results
    reranked: List[Dict[str, Any]] = Field(default_factory=list, description="Reranked search results")
    
    # Metadata
    result_count: int = Field(default=0, description="Number of results returned")
    timestamp: Optional[str] = Field(default=None, description="Query execution timestamp")
    
    class Config:
        arbitrary_types_allowed = True
