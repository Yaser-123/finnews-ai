"""
Process the complete test article through the entity extraction pipeline
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_session, init_db
from database.schema import Article
from sqlalchemy import select
from agents.entity.agent import EntityAgent

async def test_complete_article():
    init_db()
    
    # Get the complete article from database
    session = await get_session()
    try:
        result = await session.execute(
            select(Article).where(Article.id == 26)
        )
        article = result.scalar_one_or_none()
        
        if not article:
            print("❌ Article not found")
            return
        
        print("="*70)
        print("TESTING COMPLETE ARTICLE ENTITY EXTRACTION")
        print("="*70)
        print(f"\nArticle ID: {article.id}")
        print(f"Text length: {len(article.text)} characters")
        print(f"\nFirst 200 chars:")
        print(article.text[:200])
        print("...")
        
        # Extract entities using the EntityAgent
        entity_agent = EntityAgent()
        entities = entity_agent.extract_entities(article.text)
        
        print("\n" + "="*70)
        print("EXTRACTED ENTITIES")
        print("="*70)
        
        print(f"\n✅ Companies ({len(entities['companies'])}):")
        for company in entities['companies']:
            print(f"   - {company}")
        
        print(f"\n✅ Sectors ({len(entities['sectors'])}):")
        for sector in entities['sectors']:
            print(f"   - {sector}")
        
        print(f"\n✅ Regulators ({len(entities['regulators'])}):")
        for regulator in entities['regulators']:
            print(f"   - {regulator}")
        
        print(f"\n✅ Events ({len(entities['events'])}):")
        for event in entities['events']:
            print(f"   - {event}")
        
        print(f"\n✅ Dates ({len(entities['dates'])}):")
        for date in entities['dates']:
            print(f"   - {date}")
        
        print("\n" + "="*70)
        print("ENTITY EXTRACTION TEST COMPLETE")
        print("="*70)
        
        # Count non-empty categories
        non_empty = sum(1 for v in [entities['companies'], entities['sectors'], 
                                     entities['regulators'], entities['events']] 
                       if len(v) > 0)
        
        print(f"\n🎯 Result: {non_empty}/4 entity categories populated")
        if non_empty == 4:
            print("✅ PERFECT! All entity types extracted successfully!")
        
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(test_complete_article())
