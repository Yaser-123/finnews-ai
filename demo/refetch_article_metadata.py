"""
Re-fetch articles from RSS feeds to get actual source and published_at metadata.
Matches existing articles by text similarity and updates with real metadata.
"""
import asyncio
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text
from ingest.realtime import fetch_all, DEFAULT_FEEDS

def text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (0.0 to 1.0)."""
    # Normalize texts for comparison
    t1 = text1.lower().strip()[:200]  # First 200 chars
    t2 = text2.lower().strip()[:200]
    return SequenceMatcher(None, t1, t2).ratio()

async def refetch_and_update_metadata():
    """Re-fetch RSS articles and match with existing database articles to get real metadata."""
    print("\n" + "="*70)
    print("🔄 RE-FETCHING REAL METADATA FROM RSS FEEDS")
    print("="*70)
    
    # Initialize database
    init_db()
    
    # Step 1: Fetch fresh articles from RSS feeds
    print(f"\n📡 Fetching articles from {len(DEFAULT_FEEDS)} RSS feeds...")
    print("   (This may take 30-60 seconds...)")
    
    rss_articles = await fetch_all(DEFAULT_FEEDS)
    print(f"✅ Fetched {len(rss_articles)} articles from RSS feeds")
    
    # Step 2: Get articles with 'manual_entry' source from database
    session = await get_session()
    
    async with session:
        result = await session.execute(sql_text("""
            SELECT id, text, source, hash
            FROM articles
            WHERE source = 'manual_entry'
            ORDER BY id
        """))
        
        db_articles = result.fetchall()
        total_to_match = len(db_articles)
        
        if total_to_match == 0:
            print("\n✅ No articles with 'manual_entry' source found!")
            return
        
        print(f"\n📊 Found {total_to_match} articles with 'manual_entry' source")
        print(f"\n🔍 Matching with RSS feed articles...")
        
        matched_count = 0
        updated_count = 0
        
        for db_id, db_text, db_source, db_hash in db_articles:
            # Try to find matching RSS article by text similarity
            best_match = None
            best_similarity = 0.0
            
            # Extract key phrases from db_text for matching
            db_text_short = db_text[:300].lower()
            
            for rss_article in rss_articles:
                rss_text_short = rss_article.get('text', '')[:300].lower()
                
                # Calculate similarity
                similarity = text_similarity(db_text, rss_article.get('text', ''))
                
                if similarity > best_similarity and similarity > 0.7:  # 70% similarity threshold
                    best_similarity = similarity
                    best_match = rss_article
            
            if best_match:
                matched_count += 1
                
                # Update with real metadata
                await session.execute(sql_text("""
                    UPDATE articles
                    SET 
                        source = :source,
                        published_at = :published_at,
                        hash = :hash
                    WHERE id = :id
                """), {
                    "id": db_id,
                    "source": best_match.get('source'),
                    "published_at": best_match.get('published_at'),
                    "hash": best_match.get('hash')
                })
                
                updated_count += 1
                
                if updated_count % 5 == 0:
                    print(f"   ✅ Updated {updated_count}/{matched_count} matched articles...")
        
        # Commit changes
        await session.commit()
        
        print(f"\n📊 Results:")
        print(f"   Total manual_entry articles: {total_to_match}")
        print(f"   Matched with RSS feeds: {matched_count} ({matched_count/total_to_match*100:.1f}%)")
        print(f"   Updated with real metadata: {updated_count}")
        print(f"   Unable to match: {total_to_match - matched_count}")
        
        if total_to_match - matched_count > 0:
            print(f"\n⚠️  {total_to_match - matched_count} articles couldn't be matched with RSS feeds.")
            print(f"   These might be:")
            print(f"   - Demo/test articles not from RSS feeds")
            print(f"   - Articles older than RSS feed history")
            print(f"   - Articles from feeds that changed their content")
        
        # Show sample of updated articles
        result = await session.execute(sql_text("""
            SELECT id, source, published_at, LEFT(hash, 20) as hash_preview, LEFT(text, 60) as text_preview
            FROM articles
            WHERE source != 'manual_entry'
            ORDER BY id
            LIMIT 10
        """))
        
        print(f"\n📰 Sample of Articles with Real Metadata:")
        print(f"   {'ID':<6} {'Source':<40} {'Published':<20}")
        print(f"   {'-'*6} {'-'*40} {'-'*20}")
        
        for row in result.fetchall():
            article_id = row[0]
            source = row[1][:38] + ".." if len(row[1]) > 40 else row[1]
            published = str(row[2])[:19] if row[2] else "NULL"
            
            print(f"   {article_id:<6} {source:<40} {published:<20}")
        
        print(f"\n{'='*70}")
        print(f"✅ METADATA UPDATE COMPLETE!")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(refetch_and_update_metadata())
