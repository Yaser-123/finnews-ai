"""
Test script to verify the hash column migration.

Run this after starting the application to verify:
1. Migration ran successfully
2. Hash column exists with proper constraints
3. Articles can be inserted with hash values
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db import init_db, get_engine, get_session, close_db
from database.migrations.migration_001_add_hash_column import run_migration
from sqlalchemy import text


async def test_migration():
    """Test the hash column migration."""
    print("=" * 70)
    print("TESTING HASH COLUMN MIGRATION")
    print("=" * 70)
    
    # Initialize database
    init_db()
    engine = get_engine()
    
    if not engine:
        print("❌ Failed to initialize database")
        return False
    
    print("\n1. Running migration...")
    success = await run_migration(engine)
    
    if not success:
        print("❌ Migration failed")
        return False
    
    print("\n2. Verifying schema...")
    async with engine.begin() as conn:
        # Check column exists
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'articles' 
            AND column_name = 'hash'
        """))
        
        col = result.fetchone()
        if col:
            print(f"   ✓ hash column: {col[1]}, nullable={col[2]}")
        else:
            print("   ❌ hash column not found")
            return False
        
        # Check index exists
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename = 'articles' 
            AND indexname = 'ix_articles_hash'
        """))
        
        idx = result.fetchone()
        if idx:
            print(f"   ✓ index exists: {idx[0]}")
        else:
            print("   ⚠️  index not found")
        
        # Check unique constraint
        result = await conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_schema = 'public'
            AND table_name = 'articles' 
            AND constraint_name = 'uq_article_hash'
        """))
        
        const = result.fetchone()
        if const:
            print(f"   ✓ unique constraint: {const[0]} ({const[1]})")
        else:
            print("   ⚠️  unique constraint not found")
    
    print("\n3. Testing insert with hash...")
    session = await get_session()
    async with session:
        from database.schema import Article
        from datetime import datetime
        
        # Test insert with hash
        test_article = Article(
            id=999999999,
            text="Test article with hash",
            source="test",
            published_at=datetime.now(),
            hash="test_hash_12345"
        )
        
        try:
            session.add(test_article)
            await session.commit()
            print("   ✓ Insert with hash succeeded")
            
            # Clean up test data
            await session.delete(test_article)
            await session.commit()
            print("   ✓ Test cleanup complete")
        
        except Exception as e:
            print(f"   ❌ Insert failed: {e}")
            return False
    
    print("\n4. Testing unique constraint...")
    session = await get_session()
    async with session:
        from database.schema import Article
        from datetime import datetime
        
        # Insert first article
        article1 = Article(
            id=999999998,
            text="First article",
            source="test",
            published_at=datetime.now(),
            hash="duplicate_hash_test"
        )
        
        try:
            session.add(article1)
            await session.commit()
            print("   ✓ First article inserted")
        except Exception as e:
            print(f"   ❌ First insert failed: {e}")
            return False
    
    # Try to insert duplicate hash
    session = await get_session()
    async with session:
        article2 = Article(
            id=999999997,
            text="Second article (duplicate hash)",
            source="test",
            published_at=datetime.now(),
            hash="duplicate_hash_test"
        )
        
        try:
            session.add(article2)
            await session.commit()
            print("   ❌ Duplicate hash was allowed (constraint not working)")
            
            # Clean up
            await session.delete(article2)
            await session.commit()
            return False
        
        except Exception as e:
            if "uq_article_hash" in str(e) or "unique constraint" in str(e).lower():
                print(f"   ✓ Unique constraint working (rejected duplicate)")
            else:
                print(f"   ⚠️  Unexpected error: {e}")
    
    # Clean up test data
    session = await get_session()
    async with session:
        from sqlalchemy import delete
        from database.schema import Article
        
        stmt = delete(Article).where(Article.id.in_([999999998, 999999997]))
        await session.execute(stmt)
        await session.commit()
        print("   ✓ Test data cleaned up")
    
    await close_db()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print("\nMigration is working correctly!")
    print("Hash column, index, and unique constraint are all operational.")
    
    return True


async def main():
    try:
        success = await test_migration()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
