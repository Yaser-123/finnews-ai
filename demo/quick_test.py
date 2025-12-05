"""Quick test to check entities data."""
import asyncio
from database import db
from sqlalchemy import text

async def test():
    db.init_db()
    s = await db.get_session()
    
    # Check entities with sectors
    r = await s.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(sectors) as with_sectors,
            COUNT(companies) as with_companies
        FROM entities
    """))
    row = r.fetchone()
    print(f"Total entities: {row.total}")
    print(f"With sectors: {row.with_sectors}")
    print(f"With companies: {row.with_companies}")
    
    # Sample entities with sectors
    r = await s.execute(text("""
        SELECT article_id, sectors, companies
        FROM entities
        WHERE sectors IS NOT NULL
        LIMIT 3
    """))
    print("\nSample entities with sectors:")
    for row in r.fetchall():
        print(f"  Article {row.article_id}: Sectors={row.sectors}, Companies={row.companies[:2] if row.companies else None}")

asyncio.run(test())
