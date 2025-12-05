"""
Test RSS ingestion to verify source, published_at, and hash are properly populated
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.realtime import fetch_all, DEFAULT_FEEDS

async def test_rss_ingestion():
    print("\n" + "="*70)
    print("🧪 TESTING RSS INGESTION METADATA")
    print("="*70)
    
    # Use just 2 feeds for quick test
    test_feeds = DEFAULT_FEEDS[:2]
    
    print(f"\n📡 Fetching from {len(test_feeds)} RSS feeds...")
    print(f"   1. {test_feeds[0]}")
    print(f"   2. {test_feeds[1]}")
    
    articles = await fetch_all(test_feeds)
    
    if not articles:
        print("\n❌ No articles fetched!")
        return
    
    print(f"\n✅ Fetched {len(articles)} articles")
    
    # Check if all required fields are present
    print(f"\n📊 Field Validation:")
    
    missing_source = sum(1 for a in articles if not a.get("source"))
    missing_published = sum(1 for a in articles if not a.get("published_at"))
    missing_hash = sum(1 for a in articles if not a.get("hash"))
    
    print(f"   Articles with source: {len(articles) - missing_source}/{len(articles)}")
    print(f"   Articles with published_at: {len(articles) - missing_published}/{len(articles)}")
    print(f"   Articles with hash: {len(articles) - missing_hash}/{len(articles)}")
    
    if missing_source == 0 and missing_published == 0 and missing_hash == 0:
        print(f"\n✅ ALL FIELDS POPULATED CORRECTLY!")
    else:
        print(f"\n❌ Some fields are missing!")
    
    # Show sample articles
    print(f"\n📰 Sample Articles (first 3):")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n   Article {i}:")
        print(f"      ID: {article.get('id')}")
        print(f"      Source: {article.get('source', 'NULL')[:60]}...")
        print(f"      Published: {article.get('published_at', 'NULL')}")
        print(f"      Hash: {article.get('hash', 'NULL')[:40]}...")
        print(f"      Title: {article.get('title', 'N/A')[:70]}...")
        print(f"      Text length: {len(article.get('text', ''))} chars")
    
    print(f"\n{'='*70}")
    print(f"✅ RSS INGESTION TEST COMPLETE!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(test_rss_ingestion())
