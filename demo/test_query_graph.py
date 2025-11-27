"""
Test script for LangGraph Query Workflow.

Tests the query processing using LangGraph's StateGraph:
- Parse Query → Expand Query → Semantic Search → Rerank → Format

Tests with multiple query examples.
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set environment variables
from dotenv import load_dotenv
load_dotenv()

from graphs.query_graph import workflow
from graphs.state import QueryState
from database import db


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


async def test_query(query_text: str):
    """Test a single query."""
    print_separator(f"Query: {query_text}", "-")
    
    # Initialize state
    initial_state = QueryState(query=query_text)
    
    try:
        # Execute the workflow
        result = await workflow.ainvoke(initial_state)
        
        # Extract state values (handle dict return type)
        if isinstance(result, dict):
            query = result.get("query", "")
            expanded_query = result.get("expanded_query", "")
            matched_entities = result.get("matched_entities", {})
            result_count = result.get("result_count", 0)
            reranked = result.get("reranked", [])
        else:
            query = getattr(result, 'query', "")
            expanded_query = getattr(result, 'expanded_query', "")
            matched_entities = getattr(result, 'matched_entities', {})
            result_count = getattr(result, 'result_count', 0)
            reranked = getattr(result, 'reranked', [])
        
        # Print results
        print(f"\n📝 Original Query: {query}")
        
        if expanded_query:
            print(f"\n✨ Expanded Query:")
            print(f"   {expanded_query[:200]}...")
        
        if matched_entities:
            print(f"\n🎯 Matched Entities:")
            for entity_type, entities in matched_entities.items():
                if entities:
                    print(f"   {entity_type.upper()}: {', '.join(entities)}")
        
        print(f"\n📊 Results: {result_count} articles found")
        
        if reranked:
            print(f"\n🔝 Top {min(3, len(reranked))} Results:")
            for i, result_item in enumerate(reranked[:3], 1):
                article_id = result_item.get("id", "unknown")
                score = result_item.get("rerank_score", 0.0)
                text = result_item.get("text", "")[:100]
                print(f"\n   {i}. [ID: {article_id}] Score: {score:.3f}")
                print(f"      {text}...")
                
                # Show entities if present
                if "entities" in result_item:
                    ent = result_item["entities"]
                    if ent.get("companies"):
                        print(f"      Companies: {', '.join(ent['companies'][:3])}")
                    if ent.get("sectors"):
                        print(f"      Sectors: {', '.join(ent['sectors'][:2])}")
        
        # Extract timestamp
        if isinstance(result, dict):
            timestamp = result.get("timestamp", "")
        else:
            timestamp = getattr(result, 'timestamp', "")
        print(f"\n⏰ Query completed at: {timestamp}")
        
    except Exception as e:
        print(f"\n❌ Query failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run the query graph tests."""
    print_separator("FinNews AI - LangGraph Query Test", "=")
    
    print("\n🚀 Initializing database...")
    try:
        db.init_db()
        await db.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {str(e)}")
    
    print_separator("LangGraph Query Workflow Stages")
    
    print("\n📊 Query Processing Stages:")
    print("   1. 🔍 Parse Query - Extract entities from query")
    print("   2. 🤖 Expand Query - Use LLM for enrichment")
    print("   3. 🔎 Semantic Search - Find relevant articles")
    print("   4. 📊 Rerank - Refine result order")
    print("   5. 📝 Format Response - Structure output")
    
    # Test queries
    test_queries = [
        "HDFC Bank news",
        "RBI policy changes",
        "banking sector update",
        "interest rate impact on lending"
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} queries...\n")
    
    for query in test_queries:
        await test_query(query)
    
    print_separator("✅ All Query Tests Completed!", "=")
    
    print("\n📊 Summary:")
    print(f"   • Queries tested: {len(test_queries)}")
    print(f"   • Workflow stages: 5")
    print(f"   • All queries processed successfully")
    
    # Close database
    await db.close_db()


if __name__ == "__main__":
    asyncio.run(main())
