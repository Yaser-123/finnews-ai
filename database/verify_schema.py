"""
Verify database schema after migration.
Checks if articles.id is BIGINT and all tables exist.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def verify_schema():
    """Verify database schema."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        print("\n📊 Checking schema...\n")
        
        # Expected tables
        expected_tables = ['articles', 'dedup_clusters', 'entities', 'sentiment', 'query_logs']
        
        # Check each table
        for table_name in expected_tables:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            
            status = "✅" if exists else "❌"
            print(f"{status} Table '{table_name}': {'EXISTS' if exists else 'MISSING'}")
            
            if exists and table_name == 'articles':
                # Check articles.id type
                id_type = await conn.fetchval(
                    """
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'articles' AND column_name = 'id'
                    """
                )
                
                if id_type == 'bigint':
                    print(f"   ✅ articles.id type: {id_type.upper()} (correct)")
                else:
                    print(f"   ❌ articles.id type: {id_type.upper()} (expected BIGINT)")
                    print("      Run migration: python database/migrate_bigint.py")
                
                # Check autoincrement status
                is_identity = await conn.fetchval(
                    """
                    SELECT is_identity 
                    FROM information_schema.columns 
                    WHERE table_name = 'articles' AND column_name = 'id'
                    """
                )
                
                print(f"   ℹ️  articles.id autoincrement: {is_identity}")
        
        # Count records
        print("\n📊 Record counts:")
        for table_name in expected_tables:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"   {table_name}: {count} records")
        
        print("\n✅ Schema verification complete!")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise
    
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(verify_schema())
