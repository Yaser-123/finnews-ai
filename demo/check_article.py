"""Check if complete article exists in database"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_session, init_db
from database.schema import Article
from sqlalchemy import select

async def check():
    init_db()
    session = await get_session()
    try:
        result = await session.execute(
            select(Article).where(Article.source == 'test_complete')
        )
        article = result.scalar_one_or_none()
        if article:
            print(f'✅ Found article ID: {article.id}')
            print(f'Text length: {len(article.text)}')
            print(f'Preview: {article.text[:200]}...')
        else:
            print('❌ Article not found in database')
    finally:
        await session.close()

asyncio.run(check())
