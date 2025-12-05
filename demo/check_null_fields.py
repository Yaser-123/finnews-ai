"""
Check articles with NULL source, published_at, or hash fields
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text

async def check_null_fields():
    # Initialize database
    init_db()
    
    # Get session
    session = await get_session()
    
    async with session:
        # Check total articles
        result = await session.execute(text("SELECT COUNT(*) FROM articles"))
        total = result.scalar()
        print(f"\n📊 Database Statistics:")
        print(f"   Total articles: {total}")
        
        # Check NULL fields
        result = await session.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE source IS NULL) as null_source,
                COUNT(*) FILTER (WHERE published_at IS NULL) as null_published,
                COUNT(*) FILTER (WHERE hash IS NULL) as null_hash,
                COUNT(*) FILTER (WHERE source IS NULL AND published_at IS NULL AND hash IS NULL) as all_null
            FROM articles
        """))
        row = result.fetchone()
        
        print(f"\n❌ NULL Field Counts:")
        print(f"   Articles with NULL source: {row[0]}")
        print(f"   Articles with NULL published_at: {row[1]}")
        print(f"   Articles with NULL hash: {row[2]}")
        print(f"   Articles with ALL three NULL: {row[3]}")
        
        # Show sample of articles with NULL fields
        result = await session.execute(text("""
            SELECT id, LEFT(text, 80) as text_preview, source, published_at, hash
            FROM articles
            WHERE source IS NULL OR published_at IS NULL OR hash IS NULL
            ORDER BY id
            LIMIT 10
        """))
        
        print(f"\n📰 Sample Articles with NULL Fields:")
        print(f"   {'ID':<6} {'Source':<15} {'Published':<20} {'Hash':<35} {'Text Preview'}")
        print(f"   {'-'*6} {'-'*15} {'-'*20} {'-'*35} {'-'*50}")
        
        for row in result.fetchall():
            article_id = row[0]
            text_preview = row[1][:50] + "..." if row[1] else "NULL"
            source = (row[2][:12] + "...") if row[2] else "NULL"
            published = str(row[3])[:19] if row[3] else "NULL"
            hash_val = (row[4][:30] + "...") if row[4] else "NULL"
            
            print(f"   {article_id:<6} {source:<15} {published:<20} {hash_val:<35} {text_preview}")

if __name__ == "__main__":
    asyncio.run(check_null_fields())
