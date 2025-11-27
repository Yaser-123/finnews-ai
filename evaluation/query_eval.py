"""
Query Retrieval Evaluation Module

Evaluates semantic search and query expansion quality using
benchmark queries with known expected results.
"""

import json
import os
import asyncio
from typing import Dict, List, Any, Set
import logging

logger = logging.getLogger(__name__)

# Benchmark queries with expected relevant article IDs
BENCHMARK_QUERIES = [
    {
        "query": "RBI monetary policy changes",
        "expected_articles": [1, 3, 7, 13],  # Articles about RBI/repo rate
        "description": "Regulatory policy query"
    },
    {
        "query": "Reliance earnings and profit",
        "expected_articles": [2, 6, 8, 14],  # Reliance financial news
        "description": "Company earnings query"
    },
    {
        "query": "Tesla India market expansion",
        "expected_articles": [5, 10, 15],  # Tesla India news
        "description": "Market expansion query"
    },
    {
        "query": "Banking sector performance",
        "expected_articles": [1, 4, 9, 16],  # Banking sector articles
        "description": "Sector-level query"
    }
]


def calculate_hit_rate(retrieved: List[int], expected: List[int]) -> float:
    """
    Calculate hit rate: Was at least one expected article retrieved?
    
    Args:
        retrieved: List of retrieved article IDs
        expected: List of expected article IDs
    
    Returns:
        1.0 if hit, 0.0 if miss
    """
    retrieved_set = set(retrieved)
    expected_set = set(expected)
    
    return 1.0 if bool(retrieved_set & expected_set) else 0.0


def calculate_recall_at_k(retrieved: List[int], expected: List[int], k: int = 5) -> float:
    """
    Calculate Recall@K: What fraction of expected articles are in top K results?
    
    Args:
        retrieved: List of retrieved article IDs (ranked)
        expected: List of expected article IDs
        k: Number of top results to consider
    
    Returns:
        Recall@K score (0-1)
    """
    top_k = set(retrieved[:k])
    expected_set = set(expected)
    
    if not expected_set:
        return 0.0
    
    hits = top_k & expected_set
    return len(hits) / len(expected_set)


def calculate_mrr(retrieved: List[int], expected: List[int]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).
    
    MRR is 1/rank of the first relevant result.
    Example: If first relevant result is at position 2, MRR = 1/2 = 0.5
    
    Args:
        retrieved: List of retrieved article IDs (ranked)
        expected: List of expected article IDs
    
    Returns:
        MRR score (0-1)
    """
    expected_set = set(expected)
    
    for rank, article_id in enumerate(retrieved, start=1):
        if article_id in expected_set:
            return 1.0 / rank
    
    return 0.0  # No relevant results found


async def run_query_via_agent(query: str) -> List[int]:
    """
    Run a query using the existing query agent.
    
    Args:
        query: Query string
    
    Returns:
        List of retrieved article IDs
    """
    try:
        # Import here to avoid circular dependencies
        from graphs.query_graph import workflow as query_workflow
        from graphs.states import QueryState
        
        # Initialize state
        initial_state = QueryState(
            query=query,
            expanded_query="",
            retrieved_articles=[],
            summaries=[],
            final_response=""
        )
        
        # Run query workflow
        result = await query_workflow.ainvoke(initial_state)
        
        # Extract article IDs from retrieved articles
        article_ids = [
            article.get("id") 
            for article in result.get("retrieved_articles", [])
            if article.get("id") is not None
        ]
        
        return article_ids
    
    except Exception as e:
        logger.error(f"Failed to run query '{query}': {str(e)}")
        return []


async def evaluate_single_query(
    query: str,
    expected: List[int],
    description: str
) -> Dict[str, Any]:
    """
    Evaluate a single query.
    
    Args:
        query: Query string
        expected: Expected article IDs
        description: Query description
    
    Returns:
        Dict with metrics for this query
    """
    logger.info(f"Evaluating query: {query}")
    
    # Run query
    retrieved = await run_query_via_agent(query)
    
    # Calculate metrics
    hit_rate = calculate_hit_rate(retrieved, expected)
    recall_at_5 = calculate_recall_at_k(retrieved, expected, k=5)
    mrr = calculate_mrr(retrieved, expected)
    
    return {
        "query": query,
        "description": description,
        "expected_count": len(expected),
        "retrieved_count": len(retrieved),
        "hit_rate": round(hit_rate, 4),
        "recall_at_5": round(recall_at_5, 4),
        "mrr": round(mrr, 4),
        "retrieved_ids": retrieved[:10]  # Top 10 for inspection
    }


async def evaluate_queries() -> Dict[str, Any]:
    """
    Evaluate all benchmark queries.
    
    Returns:
        Dict with aggregated metrics and per-query results
    """
    logger.info("Starting query evaluation...")
    
    query_results = []
    
    # Evaluate each benchmark query
    for benchmark in BENCHMARK_QUERIES:
        result = await evaluate_single_query(
            query=benchmark["query"],
            expected=benchmark["expected_articles"],
            description=benchmark["description"]
        )
        query_results.append(result)
    
    # Aggregate metrics
    avg_hit_rate = sum(r["hit_rate"] for r in query_results) / len(query_results)
    avg_recall_at_5 = sum(r["recall_at_5"] for r in query_results) / len(query_results)
    avg_mrr = sum(r["mrr"] for r in query_results) / len(query_results)
    
    logger.info(f"Query Evaluation: Hit Rate={avg_hit_rate:.3f}, Recall@5={avg_recall_at_5:.3f}, MRR={avg_mrr:.3f}")
    
    return {
        "average_hit_rate": round(avg_hit_rate, 4),
        "average_recall_at_5": round(avg_recall_at_5, 4),
        "average_mrr": round(avg_mrr, 4),
        "total_queries": len(query_results),
        "by_query": query_results
    }


def evaluate_queries_sync() -> Dict[str, Any]:
    """Synchronous wrapper for evaluate_queries()."""
    return asyncio.run(evaluate_queries())


if __name__ == "__main__":
    # Test query evaluation
    logging.basicConfig(level=logging.INFO)
    
    results = asyncio.run(evaluate_queries())
    print(json.dumps(results, indent=2))
