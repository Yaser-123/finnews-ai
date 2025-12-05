"""
Verify entity extraction and ChromaDB indexing after pipeline run
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session
from sqlalchemy import text as sql_text
from vector_store.chroma_db import get_or_create_collection

async def verify_pipeline_results():
    print("\n" + "="*70)
    print("✅ STEP 3: ENTITY EXTRACTION & INDEXING VERIFICATION")
    print("="*70)
    
    # Initialize database
    init_db()
    
    session = await get_session()
    
    async with session:
        # Check articles
        result = await session.execute(sql_text("SELECT COUNT(*) FROM articles"))
        total_articles = result.scalar()
        
        # Check entities
        result = await session.execute(sql_text("SELECT COUNT(*) FROM entities"))
        total_entities = result.scalar()
        
        # Check sentiment
        result = await session.execute(sql_text("SELECT COUNT(*) FROM sentiment"))
        total_sentiment = result.scalar()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total articles: {total_articles}")
        print(f"   Articles with entities extracted: {total_entities}")
        print(f"   Articles with sentiment analyzed: {total_sentiment}")
        print(f"   Coverage: {total_entities/total_articles*100:.1f}% entities, {total_sentiment/total_articles*100:.1f}% sentiment")
        
        # Show sample entities
        result = await session.execute(sql_text("""
            SELECT 
                a.id,
                LEFT(a.text, 60) as text_preview,
                e.companies,
                e.sectors,
                e.regulators,
                e.events,
                s.label as sentiment,
                s.score as sentiment_score
            FROM articles a
            LEFT JOIN entities e ON a.id = e.article_id
            LEFT JOIN sentiment s ON a.id = s.article_id
            WHERE e.id IS NOT NULL
            ORDER BY a.id
            LIMIT 15
        """))
        
        print(f"\n📰 Sample Articles with Extracted Entities:")
        print(f"   {'ID':<6} {'Preview':<45} {'Companies':<15} {'Sectors':<15} {'Sentiment'}")
        print(f"   {'-'*6} {'-'*45} {'-'*15} {'-'*15} {'-'*20}")
        
        for row in result.fetchall():
            article_id = row[0]
            preview = row[1][:43] + "..." if row[1] else "N/A"
            companies = str(len(row[2])) + " cos" if row[2] else "0"
            sectors = str(len(row[3])) + " sec" if row[3] else "0"
            sentiment = f"{row[6]} ({row[7]:.2f})" if row[6] else "N/A"
            
            print(f"   {article_id:<6} {preview:<45} {companies:<15} {sectors:<15} {sentiment}")
    
    # Check ChromaDB
    print(f"\n📦 ChromaDB Vector Store:")
    try:
        collection = get_or_create_collection()
        count = collection.count()
        print(f"   Total indexed articles: {count}")
        
        # Get a sample
        if count > 0:
            results = collection.get(limit=3, include=["metadatas"])
            print(f"\n   Sample indexed articles (first 3):")
            for i, metadata in enumerate(results['metadatas'], 1):
                article_id = metadata.get('article_id', 'N/A')
                companies = metadata.get('companies', '[]')
                sectors = metadata.get('sectors', '[]')
                print(f"      {i}. ID {article_id}: {companies[:50]}...")
    except Exception as e:
        print(f"   ❌ Error accessing ChromaDB: {str(e)}")
    
    print(f"\n{'='*70}")
    print(f"✅ STEP 3 VERIFICATION COMPLETE!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    asyncio.run(verify_pipeline_results())
