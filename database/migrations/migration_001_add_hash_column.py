"""
Migration: Add hash column to articles table with unique constraint.

This migration is idempotent and safe for production use with Neon PostgreSQL.
It adds:
1. hash column (VARCHAR, nullable)
2. Index on hash for fast lookups
3. Unique constraint for content deduplication

Run automatically on application startup via database/db.py
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def run_migration(engine: AsyncEngine) -> bool:
    """
    Add hash column to articles table with index and unique constraint.
    
    This migration is idempotent - it can be run multiple times safely.
    It checks for existing column/index/constraint before attempting to add them.
    
    Args:
        engine: Async SQLAlchemy engine
        
    Returns:
        True if migration succeeded, False otherwise
    """
    try:
        logger.info("🔄 Running migration: 001_add_hash_column")
        
        async with engine.begin() as conn:
            # Step 1: Check if hash column exists
            logger.info("   Step 1/4: Checking if hash column exists...")
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'articles' 
                AND column_name = 'hash'
            """))
            
            hash_column_exists = result.fetchone() is not None
            
            if hash_column_exists:
                logger.info("   ✓ hash column already exists")
            else:
                logger.info("   → Adding hash column...")
                await conn.execute(text("""
                    ALTER TABLE articles 
                    ADD COLUMN hash VARCHAR
                """))
                logger.info("   ✓ hash column added successfully")
            
            # Step 2: Check if index exists
            logger.info("   Step 2/4: Checking if hash index exists...")
            result = await conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND tablename = 'articles' 
                AND indexname = 'ix_articles_hash'
            """))
            
            index_exists = result.fetchone() is not None
            
            if index_exists:
                logger.info("   ✓ hash index already exists")
            else:
                logger.info("   → Creating index on hash column...")
                # Use IF NOT EXISTS for safe idempotent creation
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_articles_hash 
                    ON articles(hash)
                """))
                logger.info("   ✓ hash index created successfully")
            
            # Step 3: Check if unique constraint exists
            logger.info("   Step 3/4: Checking if unique constraint exists...")
            result = await conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_schema = 'public'
                AND table_name = 'articles' 
                AND constraint_name = 'uq_article_hash'
                AND constraint_type = 'UNIQUE'
            """))
            
            constraint_exists = result.fetchone() is not None
            
            if constraint_exists:
                logger.info("   ✓ unique constraint already exists")
            else:
                logger.info("   → Adding unique constraint on hash...")
                await conn.execute(text("""
                    ALTER TABLE articles 
                    ADD CONSTRAINT uq_article_hash UNIQUE (hash)
                """))
                logger.info("   ✓ unique constraint added successfully")
            
            # Step 4: Verify migration
            logger.info("   Step 4/4: Verifying migration...")
            result = await conn.execute(text("""
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    (SELECT COUNT(*) FROM pg_indexes 
                     WHERE tablename = 'articles' AND indexname = 'ix_articles_hash') as has_index,
                    (SELECT COUNT(*) FROM information_schema.table_constraints 
                     WHERE table_name = 'articles' AND constraint_name = 'uq_article_hash') as has_constraint
                FROM information_schema.columns c
                WHERE c.table_schema = 'public'
                AND c.table_name = 'articles' 
                AND c.column_name = 'hash'
            """))
            
            verification = result.fetchone()
            
            if verification:
                logger.info("   ✓ Migration verified:")
                logger.info(f"      - Column: hash ({verification[1]}, nullable={verification[2]})")
                logger.info(f"      - Index: {'✓' if verification[3] > 0 else '✗'}")
                logger.info(f"      - Unique constraint: {'✓' if verification[4] > 0 else '✗'}")
            else:
                logger.warning("   ⚠ Could not verify hash column after migration")
                return False
        
        logger.info("✅ Migration 001_add_hash_column completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ Migration 001_add_hash_column failed: {e}")
        logger.exception(e)
        return False


async def rollback_migration(engine: AsyncEngine) -> bool:
    """
    Rollback migration by removing hash column and related constraints.
    
    WARNING: This will delete all hash values from the database.
    Only use this for rollback purposes.
    
    Args:
        engine: Async SQLAlchemy engine
        
    Returns:
        True if rollback succeeded, False otherwise
    """
    try:
        logger.warning("🔄 Rolling back migration: 001_add_hash_column")
        
        async with engine.begin() as conn:
            # Drop unique constraint
            logger.info("   → Dropping unique constraint...")
            await conn.execute(text("""
                ALTER TABLE articles 
                DROP CONSTRAINT IF EXISTS uq_article_hash
            """))
            logger.info("   ✓ Unique constraint dropped")
            
            # Drop index
            logger.info("   → Dropping index...")
            await conn.execute(text("""
                DROP INDEX IF EXISTS ix_articles_hash
            """))
            logger.info("   ✓ Index dropped")
            
            # Drop column
            logger.info("   → Dropping hash column...")
            await conn.execute(text("""
                ALTER TABLE articles 
                DROP COLUMN IF EXISTS hash
            """))
            logger.info("   ✓ hash column dropped")
        
        logger.info("✅ Rollback completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    """
    Standalone migration script for manual execution.
    """
    import asyncio
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from database.db import get_engine
    from config import settings
    
    async def main():
        print("=" * 70)
        print("MANUAL MIGRATION: 001_add_hash_column")
        print("=" * 70)
        print(f"\nDatabase: {settings.DATABASE_URL[:50]}...")
        print("\nThis will add:")
        print("  1. hash column (VARCHAR, nullable)")
        print("  2. Index on hash column")
        print("  3. Unique constraint on hash")
        print("\n" + "=" * 70)
        
        # Get confirmation
        response = input("\nProceed with migration? (yes/no): ").strip().lower()
        
        if response != "yes":
            print("❌ Migration cancelled")
            return 1
        
        # Run migration
        engine = get_engine()
        success = await run_migration(engine)
        
        await engine.dispose()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("  1. Restart your application")
            print("  2. New articles will automatically get hash values")
            print("  3. Monitor logs for deduplication metrics")
            return 0
        else:
            print("\n❌ Migration failed! Check logs for details.")
            return 1
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
