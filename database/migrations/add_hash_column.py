"""
Database migration script to add hash column to articles table.

This migration adds:
1. hash column (String, nullable, indexed)
2. Unique constraint on hash for deduplication

Run this script after deploying the code changes.

Usage:
    python database/migrations/add_hash_column.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from database.db import get_engine
from config import settings


async def add_hash_column():
    """
    Add hash column to articles table with unique constraint.
    
    This is a safe migration that:
    - Adds nullable hash column (won't break existing data)
    - Adds index on hash for fast lookups
    - Adds unique constraint on hash for deduplication
    """
    engine = get_engine()
    
    print("=" * 70)
    print("DATABASE MIGRATION: Add hash column to articles")
    print("=" * 70)
    print(f"\nConnecting to: {settings.DATABASE_URL[:50]}...")
    
    async with engine.begin() as conn:
        # Check if hash column already exists
        print("\n1. Checking if hash column exists...")
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'articles' 
            AND column_name = 'hash'
        """))
        
        existing_hash = result.fetchone()
        
        if existing_hash:
            print("   ℹ️  hash column already exists")
        else:
            print("   ➕ Adding hash column...")
            await conn.execute(text("""
                ALTER TABLE articles 
                ADD COLUMN hash VARCHAR
            """))
            print("   ✅ hash column added")
        
        # Check if index exists
        print("\n2. Checking if hash index exists...")
        result = await conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'articles' 
            AND indexname = 'ix_articles_hash'
        """))
        
        existing_index = result.fetchone()
        
        if existing_index:
            print("   ℹ️  hash index already exists")
        else:
            print("   📊 Creating index on hash column...")
            await conn.execute(text("""
                CREATE INDEX ix_articles_hash ON articles(hash)
            """))
            print("   ✅ hash index created")
        
        # Check if unique constraint exists
        print("\n3. Checking if unique constraint exists...")
        result = await conn.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'articles' 
            AND constraint_name = 'uq_article_hash'
        """))
        
        existing_constraint = result.fetchone()
        
        if existing_constraint:
            print("   ℹ️  unique constraint already exists")
        else:
            print("   🔒 Adding unique constraint on hash...")
            await conn.execute(text("""
                ALTER TABLE articles 
                ADD CONSTRAINT uq_article_hash UNIQUE (hash)
            """))
            print("   ✅ unique constraint added")
        
        # Verify migration
        print("\n4. Verifying migration...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'articles' 
            AND column_name = 'hash'
        """))
        
        hash_col = result.fetchone()
        if hash_col:
            print(f"   ✅ hash column verified:")
            print(f"      Type: {hash_col[1]}")
            print(f"      Nullable: {hash_col[2]}")
        else:
            print("   ❌ hash column not found after migration")
            return False
    
    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE ✅")
    print("=" * 70)
    print("\nThe articles table now has:")
    print("  - hash column (VARCHAR, nullable, indexed)")
    print("  - Unique constraint on hash for deduplication")
    print("\nExisting articles will have NULL hash values.")
    print("New articles will automatically get hash values from ingestion.")
    
    return True


async def main():
    """Run migration."""
    try:
        success = await add_hash_column()
        
        if success:
            print("\n✅ Migration successful!")
            print("\nNext steps:")
            print("1. Restart the application")
            print("2. Run ingestion to populate hash values for new articles")
            print("3. Monitor logs for deduplication metrics")
            return 0
        else:
            print("\n❌ Migration failed!")
            return 1
    
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
