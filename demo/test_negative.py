"""Check what negative articles exist."""
import asyncio
from database import db
from sqlalchemy import text

async def test():
    db.init_db()
    s = await db.get_session()
    
    # Check total negative articles
    r = await s.execute(text("""
        SELECT COUNT(*) as count
        FROM sentiment
        WHERE label = 'negative'
    """))
    print(f"Total negative articles: {r.fetchone().count}")
    
    # Sample negative articles with their text
    r = await s.execute(text("""
        SELECT 
            a.id,
            a.text,
            s.score,
            e.companies
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        LEFT JOIN entities e ON a.id = e.article_id
        WHERE s.label = 'negative'
        ORDER BY s.score DESC
        LIMIT 5
    """))
    print("\nTop 5 negative articles:")
    for row in r.fetchall():
        print(f"\nID {row.id} (Score: {row.score:.3f})")
        print(f"Companies: {row.companies[:3] if row.companies else 'None'}")
        print(f"Text: {row.text[:200]}...")

asyncio.run(test())
