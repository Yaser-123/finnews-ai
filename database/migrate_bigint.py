"""
Migration script to change articles.id from INTEGER to BIGINT.
This is required for real-time ingestion which uses large hash-based IDs.

Run this script ONCE before using the real-time ingestion feature.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate():
    """Migrate articles.id from INTEGER to BIGINT."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("   Please set DATABASE_URL in .env file with your Neon connection string")
        return
    
    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Check if articles table exists
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'articles')"
        )
        
        if not table_exists:
            print("⏭️  Articles table doesn't exist yet - no migration needed")
            return
        
        # Check current id type
        id_type = await conn.fetchval(
            """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'articles' AND column_name = 'id'
            """
        )
        
        print(f"📊 Current articles.id type: {id_type}")
        
        if id_type == 'bigint':
            print("✅ Articles.id is already BIGINT - no migration needed")
            return
        
        print("🔄 Starting migration...")
        
        # Start transaction
        async with conn.transaction():
            # Backup articles table
            print("  1. Creating backup table...")
            await conn.execute("CREATE TABLE articles_backup AS SELECT * FROM articles")
            
            # Drop dependent tables (they reference articles.id)
            print("  2. Dropping dependent tables...")
            await conn.execute("DROP TABLE IF EXISTS sentiment CASCADE")
            await conn.execute("DROP TABLE IF EXISTS entities CASCADE")
            await conn.execute("DROP TABLE IF EXISTS dedup_clusters CASCADE")
            
            # Drop and recreate articles table
            print("  3. Dropping articles table...")
            await conn.execute("DROP TABLE articles CASCADE")
            
            print("  4. Creating new articles table with BIGINT id...")
            await conn.execute("""
                CREATE TABLE articles (
                    id BIGINT PRIMARY KEY,
                    text TEXT NOT NULL,
                    source TEXT,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            # Restore data
            print("  5. Restoring article data...")
            await conn.execute("""
                INSERT INTO articles (id, text, source, published_at, created_at)
                SELECT id, text, source, published_at, created_at FROM articles_backup
            """)
            count = await conn.fetchval("SELECT COUNT(*) FROM articles")
            print(f"     ✅ Restored {count} articles")
            
            # Recreate dependent tables
            print("  6. Recreating dependent tables...")
            
            await conn.execute("""
                CREATE TABLE dedup_clusters (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL,
                    cluster_main_id INTEGER,
                    merged_ids INTEGER[],
                    similarity_score FLOAT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE entities (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL,
                    companies TEXT[],
                    sectors TEXT[],
                    regulators TEXT[],
                    people TEXT[],
                    events TEXT[],
                    stocks JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE sentiment (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    score FLOAT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """)
            
            # Drop backup table
            print("  7. Cleaning up backup table...")
            await conn.execute("DROP TABLE articles_backup")
        
        print("✅ Migration completed successfully!")
        print("\n📝 Summary:")
        print(f"   - Changed articles.id from {id_type.upper()} to BIGINT")
        print(f"   - Preserved {count} existing articles")
        print("   - Recreated dependent tables (dedup_clusters, entities, sentiment)")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n💡 If migration fails, you can:")
        print("   1. Drop all tables: DROP TABLE articles, dedup_clusters, entities, sentiment, query_logs CASCADE")
        print("   2. Restart the app to recreate tables with correct schema")
        raise
    
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    asyncio.run(migrate())
