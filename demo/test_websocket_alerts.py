"""
WebSocket Alert System Test

Tests real-time alert broadcasting during pipeline execution.
Open websocket_test_client.html in a browser before running this script.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.pipeline_graph import workflow
from graphs.state import PipelineState
from database import db


async def main():
    print("=" * 70)
    print(" " * 15 + "WebSocket Alert System Test")
    print("=" * 70)
    print()
    print("📋 Instructions:")
    print("   1. Open demo/websocket_test_client.html in your browser")
    print("   2. Make sure the server is running (uvicorn main:app --reload)")
    print("   3. Watch for real-time alerts as the pipeline processes articles")
    print()
    print("🔔 Alert Types:")
    print("   • 🚨 HIGH_RISK - Negative sentiment > 0.90")
    print("   • 📈 BULLISH - Positive sentiment > 0.90")
    print("   • 🏛️ REGULATORY_UPDATE - RBI/inflation/repo rate mentions")
    print("   • 💰 EARNINGS_UPDATE - Profit/growth/dividend mentions")
    print()
    print("=" * 70)
    print()
    
    # Initialize database
    print("🚀 Initializing database...")
    db.init_db()
    await db.create_tables()
    print("✅ Database initialized")
    print()
    
    # Create initial state
    print("=" * 70)
    print(" " * 20 + "Running Pipeline with Alerts")
    print("=" * 70)
    print()
    
    initial_state = PipelineState(
        articles=[],
        unique_articles=[],
        clusters=[],
        entities={},
        sentiment={},
        llm_outputs={},
        stats={},
        index_done=False
    )
    
    try:
        # Execute workflow - alerts will be broadcast automatically
        print("⏳ Executing pipeline workflow...")
        print("   Watch your browser for real-time alerts!")
        print()
        
        result = await workflow.ainvoke(initial_state)
        
        # Extract results
        if isinstance(result, dict):
            stats = result.get("stats", {})
        else:
            stats = getattr(result, 'stats', {})
        
        print()
        print("=" * 70)
        print(" " * 25 + "Pipeline Results")
        print("=" * 70)
        print()
        print(f"📊 Statistics:")
        print(f"   • Total input: {stats.get('total_input', 0)} articles")
        print(f"   • Unique: {stats.get('unique_count', 0)} articles")
        print(f"   • Sentiment analyzed: {stats.get('sentiment_analyzed', 0)}")
        print(f"   • LLM summaries: {stats.get('llm_summaries', 0)}")
        print(f"   • Indexed: {stats.get('indexed_count', 0)}")
        print()
        
        # Show sentiment distribution
        sentiment_dist = stats.get('sentiment_distribution', {})
        if sentiment_dist:
            print(f"💹 Sentiment Distribution:")
            print(f"   • Positive: {sentiment_dist.get('positive', 0)}")
            print(f"   • Negative: {sentiment_dist.get('negative', 0)}")
            print(f"   • Neutral: {sentiment_dist.get('neutral', 0)}")
            print()
        
        print("=" * 70)
        print()
        print("✅ Pipeline completed!")
        print()
        print("💡 Check your browser to see the real-time alerts that were broadcast")
        print("   during sentiment analysis and LLM summary generation.")
        print()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database
        await db.close_db()
        print("✅ Database connections closed")


if __name__ == "__main__":
    asyncio.run(main())
