"""
Test script for LangGraph Pipeline Workflow.

Tests the full pipeline using LangGraph's StateGraph:
- Ingest → Dedup → Entity → Sentiment → LLM → Index

Prints statistics and sample outputs from each stage.
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variables
from dotenv import load_dotenv
load_dotenv()

from graphs.pipeline_graph import workflow
from graphs.state import PipelineState
from database import db


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


async def main():
    """Run the pipeline graph test."""
    print_separator("FinNews AI - LangGraph Pipeline Test", "=")
    
    print("\n🚀 Initializing database...")
    try:
        db.init_db()
        await db.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {str(e)}")
    
    print_separator("Executing LangGraph Pipeline Workflow")
    
    # Initialize state
    initial_state = PipelineState(stats={})
    
    print("\n📊 Pipeline Stages:")
    print("   1. 📥 Ingest - Load demo articles")
    print("   2. 🔄 Dedup - Remove duplicates")
    print("   3. 🏢 Entity - Extract financial entities")
    print("   4. 📊 Sentiment - Analyze sentiment")
    print("   5. 🤖 LLM - Generate summaries")
    print("   6. 🔍 Index - Store in vector DB")
    
    print("\n⏳ Running workflow...")
    
    try:
        # Execute the workflow
        result = await workflow.ainvoke(initial_state)
        
        # Handle both dict and object responses
        if isinstance(result, dict):
            final_state = result
            stats = final_state.get('stats', {})
        else:
            final_state = result
            stats = final_state.stats if hasattr(final_state, 'stats') else {}
        
        print_separator("Pipeline Execution Results")
        
        # Print statistics
        print("\n📈 Statistics:")
        print(f"   • Total input articles: {stats.get('total_input', 0)}")
        print(f"   • Unique articles: {stats.get('unique_count', 0)}")
        print(f"   • Clusters found: {stats.get('clusters_count', 0)}")
        print(f"   • Entities extracted: {stats.get('entities_extracted', 0)}")
        print(f"   • Sentiment analyzed: {stats.get('sentiment_analyzed', 0)}")
        print(f"   • LLM summaries: {stats.get('llm_summaries', 0)}")
        print(f"   • Articles indexed: {stats.get('indexed_count', 0)}")
        
        # Sentiment distribution
        if "sentiment_distribution" in stats:
            dist = stats["sentiment_distribution"]
            print(f"\n💹 Sentiment Distribution:")
            print(f"   • Positive: {dist.get('positive', 0)}")
            print(f"   • Negative: {dist.get('negative', 0)}")
            print(f"   • Neutral: {dist.get('neutral', 0)}")
        
        # Sample clusters
        clusters = final_state.get('clusters', []) if isinstance(final_state, dict) else (final_state.clusters if hasattr(final_state, 'clusters') else [])
        if clusters:
            print(f"\n🔗 Sample Clusters (showing first 3):")
            for i, cluster in enumerate(clusters[:3], 1):
                main_id = cluster.get("main_id")
                merged = cluster.get("merged_ids", [])
                if len(merged) > 1:
                    print(f"   {i}. Main ID {main_id} merged with: {merged}")
                else:
                    print(f"   {i}. ID {main_id} (no duplicates)")
        
        # Sample entities
        entities = final_state.get('entities', {}) if isinstance(final_state, dict) else (final_state.entities if hasattr(final_state, 'entities') else {})
        if entities:
            print(f"\n🏢 Sample Entities (first 3 articles):")
            for article_id in list(entities.keys())[:3]:
                ent = entities[article_id]
                print(f"   Article {article_id}:")
                if ent.get("companies"):
                    print(f"      Companies: {', '.join(ent['companies'][:3])}")
                if ent.get("sectors"):
                    print(f"      Sectors: {', '.join(ent['sectors'][:2])}")
                if ent.get("regulators"):
                    print(f"      Regulators: {', '.join(ent['regulators'])}")
        
        # Sample sentiment
        sentiment = final_state.get('sentiment', {}) if isinstance(final_state, dict) else (final_state.sentiment if hasattr(final_state, 'sentiment') else {})
        if sentiment:
            print(f"\n📊 Sample Sentiment (first 3 articles):")
            for article_id in list(sentiment.keys())[:3]:
                sent = sentiment[article_id]
                label = sent.get("label", "unknown").upper()
                score = sent.get("score", 0.0)
                print(f"   Article {article_id}: {label} (confidence: {score:.4f})")
        
        # LLM summaries
        llm_outputs = final_state.get('llm_outputs', {}) if isinstance(final_state, dict) else (final_state.llm_outputs if hasattr(final_state, 'llm_outputs') else {})
        if llm_outputs and "summaries" in llm_outputs:
            print(f"\n🤖 LLM Summaries (first 2):")
            for i, summary in enumerate(llm_outputs["summaries"][:2], 1):
                print(f"   {i}. Article {summary['id']}:")
                print(f"      {summary['summary']}")
        
        # Timestamp
        timestamp = final_state.get('timestamp') if isinstance(final_state, dict) else (final_state.timestamp if hasattr(final_state, 'timestamp') else None)
        if timestamp:
            print(f"\n⏰ Completed at: {timestamp}")
        
        print_separator("✅ Pipeline Test Completed Successfully!", "=")
        
        # Close database
        await db.close_db()
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
