"""
Database connection and operations test script.

Tests:
1. Database connection
2. Table creation
3. Article insertion
4. Article retrieval
5. Entity, sentiment, and query log operations
"""

import sys
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from database import db


def print_separator(title: str = "", char: str = "=", width: int = 80):
    """Print a formatted separator."""
    print("\n" + char * width)
    if title:
        print(f"{title:^{width}}")
        print(char * width)


async def test_connection():
    """Test database connection."""
    print_separator("Test 1: Database Connection")
    
    try:
        # Initialize database
        db.init_db()
        print("✅ Database engine initialized")
        
        # Create tables
        await db.create_tables()
        print("✅ Database tables created/verified")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False


async def test_article_operations():
    """Test article insert and retrieval."""
    print_separator("Test 2: Article Operations")
    
    try:
        # Insert test articles
        test_articles = [
            {
                "id": 9001,
                "text": "Test article about HDFC Bank quarterly results",
                "source": "test_source",
                "published_at": datetime.utcnow()
            },
            {
                "id": 9002,
                "text": "Test article about RBI policy announcement",
                "source": "test_source",
                "published_at": datetime.utcnow()
            }
        ]
        
        inserted_ids = await db.save_articles(test_articles)
        print(f"✅ Inserted {len(inserted_ids)} articles: {inserted_ids}")
        
        # Retrieve recent articles
        recent = await db.get_recent_articles(limit=5)
        print(f"\n📰 Retrieved {len(recent)} recent articles:")
        for article in recent[:3]:
            print(f"   - ID {article['id']}: {article['text'][:60]}...")
        
        return True
    except Exception as e:
        print(f"❌ Article operations failed: {str(e)}")
        return False


async def test_entity_operations():
    """Test entity extraction persistence."""
    print_separator("Test 3: Entity Operations")
    
    try:
        test_entities = {
            "companies": ["HDFC Bank", "ICICI Bank"],
            "sectors": ["Banking", "Finance"],
            "regulators": ["RBI"],
            "people": [],
            "events": ["Quarterly Results"],
            "impacted_stocks": [
                {"symbol": "HDFCBANK", "confidence": 1.0, "type": "direct"},
                {"symbol": "ICICIBANK", "confidence": 0.8, "type": "mention"}
            ]
        }
        
        success = await db.save_entities(9001, test_entities)
        if success:
            print(f"✅ Saved entities for article 9001")
            print(f"   Companies: {', '.join(test_entities['companies'])}")
            print(f"   Sectors: {', '.join(test_entities['sectors'])}")
            print(f"   Stocks: {len(test_entities['impacted_stocks'])} mapped")
        
        return success
    except Exception as e:
        print(f"❌ Entity operations failed: {str(e)}")
        return False


async def test_sentiment_operations():
    """Test sentiment analysis persistence."""
    print_separator("Test 4: Sentiment Operations")
    
    try:
        test_sentiment = {
            "label": "positive",
            "score": 0.9566
        }
        
        success = await db.save_sentiment(9001, test_sentiment)
        if success:
            print(f"✅ Saved sentiment for article 9001")
            print(f"   Label: {test_sentiment['label'].upper()}")
            print(f"   Score: {test_sentiment['score']:.4f}")
        
        return success
    except Exception as e:
        print(f"❌ Sentiment operations failed: {str(e)}")
        return False


async def test_dedup_operations():
    """Test deduplication results persistence."""
    print_separator("Test 5: Deduplication Operations")
    
    try:
        test_dedup = {
            "unique_articles": [],
            "clusters": [
                {"main_id": 9001, "merged_ids": [9001]},
                {"main_id": 9002, "merged_ids": [9002]}
            ]
        }
        
        success = await db.save_dedup_results(test_dedup)
        if success:
            print(f"✅ Saved deduplication results")
            print(f"   Clusters: {len(test_dedup['clusters'])}")
        
        return success
    except Exception as e:
        print(f"❌ Dedup operations failed: {str(e)}")
        return False


async def test_query_log_operations():
    """Test query log persistence."""
    print_separator("Test 6: Query Log Operations")
    
    try:
        success = await db.save_query_log(
            query="HDFC Bank news",
            expanded_query="HDFC Bank recent updates including financial performance and market news",
            result_count=5
        )
        
        if success:
            print(f"✅ Saved query log")
            print(f"   Query: HDFC Bank news")
            print(f"   Results: 5 articles")
        
        return success
    except Exception as e:
        print(f"❌ Query log operations failed: {str(e)}")
        return False


async def main():
    """Run all database tests."""
    print_separator("FinNews AI - Database Test Suite (PostgreSQL + Neon)")
    
    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or db_url == "YOUR_NEON_DB_URL_HERE":
        print("\n⚠️  WARNING: DATABASE_URL not configured!")
        print("   Please set DATABASE_URL in .env file with your Neon connection string")
        print("   Example: DATABASE_URL='postgresql://user:pass@host/db?sslmode=require'")
        print("\n   Tests will run but database operations will be skipped.\n")
    
    results = []
    
    # Run tests
    results.append(("Connection", await test_connection()))
    results.append(("Articles", await test_article_operations()))
    results.append(("Entities", await test_entity_operations()))
    results.append(("Sentiment", await test_sentiment_operations()))
    results.append(("Deduplication", await test_dedup_operations()))
    results.append(("Query Logs", await test_query_log_operations()))
    
    # Cleanup
    await db.close_db()
    
    # Summary
    print_separator("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed\n")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name:20s} {status}")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
