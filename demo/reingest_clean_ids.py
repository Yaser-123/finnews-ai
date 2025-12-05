"""
Clear database and re-ingest articles with clean auto-incrementing IDs
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session, save_articles
from sqlalchemy import text as sql_text
from ingest.realtime import fetch_all, DEFAULT_FEEDS

async def reingest_with_clean_ids():
    """Clear database and re-ingest with auto-incrementing IDs."""
    print("\n" + "="*70)
    print("🔄 RE-INGESTING WITH CLEAN AUTO-INCREMENT IDs")
    print("="*70)
    
    # Initialize database
    init_db()
    
    session = await get_session()
    
    async with session:
        # Step 1: Clear all articles
        result = await session.execute(sql_text("SELECT COUNT(*) FROM articles"))
        old_count = result.scalar()
        
        print(f"\n📊 Current database: {old_count} articles with hash-based IDs")
        print(f"🗑️  Clearing database...")
        
        await session.execute(sql_text("DELETE FROM articles"))
        await session.commit()
        print(f"✅ Database cleared")
        
        # Step 2: Reset auto-increment sequence to 1
        print(f"\n🔄 Resetting ID sequence to 1...")
        await session.execute(sql_text("ALTER SEQUENCE articles_id_seq RESTART WITH 1"))
        await session.commit()
        print(f"✅ Sequence reset")
    
    # Step 3: Fetch fresh articles
    print(f"\n📡 Fetching articles from {len(DEFAULT_FEEDS)} RSS feeds...")
    print("   (This may take 30-60 seconds...)")
    
    rss_articles = await fetch_all(DEFAULT_FEEDS)
    print(f"✅ Fetched {len(rss_articles)} articles")
    
    # Verify articles don't have explicit IDs
    has_ids = sum(1 for a in rss_articles if 'id' in a)
    print(f"\n🔍 Articles with explicit ID field: {has_ids}/{len(rss_articles)}")
    
    if has_ids > 0:
        print(f"⚠️  WARNING: Some articles still have explicit IDs!")
    else:
        print(f"✅ Perfect! Articles will use auto-increment IDs")
    
    # Step 4: Save to database
    print(f"\n💾 Saving articles to database with auto-increment IDs...")
    
    inserted_count = await save_articles(rss_articles)
    print(f"✅ Inserted {inserted_count} articles")
    
    # Step 5: Verify clean IDs
    session = await get_session()
    async with session:
        result = await session.execute(sql_text("""
            SELECT 
                COUNT(*) as total,
                MIN(id) as min_id,
                MAX(id) as max_id,
                COUNT(DISTINCT id) as unique_ids
            FROM articles
        """))
        row = result.fetchone()
        
        print(f"\n📊 Final Database Statistics:")
        print(f"   Total articles: {row[0]}")
        print(f"   ID range: {row[1]} to {row[2]}")
        print(f"   Unique IDs: {row[3]}")
        print(f"   ✅ Clean sequential IDs: {'Yes' if row[2] <= row[0] + 100 else 'No (still hash-based)'}")
        
        # Show sample IDs
        result = await session.execute(sql_text("""
            SELECT id, LEFT(text, 70) as text_preview, published_at
            FROM articles
            ORDER BY id
            LIMIT 20
        """))
        
        print(f"\n📰 First 20 Articles (Clean Sequential IDs):")
        print(f"   {'ID':<8} {'Published':<20} {'Preview'}")
        print(f"   {'-'*8} {'-'*20} {'-'*50}")
        
        for row in result.fetchall():
            article_id = str(row[0])
            published = str(row[2])[:19] if row[2] else "N/A"
            preview = row[1][:48] + "..." if row[1] else "N/A"
            
            print(f"   {article_id:<8} {published:<20} {preview}")
    
    print(f"\n{'='*70}")
    print(f"✅ DATABASE NOW USES CLEAN AUTO-INCREMENT IDs (1, 2, 3, ...)!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(reingest_with_clean_ids())
