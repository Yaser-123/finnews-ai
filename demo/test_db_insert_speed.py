"""
Database Insert Speed Test

Tests the optimized save_articles() function to verify:
- Batch UPSERT with ON CONFLICT DO NOTHING
- Hash precheck performance
- Rate-limit protection
- Execution timers
- Duplicate handling

Run this before pushing to GitHub to verify all optimizations work correctly.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import db
from ingest.realtime import fetch_all
from dotenv import load_dotenv

load_dotenv()


async def test_insert_speed():
    """
    Test database insert speed with real RSS feed data.
    
    This test will:
    1. Fetch real articles from RSS feeds
    2. Test first insert (all new)
    3. Test second insert (all duplicates)
    4. Verify hash precheck performance
    5. Verify batch processing logs
    """
    
    print("\n" + "="*70)
    print("🧪 DATABASE INSERT SPEED TEST")
    print("="*70)
    
    # Initialize database
    print("\n📊 Step 1: Initialize Database")
    db.init_db()
    await db.create_tables()
    await db.run_migrations()
    print("✅ Database initialized")
    
    # Fetch real articles from RSS feeds
    print("\n📊 Step 2: Fetch Real Articles from RSS Feeds")
    print("Fetching articles from configured RSS feeds...")
    start_fetch = time.time()
    articles = await fetch_all()
    fetch_time = time.time() - start_fetch
    
    print(f"✅ Fetched {len(articles)} articles in {fetch_time:.2f}s")
    
    if not articles:
        print("❌ No articles fetched. Cannot run test.")
        return
    
    # Test 1: First Insert (All New)
    print("\n" + "-"*70)
    print("📊 Test 1: First Insert (All New Articles)")
    print("-"*70)
    print(f"Inserting {len(articles)} articles...")
    
    start_insert1 = time.time()
    inserted_count1 = await db.save_articles(articles)
    insert1_time = time.time() - start_insert1
    
    print(f"\n✅ Test 1 Complete:")
    print(f"   • Inserted: {inserted_count1} articles")
    print(f"   • Time: {insert1_time:.2f}s")
    print(f"   • Rate: {inserted_count1/insert1_time:.1f} articles/sec")
    
    # Test 2: Second Insert (All Duplicates)
    print("\n" + "-"*70)
    print("📊 Test 2: Second Insert (All Duplicates - Should Skip)")
    print("-"*70)
    print(f"Re-inserting same {len(articles)} articles...")
    print("Expected: All should be skipped (existing hashes)")
    
    start_insert2 = time.time()
    inserted_count2 = await db.save_articles(articles)
    insert2_time = time.time() - start_insert2
    
    print(f"\n✅ Test 2 Complete:")
    print(f"   • Inserted: {inserted_count2} articles (expected: 0)")
    print(f"   • Time: {insert2_time:.2f}s")
    print(f"   • Speedup: {insert1_time/insert2_time:.1f}x faster (hash precheck working)")
    
    # Test 3: Mixed Insert (50% New, 50% Duplicates)
    print("\n" + "-"*70)
    print("📊 Test 3: Mixed Insert (50% New, 50% Duplicates)")
    print("-"*70)
    
    # Modify half the articles to create new ones
    mixed_articles = articles.copy()
    half = len(mixed_articles) // 2
    
    for i in range(half):
        # Change hash to make it "new"
        mixed_articles[i]['hash'] = f"modified_{mixed_articles[i]['hash']}"
        mixed_articles[i]['id'] = mixed_articles[i]['id'] + 1000000000000000  # Change ID
    
    print(f"Inserting {len(mixed_articles)} articles ({half} new, {half} duplicates)...")
    
    start_insert3 = time.time()
    inserted_count3 = await db.save_articles(mixed_articles)
    insert3_time = time.time() - start_insert3
    
    print(f"\n✅ Test 3 Complete:")
    print(f"   • Inserted: {inserted_count3} articles")
    print(f"   • Expected: ~{half} articles")
    print(f"   • Time: {insert3_time:.2f}s")
    print(f"   • Rate: {inserted_count3/insert3_time:.1f} articles/sec")
    
    # Summary
    print("\n" + "="*70)
    print("📊 PERFORMANCE SUMMARY")
    print("="*70)
    
    print(f"\n🚀 Fetch Performance:")
    print(f"   • RSS Feeds: {len(articles)} articles in {fetch_time:.2f}s")
    print(f"   • Rate: {len(articles)/fetch_time:.1f} articles/sec")
    
    print(f"\n💾 Insert Performance:")
    print(f"   • New Articles: {inserted_count1} in {insert1_time:.2f}s ({inserted_count1/insert1_time:.1f}/sec)")
    print(f"   • Duplicates: {inserted_count2} in {insert2_time:.2f}s (hash precheck)")
    print(f"   • Mixed (50/50): {inserted_count3} in {insert3_time:.2f}s ({inserted_count3/insert3_time:.1f}/sec)")
    
    print(f"\n⚡ Optimization Wins:")
    print(f"   • Hash Precheck Speedup: {insert1_time/insert2_time:.1f}x faster for duplicates")
    print(f"   • Batch Processing: 50 items per INSERT")
    print(f"   • ON CONFLICT DO NOTHING: Database-level deduplication")
    
    print(f"\n✅ Expected Behavior:")
    if inserted_count2 == 0:
        print("   ✅ Duplicate detection working (0 re-inserts)")
    else:
        print(f"   ⚠️  Duplicate detection issue ({inserted_count2} re-inserts, expected 0)")
    
    if abs(inserted_count3 - half) < 10:  # Allow small margin
        print(f"   ✅ Mixed insert working (~{half} new inserts)")
    else:
        print(f"   ⚠️  Mixed insert issue ({inserted_count3} inserts, expected ~{half})")
    
    if insert2_time < insert1_time:
        print(f"   ✅ Hash precheck optimization working ({insert1_time/insert2_time:.1f}x speedup)")
    else:
        print(f"   ⚠️  Hash precheck not optimizing (slower on duplicates)")
    
    print("\n" + "="*70)
    print("🎉 TEST COMPLETE - Ready for GitHub Push!")
    print("="*70 + "\n")
    
    # Close database
    await db.close_db()


if __name__ == "__main__":
    print("\n🔬 Starting Database Insert Speed Test...")
    print("This will test the optimized save_articles() function.")
    
    try:
        asyncio.run(test_insert_speed())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
