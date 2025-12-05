"""
Show full LTIMindtree article content
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text

async def show_article():
    init_db()
    session = await get_session()
    
    async with session:
        result = await session.execute(sql_text("""
            SELECT id, text, source, published_at
            FROM articles
            WHERE id = 35
        """))
        
        row = result.fetchone()
        
        if row:
            print(f"\n{'='*70}")
            print(f"ARTICLE ID: {row[0]}")
            print(f"{'='*70}")
            print(f"Published: {row[3]}")
            print(f"Source: {row[2]}")
            print(f"\nText ({len(row[1])} characters):")
            print(f"{'='*70}")
            print(row[1])
            print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(show_article())
