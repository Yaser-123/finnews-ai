"""Test date ranges for negative articles."""
import asyncio
from database import db
from sqlalchemy import text

async def test():
    db.init_db()
    s = await db.get_session()
    
    # Check negative articles without date filter
    r = await s.execute(text("""
        SELECT 
            COUNT(*) as count,
            MIN(a.published_at) as oldest,
            MAX(a.published_at) as newest
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        WHERE s.label = 'negative'
          AND a.text ILIKE '%Banking%'
    """))
    row = r.fetchone()
    print(f"Negative Banking articles (no date filter): {row.count}")
    print(f"Oldest: {row.oldest}")
    print(f"Newest: {row.newest}")
    
    # Check with 30-day filter
    r = await s.execute(text("""
        SELECT COUNT(*) as count
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        WHERE s.label = 'negative'
          AND a.text ILIKE '%Banking%'
          AND a.published_at >= NOW() - INTERVAL '30 days'
    """))
    row = r.fetchone()
    print(f"\nWith 30-day filter: {row.count}")
    
    # Check with 180-day filter
    r = await s.execute(text("""
        SELECT COUNT(*) as count
        FROM articles a
        JOIN sentiment s ON a.id = s.article_id
        WHERE s.label = 'negative'
          AND a.text ILIKE '%Banking%'
          AND a.published_at >= NOW() - INTERVAL '180 days'
    """))
    row = r.fetchone()
    print(f"With 180-day filter: {row.count}")

asyncio.run(test())
