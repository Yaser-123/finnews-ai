"""
Fix PostgreSQL sequence for articles table ID auto-increment
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def fix_sequence():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get current max ID
        max_id = await conn.fetchval('SELECT COALESCE(MAX(id), 0) FROM articles')
        print(f"Current max ID in table: {max_id}")
        
        # Reset sequence to max_id + 1
        new_seq = await conn.fetchval(
            "SELECT setval('articles_id_seq', $1, true)",
            max_id
        )
        print(f"✅ Sequence reset to: {new_seq}")
        print(f"Next auto-generated ID will be: {new_seq + 1}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_sequence())
