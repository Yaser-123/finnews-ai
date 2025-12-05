"""Check actual article count in database"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text

async def main():
    # Initialize database
    init_db()
    session = await get_session()
    
    # Get total articles
    result = await session.execute(sql_text("SELECT COUNT(*) as total FROM articles"))
    total = result.fetchone()[0]
    
    # Get articles by source
    result = await session.execute(sql_text("""
        SELECT source, COUNT(*) as count
        FROM articles
        GROUP BY source
        ORDER BY count DESC
    """))
    sources = result.fetchall()
    
    # Get ID range
    result = await session.execute(sql_text(
        "SELECT MIN(id) as min_id, MAX(id) as max_id FROM articles"
    ))
    id_range = result.fetchone()
    
    # Get metadata coverage
    result = await session.execute(sql_text("""
        SELECT 
            COUNT(*) as total,
            COUNT(source) as has_source,
            COUNT(published_at) as has_published,
            COUNT(hash) as has_hash
        FROM articles
    """))
    metadata = result.fetchone()
    
    print(f"\n{'='*60}")
    print(f"TOTAL ARTICLES IN DATABASE: {total}")
    print(f"{'='*60}\n")
    
    print("Articles by Source:")
    print(f"{'Source':<50} {'Count':>10}")
    print("-" * 60)
    for row in sources:
        source = row[0][:47] + "..." if len(row[0]) > 50 else row[0]
        print(f"{source:<50} {row[1]:>10}")
    
    print(f"\n{'='*60}")
    print(f"ID Range: {id_range[0]} to {id_range[1]}")
    print(f"{'='*60}")
    
    print(f"\nMetadata Coverage:")
    print(f"  Source:        {metadata[1]}/{metadata[0]} ({metadata[1]*100//metadata[0]}%)")
    print(f"  Published At:  {metadata[2]}/{metadata[0]} ({metadata[2]*100//metadata[0]}%)")
    print(f"  Hash:          {metadata[3]}/{metadata[0]} ({metadata[3]*100//metadata[0]}%)")

if __name__ == "__main__":
    asyncio.run(main())
