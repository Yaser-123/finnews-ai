"""
Drop all database tables.
WARNING: This will delete ALL data in the database!

Use this script to:
1. Reset the database for fresh start
2. Clean up before schema migration
3. Recover from migration errors

Tables will be automatically recreated on next app startup.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def drop_tables():
    """Drop all tables from the database."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please set DATABASE_URL in .env file")
        return
    
    # Confirm action
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("\nTables to be dropped:")
    print("  - articles")
    print("  - dedup_clusters")
    print("  - entities")
    print("  - sentiment")
    print("  - query_logs")
    
    response = input("\nAre you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return
    
    print("\n🔄 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        tables = ['sentiment', 'entities', 'dedup_clusters', 'query_logs', 'articles']
        
        print("🔄 Dropping tables...")
        for table in tables:
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"   ✅ Dropped {table}")
            except Exception as e:
                print(f"   ⚠️  Failed to drop {table}: {e}")
        
        print("\n✅ All tables dropped successfully!")
        print("\n📝 Next steps:")
        print("   1. Tables will be recreated automatically on next app startup")
        print("   2. Or run: python database/db.py to manually create tables")
        
    except Exception as e:
        print(f"❌ Failed to drop tables: {e}")
        raise
    
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(drop_tables())
