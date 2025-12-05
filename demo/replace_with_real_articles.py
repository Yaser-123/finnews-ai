"""
Clear manual_entry articles and populate with real RSS feed articles
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session, save_articles
from sqlalchemy import text as sql_text
from ingest.realtime import fetch_all, DEFAULT_FEEDS

async def replace_with_real_articles():
    """Delete manual_entry articles and replace with real RSS articles."""
    print("\n" + "="*70)
    print("🔄 REPLACING TEST DATA WITH REAL RSS ARTICLES")
    print("="*70)
    
    # Initialize database
    init_db()
    
    session = await get_session()
    
    async with session:
        # Step 1: Count manual_entry articles
        result = await session.execute(sql_text("""
            SELECT COUNT(*) FROM articles WHERE source = 'manual_entry'
        """))
        manual_count = result.scalar()
        
        print(f"\n📊 Current database status:")
        print(f"   Manual/test articles: {manual_count}")
        
        if manual_count > 0:
            print(f"\n🗑️  Deleting {manual_count} test articles...")
            await session.execute(sql_text("""
                DELETE FROM articles WHERE source = 'manual_entry'
            """))
            await session.commit()
            print(f"✅ Deleted {manual_count} test articles")
        
        # Step 2: Fetch real RSS articles
        print(f"\n📡 Fetching fresh articles from {len(DEFAULT_FEEDS)} RSS feeds...")
        print("   (This may take 30-60 seconds...)")
        
        rss_articles = await fetch_all(DEFAULT_FEEDS)
        print(f"✅ Fetched {len(rss_articles)} articles from RSS feeds")
        
        # Step 3: Save to database
        print(f"\n💾 Saving articles to database...")
        
    # Note: We need to use save_articles which handles its own session
    inserted_count = await save_articles(rss_articles)
    
    print(f"✅ Inserted {inserted_count} new articles")
    
    # Step 4: Verify
    session = await get_session()
    async with session:
        # Check total articles
        result = await session.execute(sql_text("SELECT COUNT(*) FROM articles"))
        total = result.scalar()
        
        # Check NULL fields
        result = await session.execute(sql_text("""
            SELECT 
                COUNT(*) FILTER (WHERE source IS NULL) as null_source,
                COUNT(*) FILTER (WHERE published_at IS NULL) as null_published,
                COUNT(*) FILTER (WHERE hash IS NULL) as null_hash,
                COUNT(*) FILTER (WHERE source = 'manual_entry') as manual_entry
            FROM articles
        """))
        row = result.fetchone()
        
        print(f"\n📊 Final Database Status:")
        print(f"   Total articles: {total}")
        print(f"   Articles with NULL source: {row[0]}")
        print(f"   Articles with NULL published_at: {row[1]}")
        print(f"   Articles with NULL hash: {row[2]}")
        print(f"   Articles with manual_entry source: {row[3]}")
        
        # Show sample of real articles
        result = await session.execute(sql_text("""
            SELECT id, LEFT(source, 50) as source, published_at, LEFT(text, 70) as text_preview
            FROM articles
            ORDER BY published_at DESC
            LIMIT 10
        """))
        
        print(f"\n📰 Sample of Latest Real Articles:")
        print(f"   {'Source':<52} {'Published':<20} {'Preview'}")
        print(f"   {'-'*52} {'-'*20} {'-'*50}")
        
        for row in result.fetchall():
            source = row[0][:50] if row[0] else "NULL"
            published = str(row[1])[:19] if row[1] else "NULL"
            preview = row[2][:50] + "..." if row[2] else "NULL"
            
            print(f"   {source:<52} {published:<20} {preview}")
    
    print(f"\n{'='*70}")
    print(f"✅ DATABASE NOW CONTAINS ONLY REAL RSS ARTICLES!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(replace_with_real_articles())
