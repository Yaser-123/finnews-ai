"""
Fix articles with NULL source, published_at, and hash fields by:
1. Computing hash from text
2. Setting source as 'manual_entry'
3. Using created_at as published_at fallback
"""
import asyncio
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text

def compute_hash(text: str) -> str:
    """Compute MD5 hash of text for deduplication."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

async def fix_null_fields():
    """Fix articles with NULL source, published_at, or hash."""
    print("\n" + "="*70)
    print("🔧 FIXING ARTICLES WITH NULL FIELDS")
    print("="*70)
    
    # Initialize database
    init_db()
    
    # Get session
    session = await get_session()
    
    async with session:
        # Find articles with NULL fields
        result = await session.execute(sql_text("""
            SELECT id, text, created_at
            FROM articles
            WHERE source IS NULL OR published_at IS NULL OR hash IS NULL
            ORDER BY id
        """))
        
        articles_to_fix = result.fetchall()
        total_to_fix = len(articles_to_fix)
        
        if total_to_fix == 0:
            print("\n✅ All articles already have proper metadata!")
            return
        
        print(f"\n📊 Found {total_to_fix} articles with NULL fields")
        print(f"\nFixing articles...")
        
        fixed_count = 0
        for article_id, text, created_at in articles_to_fix:
            # Compute hash from text
            content_hash = compute_hash(text)
            
            # Use created_at as fallback for published_at
            published_at = created_at if created_at else datetime.now()
            
            # Set source as 'manual_entry' for demo articles
            source = "manual_entry"
            
            # Update article
            await session.execute(sql_text("""
                UPDATE articles
                SET 
                    source = :source,
                    published_at = :published_at,
                    hash = :hash
                WHERE id = :id
            """), {
                "id": article_id,
                "source": source,
                "published_at": published_at,
                "hash": content_hash
            })
            
            fixed_count += 1
            
            if fixed_count % 5 == 0:
                print(f"   ✅ Fixed {fixed_count}/{total_to_fix} articles...")
        
        # Commit changes
        await session.commit()
        
        print(f"\n✅ Successfully fixed {fixed_count} articles!")
        
        # Verify fixes
        result = await session.execute(sql_text("""
            SELECT 
                COUNT(*) FILTER (WHERE source IS NULL) as null_source,
                COUNT(*) FILTER (WHERE published_at IS NULL) as null_published,
                COUNT(*) FILTER (WHERE hash IS NULL) as null_hash
            FROM articles
        """))
        row = result.fetchone()
        
        print(f"\n📊 Verification:")
        print(f"   Articles with NULL source: {row[0]}")
        print(f"   Articles with NULL published_at: {row[1]}")
        print(f"   Articles with NULL hash: {row[2]}")
        
        # Show sample of fixed articles
        result = await session.execute(sql_text("""
            SELECT id, source, published_at, LEFT(hash, 20) as hash_preview, LEFT(text, 60) as text_preview
            FROM articles
            WHERE id <= 10
            ORDER BY id
        """))
        
        print(f"\n📰 Sample of Fixed Articles:")
        print(f"   {'ID':<6} {'Source':<15} {'Published':<20} {'Hash (first 20 chars)':<25} {'Text Preview'}")
        print(f"   {'-'*6} {'-'*15} {'-'*20} {'-'*25} {'-'*50}")
        
        for row in result.fetchall():
            article_id = row[0]
            source = (row[1][:13] + "..") if len(row[1]) > 15 else row[1]
            published = str(row[2])[:19] if row[2] else "NULL"
            hash_preview = row[3] if row[3] else "NULL"
            text_preview = row[4][:50] + "..." if row[4] else "NULL"
            
            print(f"   {article_id:<6} {source:<15} {published:<20} {hash_preview:<25} {text_preview}")
        
        print(f"\n{'='*70}")
        print(f"✅ ALL ARTICLES FIXED!")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(fix_null_fields())
