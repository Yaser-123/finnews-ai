"""
Check Sentiment Distribution

Checks the sentiment labels and sectors in the database.
"""

import asyncio
import sys
sys.path.insert(0, '..')
from database import db
from sqlalchemy import text

async def check_sentiment_distribution():
    """Check sentiment distribution by sector."""
    
    # Initialize database
    db.init_db()
    session = await db.get_session()
    
    print("=" * 80)
    print("SENTIMENT DISTRIBUTION CHECK")
    print("=" * 80)
    
    # Check total sentiment counts
    query = text("""
        SELECT 
            label,
            COUNT(*) as count,
            AVG(score) as avg_score
        FROM sentiment
        GROUP BY label
        ORDER BY count DESC
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    print("\n📊 Sentiment Distribution:")
    print("-" * 80)
    for row in rows:
        print(f"  {row.label.upper():10} - Count: {row.count:4} | Avg Score: {row.avg_score:.3f}")
    
    # Check sectors with negative sentiment
    query = text("""
        SELECT 
            unnest(e.sectors) as sector,
            COUNT(*) as negative_count
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        JOIN entities e ON a.id = e.article_id
        WHERE s.label = 'negative'
          AND e.sectors IS NOT NULL
        GROUP BY sector
        ORDER BY negative_count DESC
        LIMIT 10
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    print("\n🚨 Sectors with Negative Sentiment Articles:")
    print("-" * 80)
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"  {i:2}. {row.sector:20} - {row.negative_count} articles")
    else:
        print("  No negative sentiment articles found with sectors")
    
    # Check sample negative articles
    query = text("""
        SELECT 
            a.id,
            a.text,
            s.score,
            e.sectors,
            e.companies
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        JOIN entities e ON a.id = e.article_id
        WHERE s.label = 'negative'
        ORDER BY s.score DESC
        LIMIT 5
    """)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    print("\n📰 Sample Negative Articles:")
    print("-" * 80)
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"\n  {i}. Article {row.id} (Score: {row.score:.3f})")
            print(f"     Sectors: {row.sectors if row.sectors else 'None'}")
            print(f"     Companies: {row.companies[:3] if row.companies else 'None'}")
            print(f"     Text: {row.text[:150]}...")
    else:
        print("  No negative sentiment articles found")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(check_sentiment_distribution())
