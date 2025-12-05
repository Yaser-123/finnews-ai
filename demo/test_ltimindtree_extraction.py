"""
Test entity extraction for LTIMindtree article
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text
from agents.entity.agent import EntityAgent

async def test_ltimindtree_extraction():
    print("\n" + "="*70)
    print("🧪 TESTING ENTITY EXTRACTION FOR LTIMINDTREE ARTICLE")
    print("="*70)
    
    init_db()
    session = await get_session()
    
    # Get the article
    async with session:
        result = await session.execute(sql_text("""
            SELECT id, text
            FROM articles
            WHERE LOWER(text) LIKE '%ltimindtree%'
            LIMIT 1
        """))
        
        article = result.fetchone()
        
        if not article:
            print("\n❌ Article not found!")
            return
        
        article_id, text = article
        
        print(f"\n📰 Article ID: {article_id}")
        print(f"📝 Text: {text[:200]}...")
        
        # Test entity extraction
        print(f"\n🔍 Running entity extraction...")
        entity_agent = EntityAgent()
        entities = entity_agent.extract_entities(text)
        
        print(f"\n✅ EXTRACTION RESULTS:")
        print(f"\n🏢 Companies ({len(entities.get('companies', []))}):")
        for company in entities.get('companies', [])[:10]:
            print(f"   • {company}")
        
        print(f"\n🏭 Sectors ({len(entities.get('sectors', []))}):")
        for sector in entities.get('sectors', [])[:10]:
            print(f"   • {sector}")
        
        print(f"\n🏛️  Regulators ({len(entities.get('regulators', []))}):")
        for regulator in entities.get('regulators', [])[:10]:
            print(f"   • {regulator}")
        
        print(f"\n📅 Events ({len(entities.get('events', []))}):")
        for event in entities.get('events', [])[:10]:
            print(f"   • {event}")
        
        # Check if already in database
        result = await session.execute(sql_text("""
            SELECT companies, sectors, regulators, events
            FROM entities
            WHERE article_id = :article_id
        """), {"article_id": article_id})
        
        db_entities = result.fetchone()
        
        if db_entities:
            print(f"\n📊 STORED IN DATABASE:")
            print(f"   Companies: {len(db_entities[0]) if db_entities[0] else 0}")
            print(f"   Sectors: {len(db_entities[1]) if db_entities[1] else 0}")
            print(f"   Regulators: {len(db_entities[2]) if db_entities[2] else 0}")
            print(f"   Events: {len(db_entities[3]) if db_entities[3] else 0}")
        else:
            print(f"\n⚠️  NOT YET STORED IN DATABASE")
            print(f"   Run pipeline to save these entities")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(test_ltimindtree_extraction())
