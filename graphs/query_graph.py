"""
LangGraph Query Workflow for FinNews AI.

Orchestrates the query processing pipeline using LangGraph StateGraph:
1. Parse Query → Extract entities from query
2. Expand Query → Use LLM to enrich query
3. Semantic Search → Find relevant articles
4. Rerank → Refine results ordering
5. Format Response → Structure final output

Each node processes the query state and passes it to the next stage.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any
import logging
import spacy

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, END
from graphs.state import QueryState
from agents.llm.agent import LLMAgent
from agents.query.agent import QueryAgent
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model for entity extraction
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

# Singleton agent instances
_agents = {
    "llm": None,
    "query": None
}


def get_agents():
    """Lazy-load agents (singleton pattern)."""
    if _agents["llm"] is None:
        _agents["llm"] = LLMAgent()
        _agents["query"] = QueryAgent()
    return _agents


async def parse_query_node(state: QueryState) -> Dict[str, Any]:
    """
    Node 1: Parse query and extract entities.
    
    - Use spaCy NER to find companies, locations, etc.
    - Classify into financial categories
    - Update state with matched entities
    """
    logger.info(f"🔍 Node: Parse Query - Analyzing: '{state.query}'")
    
    try:
        if not nlp:
            logger.warning("spaCy not available, skipping entity extraction")
            return {"matched_entities": {}}
        
        # Extract entities using spaCy
        doc = nlp(state.query)
        
        companies = []
        sectors = []
        regulators = []
        
        for ent in doc.ents:
            entity_text = ent.text
            
            # Simple classification logic
            if ent.label_ == "ORG":
                # Check if it's a regulator
                if any(word in entity_text.lower() for word in ["rbi", "sebi", "reserve bank", "securities", "exchange"]):
                    regulators.append(entity_text)
                # Check if it's a sector reference
                elif any(word in entity_text.lower() for word in ["sector", "banking", "finance", "technology", "pharma"]):
                    sectors.append(entity_text)
                else:
                    companies.append(entity_text)
        
        matched_entities = {
            "companies": companies,
            "sectors": sectors,
            "regulators": regulators
        }
        
        state.matched_entities = matched_entities
        
        logger.info(f"✅ Parsed entities: {matched_entities}")
        return {"matched_entities": matched_entities}
    
    except Exception as e:
        logger.error(f"❌ Parse query node failed: {str(e)}")
        return {"matched_entities": {}}


async def expand_query_node(state: QueryState) -> Dict[str, Any]:
    """
    Node 2: Expand query using LLM.
    
    - Use LLMAgent to generate expanded query
    - Add financial context, synonyms, related terms
    - Update state with expanded query
    """
    logger.info("🤖 Node: Expand Query - Using LLM for enrichment")
    
    try:
        agents = get_agents()
        llm_agent = agents["llm"]
        
        # Expand query
        expansion_result = llm_agent.expand_query({"query": state.query})
        expanded_query = expansion_result.get("expanded", state.query)
        
        state.expanded_query = expanded_query
        
        logger.info(f"✅ Expanded query: '{expanded_query[:100]}...'")
        return {"expanded_query": expanded_query}
    
    except Exception as e:
        logger.error(f"❌ Expand query node failed: {str(e)}")
        # Fallback to original query
        state.expanded_query = state.query
        return {"expanded_query": state.query}


async def semantic_search_node(state: QueryState) -> Dict[str, Any]:
    """
    Node 3: Semantic search using ChromaDB.
    
    - Use persistent ChromaDB collection
    - Use expanded query if available, otherwise original
    - Fallback to original query if expanded query returns no results
    - Update state with search results
    """
    logger.info("🔍 Node: Semantic Search - Querying vector database")
    
    try:
        from vector_store import chroma_db
        from sentence_transformers import SentenceTransformer
        
        # Get collection
        collection = chroma_db.get_or_create_collection(chroma_db.COLLECTION_NAME)
        
        # Initialize embedding model
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        
        # Use expanded query if available, otherwise original
        search_query = state.expanded_query or state.query
        
        # Generate query embedding
        query_embedding = model.encode(search_query).tolist()
        
        # Execute semantic search
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10
        )
        
        # Fallback: if expanded query returns no results, try original query
        if not search_results["documents"] or len(search_results["documents"][0]) == 0:
            logger.info("⚠️ Expanded query returned no results, trying original query...")
            
            # Try with original query text
            original_embedding = model.encode(state.query).tolist()
            fallback_results = collection.query(
                query_embeddings=[original_embedding],
                n_results=10
            )
            
            if fallback_results["documents"] and len(fallback_results["documents"][0]) > 0:
                search_results = fallback_results
                logger.info(f"✅ Fallback search found {len(fallback_results['documents'][0])} results")
        
        # Process results
        results = []
        if search_results['ids'] and len(search_results['ids'][0]) > 0:
            for idx, doc_id in enumerate(search_results['ids'][0]):
                # Calculate relevance score
                distance = search_results['distances'][0][idx] if 'distances' in search_results else 0
                score = 1.0 / (1.0 + distance)
                
                # Get metadata
                metadata = search_results['metadatas'][0][idx]
                document = search_results['documents'][0][idx]
                
                # Parse entities from metadata
                entities = {
                    "companies": [c for c in metadata.get("companies", "").split(",") if c],
                    "sectors": [s for s in metadata.get("sectors", "").split(",") if s],
                    "regulators": [r for r in metadata.get("regulators", "").split(",") if r],
                    "events": [e for e in metadata.get("events", "").split(",") if e]
                }
                
                results.append({
                    "id": int(doc_id),
                    "text": document,
                    "entities": entities,
                    "score": round(score, 3)
                })
        
        state.results = results
        state.result_count = len(results)
        
        logger.info(f"✅ Found {len(results)} results")
        return {"results": results, "result_count": len(results)}
    
    except Exception as e:
        logger.error(f"❌ Semantic search node failed: {str(e)}")
        import traceback
        traceback.print_exc()
        state.results = []
        return {"results": [], "result_count": 0}


async def rerank_node(state: QueryState) -> Dict[str, Any]:
    """
    Node 4: Rerank results for relevance.
    
    - Apply simple relevance boosting based on matched entities
    - Boost articles mentioning query entities
    - Update state with reranked results
    """
    logger.info("📊 Node: Rerank - Refining result order")
    
    try:
        if not state.results:
            logger.info("No results to rerank")
            return {"reranked": []}
        
        # Simple reranking: boost articles with matched entities
        reranked = []
        for result in state.results:
            relevance_boost = 0.0
            
            # Check if article mentions any matched entities
            article_text = result.get("text", "").lower()
            
            for company in state.matched_entities.get("companies", []):
                if company.lower() in article_text:
                    relevance_boost += 0.1
            
            for sector in state.matched_entities.get("sectors", []):
                if sector.lower() in article_text:
                    relevance_boost += 0.05
            
            for regulator in state.matched_entities.get("regulators", []):
                if regulator.lower() in article_text:
                    relevance_boost += 0.15
            
            # Update score
            result["rerank_score"] = result.get("score", 0.0) + relevance_boost
            reranked.append(result)
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        
        state.reranked = reranked[:5]  # Top 5 results
        
        logger.info(f"✅ Reranked {len(state.reranked)} results")
        return {"reranked": state.reranked}
    
    except Exception as e:
        logger.error(f"❌ Rerank node failed: {str(e)}")
        state.reranked = state.results[:5]
        return {"reranked": state.reranked}


async def format_response_node(state: QueryState) -> Dict[str, Any]:
    """
    Node 5: Format final response.
    
    - Structure output for API response
    - Add timestamp and metadata
    - Save query log to database
    """
    logger.info("📝 Node: Format Response - Structuring output")
    
    try:
        state.timestamp = datetime.utcnow().isoformat()
        
        # Save query log to database
        await db.save_query_log(
            query=state.query,
            expanded_query=state.expanded_query,
            result_count=state.result_count
        )
        
        logger.info("✅ Response formatted and logged")
        return {"timestamp": state.timestamp}
    
    except Exception as e:
        logger.error(f"❌ Format response node failed: {str(e)}")
        state.timestamp = datetime.utcnow().isoformat()
        return {"timestamp": state.timestamp}


# Build the graph
def build_query_graph() -> StateGraph:
    """
    Build and compile the query graph.
    
    Graph structure:
    parse_query → expand_query → semantic_search → rerank → format_response
    """
    graph = StateGraph(QueryState)
    
    # Add nodes
    graph.add_node("parse_query", parse_query_node)
    graph.add_node("expand_query", expand_query_node)
    graph.add_node("semantic_search", semantic_search_node)
    graph.add_node("rerank", rerank_node)
    graph.add_node("format_response", format_response_node)
    
    # Set entry point
    graph.set_entry_point("parse_query")
    
    # Add edges (linear flow)
    graph.add_edge("parse_query", "expand_query")
    graph.add_edge("expand_query", "semantic_search")
    graph.add_edge("semantic_search", "rerank")
    graph.add_edge("rerank", "format_response")
    graph.add_edge("format_response", END)
    
    return graph.compile()


# Compile the workflow
workflow = build_query_graph()


# Export visualization
def export_graph_image(output_path: str = "query_graph.png"):
    """Export graph visualization to PNG."""
    try:
        png_data = workflow.get_graph().draw_mermaid_png()
        with open(output_path, 'wb') as f:
            f.write(png_data)
        logger.info(f"✅ Graph visualization saved to {output_path}")
    except Exception as e:
        logger.warning(f"⚠️ Could not export graph visualization: {str(e)}")


if __name__ == "__main__":
    # Export graph visualization
    export_graph_image()
