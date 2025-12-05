"""
LangGraph Pipeline Workflow for FinNews AI.

Orchestrates the multi-agent pipeline using LangGraph StateGraph:
1. Ingest → Load demo articles
2. Dedup → Remove duplicate articles  
3. Entity → Extract financial entities
4. Sentiment → Analyze sentiment
5. LLM → Generate summaries
6. Index → Store in vector database

Each node is async and persists data to PostgreSQL.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langgraph.graph import StateGraph, END
from graphs.state import PipelineState
from agents.dedup.agent import DeduplicationAgent
from agents.entity.agent import EntityAgent
from agents.sentiment.agent import SentimentAgent
from agents.llm.agent import LLMAgent
from agents.query.agent import QueryAgent
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton agent instances
_agents = {
    "dedup": None,
    "entity": None,
    "sentiment": None,
    "llm": None,
    "query": None
}


def get_agents():
    """Lazy-load agents (singleton pattern)."""
    if _agents["dedup"] is None:
        _agents["dedup"] = DeduplicationAgent(threshold=0.80)
        _agents["entity"] = EntityAgent()
        _agents["sentiment"] = SentimentAgent()
        _agents["llm"] = LLMAgent()
        _agents["query"] = QueryAgent()
    return _agents


async def ingest_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 1: Ingest raw articles.
    
    - Load demo articles from ingest/demo_data.py
    - Save to PostgreSQL database
    - Update state with articles
    """
    logger.info("📥 Node: Ingest - Loading demo articles")
    
    try:
        from ingest.demo_data import get_demo_articles
        articles = get_demo_articles()
        
        # Save to database
        await db.save_articles(articles)
        
        state.articles = articles
        state.timestamp = datetime.utcnow().isoformat()
        state.stats["total_input"] = len(articles)
        
        logger.info(f"✅ Ingested {len(articles)} articles")
        return {"articles": articles, "stats": state.stats, "timestamp": state.timestamp}
    
    except Exception as e:
        logger.error(f"❌ Ingest node failed: {str(e)}")
        raise


async def dedup_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 2: Deduplication.
    
    - Run DeduplicationAgent on articles
    - Save clusters to database
    - Update state with unique articles and clusters
    """
    logger.info("🔄 Node: Dedup - Removing duplicate articles")
    
    try:
        agents = get_agents()
        dedup_agent = agents["dedup"]
        
        # Run deduplication
        dedup_result = dedup_agent.run(state.articles)
        unique_articles = dedup_result["unique_articles"]
        clusters = dedup_result["clusters"]
        
        # Save to database
        await db.save_dedup_results(dedup_result)
        
        state.unique_articles = unique_articles
        state.clusters = clusters
        state.stats["unique_count"] = len(unique_articles)
        state.stats["clusters_count"] = len(clusters)
        
        logger.info(f"✅ Deduplication: {len(unique_articles)} unique from {len(state.articles)} total")
        return {
            "unique_articles": unique_articles,
            "clusters": clusters,
            "stats": state.stats
        }
    
    except Exception as e:
        logger.error(f"❌ Dedup node failed: {str(e)}")
        raise


async def entity_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 3: Entity extraction.
    
    - Run EntityAgent on each unique article
    - Save entities to database
    - Update state with entity data
    """
    logger.info("🏢 Node: Entity - Extracting financial entities")
    
    try:
        agents = get_agents()
        entity_agent = agents["entity"]
        
        # Run entity extraction
        enriched_articles = entity_agent.run(state.unique_articles)
        
        # Save entities to database and build entity dict
        entities = {}
        for article in enriched_articles:
            article_id = article["id"]
            if "entities" in article:
                entities[article_id] = article["entities"]
                await db.save_entities(article_id, article["entities"])
        
        state.entities = entities
        state.unique_articles = enriched_articles
        state.stats["entities_extracted"] = len(entities)
        
        logger.info(f"✅ Extracted entities for {len(entities)} articles")
        return {"entities": entities, "unique_articles": enriched_articles, "stats": state.stats}
    
    except Exception as e:
        logger.error(f"❌ Entity node failed: {str(e)}")
        raise


async def sentiment_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 4: Sentiment analysis.
    
    - Run SentimentAgent on each article
    - Save sentiment to database
    - Update state with sentiment data
    """
    logger.info("📊 Node: Sentiment - Analyzing financial sentiment")
    
    try:
        agents = get_agents()
        sentiment_agent = agents["sentiment"]
        
        # Run sentiment analysis
        sentiment_articles = sentiment_agent.run(state.unique_articles)
        
        # Save sentiment to database and build sentiment dict
        from api.websocket.alerts import alert_manager
        
        sentiment_data = {}
        for article in sentiment_articles:
            article_id = article["id"]
            if "sentiment" in article:
                sentiment_data[article_id] = article["sentiment"]
                await db.save_sentiment(article_id, article["sentiment"])
                
                # Broadcast real-time alerts for high-confidence sentiment
                sentiment = article["sentiment"]
                label = sentiment.get("label", "").upper()
                score = sentiment.get("score", 0.0)
                
                # HIGH_RISK alert: Negative sentiment > 0.90
                if label == "NEGATIVE" and score > 0.90:
                    await alert_manager.send_alert(
                        level="HIGH_RISK",
                        article_id=article_id,
                        text=article.get("text", ""),
                        sentiment=label,
                        entities=article.get("entities", {})
                    )
                    logger.info(f"🚨 HIGH_RISK alert: Article {article_id} (score: {score:.3f})")
                
                # BULLISH alert: Positive sentiment > 0.90
                elif label == "POSITIVE" and score > 0.90:
                    await alert_manager.send_alert(
                        level="BULLISH",
                        article_id=article_id,
                        text=article.get("text", ""),
                        sentiment=label,
                        entities=article.get("entities", {})
                    )
                    logger.info(f"📈 BULLISH alert: Article {article_id} (score: {score:.3f})")
        
        state.sentiment = sentiment_data
        state.unique_articles = sentiment_articles
        state.stats["sentiment_analyzed"] = len(sentiment_data)
        
        # Calculate sentiment distribution
        positive = sum(1 for s in sentiment_data.values() if s.get("label") == "positive")
        negative = sum(1 for s in sentiment_data.values() if s.get("label") == "negative")
        neutral = sum(1 for s in sentiment_data.values() if s.get("label") == "neutral")
        
        state.stats["sentiment_distribution"] = {
            "positive": positive,
            "negative": negative,
            "neutral": neutral
        }
        
        logger.info(f"✅ Sentiment: {positive} positive, {negative} negative, {neutral} neutral")
        return {"sentiment": sentiment_data, "unique_articles": sentiment_articles, "stats": state.stats}
    
    except Exception as e:
        logger.error(f"❌ Sentiment node failed: {str(e)}")
        raise


async def llm_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 5: LLM enrichment.
    
    - Generate summaries using LLMAgent
    - Store summaries in state
    """
    logger.info("🤖 Node: LLM - Generating summaries")
    
    try:
        from api.websocket.alerts import alert_manager
        
        agents = get_agents()
        llm_agent = agents["llm"]
        
        # Generate summaries for all articles
        summaries = []
        for article in state.unique_articles[:5]:  # Limit to first 5 for demo
            try:
                summary = llm_agent.summarize_article(article)
                summaries.append(summary)
                
                # Broadcast alerts based on LLM summary keywords
                summary_text = summary.get("summary", "").lower()
                article_id = article["id"]
                article_text = article.get("text", "")
                
                # REGULATORY_UPDATE: RBI, inflation, repo rate mentions
                if any(keyword in summary_text for keyword in ["repo", "inflation", "rbi", "reserve bank", "monetary policy"]):
                    await alert_manager.send_alert(
                        level="REGULATORY_UPDATE",
                        article_id=article_id,
                        text=article_text,
                        summary=summary.get("summary"),
                        entities=article.get("entities", {})
                    )
                    logger.info(f"🏛️ REGULATORY_UPDATE alert: Article {article_id}")
                
                # EARNINGS_UPDATE: Profit, growth, earnings mentions
                if any(keyword in summary_text for keyword in ["profit", "growth", "earnings", "revenue", "dividend"]):
                    await alert_manager.send_alert(
                        level="EARNINGS_UPDATE",
                        article_id=article_id,
                        text=article_text,
                        summary=summary.get("summary"),
                        entities=article.get("entities", {})
                    )
                    logger.info(f"💰 EARNINGS_UPDATE alert: Article {article_id}")
                
            except Exception as e:
                logger.warning(f"Failed to summarize article {article['id']}: {str(e)}")
        
        state.llm_outputs = {
            "summaries": summaries,
            "summary_count": len(summaries)
        }
        state.stats["llm_summaries"] = len(summaries)
        
        logger.info(f"✅ Generated {len(summaries)} LLM summaries")
        return {"llm_outputs": state.llm_outputs, "stats": state.stats}
    
    except Exception as e:
        logger.error(f"❌ LLM node failed: {str(e)}")
        # Don't fail the pipeline if LLM fails
        state.llm_outputs = {"error": str(e)}
        return {"llm_outputs": state.llm_outputs}


async def index_node(state: PipelineState) -> Dict[str, Any]:
    """
    Node 6: Vector indexing.
    
    - Index articles into ChromaDB with LLM summaries
    - Enhance article text with summaries for better search
    - Set index_done flag
    """
    logger.info("🔍 Node: Index - Storing in vector database")
    
    try:
        from vector_store import chroma_db
        from sentence_transformers import SentenceTransformer
        
        # Get collection
        collection = chroma_db.get_or_create_collection(chroma_db.COLLECTION_NAME)
        
        # Initialize embedding model
        model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        
        # Get LLM summaries
        summaries = state.llm_outputs.get("summaries", []) if state.llm_outputs else []
        summary_map = {s.get("id"): s.get("summary") for s in summaries if s.get("id")}
        
        # Prepare data for indexing
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for article in state.unique_articles:
            article_id = str(article["id"])
            
            # Enhance document text with LLM summary if available
            doc_text = article.get("text", "")
            summary = summary_map.get(article["id"])
            if summary:
                doc_text += f"\n\nSummary: {summary}"
            
            # Generate embedding
            embedding = model.encode(doc_text).tolist()
            
            # Extract entities for metadata
            entities = article.get("entities", {})
            metadata = {
                "companies": ",".join(entities.get("companies", [])),
                "sectors": ",".join(entities.get("sectors", [])),
                "regulators": ",".join(entities.get("regulators", [])),
                "events": ",".join(entities.get("events", []))
            }
            
            ids.append(article_id)
            embeddings.append(embedding)
            documents.append(doc_text)
            metadatas.append(metadata)
        
        # Add to ChromaDB collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        state.index_done = True
        state.stats["indexed_count"] = len(state.unique_articles)
        
        logger.info(f"✅ Indexed {len(state.unique_articles)} articles (with {len(summary_map)} summaries)")
        return {"index_done": True, "stats": state.stats}
    
    except Exception as e:
        logger.error(f"❌ Index node failed: {str(e)}")
        raise


# Build the graph
def build_pipeline_graph() -> StateGraph:
    """
    Build and compile the pipeline graph.
    
    Graph structure:
    ingest → dedup → entities → sentiment → llm → index
    """
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("dedup", dedup_node)
    graph.add_node("extract_entities", entity_node)
    graph.add_node("analyze_sentiment", sentiment_node)
    graph.add_node("llm", llm_node)
    graph.add_node("index", index_node)
    
    # Set entry point
    graph.set_entry_point("ingest")
    
    # Add edges (linear flow)
    graph.add_edge("ingest", "dedup")
    graph.add_edge("dedup", "extract_entities")
    graph.add_edge("extract_entities", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "llm")
    graph.add_edge("llm", "index")
    graph.add_edge("index", END)
    
    return graph.compile()


# Compile the workflow
workflow = build_pipeline_graph()


# Export visualization
def export_graph_image(output_path: str = "pipeline_graph.png"):
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
